"""Pipeline orchestrator: wires section-03 source clients + section-04's
lexical_entry builder + section-02's OKF writer into one run() that builds
and prunes the Lexical Entry concept files under out_dir/words. Grammatical
Rule and Cultural Context entries are hand-authored directly (see
templates/) and checked, not generated -- see okfbuild/check.py.
"""

import csv
import logging
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path

from okfbuild import okf
from okfbuild.concepts import lexical_entry
from okfbuild.concepts.lexical_entry import GapFillRecord
from okfbuild.okf import ConceptFile
from okfbuild.sources import SourceBundle
from okfbuild.sources.llm_gap_filler import GapFillCache, RequestBudgetExceededError

logger = logging.getLogger(__name__)

_ALL_PERIODS = ["homeric", "attic", "byzantine", "modern"]

_GAP_FILL_RUNS_DIRNAME = ".gap_fill_runs"
_GAP_FILL_CACHE_FILENAME = "cache.json"
_GAP_FILL_CHECKPOINT_INTERVAL = 10  # new cache entries between checkpoint saves -- see run()

_FILENAME_TO_POS: dict[str, str] = {
    "nouns.tsv": "noun",
    "verbs.tsv": "verb",
    "verbs+.tsv": "verb",
    "adjectives.tsv": "adj",
    "adjs.tsv": "adj",
    "pronouns.tsv": "pronoun",
    "particles.tsv": "particle",
    "cap1_particles.tsv": "particle",
}

_VOCABULARY_TYPE_TO_POS: dict[str, str] = {
    "noun": "noun",
    "verb": "verb",
    "adjective": "adj",
    "adverb": "adv",
    "pronoun": "pronoun",
}

# Confirmed, catalogued Type values that intentionally skip (multi-word
# idioms, or no usable POS signal) -- distinct from a genuinely
# unrecognized value, so these must not trigger the "unrecognized" warning.
_VOCABULARY_TYPE_KNOWN_SKIP = {"phrase", "adverb phrase", "literary term"}

_SINGULAR_ARTICLES = {"ο", "η", "το", "ὁ", "ἡ", "τό", "τὸ"}
_PLURAL_ARTICLES = {"οι", "τα", "τις"}

_LANGUAGE_SUFFIX_RE = re.compile(r"_[a-z]{2}\.tsv$")


@dataclass
class BuildReport:
    """Summary of one pipeline.run() invocation."""

    written: int = 0
    unchanged: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)  # one human-readable message per failed concept


@dataclass(frozen=True)
class _LexicalCandidate:
    lemma: str
    pos: str
    level: list[str]
    tags: list[str]
    source_course: str | None = None


def _slugify(text: str) -> str:
    """Lowercase + hyphenate; Greek diacritics are preserved (they're
    meaningful, distinguishing characters, not accents to strip) — matches
    words/index.md's documented slug convention."""
    return text.strip().lower().replace(" ", "-")


def _resolve_noun_lemma(word: str) -> str | None:
    """Returns the lemma to use for a noun-typed Word value, or None if
    this row should be skipped entirely (starts with a plural article --
    the pluralia tantum risk: e.g. "τα σκουπίδια" (garbage) has no natural
    singular, so stripping "τα" would fabricate a false, possibly
    non-existent singular lemma).

    - Starts with a token in _SINGULAR_ARTICLES: strip it, return the
      remainder.
    - Starts with a token in _PLURAL_ARTICLES: return None (skip).
    - Neither: return word unchanged (a bare lemma with no article, e.g.
      "παροιμία" -- confirmed a real, valid case, not an error)."""
    parts = word.split(maxsplit=1)
    if len(parts) == 2 and parts[0] in _SINGULAR_ARTICLES:
        return parts[1]
    if len(parts) == 2 and parts[0] in _PLURAL_ARTICLES:
        return None
    return word


def _read_word_translation_row(
    row: dict, filename: str, pos: str, source_course: str | None = None
) -> _LexicalCandidate | None:
    """Build a candidate from one Word/Translation-format row already
    resolved to a `pos`, or None if this row should be skipped (empty
    Word, or a noun-typed row starting with a plural article -- logged
    here since the caller already has `filename` for context)."""
    word = (row.get("Word") or "").strip()
    if not word:
        return None
    lemma = word
    if pos == "noun":
        lemma = _resolve_noun_lemma(word)
        if lemma is None:
            logger.warning("Skipping pluralia-tantum-risk row %r in %s (plural article, no safe singular)", word, filename)
            return None
    return _LexicalCandidate(lemma=lemma, pos=pos, level=[], tags=[], source_course=source_course)


def _read_vocabulary_candidates(course_path: Path) -> list[_LexicalCandidate]:
    """Read every *.tsv under course_path (searched recursively — real
    courses nest one vocabulary file per chapter). Each file is dispatched
    per its own header/filename shape:

    1. `lemma` AND `pos` columns both present -> the reading-course format
       (lemma/pos/level/tags, semicolon-separated level/tags). `pos` is
       required, not just `lemma`, specifically to rule out
       translation_presence.tsv below -- across every course in this
       repo family, that's the only other `lemma`-column shape, and it
       has no `pos` column at all.
    2. A `_XX.tsv` language-suffix filename -> skipped quietly (a
       translation twin of a sibling file, e.g. nouns_ru.tsv).
    3. Exactly `translation_presence.tsv` -> skipped quietly. This is a
       per-lesson quiz answer key (see translation_presence_SCHEMA.md in
       the course repo), not vocabulary -- it has its own `lemma` column
       (naming which word each row judges) that would otherwise satisfy
       case 1 above, feeding every row -- including intentionally
       comment-prefixed stale ones (`#`-prefixed lemma, e.g. "#ἐγώ") --
       into the build as a bogus candidate with no attested data.
    4. Exactly `vocabulary.tsv` -> Word/Translation/Type format, pos from
       the per-row Type column via _VOCABULARY_TYPE_TO_POS.
    5. Filename is a key in _FILENAME_TO_POS -> Word/Translation format,
       pos fixed per file.
    6. Anything else -> skipped, with a warning (an unrecognized vocab
       file this code doesn't know how to read yet)."""
    candidates = []
    for tsv_path in sorted(course_path.rglob("*.tsv")):
        with tsv_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            if reader.fieldnames and "lemma" in reader.fieldnames and "pos" in reader.fieldnames:
                for row in reader:
                    lemma = (row.get("lemma") or "").strip()
                    if not lemma:
                        continue
                    level = [part for part in (row.get("level") or "").split(";") if part]
                    tags = [part for part in (row.get("tags") or "").split(";") if part]
                    candidates.append(
                        _LexicalCandidate(
                            lemma=lemma,
                            pos=(row.get("pos") or "").strip(),
                            level=level,
                            tags=tags,
                            source_course=course_path.name,
                        )
                    )
                continue

            if _LANGUAGE_SUFFIX_RE.search(tsv_path.name):
                logger.info("Skipping translation-twin vocabulary file %r in %s", tsv_path.name, course_path)
                continue

            if tsv_path.name == "translation_presence.tsv":
                logger.info("Skipping translation-presence quiz file %r in %s (not vocabulary)", tsv_path.name, course_path)
                continue

            if tsv_path.name == "vocabulary.tsv":
                for row in reader:
                    type_value = (row.get("Type") or "").strip()
                    normalized = type_value.split(" (")[0]
                    pos = _VOCABULARY_TYPE_TO_POS.get(normalized)
                    if pos is None:
                        if type_value and normalized not in _VOCABULARY_TYPE_KNOWN_SKIP:
                            logger.warning("Unrecognized vocabulary Type %r in %s", type_value, tsv_path.name)
                        continue
                    candidate = _read_word_translation_row(row, tsv_path.name, pos, source_course=course_path.name)
                    if candidate is not None:
                        candidates.append(candidate)
                continue

            pos = _FILENAME_TO_POS.get(tsv_path.name)
            if pos is None:
                logger.warning("Unrecognized vocabulary file %r in %s", tsv_path.name, course_path)
                continue
            for row in reader:
                candidate = _read_word_translation_row(row, tsv_path.name, pos, source_course=course_path.name)
                if candidate is not None:
                    candidates.append(candidate)
    return candidates


def _collect_lexical_candidates(course_paths: list[Path]) -> list[_LexicalCandidate]:
    """Deduplicate across all course_paths, keyed by normalized lemma — the
    same word can legitimately appear in more than one course's vocabulary
    and must be built and written only once per run. First course wins."""
    by_lemma: dict[str, _LexicalCandidate] = {}
    for course_path in course_paths:
        for candidate in _read_vocabulary_candidates(course_path):
            by_lemma.setdefault(candidate.lemma.strip().lower(), candidate)
    return list(by_lemma.values())


def _apply_write(report: BuildReport, concept: ConceptFile, path: Path) -> None:
    if okf.write(concept, path):
        report.written += 1
    else:
        report.unchanged += 1


def _resolve_gap_fill_run_path(gap_fill_cache_dir: Path) -> Path:
    """Picks the run-ID-scoped cache.json path for this run(): resumes the
    most recently checkpointed still-incomplete run (a run-ID subdirectory
    that still has a cache.json — a run that completes successfully
    removes its own, see run()'s cleanup) if one exists, else starts a
    fresh run ID. cache.json's mere presence, not a separate "completed"
    marker, is what distinguishes an incomplete run."""
    runs_dir = gap_fill_cache_dir / _GAP_FILL_RUNS_DIRNAME
    incomplete_runs = []
    if runs_dir.is_dir():
        for run_dir in runs_dir.iterdir():
            cache_path = run_dir / _GAP_FILL_CACHE_FILENAME
            if cache_path.is_file():
                incomplete_runs.append(cache_path)

    if incomplete_runs:
        return max(incomplete_runs, key=lambda path: path.stat().st_mtime)

    return runs_dir / uuid.uuid4().hex / _GAP_FILL_CACHE_FILENAME


def _persist_gap_fill_cache(cache: GapFillCache, path: Path) -> None:
    """Saves the gap-fill cache to path, protected against I/O failures so a
    save error never masks/replaces a real exception or turns an otherwise-
    clean early stop into a raised one. Shared by both non-normal-completion
    exits of run()'s try/except/else below (a crash, and budget
    exhaustion) -- both need an unconditional attempt (even with zero new
    entries since the last periodic checkpoint) so cache.json still exists
    on disk for _resolve_gap_fill_run_path() to find on resume; resumability
    depends on the file's existence, not on whether this particular exit
    happened to grow the cache."""
    try:
        cache.save(path)
    except Exception:
        logger.exception("gap-filler: failed to save checkpoint at %s", path)


def run(
    course_paths: list[Path],
    out_dir: Path,
    sources: SourceBundle,
    gap_fill_cache_dir: Path | None = None,
    on_llm_inferred: "Callable[[GapFillRecord], None] | None" = None,
) -> BuildReport:
    """For each course in course_paths: extract candidate lemmas from its
    vocabulary TSVs, build a Lexical Entry per lemma (always querying all
    four periods — a word can be genuinely attested beyond the one course
    that surfaced it). Every concept is isolated end-to-end (build through
    write): one bad concept is logged to BuildReport.errors and skipped,
    never fatal to the run.

    Pruning: after building, any existing words/ concept file not touched
    this run is stale relative to current source material — its frontmatter
    `status` is flipped to "deprecated" (via okf.write(), so a human's
    `verified:` entry survives) rather than deleting the file; a human
    decides whether to actually remove it. grammar/ and culture/ are
    hand-authored (see templates/) and out of scope for both building and
    pruning here — okfbuild/check.py validates them instead.

    gap_fill_cache_dir: when sources.llm_gap_filler is set, run() shares
    exactly one GapFillCache across every lexical candidate it processes.
    Leaving gap_fill_cache_dir at its default (None) makes that cache
    purely in-memory/ephemeral — identical to every caller before this
    parameter existed, with no .load()/.save() calls at all. Passing a
    directory engages run-ID-scoped, interruption-safe disk persistence
    under gap_fill_cache_dir/.gap_fill_runs/<run-id>/cache.json: the cache
    is periodically checkpointed, and the next run() call against the same
    gap_fill_cache_dir automatically resumes the most recent incomplete
    run instead of re-paying for already-resolved gaps. A run that
    completes normally removes its own cache file — see
    _resolve_gap_fill_run_path() and GapFillCache.save()/load().
    Exhausting config.max_requests_per_run (llm_gap_filler.RequestBudgetExceededError)
    stops the run early rather than letting every remaining candidate fail
    the same way one-by-one, and does NOT count as "completed normally"
    for cache-cleanup purposes — the cache is preserved (pruning is also
    skipped, since the run never reached the rest of the course) so a
    later run with a higher budget resumes instead of re-paying for every
    already-resolved gap.

    on_llm_inferred, if given, is forwarded unchanged to every
    lexical_entry.build() call in the lexical-candidate loop — see that
    function's own docstring for what it does. Omitting it (the default)
    is a pure no-op.
    """
    report = BuildReport()
    touched: set[Path] = set()
    words_dir = out_dir / "words"

    gap_fill_cache: GapFillCache | None = None
    gap_fill_cache_path: Path | None = None
    if sources.llm_gap_filler is not None:
        if gap_fill_cache_dir is not None:
            gap_fill_cache_path = _resolve_gap_fill_run_path(gap_fill_cache_dir)
            gap_fill_cache = GapFillCache.load(gap_fill_cache_path)
        else:
            gap_fill_cache = GapFillCache()
    last_checkpoint_len = len(gap_fill_cache) if gap_fill_cache is not None else 0
    budget_exhausted = False

    try:
        for candidate in _collect_lexical_candidates(course_paths):
            try:
                concept = lexical_entry.build(
                    candidate.lemma,
                    candidate.pos,
                    _ALL_PERIODS,
                    sources,
                    level=candidate.level,
                    tags=candidate.tags,
                    source_course=candidate.source_course,
                    cache=gap_fill_cache,
                    on_llm_inferred=on_llm_inferred,
                )
            except Exception as exc:
                report.failed += 1
                report.errors.append(f"lexical_entry {candidate.lemma!r}: {exc}")
                if isinstance(exc, RequestBudgetExceededError):
                    # Every remaining candidate would immediately fail this
                    # exact same way (cache.request_count already exceeds
                    # the budget) -- stop now rather than burning through
                    # the rest one-by-one, each producing its own
                    # uninformative "exceeded budget" entry. _prune() is
                    # skipped below too: this run never reached the rest of
                    # the course, so pruning would wrongly mark
                    # still-current, not-yet-attempted concepts as
                    # deprecated.
                    logger.warning(
                        "gap-filler: max_requests_per_run exhausted at lemma=%r -- "
                        "stopping this run early instead of re-attempting (and "
                        "re-failing) every remaining candidate",
                        candidate.lemma,
                    )
                    budget_exhausted = True
                    break
                continue

            if not concept.extra_frontmatter.get("periods"):
                report.failed += 1
                report.errors.append(f"lexical_entry {candidate.lemma!r}: no attested data in any source")
                continue

            try:
                slug = okf.resolve_slug(words_dir, _slugify(candidate.lemma), lemma=candidate.lemma)
                path = words_dir / f"{slug}.md"
                _apply_write(report, concept, path)
                touched.add(path)
            except Exception as exc:
                report.failed += 1
                report.errors.append(f"lexical_entry {candidate.lemma!r}: {exc}")

            if (
                gap_fill_cache_path is not None
                and len(gap_fill_cache) - last_checkpoint_len >= _GAP_FILL_CHECKPOINT_INTERVAL
            ):
                gap_fill_cache.save(gap_fill_cache_path)
                last_checkpoint_len = len(gap_fill_cache)

        if not budget_exhausted:
            _prune(out_dir, touched, report)
    except BaseException:
        # Protects against ordinary exception unwinding (an unexpected bug
        # above, KeyboardInterrupt) -- NOT SIGKILL/power loss, which only
        # the periodic checkpoint above protects against. A failure here
        # is logged, never allowed to replace/mask a real exception
        # already propagating out of this function. Always attempts the
        # save (even with zero new entries since the last checkpoint) --
        # a crash before any progress must still leave a cache.json behind
        # for _resolve_gap_fill_run_path() to find on resume, matching
        # this run's own gap_fill_cache_path rather than silently losing
        # track of the attempt.
        if gap_fill_cache_path is not None:
            _persist_gap_fill_cache(gap_fill_cache, gap_fill_cache_path)
        raise
    else:
        # Only reached if the try block above returned normally --
        # "successful completion" for cache-cleanup purposes, regardless
        # of report.failed (individual candidate failures are already
        # isolated above and never reach here as a propagating exception).
        # budget_exhausted is the one exception to that: it never raises
        # (the loop breaks cleanly), but the run is genuinely incomplete --
        # most candidates were never attempted -- so it gets the same
        # cache-preserving treatment as the except BaseException branch
        # above, not deleted like a real completion. Also re-saves rather
        # than trusting the periodic checkpoint, which can be up to
        # _GAP_FILL_CHECKPOINT_INTERVAL entries stale -- unconditionally,
        # via the same shared, protected save as the crash path above (see
        # _persist_gap_fill_cache's own docstring for why "unconditional"
        # matters here too).
        if gap_fill_cache_path is not None:
            if budget_exhausted:
                _persist_gap_fill_cache(gap_fill_cache, gap_fill_cache_path)
            else:
                gap_fill_cache_path.unlink(missing_ok=True)

    return report


def _prune(out_dir: Path, touched: set[Path], report: BuildReport) -> None:
    for path in sorted((out_dir / "words").glob("*.md")):
        if path.name == "index.md" or path in touched:
            continue

        concept = okf.read(path)
        if concept is None:
            report.failed += 1
            report.errors.append(f"prune {path}: could not parse existing frontmatter")
            continue

        deprecated = replace(concept, extra_frontmatter={**concept.extra_frontmatter, "status": "deprecated"})
        try:
            _apply_write(report, deprecated, path)
        except Exception as exc:
            report.failed += 1
            report.errors.append(f"prune {path}: {exc}")
