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

TYPE_BY_DIR = {
    "words": "Lexical Entry",
    "grammar": "Grammatical Rule",
    "culture": "Cultural Context",
    "texts": "Literary Translation",
}
_DIR_BY_TYPE = {v: k for k, v in TYPE_BY_DIR.items()}

LIST_FIELDS = ("type", "level", "period", "dialect", "author")


def _period_index(period: str) -> int | None:
    try:
        return PERIOD_ORDER.index(period)
    except ValueError:
        return None


def _periods_for(concept: ConceptFile) -> list[str]:
    """Every PERIOD_ORDER value this concept counts as spanning -- via
    periods_spanned range-containment or periods list-membership,
    whichever the concept's own frontmatter uses. Computed once (not
    once per candidate period), so both _period_matches() and
    _field_values()'s period enumeration share the same derivation."""
    periods_spanned = concept.extra_frontmatter.get("periods_spanned")
    if isinstance(periods_spanned, dict):
        from_idx = _period_index(periods_spanned.get("from", ""))
        to_idx = _period_index(periods_spanned.get("to", ""))
        if from_idx is None or to_idx is None:
            return []
        return list(PERIOD_ORDER[from_idx : to_idx + 1])

    periods_list = concept.extra_frontmatter.get("periods")
    if isinstance(periods_list, list):
        return [period for period in PERIOD_ORDER if period in periods_list]

    return []


def _period_matches(concept: ConceptFile, period: str) -> bool:
    return period in _periods_for(concept)


def _field_values(concept: ConceptFile, field: str) -> list[str]:
    if field == "type":
        return [concept.type] if concept.type else []
    if field == "level":
        return list(concept.level) if isinstance(concept.level, list) else []
    if field == "dialect":
        dialect_list = concept.extra_frontmatter.get("dialect")
        return list(dialect_list) if isinstance(dialect_list, list) else []
    if field == "author":
        return [source.author for source in concept.sources if source.author]
    if field == "period":
        return _periods_for(concept)
    raise ValueError(f"unknown field: {field!r}")


def _level_matches(concept: ConceptFile, level: str) -> bool:
    return level in _field_values(concept, "level")


def _author_matches(concept: ConceptFile, author: str) -> bool:
    needle = author.lower()
    return any(needle in value.lower() for value in _field_values(concept, "author"))


def _dialect_matches(concept: ConceptFile, dialect: str) -> bool:
    return dialect in _field_values(concept, "dialect")


def _tally(matches: list[tuple[Path, ConceptFile]], field: str) -> list[tuple[str, int]]:
    tally: dict[str, int] = {}
    for _, concept in matches:
        for value in _field_values(concept, field):
            tally[value] = tally.get(value, 0) + 1
    return sorted(tally.items(), key=lambda pair: (-pair[1], pair[0]))


def list_values(
    repo_root: Path,
    field: str,
    *,
    type: str | None = None,
    level: str | None = None,
    author: str | None = None,
    period: str | None = None,
    dialect: str | None = None,
) -> list[tuple[str, int]]:
    """Return (value, count) pairs for every distinct value `field` takes
    across concepts matching the other filters given -- pass the other
    four to scope the tally (e.g. type="Grammatical Rule" to see only
    level values used on grammar rules). `field` is one of "type",
    "level", "period", "dialect", "author"; any filter matching `field`
    itself is ignored, since `field`'s own value is what's being
    enumerated, not filtered on. Sorted by count descending, then value."""
    scope = dict(type=type, level=level, author=author, period=period, dialect=dialect)
    scope.pop(field, None)
    matches = find_concepts(repo_root, **scope)
    return _tally(matches, field)


def list_mode_report(repo_root: Path, raw: dict) -> dict[str, list[tuple[str, int]]] | None:
    """CLI-facing helper shared by `greek-knowledge query` and
    examples/query_knowledge.py: given the 5 raw filter values as typed
    (a dict over LIST_FIELDS keys; `type`, if present, still in its short
    "words"/"grammar"/... form), return None if none of them is the
    literal string "list" (the caller should run a normal find_concepts()
    query instead), or a {field: [(value, count), ...]} report for every
    field that is "list" -- computed from a SINGLE shared find_concepts()
    scan (scoped by whichever other filters have a real, non-"list"
    value), not one redundant scan per listed field. "type" values come
    back in the same short form --type itself accepts ("grammar", not
    "Grammatical Rule") so a printed value is always valid input for the
    same flag, matching every other field's round-trip property; every
    other field's values are unaffected, since they have no separate
    short/long representation to begin with."""
    list_fields = [field for field in LIST_FIELDS if raw.get(field) == "list"]
    if not list_fields:
        return None
    scope = {
        field: (TYPE_BY_DIR.get(value) if field == "type" else value)
        for field, value in raw.items()
        if value is not None and value != "list"
    }
    matches = find_concepts(repo_root, **scope)
    report = {field: _tally(matches, field) for field in list_fields}
    if "type" in report:
        report["type"] = [(_DIR_BY_TYPE.get(value, value), count) for value, count in report["type"]]
    return report


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
