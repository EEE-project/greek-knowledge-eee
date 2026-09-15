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

_TYPE_BY_DIR = {
    "words": "Lexical Entry",
    "grammar": "Grammatical Rule",
    "culture": "Cultural Context",
    "texts": "Literary Translation",
}
_DIR_BY_TYPE = {v: k for k, v in _TYPE_BY_DIR.items()}


def _level_matches(concept: ConceptFile, level: str) -> bool:
    if isinstance(concept.level, list):
        return level in concept.level
    return False


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


def _dialect_matches(concept: ConceptFile, dialect: str) -> bool:
    dialect_list = concept.extra_frontmatter.get("dialect", [])
    if isinstance(dialect_list, list):
        return dialect in dialect_list
    return False


def find_concepts(
    repo_root: Path,
    *,
    type: str | None = None,
    level: str | None = None,
    author: str | None = None,
    period: str | None = None,
    dialect: str | None = None,
) -> list[tuple[Path, ConceptFile]]:
    """Return every (path, ConceptFile) under repo_root's words/grammar/
    culture/texts trees matching every filter given (None = no constraint
    on that dimension). Results are sorted by path."""
    matches: list[tuple[Path, ConceptFile]] = []
    concept_dirs = _CONCEPT_DIRS
    if type is not None:
        dirname = _DIR_BY_TYPE.get(type)
        concept_dirs = (dirname,) if dirname is not None else ()
    for dirname in concept_dirs:
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
            if dialect is not None and not _dialect_matches(concept, dialect):
                continue
            matches.append((path, concept))
    return sorted(matches, key=lambda pair: pair[0])
