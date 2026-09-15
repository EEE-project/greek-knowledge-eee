"""Read-only, cross-concept-type querying of this KB's own committed
files by frontmatter — level, period, dialect, author. Reads
already-written words/grammar/culture/texts content via okf.read(); never
calls any external source. See okfbuild/lookup.py for the equivalent
read-only entry point for *external* sources instead.
"""

from pathlib import Path

from okfbuild import okf
from okfbuild.okf import ConceptFile

_CONCEPT_DIRS = ("words", "grammar", "culture", "texts")


def _level_matches(concept: ConceptFile, level: str) -> bool:
    return level in concept.level


def _author_matches(concept: ConceptFile, author: str) -> bool:
    needle = author.lower()
    return any(needle in source.author.lower() for source in concept.sources)


def find_concepts(
    repo_root: Path,
    *,
    type: str | None = None,
    level: str | None = None,
    author: str | None = None,
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
            matches.append((path, concept))
    return sorted(matches, key=lambda pair: pair[0])
