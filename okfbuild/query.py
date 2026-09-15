"""Read-only, cross-concept-type querying of this KB's own committed
files by frontmatter — type, level, author. Reads
already-written words/grammar/culture/texts content via okf.read(); never
calls any external source. See okfbuild/lookup.py for the equivalent
read-only entry point for *external* sources instead.
"""

from pathlib import Path

from okfbuild import okf
from okfbuild.okf import ConceptFile
from okfbuild.periods import PERIOD_ORDER

_CONCEPT_DIRS = ("words", "grammar", "culture", "texts")


def _level_matches(concept: ConceptFile, level: str) -> bool:
    return level in concept.level


def _author_matches(concept: ConceptFile, author: str) -> bool:
    needle = author.lower()
    return any(needle in source.author.lower() for source in concept.sources)


def _period_index(period: str) -> int | None:
    try:
        return PERIOD_ORDER.index(period)
    except ValueError:
        return None


def _period_matches(concept: ConceptFile, period: str) -> bool:
    target_idx = _period_index(period)
    if target_idx is None:
        return False

    periods_spanned = concept.extra_frontmatter.get("periods_spanned")
    if isinstance(periods_spanned, dict):
        from_idx = _period_index(periods_spanned.get("from", ""))
        to_idx = _period_index(periods_spanned.get("to", ""))
        if from_idx is None or to_idx is None:
            return False
        return from_idx <= target_idx <= to_idx

    periods_list = concept.extra_frontmatter.get("periods")
    if isinstance(periods_list, list):
        return period in periods_list

    return False


def find_concepts(
    repo_root: Path,
    *,
    type: str | None = None,
    level: str | None = None,
    author: str | None = None,
    period: str | None = None,
) -> list[tuple[Path, ConceptFile]]:
    """Return every (path, ConceptFile) under repo_root's words/grammar/
    culture/texts trees matching every filter given (None = no constraint
    on that dimension). Results are sorted by path."""
    matches: list[tuple[Path, ConceptFile]] = []
    for dirname in _CONCEPT_DIRS:
        concept_dir = repo_root / dirname
        if not concept_dir.is_dir():
            continue
        for path in concept_dir.rglob("*.md"):
            if path.name == "index.md":
                continue
            concept = okf.read(path)
            if concept is None:
                continue
            if type is not None and concept.type != type:
                continue
            if level is not None and not _level_matches(concept, level):
                continue
            if author is not None and not _author_matches(concept, author):
                continue
            if period is not None and not _period_matches(concept, period):
                continue
            matches.append((path, concept))
    return sorted(matches, key=lambda pair: pair[0])
