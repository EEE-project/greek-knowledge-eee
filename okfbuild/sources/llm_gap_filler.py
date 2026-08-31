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

import logging
import os
import unicodedata
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass, field, replace
from enum import Enum, auto
from importlib.metadata import PackageNotFoundError, version

from llm_backend_eee import LLMBackend

logger = logging.getLogger(__name__)

_DEFAULT_CALL_TIMEOUT_SECONDS = 30.0

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
    method: str  # e.g. "llm:gpt-4o-mini" -- names the model(s) actually queried this call
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


@dataclass
class GapFillCache:
    """Run-local (in-process, single pipeline invocation) memoization,
    keyed by (lemma, a canonical/sorted serialization of features, pos,
    language, config identity). Prevents redundant LLM calls when the
    same gap recurs across courses/periods within one run. Also caches a
    "no result" outcome (disagreement/failure), not just successes,
    within the run -- otherwise the same unfillable gap re-triggers the
    full call batch every time it recurs. Persistent (cross-run) caching
    is explicitly deferred to a later, not-yet-planned follow-up.

    Also tracks `request_count`, the running total of LLM calls issued
    through this cache -- see fill_gap()'s request-budget enforcement."""

    _results: dict[tuple, GapFillResult] = field(default_factory=dict)
    request_count: int = 0

    @staticmethod
    def make_key(
        lemma: str, features: dict[str, str], pos: str, language: str, config: GapFillerConfig
    ) -> tuple:
        """GapFillerConfig and LLMModelConfig are frozen dataclasses with
        structural equality/hashing, so using `config` itself as part of
        the key is sufficient -- any field difference (models, sample
        count, budget) naturally produces a different key. `features` is
        sorted so insertion-order differences don't cause spurious cache
        misses."""
        feature_key = tuple(sorted(features.items()))
        return (lemma, feature_key, pos, language, config)

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


def _call_one(
    model_config: LLMModelConfig, lemma: str, features: dict[str, str], pos: str, language: str
) -> tuple[SampleStatus, set[str]]:
    """One sample call to one configured model. Never raises -- every
    failure mode (missing/invalid env var, network error, API error)
    is caught and reported as CALL_FAILED."""
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
        forms = backend.inflect(lemma, features, pos, language=language)
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
) -> GapFillResult:
    """Attempt to fill one morphology gap. Checks `cache` first -- a cache
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
    key = cache.make_key(lemma, features, pos, language, config)
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
            executor.submit(_call_one, model_config, lemma, features, pos, language): model_config
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
    return result
