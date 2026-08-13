"""Pipeline orchestrator: wires section-03 source clients + section-04
concept builders + section-02's OKF writer into one run() that builds and
prunes the Lexical Entry / Grammatical Rule / Cultural Context concept
files under out_dir/{words,grammar,culture}.
"""

import csv
from dataclasses import dataclass, field, replace
from pathlib import Path

from okfbuild import okf
from okfbuild.concepts import cultural_context, grammatical_rule, lexical_entry
from okfbuild.okf import ConceptFile
from okfbuild.sources import SourceBundle

_ALL_PERIODS = ["homeric", "attic", "byzantine", "modern"]


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


def _read_vocabulary_candidates(course_path: Path) -> list[_LexicalCandidate]:
    """Read every *.tsv under course_path (searched recursively — real
    courses nest one vocabulary file per chapter) expecting a header row
    with lemma/pos/level/tags columns. `level` and `tags` are semicolon-
    separated; both may be empty. Exact real-course TSV layout is confirmed
    in section-07; this shape is this section's own fixture convention."""
    candidates = []
    for tsv_path in sorted(course_path.rglob("*.tsv")):
        with tsv_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                lemma = (row.get("lemma") or "").strip()
                if not lemma:
                    continue
                level = [part for part in (row.get("level") or "").split(";") if part]
                tags = [part for part in (row.get("tags") or "").split(";") if part]
                candidates.append(_LexicalCandidate(lemma=lemma, pos=(row.get("pos") or "").strip(), level=level, tags=tags))
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
