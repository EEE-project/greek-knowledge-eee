"""Pipeline orchestrator: wires section-03 source clients + section-04
concept builders + section-02's OKF writer into one run() that builds and
prunes the Lexical Entry / Grammatical Rule / Cultural Context concept
files under out_dir/{words,grammar,culture}.
"""

import csv
import logging
import re
from dataclasses import dataclass, field, replace
from pathlib import Path

from okfbuild import okf
from okfbuild.concepts import cultural_context, grammatical_rule, lexical_entry
from okfbuild.okf import ConceptFile
from okfbuild.sources import SourceBundle

logger = logging.getLogger(__name__)

_ALL_PERIODS = ["homeric", "attic", "byzantine", "modern"]

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
class GrammarRuleSpec:
    rule_id: str
    sophocles_excerpt: str
    example_forms: list[tuple[str, str]]
    period_from: str
    period_to: str
    level: list[str]
    tags: list[str]


@dataclass
class CulturalTopicSpec:
    topic_id: str
    lesson_prose: list[str]
    wiki_title: str | None
    level: list[str]
    tags: list[str]
    related_words: list[str] | None = None
    related_lessons: list[str] | None = None


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


def _read_word_translation_row(row: dict, filename: str, pos: str) -> _LexicalCandidate | None:
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
    return _LexicalCandidate(lemma=lemma, pos=pos, level=[], tags=[])


def _read_vocabulary_candidates(course_path: Path) -> list[_LexicalCandidate]:
    """Read every *.tsv under course_path (searched recursively — real
    courses nest one vocabulary file per chapter). Each file is dispatched
    per its own header/filename shape:

    1. A `lemma` column present -> the reading-course format
       (lemma/pos/level/tags, semicolon-separated level/tags).
    2. A `_XX.tsv` language-suffix filename -> skipped quietly (a
       translation twin of a sibling file, e.g. nouns_ru.tsv).
    3. Exactly `vocabulary.tsv` -> Word/Translation/Type format, pos from
       the per-row Type column via _VOCABULARY_TYPE_TO_POS.
    4. Filename is a key in _FILENAME_TO_POS -> Word/Translation format,
       pos fixed per file.
    5. Anything else -> skipped, with a warning (an unrecognized vocab
       file this code doesn't know how to read yet)."""
    candidates = []
    for tsv_path in sorted(course_path.rglob("*.tsv")):
        with tsv_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            if reader.fieldnames and "lemma" in reader.fieldnames:
                for row in reader:
                    lemma = (row.get("lemma") or "").strip()
                    if not lemma:
                        continue
                    level = [part for part in (row.get("level") or "").split(";") if part]
                    tags = [part for part in (row.get("tags") or "").split(";") if part]
                    candidates.append(
                        _LexicalCandidate(lemma=lemma, pos=(row.get("pos") or "").strip(), level=level, tags=tags)
                    )
                continue

            if _LANGUAGE_SUFFIX_RE.search(tsv_path.name):
                logger.info("Skipping translation-twin vocabulary file %r in %s", tsv_path.name, course_path)
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
                    candidate = _read_word_translation_row(row, tsv_path.name, pos)
                    if candidate is not None:
                        candidates.append(candidate)
                continue

            pos = _FILENAME_TO_POS.get(tsv_path.name)
            if pos is None:
                logger.warning("Unrecognized vocabulary file %r in %s", tsv_path.name, course_path)
                continue
            for row in reader:
                candidate = _read_word_translation_row(row, tsv_path.name, pos)
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


def run(
    course_paths: list[Path],
    out_dir: Path,
    sources: SourceBundle,
    grammar_rules: list[GrammarRuleSpec] | None = None,
    cultural_topics: list[CulturalTopicSpec] | None = None,
) -> BuildReport:
    """For each course in course_paths: extract candidate lemmas from its
    vocabulary TSVs, build a Lexical Entry per lemma (always querying all
    four periods — a word can be genuinely attested beyond the one course
    that surfaced it). grammar_rules/cultural_topics are supplied
    explicitly by the caller (not derived from course_paths). Every concept
    is isolated end-to-end (build through write): one bad concept is
    logged to BuildReport.errors and skipped, never fatal to the run.

    Pruning: after building, any existing words/grammar/culture concept
    file not touched this run is stale relative to current source
    material — its frontmatter `status` is flipped to "deprecated" (via
    okf.write(), so a human's `verified:` entry survives) rather than
    deleting the file; a human decides whether to actually remove it.
    """
    report = BuildReport()
    touched: set[Path] = set()
    words_dir = out_dir / "words"
    grammar_dir = out_dir / "grammar"
    culture_dir = out_dir / "culture"

    for candidate in _collect_lexical_candidates(course_paths):
        try:
            concept = lexical_entry.build(
                candidate.lemma,
                candidate.pos,
                _ALL_PERIODS,
                sources,
                level=candidate.level,
                tags=candidate.tags,
            )
        except Exception as exc:
            report.failed += 1
            report.errors.append(f"lexical_entry {candidate.lemma!r}: {exc}")
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

    for spec in grammar_rules or []:
        try:
            concept = grammatical_rule.build(
                spec.rule_id,
                spec.sophocles_excerpt,
                spec.example_forms,
                spec.period_from,
                spec.period_to,
                level=spec.level,
                tags=spec.tags,
            )
            path = grammar_dir / f"{_slugify(spec.rule_id)}.md"
            _apply_write(report, concept, path)
            touched.add(path)
        except Exception as exc:
            report.failed += 1
            report.errors.append(f"grammatical_rule {spec.rule_id!r}: {exc}")

    for spec in cultural_topics or []:
        try:
            concept = cultural_context.build(
                spec.topic_id,
                spec.lesson_prose,
                spec.wiki_title,
                sources,
                level=spec.level,
                tags=spec.tags,
                related_words=spec.related_words,
                related_lessons=spec.related_lessons,
            )
            path = culture_dir / f"{_slugify(spec.topic_id)}.md"
            _apply_write(report, concept, path)
            touched.add(path)
        except Exception as exc:
            report.failed += 1
            report.errors.append(f"cultural_context {spec.topic_id!r}: {exc}")

    _prune(out_dir, touched, report)

    return report


def _prune(out_dir: Path, touched: set[Path], report: BuildReport) -> None:
    for type_dir in (out_dir / "words", out_dir / "grammar", out_dir / "culture"):
        for path in sorted(type_dir.glob("*.md")):
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
