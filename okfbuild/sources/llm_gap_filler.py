"""Wraps llm-backend-eee to fill a morphology gap the rule-based EEE engine
and the corpus sources (Morpheus, the Byzantine lexicon, Wiktextract) leave
empty.

fill_gap() is a plain, directly-callable function -- NOT wired through
eee_project's own set_chain()/post_hook dispatch machinery. The pipeline's
actual call path (inflect_slot()) bypasses chains and hooks entirely, so
that machinery cannot reach it. Deciding WHEN to call fill_gap() -- only on
a clean empty rule-based result, never when the rule-based call raises -- is
the caller's responsibility (see okfbuild/sources/eee_engine.py), not this
module's.
"""

import json
import logging
import os
import unicodedata
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import asdict, dataclass, field, replace
from enum import Enum, auto
from functools import cache
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from llm_backend_eee import LLMBackend

logger = logging.getLogger(__name__)

_DEFAULT_CALL_TIMEOUT_SECONDS = 30.0
_CACHE_FORMAT_VERSION = 1

REQUEST_BUDGET_ERROR = "GapFiller exceeded its configured max_requests_per_run budget"


def _installed_llm_backend_version() -> str:
    try:
        return version("llm-backend-eee")
    except PackageNotFoundError:
        return "unknown"


_LLM_BACKEND_VERSION = _installed_llm_backend_version()


@dataclass(frozen=True)
class LLMModelConfig:
    """One selectable LLM backend option -- name is the caller-facing
    selector key; the rest map directly onto llm-backend-eee's own
    LLMBackend(model=, base_url=, api_key=) constructor.

    api_key_env is REQUIRED, not defaulted -- a default value here (e.g.
    "OPENAI_API_KEY") is a real footgun once two models from different
    providers are configured together (OpenAI + Anthropic + local Ollama,
    say): both would silently try to read the same env var. Every model
    config must name its own key's env var explicitly."""

    name: str
    model: str
    api_key_env: str
    # TODO: base_url is caller-supplied and never validated against an allowlist --
    # SSRF hardening is a deliberate, deferred non-goal that must be revisited before
    # use in any automated/multi-user context (a human configures this today).
    base_url: str | None = None


@dataclass(frozen=True)
class GapFillerConfig:
    """Caller-supplied gap-filler configuration. Threading a GapFillerConfig
    into SourceBundle/build() is what opts a run into LLM gap-filling at
    all -- its absence (None, the default) leaves today's behavior
    completely unchanged. Constructing one at all requires a non-empty,
    fully-specified `models` list (each entry needing its own real
    api_key_env) -- there is no way to end up with live network calls by
    accident; a separate `enabled` boolean was considered and rejected as
    redundant with this.

    models: the configured set of usable LLM backends. Must be non-empty
        and have unique names -- __post_init__ raises ValueError
        otherwise, so a misconfiguration fails fast at construction time.
    samples_per_model: how many independent calls to make to EACH
        configured model per gap (total calls per gap = len(models) *
        samples_per_model). Deliberately not a single blended
        `sample_count` cycling round-robin through `models` -- that would
        silently give models earlier in the list more "votes" than later
        ones whenever the count doesn't divide evenly. This form gives
        every configured model equal weight, always. Must be >= 1.
    max_requests_per_run: safety cap on total LLM calls issued across every
        fill_gap() call sharing one GapFillCache. See GapFillCache and
        fill_gap() for how the running count is tracked and enforced.
    """

    models: tuple[LLMModelConfig, ...]
    samples_per_model: int = 1
    max_requests_per_run: int = 1000

    def __post_init__(self) -> None:
        if not self.models:
            raise ValueError("GapFillerConfig.models cannot be empty")
        if len({m.name for m in self.models}) != len(self.models):
            raise ValueError("GapFillerConfig.models names must be unique")
        if self.samples_per_model < 1:
            raise ValueError("GapFillerConfig.samples_per_model must be >= 1")
        if self.max_requests_per_run < 1:
            raise ValueError("GapFillerConfig.max_requests_per_run must be >= 1")


class SampleStatus(Enum):
    """Distinguishes a genuine model response from an infrastructure
    failure -- these must never be logged/counted identically. A
    timeout tells you nothing about what the model would have said; an
    empty response is real information about the model's own behavior."""

    SUCCESS = auto()  # model returned a non-empty form set
    ABSTAINED = auto()  # model call succeeded, returned nothing
    CALL_FAILED = auto()  # timeout, network error, API error, or a missing/invalid API key


@dataclass(frozen=True)
class GapFillResult:
    """One filled (or not-filled) slot. `forms` is empty whenever this
    wasn't a clean, unanimous fill -- see fill_gap()'s docstring for the
    exact conditions; callers must check `forms` before treating this as
    a successful fill. `sample_statuses` preserves what actually happened
    per call, for logging/metrics -- do not collapse this back down to a
    single empty/non-empty bit."""

    forms: set[str]
    # e.g. "llm:gpt-4o-mini" -- names the model(s) REQUESTED for this call, not necessarily
    # the model that actually served it. Confirmed (OpenRouter's own API reference, and
    # llm-backend-eee v0.2.1's _openai.py: call_openai() reads only
    # resp.choices[0].message.content, never resp.model) that a routing/fallback provider
    # (e.g. OpenRouter) CAN silently substitute a different underlying model, and that
    # llm-backend-eee v0.2.1 has no mechanism to surface which model actually responded --
    # fixing this would require a change in that separate package, out of scope here.
    method: str
    llm_backend_version: str  # installed llm-backend-eee version, for reproducibility
    sample_statuses: tuple[SampleStatus, ...]


def normalize_form(form: str) -> str:
    """Canonicalize a form for agreement comparison (NOT for display --
    the original, un-normalized form is what gets stored/cited). Applied
    to every sample before comparing for agreement; raw string equality
    on polytonic Greek would make "agreement" nearly meaningless (Unicode
    NFC vs NFD, combining-diacritic order, and incidental whitespace can
    all vary between otherwise-identical forms)."""
    return unicodedata.normalize("NFC", form.strip())


def _encode_key_element(element: str | tuple | GapFillerConfig) -> dict:
    """Tags each cache-key tuple element with its type so load() can
    reconstruct it exactly. A key element is always one of these three
    shapes (see make_key()) -- this deliberately does not assume how many
    elements the key has or in what order, only what each element's own
    type can be."""
    if isinstance(element, GapFillerConfig):
        return {"type": "config", "value": _encode_config(element)}
    if isinstance(element, tuple):
        return {"type": "tuple", "value": [list(pair) for pair in element]}
    return {"type": "str", "value": element}


def _decode_key_element(encoded: dict) -> str | tuple | GapFillerConfig:
    kind = encoded["type"]
    if kind == "config":
        return _decode_config(encoded["value"])
    if kind == "tuple":
        return tuple(tuple(pair) for pair in encoded["value"])
    if kind == "str":
        return encoded["value"]
    raise ValueError(f"GapFillCache.load(): unknown cache key element type {kind!r}")


@cache
def load_versioned_json(path: Path, expected_version: int, label: str) -> dict:
    """Reads `path` as JSON, raising a clear, path-naming ValueError for
    either corrupt JSON or a format_version that doesn't match
    `expected_version` -- silently falling back to some default here
    would silently mask a real problem with the file, for any caller.
    `label` (e.g. "cache", "handoff") names the artifact kind in the
    error message, so two different callers' errors stay distinguishable
    without each hand-rolling this same parse-and-validate logic. Shared
    by GapFillCache.load() (below) and
    okfbuild.morpheus_crosscheck.crosscheck_handoff_file()."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"corrupt {label} file at {path}: {exc}") from exc

    format_version = data.get("format_version")
    if format_version != expected_version:
        raise ValueError(
            f"unsupported {label} format_version {format_version!r} at {path} (expected {expected_version})"
        )
    return data


def _encode_config(config: GapFillerConfig) -> dict:
    """Every GapFillerConfig/LLMModelConfig field is already a JSON-safe
    primitive (str/int/None or a tuple of such), so asdict() alone is
    sufficient -- no custom field-by-field handling needed. Memoized:
    every entry in one run shares the identical (frozen, hashable)
    config object, so re-deriving this dict from scratch on every save()
    -- potentially thousands of times across a long run's periodic
    checkpoints -- would be pure waste."""
    return asdict(config)


def _decode_config(data: dict) -> GapFillerConfig:
    """Reconstructs a REAL GapFillerConfig, not a plain dict -- because
    both dataclasses are frozen with structural equality/hashing, this
    reconstructed-but-not-identical instance still correctly compares
    equal to (and hashes the same as) whatever live GapFillerConfig a
    resumed run's caller constructs, as long as field values match. That
    equality is what makes a resumed run's cache hits actually work."""
    models = tuple(LLMModelConfig(**model) for model in data["models"])
    return GapFillerConfig(
        models=models, samples_per_model=data["samples_per_model"], max_requests_per_run=data["max_requests_per_run"]
    )


def _encode_result(result: GapFillResult) -> dict:
    return {
        "forms": sorted(result.forms),
        "method": result.method,
        "llm_backend_version": result.llm_backend_version,
        "sample_statuses": [status.name for status in result.sample_statuses],
    }


def _decode_result(data: dict) -> GapFillResult:
    return GapFillResult(
        forms=set(data["forms"]),
        method=data["method"],
        llm_backend_version=data["llm_backend_version"],
        sample_statuses=tuple(SampleStatus[name] for name in data["sample_statuses"]),
    )


@dataclass
class GapFillCache:
    """Run-local (in-process, single pipeline invocation) memoization,
    keyed by (lemma, a canonical/sorted serialization of features, pos,
    language, config identity, context string -- see make_key()). Prevents
    redundant LLM calls when the same gap recurs with the same context
    across courses/periods within one run. Also caches a "no result"
    outcome (disagreement/failure), not just successes, within the run --
    otherwise the same unfillable gap re-triggers the full call batch
    every time it recurs. Optional, run-scoped disk persistence (save()/
    load(), below) lets a caller resume an interrupted run without
    re-spending on already-resolved gaps -- see pipeline.run()'s
    gap_fill_cache_dir for the orchestration; this class itself has no
    opinion on *when* to persist, only how.

    Also tracks `request_count`, the running total of LLM calls issued
    through this cache -- see fill_gap()'s request-budget enforcement.

    NOT thread-safe: `_results` is a plain dict and `request_count` a
    plain int, neither guarded by a lock. Harmless today since
    pipeline.run()'s lexical-candidate loop is single-threaded; save()
    additionally assumes no concurrent set() call is mutating this
    instance while it serializes. A parallelized caller would need its
    own locking around both."""

    _results: dict[tuple, GapFillResult] = field(default_factory=dict)
    request_count: int = 0

    @staticmethod
    def make_key(
        lemma: str,
        features: dict[str, str],
        pos: str,
        language: str,
        config: GapFillerConfig,
        context: str = "",
    ) -> tuple:
        """GapFillerConfig and LLMModelConfig are frozen dataclasses with
        structural equality/hashing, so using `config` itself as part of
        the key is sufficient -- any field difference (models, sample
        count, budget) naturally produces a different key. `features` is
        sorted so insertion-order differences don't cause spurious cache
        misses. `context` (the slot/period/dialect/author string also sent
        to the LLM as the prompt's `label`) is part of the key too -- a
        query asked under different context must never be served from a
        differently-scoped cache hit."""
        feature_key = tuple(sorted(features.items()))
        return (lemma, feature_key, pos, language, config, context)

    def get(self, key: tuple) -> GapFillResult | None:
        """Returns a copy with its own `forms` set, not the stored instance
        -- GapFillResult.forms is plain mutable set[str] on an otherwise
        frozen dataclass, so handing back the same instance on every hit
        would let a caller's in-place mutation (e.g. `.discard(...)`)
        silently corrupt every future hit on this key."""
        result = self._results.get(key)
        if result is None:
            return None
        return replace(result, forms=set(result.forms))

    def set(self, key: tuple, result: GapFillResult) -> None:
        self._results[key] = result

    def __len__(self) -> int:
        """Current entry count -- lets a caller outside this module (e.g.
        pipeline.run()'s checkpoint-by-new-entries logic) observe cache
        growth without reaching into `_results` directly."""
        return len(self._results)

    def save(self, path: Path) -> None:
        """Atomically writes this cache to `path`: writes a `.tmp` sibling
        first, then os.replace()s it onto `path` -- a process killed
        mid-write leaves the previous good `path` untouched instead of a
        truncated, unparseable file. Entries whose sample_statuses are ALL
        CALL_FAILED are excluded from the written file (this in-memory
        instance is unaffected) -- persisting a transient infrastructure
        failure as a stable "already tried" result would wrongly block a
        legitimate retry on resume."""
        entries = [
            {"key": [_encode_key_element(element) for element in key], "result": _encode_result(result)}
            for key, result in self._results.items()
            if any(status is not SampleStatus.CALL_FAILED for status in result.sample_statuses)
        ]
        data = {"format_version": _CACHE_FORMAT_VERSION, "request_count": self.request_count, "entries": entries}

        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(path.name + ".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp_path, path)

    @staticmethod
    def load(path: Path) -> "GapFillCache":
        """A missing `path` means there is nothing to resume -- returns a
        fresh, empty GapFillCache, not an error. A `path` that exists but
        fails to parse as JSON, or parses but carries a format_version
        this code doesn't recognize, raises ValueError naming `path` --
        silently falling back to an empty cache here would silently
        re-spend on every gap that had already been resolved before
        whatever produced this file."""
        if not path.exists():
            return GapFillCache()

        data = load_versioned_json(path, _CACHE_FORMAT_VERSION, "cache")

        cache = GapFillCache(request_count=data["request_count"])
        for entry in data["entries"]:
            key = tuple(_decode_key_element(element) for element in entry["key"])
            cache._results[key] = _decode_result(entry["result"])
        return cache


def _call_one(
    model_config: LLMModelConfig,
    lemma: str,
    features: dict[str, str],
    pos: str,
    language: str,
    context: str,
) -> tuple[SampleStatus, set[str]]:
    """One sample call to one configured model. Never raises -- every
    failure mode (missing/invalid env var, network error, API error)
    is caught and reported as CALL_FAILED. `context` is passed through as
    llm-backend-eee's own `label` kwarg -- per its real source, this is
    appended to the actual prompt text as `slot="..."`, telling the model
    which grammatical slot/period/dialect/author it's being asked about,
    not just disambiguating the cache key."""
    try:
        api_key = os.environ.get(model_config.api_key_env)
        if api_key is None:
            raise RuntimeError(
                f"environment variable {model_config.api_key_env!r} "
                f"(for model {model_config.name!r}) is not set"
            )
        # use_cache=False: LLMBackend's own default is a *persistent*, on-disk
        # cache keyed only on (lemma, pos, language, features, model, ...) --
        # no per-sample nonce -- so with the default left on, every sample
        # past the first in a batch (and every future run) would silently
        # replay one cached string instead of an independent call, defeating
        # this module's whole agreement mechanism and reintroducing the
        # persistent cross-run caching GapFillCache deliberately does not
        # have (see GapFillCache's own docstring).
        backend = LLMBackend(
            model=model_config.model, api_key=api_key, base_url=model_config.base_url, use_cache=False
        )
        forms = backend.inflect(lemma, features, pos, language=language, label=context)
    except Exception:
        logger.debug(
            "gap-filler: call failed for model=%s lemma=%s pos=%s",
            model_config.name,
            lemma,
            pos,
            exc_info=True,
        )
        return SampleStatus.CALL_FAILED, set()

    if not forms:
        return SampleStatus.ABSTAINED, set()
    return SampleStatus.SUCCESS, forms


def _describe(lemma: str, features: dict[str, str], pos: str) -> str:
    feature_str = ", ".join(f"{k}={v}" for k, v in sorted(features.items()))
    return f"lemma={lemma!r} pos={pos!r} features={{{feature_str}}}"


def fill_gap(
    lemma: str,
    features: dict[str, str],
    pos: str,
    language: str,
    config: GapFillerConfig,
    cache: GapFillCache,
    context: str = "",
) -> GapFillResult:
    """Attempt to fill one morphology gap. `context` (e.g. a grammatical
    slot label, and when known, period/dialect/author/work) is forwarded
    to every sample call as llm-backend-eee's own `label` kwarg -- it
    reaches the real prompt text, not just the cache key below -- and is
    itself part of the cache key, so two calls differing only in context
    are never conflated. Checks `cache` first -- a cache
    hit returns immediately with zero LLM calls. On a miss, issues
    len(config.models) * config.samples_per_model independent calls to
    LLMBackend.inflect(lemma, features, pos, language=...), one batch per
    model. These calls are independent and are issued in parallel via a
    thread pool, not sequentially.

    Each call's outcome becomes one SampleStatus (SUCCESS/ABSTAINED/
    CALL_FAILED -- a call failure, including a missing/invalid API key or
    a timeout, is caught and recorded as CALL_FAILED, never conflated
    with a genuine ABSTAINED result). `forms` is the agreed set (via
    normalize_form()) only if the WHOLE batch is clean -- every single
    sample is SUCCESS (no ABSTAINED, no CALL_FAILED) -- AND every SUCCESS
    sample produced the identical normalized form set; otherwise forms is
    empty. A lone success alongside any failure/abstention is NOT
    accepted, even though the successful sample "agrees with itself" --
    unanimity means unanimous across the whole clean batch, not just
    among the samples that happened to succeed.

    A logged warning accompanies every non-accepted outcome, naming the
    lemma/pos/features and which SampleStatus mix produced it:
    disagreement among all-SUCCESS samples, an all-CALL_FAILED batch, an
    all-ABSTAINED batch, and any other mixed batch all log distinguishable
    messages -- never one generic "no forms" line. On a genuine result
    (unanimous, non-empty), the result is written to `cache` before
    returning; a non-result is cached too, so a recurring unfillable gap
    does not re-trigger the full call batch every time.

    Once `cache.request_count` would exceed `config.max_requests_per_run`,
    this raises RuntimeError(REQUEST_BUDGET_ERROR) instead of issuing any
    new calls -- a budget-exhausted run must fail loudly, not silently
    return an empty result indistinguishable from a real disagreement.
    """
    key = cache.make_key(lemma, features, pos, language, config, context)
    cached = cache.get(key)
    if cached is not None:
        return cached

    calls = [model_config for model_config in config.models for _ in range(config.samples_per_model)]

    if cache.request_count + len(calls) > config.max_requests_per_run:
        raise RuntimeError(REQUEST_BUDGET_ERROR)
    cache.request_count += len(calls)

    # Not a `with ThreadPoolExecutor(...) as executor:` block: __exit__ calls
    # shutdown(wait=True), which blocks until every submitted call actually
    # returns -- including one a wait() timeout below has already given up
    # on. Python cannot forcibly stop a thread stuck in a synchronous network
    # call, so the best available bound is to stop *waiting* on it and let it
    # finish in the background (shutdown(wait=False) in the finally below),
    # rather than let fill_gap() itself hang on a single stuck call.
    executor = ThreadPoolExecutor(max_workers=len(calls))
    try:
        futures = {
            executor.submit(_call_one, model_config, lemma, features, pos, language, context): model_config
            for model_config in calls
        }
        # A single wait() over the whole batch bounds fill_gap()'s total
        # wait to ~_DEFAULT_CALL_TIMEOUT_SECONDS regardless of how many
        # calls are in flight -- looping future.result(timeout=...) per
        # future would instead sum each call's timeout sequentially.
        done, not_done = wait(futures, timeout=_DEFAULT_CALL_TIMEOUT_SECONDS)

        outcomes: list[tuple[LLMModelConfig, SampleStatus, set[str]]] = []
        for future in done:
            model_config = futures[future]
            status, forms = future.result()  # already finished -- never blocks, never raises
            outcomes.append((model_config, status, forms))
        for future in not_done:
            model_config = futures[future]
            logger.debug(
                "gap-filler: call timed out for model=%s lemma=%s pos=%s",
                model_config.name,
                lemma,
                pos,
            )
            outcomes.append((model_config, SampleStatus.CALL_FAILED, set()))
    finally:
        executor.shutdown(wait=False)

    statuses = tuple(status for _, status, _ in outcomes)
    all_success = bool(statuses) and all(status is SampleStatus.SUCCESS for status in statuses)

    result_forms: set[str] = set()
    if all_success:
        normalized_sets = {frozenset(normalize_form(f) for f in forms) for _, _, forms in outcomes}
        if len(normalized_sets) == 1:
            result_forms = outcomes[0][2]

    method = "llm:" + ",".join(sorted({model_config.model for model_config in config.models}))
    result = GapFillResult(
        forms=result_forms,
        method=method,
        llm_backend_version=_LLM_BACKEND_VERSION,
        sample_statuses=statuses,
    )

    description = _describe(lemma, features, pos)
    if result_forms:
        logger.info("gap-filler: accepted %s (%s)", description, result_forms)
    else:
        failed_count = sum(1 for status in statuses if status is SampleStatus.CALL_FAILED)
        abstained_count = sum(1 for status in statuses if status is SampleStatus.ABSTAINED)
        if failed_count == len(statuses):
            logger.warning("gap-filler: all %d sample(s) failed to call for %s", failed_count, description)
        elif abstained_count == len(statuses):
            logger.warning(
                "gap-filler: all %d sample(s) abstained (empty result) for %s", abstained_count, description
            )
        elif all_success:
            logger.warning("gap-filler: samples disagreed on the form for %s", description)
        else:
            success_count = len(statuses) - failed_count - abstained_count
            logger.warning(
                "gap-filler: mixed outcome (success=%d abstained=%d failed=%d) for %s, not accepting a lone success",
                success_count,
                abstained_count,
                failed_count,
                description,
            )

    cache.set(key, result)
    # Returns via cache.get(), not the local `result` object directly:
    # `result` is the exact instance now stored internally, so returning it
    # as-is would hand the caller a live alias into the cache's own storage
    # -- get()'s defensive copy (see its docstring) only protects a HIT
    # against this; without going through it here too, the very first,
    # uncopied caller on a MISS could mutate `.forms` in place and silently
    # corrupt this cache entry for every future hit.
    return cache.get(key)
