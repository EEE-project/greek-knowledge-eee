"""Read-only, cross-concept-type querying of this KB's own committed
files by frontmatter — type, level, period, dialect, author, work,
language — and, on request, by whether the file's current text carries a
verification record. Reads
already-written words/grammar/culture/texts content via okf.read(); never
calls any external source. See okfbuild/lookup.py for the equivalent
read-only entry point for *external* sources instead.
"""

import argparse
import re
from collections import Counter
from collections.abc import Collection
from pathlib import Path

from okfbuild import okf
from okfbuild.okf import ConceptFile
from okfbuild.periods import PERIOD_ORDER

_CONCEPT_DIRS = ("words", "grammar", "culture", "texts")

# texts/ holds each work's original (Literary Text) beside its translations, so --type texts spans both.
TYPES_BY_DIR = {
    "words": {"Lexical Entry"},
    "grammar": {"Grammatical Rule"},
    "culture": {"Cultural Context"},
    "texts": {"Literary Translation", "Literary Text"},
}
_DIR_BY_TYPE = {concept_type: dirname for dirname, types in TYPES_BY_DIR.items() for concept_type in types}

LIST_FIELDS = ("type", "level", "period", "dialect", "author", "work", "language")

Selection = str | Collection[str] | None


def _values(selection: Selection) -> list[str]:
    if selection is None:
        return []
    return [selection] if isinstance(selection, str) else list(selection)


def split_values(text: str) -> list[str]:
    """One command-line occurrence of a filter as its values: split at each comma not followed
    by whitespace, so `ru,en` is two values while a printed `Kavafis, Ithaka` stays one."""
    return [part for part in (piece.strip() for piece in re.split(r",(?!\s)", text)) if part]


def concept_types(shorthands: Selection) -> set[str] | None:
    """The concept types behind `--type` short names (`texts` names two), or None when none were given."""
    names = _values(shorthands)
    if not names:
        return None
    return {concept_type for name in names for concept_type in TYPES_BY_DIR.get(name, ())}


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


def _selected_periods(selection: Selection) -> set[str] | None:
    """The periods a selection names -- each value one period or a `from..to` range, ends included --
    or None when nothing is selected. An unknown name or a reversed range names nothing."""
    values = _values(selection)
    if not values:
        return None
    chosen: set[str] = set()
    for value in values:
        first, dots, last = value.partition("..")
        if not dots:
            chosen.add(value)
            continue
        first_index, last_index = _period_index(first), _period_index(last)
        if first_index is not None and last_index is not None:
            chosen.update(PERIOD_ORDER[first_index : last_index + 1])
    return chosen


def _period_matches(concept: ConceptFile, periods: set[str]) -> bool:
    return not periods.isdisjoint(_periods_for(concept))


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
    if field in ("work", "language"):
        value = concept.extra_frontmatter.get(field)
        return [value] if isinstance(value, str) and value else []
    raise ValueError(f"unknown field: {field!r}")


def _contains_any(values: list[str], needles: list[str]) -> bool:
    return any(needle.lower() in value.lower() for needle in needles for value in values)


def _level_matches(concept: ConceptFile, levels: list[str]) -> bool:
    return not set(levels).isdisjoint(_field_values(concept, "level"))


def _author_matches(concept: ConceptFile, authors: list[str]) -> bool:
    return _contains_any(_field_values(concept, "author"), authors)


def _dialect_matches(concept: ConceptFile, dialects: list[str]) -> bool:
    return not set(dialects).isdisjoint(_field_values(concept, "dialect"))


def _work_matches(concept: ConceptFile, works: list[str]) -> bool:
    return _contains_any(_field_values(concept, "work"), works)


def _language_matches(concept: ConceptFile, languages: list[str]) -> bool:
    wanted = {language.lower() for language in languages}
    return any(value.lower() in wanted for value in _field_values(concept, "language"))


def _ranked(counts: Counter[str]) -> list[tuple[str, int]]:
    return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))


def _tally(matches: list[tuple[Path, ConceptFile]], field: str) -> list[tuple[str, int]]:
    return _ranked(Counter(value for _, concept in matches for value in _field_values(concept, field)))


def list_values(
    repo_root: Path,
    field: str,
    *,
    type: Selection = None,
    level: Selection = None,
    author: Selection = None,
    period: Selection = None,
    dialect: Selection = None,
    work: Selection = None,
    language: Selection = None,
    verified: bool = False,
) -> list[tuple[str, int]]:
    """Return (value, count) pairs for every distinct value `field` takes
    across concepts matching the other filters given -- pass the others
    to scope the tally (e.g. type="Grammatical Rule" to see only
    level values used on grammar rules, verified=True to count only
    concepts with a current verification record). `field` is one of "type",
    "level", "period", "dialect", "author", "work", "language"; any
    filter matching `field` itself is ignored, since `field`'s own value
    is what's being enumerated, not filtered on. Sorted by count
    descending, then value."""
    scope = dict(type=type, level=level, author=author, period=period, dialect=dialect, work=work, language=language)
    scope.pop(field, None)
    matches = find_concepts(repo_root, verified=verified, **scope)
    return _tally(matches, field)


def list_mode_report(repo_root: Path, raw: dict, *, verified: bool = False) -> dict[str, list[tuple[str, int]]] | None:
    """CLI-facing helper shared by `greek-knowledge query` and
    examples/query_knowledge.py: given the raw filter values as typed
    (a dict over LIST_FIELDS keys, each value a string or a list of them as
    the flags give them; `type`, if present, still in its short
    "words"/"grammar"/... form), return None if none of them is exactly
    "list" (the caller should run a normal find_concepts()
    query instead), or a {field: [(value, count), ...]} report for every
    field that is "list" -- computed from a SINGLE shared find_concepts()
    scan (scoped by whichever other filters have a real, non-"list"
    value), not one redundant scan per listed field. "type" values come
    back in the same short form --type itself accepts ("grammar", not
    "Grammatical Rule") so a printed value is always valid input for the
    same flag, matching every other field's round-trip property; every
    other field's values are unaffected, since they have no separate
    short/long representation to begin with. `verified` (the --verified
    switch) scopes the tally like any other filter given alongside."""
    list_fields = [field for field in LIST_FIELDS if _values(raw.get(field)) == ["list"]]
    if not list_fields:
        return None
    scope = {
        field: (concept_types(value) if field == "type" else value)
        for field, value in raw.items()
        if _values(value) and _values(value) != ["list"]
    }
    matches = find_concepts(repo_root, verified=verified, **scope)
    report = {field: _tally(matches, field) for field in list_fields}
    if "type" in report:
        merged: Counter[str] = Counter()
        for value, count in report["type"]:
            merged[_DIR_BY_TYPE.get(value, value)] += count
        report["type"] = _ranked(merged)
    return report


_FILTER_HELP = {
    "level": "a level tag on the concept (free text: beginner, A2, B1...)",
    "period": "a period the concept spans (homeric, attic, koine, byzantine, modern), or a range such as homeric..attic",
    "dialect": "a dialect tag on the concept",
    "author": "case-insensitive substring of any source's author",
    "work": "case-insensitive substring of a text's work title (e.g. ithaka)",
    "language": "a text's exact language code (el, en, ru, grc...)",
}


def add_filter_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the seven filter flags and the --verified switch shared by
    `greek-knowledge query` and examples/query_knowledge.py. Each filter
    fills a list (see split_values) that find_concepts()/list_mode_report()
    take as they are."""
    type_choices = sorted(TYPES_BY_DIR) + ["list"]

    def type_values(text: str) -> list[str]:
        values = split_values(text)
        unknown = [value for value in values if value not in type_choices]
        if unknown:
            raise argparse.ArgumentTypeError(f"invalid choice: {', '.join(unknown)} (choose from {', '.join(type_choices)})")
        return values

    group = parser.add_argument_group(
        "filters",
        "Each takes several values: repeat the flag or separate them with a comma (no space after it); "
        "a concept matching any one is kept, and different filters combine with AND. "
        "Pass `list` alone to print the values in use, with counts, instead of querying.",
    )
    group.add_argument(
        "--type", action="extend", type=type_values, metavar="TYPE",
        help=f"concept type: {', '.join(sorted(TYPES_BY_DIR))} (texts = originals and translations)",
    )
    for field, help_text in _FILTER_HELP.items():
        group.add_argument(f"--{field}", action="extend", type=split_values, help=help_text)
    group.add_argument(
        "--verified", action="store_true",
        help="a switch, not a value filter: keep only concepts whose current text has a verification record (see `greek-knowledge verify`)",
    )


def find_concepts(
    repo_root: Path,
    *,
    type: Selection = None,
    level: Selection = None,
    author: Selection = None,
    period: Selection = None,
    dialect: Selection = None,
    work: Selection = None,
    language: Selection = None,
    verified: bool = False,
) -> list[tuple[Path, ConceptFile]]:
    """Return every (path, ConceptFile) under repo_root's words/grammar/
    culture/texts trees matching every filter given (None or empty = no
    constraint on that dimension). A filter is one value or a collection of
    them, any one of which matches; different filters combine with AND.
    `type` is a concept type; `period` values may be `from..to` ranges of
    PERIOD_ORDER; `work` is a case-insensitive substring of a text's work
    title and `language` its exact language code -- only texts carry either.
    `verified=True` keeps only concepts whose current text has a
    verification record (okf.current_verification): a rule edited after its
    review is dropped. Results are sorted by path."""
    matches: list[tuple[Path, ConceptFile]] = []
    concept_dirs = _CONCEPT_DIRS
    accepted_types = set(_values(type))
    if accepted_types:
        wanted_dirs = {_DIR_BY_TYPE[t] for t in accepted_types if t in _DIR_BY_TYPE}
        concept_dirs = tuple(dirname for dirname in _CONCEPT_DIRS if dirname in wanted_dirs)
    levels = _values(level)
    authors = _values(author)
    periods = _selected_periods(period)
    dialects = _values(dialect)
    works = _values(work)
    languages = _values(language)
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
            if accepted_types and concept.type not in accepted_types:
                continue
            if levels and not _level_matches(concept, levels):
                continue
            if authors and not _author_matches(concept, authors):
                continue
            if periods is not None and not _period_matches(concept, periods):
                continue
            if dialects and not _dialect_matches(concept, dialects):
                continue
            if works and not _work_matches(concept, works):
                continue
            if languages and not _language_matches(concept, languages):
                continue
            if verified and okf.current_verification(concept) is None:
                continue
            matches.append((path, concept))
    return sorted(matches, key=lambda pair: pair[0])
