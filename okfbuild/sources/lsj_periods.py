"""Resolves the approximate historical period (century + era) of the
author/work behind an LSJ citation, from two real sources: the Diorisis
corpus's catalog.tsv (work-level dates for ~800 ancient Greek works) and
LSJ's own front-matter "I. Authors and Works" list (dates for ~900 more,
including many Diorisis doesn't cover). A third, derived table (built by
scanning the LSJ dump itself) joins the two: LSJ citations carry a TLG
author id but not always an abbreviation LSJ's front matter would
recognize, so build_tlg_author_abbreviation_map() records which
abbreviation(s) co-occur with which TLG author id in the real markup.

Deliberately decoupled from okfbuild.sources.lsj_index: this module
resolves *when* an author/work is from; lsj_index.py resolves *what*
citations exist. See period_for_citation()'s docstring for the exact
resolution order between the two date sources.
"""

import csv
import json
import logging
import math
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import defusedxml.ElementTree as ET

from okfbuild.sources.lsj_index import _LSJXMLParser, _local_name

if TYPE_CHECKING:
    from okfbuild.sources.lsj_index import LSJCitation

logger = logging.getLogger(__name__)

_TLG_MAP_CACHE_FORMAT_VERSION = 1


def _ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _format_period_label(centuries: "tuple[int, ...]", era: str, uncertain: bool) -> str:
    """"iii or ii B.C." (uncertain=True) renders ascending ("2nd or 3rd c.
    BC") even though `centuries` itself preserves the source's own
    descending order (3, 2) -- the tuple keeps the source's own order,
    the label doesn't. A span (uncertain=False, e.g. "i/ii A.D." ->
    (1, 2)) renders in the given order with "/" instead, which already
    is ascending for every real span this project's data actually
    contains, so no separate sort is needed there."""
    if uncertain:
        parts = [_ordinal(c) for c in sorted(centuries)]
        return f"{' or '.join(parts)} c. {era}"
    parts = [_ordinal(c) for c in centuries]
    return f"{'/'.join(parts)} c. {era}"


@dataclass(frozen=True)
class Period:
    """A structured, uncertainty-preserving period -- never collapse
    source ambiguity into a single guessed value. `centuries` can have
    more than one element for a genuinely uncertain/spanning date (e.g.
    "iii or ii B.C." -> centuries=(3, 2), uncertain=True; "i/ii A.D." ->
    centuries=(1, 2), uncertain=False since that's a span, not a
    disagreement). `era` has a third value, "BC/AD", for the real
    era-spanning format "i B.C./i A.D." (the number doesn't change
    across the boundary, only which era it's in is ambiguous). `label`
    is the final rendering-ready string, computed once here so callers
    (e.g. render_lsj_entry(), a later section) never reformat century
    numbers themselves."""

    centuries: "tuple[int, ...]"
    era: Literal["BC", "AD", "BC/AD"]
    uncertain: bool = False
    label: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", _format_period_label(self.centuries, self.era, self.uncertain))


def _year_to_century(year: int) -> int:
    magnitude = abs(year)
    if magnitude == 0:
        return 1
    return math.ceil(magnitude / 100)


_ROMAN_VALUES = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}


def _roman_to_int(text: str) -> "int | None":
    text = text.lower()
    if not text or any(ch not in _ROMAN_VALUES for ch in text):
        return None
    total = 0
    previous = 0
    for ch in reversed(text):
        value = _ROMAN_VALUES[ch]
        if value < previous:
            total -= value
        else:
            total += value
            previous = value
    return total


def _normalize_era(text: str) -> Literal["BC", "AD"]:
    compact = text.upper().replace(".", "").replace(" ", "")
    return "BC" if compact == "BC" else "AD"


_CENTURY = r"[ivxlcdm]+"
_ERA = r"B\.?\s?C\.?|A\.?\s?D\.?"
_TRAILING_UNCERTAINTY_RE = re.compile(r"\s*\(\?\)\s*$")
_WRAPPING_PARENS_RE = re.compile(r"^\((.*)\)$")
_ERA_SPAN_SLASH_RE = re.compile(
    rf"^(?P<c1>{_CENTURY})\.?\s*B\.?\s?C\.?\s*/\s*(?P=c1)\.?\s*A\.?\s?D\.?$", re.IGNORECASE
)
_ERA_SPAN_OR_RE = re.compile(
    rf"^(?P<c1>{_CENTURY})\.?\s*B\.?\s?C\.?\s+or\s+(?P=c1)\.?\s*A\.?\s?D\.?$", re.IGNORECASE
)
_NESTED_UNCERTAIN_RE = re.compile(
    rf"^(?P<c1>{_CENTURY})\.?\s*\(\s*(?P<c2>{_CENTURY})\.?\s*\?\s*\)\s*(?P<era>{_ERA})$", re.IGNORECASE
)
_OR_RE = re.compile(rf"^(?P<c1>{_CENTURY})\.?\s+or\s+(?P<c2>{_CENTURY})\.?\s*(?P<era>{_ERA})$", re.IGNORECASE)
_CENTURY_SPAN_RE = re.compile(rf"^(?P<c1>{_CENTURY})\.?\s*/\s*(?P<c2>{_CENTURY})\.?\s*(?P<era>{_ERA})$", re.IGNORECASE)
_CIRCA_YEAR_RE = re.compile(rf"^ca?\.\s*(?P<year>\d+)\s*(?P<era>{_ERA})$", re.IGNORECASE)
_YEAR_RANGE_RE = re.compile(rf"^(?P<y1>\d+)\s*-\s*(?P<y2>\d+)\s*(?P<era>{_ERA})$")
# A single leading word/phrase (e.g. the real "translated iv B.C.") is
# tolerated here, but nowhere else -- every other pattern is fully
# anchored, so a genuinely malformed or truncated string (the real "B.C."
# with no numeral, or "iv B" missing its "C.") still correctly falls
# through to the unparsed/None case below rather than being guessed at.
_SIMPLE_RE = re.compile(rf"^(?:.*\s)?(?P<c1>{_CENTURY})\.?\s*(?P<era>{_ERA})$", re.IGNORECASE)


def parse_date_text(raw: str) -> "Period | None":
    """Parse one of LSJ's free-text front-matter date strings into a
    structured Period, or None if the text doesn't match any recognized
    shape -- logged as a warning with the full raw string, never
    silently dropped, so gaps in this parser's coverage stay visible.
    Covers every distinct format actually found in the real front
    matter's List I (verified directly, see
    test_parse_date_text_covers_every_real_frontmatter_format), except 3
    isolated real data defects deliberately left as documented None
    cases rather than guessed at: a bare "B.C." with no century at all,
    "iv B" (missing its ".C."), and "<*>v/v A.D." (a corrupted "iv/v
    A.D." -- the "<*>" is stray Beta-Code-style markup that leaked into
    the plain-text date field). None of these is a systematic format
    this parser should learn to guess around -- each is a one-off
    encoding mistake in the source data."""
    text = raw.strip()
    uncertain = bool(_TRAILING_UNCERTAINTY_RE.search(text))
    if uncertain:
        text = _TRAILING_UNCERTAINTY_RE.sub("", text).strip()

    wrap_match = _WRAPPING_PARENS_RE.match(text)
    if wrap_match:
        # LSJ's own editorial convention: wrapping an entire date in
        # parentheses marks it as inferred, not directly stated -- treat
        # the same as an explicit "(?)" uncertainty marker.
        text = wrap_match.group(1).strip()
        uncertain = True

    match = _ERA_SPAN_SLASH_RE.match(text)
    if match:
        century = _roman_to_int(match.group("c1"))
        if century is not None:
            return Period(centuries=(century,), era="BC/AD", uncertain=uncertain)

    match = _ERA_SPAN_OR_RE.match(text)
    if match:
        century = _roman_to_int(match.group("c1"))
        if century is not None:
            return Period(centuries=(century,), era="BC/AD", uncertain=True)

    match = _NESTED_UNCERTAIN_RE.match(text)
    if match:
        c1, c2 = _roman_to_int(match.group("c1")), _roman_to_int(match.group("c2"))
        if c1 is not None and c2 is not None:
            return Period(centuries=(c1, c2), era=_normalize_era(match.group("era")), uncertain=True)

    match = _OR_RE.match(text)
    if match:
        c1, c2 = _roman_to_int(match.group("c1")), _roman_to_int(match.group("c2"))
        if c1 is not None and c2 is not None:
            return Period(centuries=(c1, c2), era=_normalize_era(match.group("era")), uncertain=True)

    match = _CENTURY_SPAN_RE.match(text)
    if match:
        c1, c2 = _roman_to_int(match.group("c1")), _roman_to_int(match.group("c2"))
        if c1 is not None and c2 is not None:
            return Period(centuries=(c1, c2), era=_normalize_era(match.group("era")), uncertain=uncertain)

    match = _CIRCA_YEAR_RE.match(text)
    if match:
        # "circa" is itself an uncertainty marker -- always True here,
        # independent of any "(?)"/wrapping-parens already seen above.
        era = _normalize_era(match.group("era"))
        signed_year = -int(match.group("year")) if era == "BC" else int(match.group("year"))
        return Period(centuries=(_year_to_century(signed_year),), era=era, uncertain=True)

    match = _YEAR_RANGE_RE.match(text)
    if match:
        # A birth-death year range (e.g. the real "384-322 B.C." for
        # Demosthenes), not century notation -- convert each year to its
        # own century; a range that happens to fall in one century
        # collapses to a single-element tuple, otherwise a genuine span
        # (not "uncertain": a lifespan crossing a century boundary is a
        # definite fact, not a disagreement between sources).
        era = _normalize_era(match.group("era"))
        sign = -1 if era == "BC" else 1
        c1 = _year_to_century(sign * int(match.group("y1")))
        c2 = _year_to_century(sign * int(match.group("y2")))
        centuries = (c1,) if c1 == c2 else (c1, c2)
        return Period(centuries=centuries, era=era, uncertain=uncertain)

    match = _SIMPLE_RE.match(text)
    if match:
        century = _roman_to_int(match.group("c1"))
        if century is not None:
            return Period(centuries=(century,), era=_normalize_era(match.group("era")), uncertain=uncertain)

    logger.warning("Unrecognized LSJ date-text format: %r", raw)
    return None


def _iter_diorisis_rows(tsv_path: Path) -> "Iterator[tuple[str, str, int]]":
    """Shared row-extraction for parse_diorisis_catalog() and
    _build_diorisis_author_fallback() -- both need every row's
    (tlgAuthor, tlgId, signed year), so this reads and validates
    catalog.tsv exactly once per call site instead of each function
    opening and re-parsing the same file independently. Yields
    (tlgAuthor, tlgId) already zero-padded to CTS URN convention
    (4-digit author, 3-digit work) regardless of the raw file's own
    padding -- read as strings throughout, never cast through int, since
    a leading zero is significant here. A row with an unparseable
    date/id is logged and skipped, not raised -- AttributeError covers a
    short row: DictReader fills its missing trailing columns with None,
    not a KeyError, and .strip() on that None is what actually raises."""
    with open(tsv_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            try:
                year = int(row["date"].strip())
                tlg_author = row["tlgAuthor"].strip().zfill(4)
                tlg_id = row["tlgId"].strip().zfill(3)
            except (ValueError, KeyError, AttributeError):
                logger.warning("Diorisis catalog row with unparseable date/id fields: %r", row)
                continue
            yield tlg_author, tlg_id, year


def parse_diorisis_catalog(tsv_path: Path) -> "dict[tuple[str, str], Period]":
    """Parse Diorisis's catalog.tsv (header: author, title, tlgAuthor,
    tlgId, lang, date, genre, subgenre; one row per WORK) into
    {(tlgAuthor, tlgId): Period}.

    The real, live catalog.tsv (verified directly) has 2 (tlgAuthor,
    tlgId) keys that repeat across more than one row -- Aristotle's
    "Economics"/"Oeconomica II" (2 alternate titles for the same work)
    and Diodorus Siculus's Bibliotheca Historica (split into 3 rows by
    book-range, all sharing tlgId "001"). Harmless here: every duplicate
    row for a given key carries the identical `date`, so last-row-wins
    produces the same Period regardless of which duplicate "wins" -- not
    treated as an error."""
    result: "dict[tuple[str, str], Period]" = {}
    for tlg_author, tlg_id, year in _iter_diorisis_rows(tsv_path):
        era: Literal["BC", "AD"] = "BC" if year < 0 else "AD"
        result[(tlg_author, tlg_id)] = Period(centuries=(_year_to_century(year),), era=era, uncertain=False)
    return result


def _build_diorisis_author_fallback(tsv_path: Path) -> "dict[str, Period]":
    """Groups catalog.tsv rows by tlgAuthor and keeps only the earliest
    (numerically smallest signed year, i.e. chronologically first) dated
    work's Period per author -- via the same _iter_diorisis_rows() rows
    parse_diorisis_catalog() reads, not derived from that function's
    already-Period-ified dict, because Period doesn't retain the
    original signed year needed to compare "earliest" across the BC/AD
    boundary."""
    earliest_year: "dict[str, int]" = {}
    earliest_period: "dict[str, Period]" = {}
    for tlg_author, _tlg_id, year in _iter_diorisis_rows(tsv_path):
        if tlg_author in earliest_year and year >= earliest_year[tlg_author]:
            continue
        earliest_year[tlg_author] = year
        era: Literal["BC", "AD"] = "BC" if year < 0 else "AD"
        earliest_period[tlg_author] = Period(centuries=(_year_to_century(year),), era=era, uncertain=False)
    return earliest_period


_BRACKETED_ABBREVIATION_RE = re.compile(r"\[([^\[\]]+)\]")


def parse_lsj_frontmatter_authors(front_matter_xml_path: Path) -> "dict[str, Period]":
    """Parse LSJ's own front-matter "I. Authors and Works" list (scoped
    to the <div1> whose direct <head> reads exactly that -- the file has
    4 other, differently-shaped lists, e.g. "II. Epigraphical
    Publications", that must not be included) into
    {bracketed abbreviation (e.g. "Hom."): Period}, via parse_date_text(),
    for items with an explicit <date>. Authors without a <date> (Homer's
    own item, deliberately, per LSJ's own preface) are simply absent --
    callers must not treat a missing key as an error. The abbreviation is
    extracted via bracket-matching specifically, not "X. = Y" text
    (Homer's own item continues with unbracketed "Il. = Ilias" etc. for
    its sub-works -- those must not be misparsed as separate author
    entries). An item with no complete bracket pair (including a real,
    malformed case where a bracket pair is split across two sibling
    <item> elements) is skipped silently, the same "missing data isn't an
    error" tolerance as the no-<date> case. Uses _LSJXMLParser (imported
    from lsj_index.py) for the same security reasons _load_entries()
    does."""
    root = ET.parse(front_matter_xml_path, parser=_LSJXMLParser()).getroot()

    target_div1 = None
    for div1 in root.iter():
        if _local_name(div1.tag) != "div1":
            continue
        head = next((child for child in div1 if _local_name(child.tag) == "head"), None)
        if head is not None and "".join(head.itertext()).strip() == "I. Authors and Works":
            target_div1 = div1
            break
    if target_div1 is None:
        logger.warning("No \"I. Authors and Works\" div1 found in %s", front_matter_xml_path)
        return {}

    result: "dict[str, Period]" = {}
    for item in target_div1.iter():
        if _local_name(item.tag) != "item":
            continue
        bracket_match = _BRACKETED_ABBREVIATION_RE.search("".join(item.itertext()))
        if not bracket_match:
            continue
        date_el = next((child for child in item.iter() if _local_name(child.tag) == "date"), None)
        if date_el is None:
            continue
        period = parse_date_text("".join(date_el.itertext()))
        if period is not None:
            result[bracket_match.group(1).strip()] = period
    return result


_CTS_URN_AUTHOR_RE = re.compile(r"^urn:cts:greekLit:tlg(\d{4})\.")


def collect_bibl_author_pairs_from_root(root, source_label: str = "<root>") -> "Iterator[tuple[str, str]]":
    """Yield (tlgAuthor, abbreviation) pairs from every <bibl> in an
    ALREADY-PARSED tree (`root`, an Element) whose n= attribute is a real
    CTS URN, reading the abbreviation from that same <bibl>'s CHILD
    <author> element (verified directly against the real dump -- not a
    sibling relationship). A <bibl> with a matching URN but no (or an
    empty) child <author> is skipped, not a crash -- logged at DEBUG, not
    WARNING: verified directly against the real full dump that this is
    the ordinary case for a citation continuing the same work as a
    preceding one (e.g. a second passage-only <bibl> right after a fuller
    one that already named the author), not an anomaly -- 72,567 real
    occurrences across the full dump, none of them a data problem.

    Takes an already-parsed root (not a file path) specifically so a
    caller that has ALSO already parsed the same file for its own
    purposes -- okfbuild.sources.lsj_index._load_entries(), for the
    single-pass requirement -- can reuse that same parse instead of
    reading and reparsing the file a second time. `source_label` is only
    used for the debug log message (a file path when the caller has one,
    otherwise a generic placeholder)."""
    for bibl in root.iter():
        if _local_name(bibl.tag) != "bibl":
            continue
        n_attr = bibl.get("n")
        if not n_attr:
            continue
        urn_match = _CTS_URN_AUTHOR_RE.match(n_attr)
        if not urn_match:
            continue
        author_el = next((child for child in bibl if _local_name(child.tag) == "author"), None)
        author_text = "".join(author_el.itertext()).strip() if author_el is not None else ""
        if not author_text:
            logger.debug(
                "bibl with CTS URN %r has no (or empty) child <author> in %s -- skipping", n_attr, source_label
            )
            continue
        yield urn_match.group(1), author_text


def build_tlg_author_abbreviation_map(tei_xml_dir: Path) -> "dict[str, set[str]]":
    """Collect {tlgAuthor (4-digit, zero-padded): {abbreviation, ...}}
    across all of tei_xml_dir's *.xml files (see
    collect_bibl_author_pairs_from_root() for the per-file logic). Most
    tlgAuthor values map to exactly one abbreviation; some map to more
    than one (a real, confirmed case: tlg0059 -> {"Pl.", "Id."}) -- never
    silently pick one here; the caller resolving a specific citation
    (LSJPeriodMap) decides how to disambiguate."""
    result: "dict[str, set[str]]" = {}
    for xml_file in sorted(Path(tei_xml_dir).glob("*.xml")):
        root = ET.parse(xml_file, parser=_LSJXMLParser()).getroot()
        for tlg_author, author_text in collect_bibl_author_pairs_from_root(root, str(xml_file)):
            result.setdefault(tlg_author, set()).add(author_text)
    return result


def _tlg_map_source_signature(tei_xml_dir: Path) -> list:
    # Lists, not tuples: a tuple survives one in-memory comparison fine,
    # but a JSON round-trip (json.dumps/json.loads, used to persist this
    # across build() calls -- see _read_tlg_map_cache) turns a tuple into
    # a list, so comparing a freshly-computed tuple against a
    # freshly-loaded list would never match and the cache would silently
    # never hit. Building the signature as lists from the start keeps
    # both sides of that comparison the same shape.
    return sorted([f.name, f.stat().st_mtime] for f in Path(tei_xml_dir).glob("*.xml"))


def _read_tlg_map_cache(cache_path: Path) -> "dict | None":
    """Returns the parsed cache dict, or None if it's missing, corrupt,
    or a format_version mismatch (all three treated as "no usable cache"
    -- the caller rebuilds from scratch either way). Deliberately NOT
    reusing llm_gap_filler.load_versioned_json() despite the near-
    identical validation shape: that helper is @cache-memoized per
    (path, version, label), correct for its own read-only-after-write-
    by-a-different-process use case, but wrong here -- _load_or_build_tlg_map()
    can read this same path, detect staleness, rebuild, and overwrite it
    more than once within a single process (exactly what the caching
    tests below do), and a memoized read would keep returning the
    pre-rebuild content on a later call in the same process."""
    if not cache_path.is_file():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Corrupt TLG-abbreviation-map cache at %s -- rebuilding", cache_path)
        return None
    if data.get("format_version") != _TLG_MAP_CACHE_FORMAT_VERSION:
        logger.warning(
            "TLG-abbreviation-map cache at %s has unexpected format_version %r -- rebuilding",
            cache_path, data.get("format_version"),
        )
        return None
    return data


def tlg_map_cache_is_fresh(tei_xml_dir: Path, cache_path: Path) -> bool:
    """True if _load_or_build_tlg_map() would return cached data without
    rescanning tei_xml_dir. Exposed publicly so a caller that ALSO needs
    to scan the same dump for another purpose -- e.g. okfbuild.sources.
    lsj_index._load_entries()'s own headword-index scan -- can decide
    ahead of time whether to share that one scan (via
    LSJPeriodMap.build()'s precomputed_tlg_abbreviation_map parameter)
    rather than triggering two independent full scans, without
    duplicating (and risking desyncing from) this module's own
    staleness-check logic."""
    cached = _read_tlg_map_cache(cache_path)
    return cached is not None and cached.get("source_signature") == _tlg_map_source_signature(tei_xml_dir)


def _write_tlg_map_cache(cache_path: Path, source_signature: list, tlg_map: "dict[str, set[str]]") -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            {
                "format_version": _TLG_MAP_CACHE_FORMAT_VERSION,
                "source_signature": source_signature,
                "map": {tlg_author: sorted(abbrevs) for tlg_author, abbrevs in tlg_map.items()},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _load_or_build_tlg_map(
    tei_xml_dir: Path, cache_path: Path, precomputed_map: "dict[str, set[str]] | None" = None
) -> "dict[str, set[str]]":
    """A plain single JSON file, not KeyedJsonCache (that's shaped for
    many independent per-key files; this is one combined artifact).
    Staleness is a source_signature comparison (sorted (filename, mtime)
    pairs across tei_xml_dir's *.xml files) -- any file added, removed,
    or touched triggers a full rebuild; a match skips the 270MB scan
    entirely.

    `precomputed_map`: for a caller that already knows the cache is
    stale (via tlg_map_cache_is_fresh()) and has ALREADY scanned
    tei_xml_dir for another purpose, sharing that one scan with
    _load_entries() instead of this function doing its own, independent
    second scan -- skips straight to persisting the given map. None (the
    default) leaves the normal check-then-scan-if-needed behavior
    completely unchanged."""
    current_signature = _tlg_map_source_signature(tei_xml_dir)

    if precomputed_map is not None:
        _write_tlg_map_cache(cache_path, current_signature, precomputed_map)
        return precomputed_map

    cached = _read_tlg_map_cache(cache_path)
    if cached is not None and cached.get("source_signature") == current_signature:
        return {tlg_author: set(abbrevs) for tlg_author, abbrevs in cached["map"].items()}

    fresh_map = build_tlg_author_abbreviation_map(tei_xml_dir)
    _write_tlg_map_cache(cache_path, current_signature, fresh_map)
    return fresh_map


def _frontmatter_file(tei_xml_dir: Path) -> Path:
    """List I ("Authors and Works") is duplicated identically across
    grc.lsj.perseus-eng1.xml, -eng18.xml, and -eng19.xml -- always read
    from -eng1.xml for determinism."""
    return Path(tei_xml_dir) / "grc.lsj.perseus-eng1.xml"


_FRONTMATTER_CACHE_FORMAT_VERSION = 1


def _period_to_dict(period: Period) -> dict:
    return {"centuries": list(period.centuries), "era": period.era, "uncertain": period.uncertain}


def _period_from_dict(data: dict) -> Period:
    # `label` isn't stored -- it's always deterministically derivable
    # from the other 3 fields, so __post_init__ recomputes it fresh
    # rather than round-tripping a 4th, redundant value.
    return Period(centuries=tuple(data["centuries"]), era=data["era"], uncertain=data["uncertain"])


def _frontmatter_cache_path(tlg_map_cache_path: Path) -> Path:
    """Derived from the TLG-map cache_path (same directory, a sibling
    filename) rather than a second constructor parameter on
    LSJPeriodMap.build() -- keeps that already-tested public signature
    unchanged."""
    return tlg_map_cache_path.parent / f"{tlg_map_cache_path.stem}-frontmatter.json"


def _read_frontmatter_cache(cache_path: Path, source_mtime: float) -> "dict[str, Period] | None":
    """Returns the cached {abbreviation: Period} dict, or None if the
    cache is missing, corrupt, a format_version mismatch, or the source
    file's mtime has changed since the cache was written -- all treated
    identically as "rebuild", never a crash or silently stale data
    (same shape as _read_tlg_map_cache() above, for a single-file
    staleness check instead of a 27-file signature)."""
    if not cache_path.is_file():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Corrupt LSJ front-matter cache at %s -- rebuilding", cache_path)
        return None
    if data.get("format_version") != _FRONTMATTER_CACHE_FORMAT_VERSION or data.get("source_mtime") != source_mtime:
        return None
    return {abbreviation: _period_from_dict(p) for abbreviation, p in data["authors"].items()}


def _load_or_parse_frontmatter_authors(front_matter_xml_path: Path, cache_path: Path) -> "dict[str, Period]":
    """Caches parse_lsj_frontmatter_authors()'s output, keyed by the
    source file's own mtime -- unlike _load_or_build_tlg_map()'s 27-file
    signature (needed since that scan spans the whole dump), front-matter
    parsing depends on exactly one file, so a single mtime check is
    sufficient.

    Originally left uncached deliberately (an earlier version of this
    module's own docstring reasoned "parse_diorisis_catalog() and
    parse_lsj_frontmatter_authors() are cheap... and are simply re-run
    fresh on every build() call; only the TLG-abbreviation map is
    cached") -- revisited after direct measurement showed this "cheap"
    parse is actually a real, recurring cost on every single
    LSJPeriodMap.build() call (~6s, confirmed via a real end-to-end
    timing run against the live dump), not a one-time bootstrap cost
    the way the TLG-map's own 270MB scan is."""
    source_mtime = front_matter_xml_path.stat().st_mtime
    cached = _read_frontmatter_cache(cache_path, source_mtime)
    if cached is not None:
        return cached

    fresh = parse_lsj_frontmatter_authors(front_matter_xml_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            {
                "format_version": _FRONTMATTER_CACHE_FORMAT_VERSION,
                "source_mtime": source_mtime,
                "authors": {abbreviation: _period_to_dict(period) for abbreviation, period in fresh.items()},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return fresh


class LSJPeriodMap:
    """Combines Diorisis (work- and author-level), LSJ's own front
    matter, and the derived TLG-author-abbreviation join table into one
    lookup. Built once per process via build(); both the derived
    TLG-abbreviation map (the part that needs a full 27-file dump scan)
    and the front-matter authors parse (a single ~10MB file, but still a
    real, measured cost repeated on every build() call otherwise) are
    persisted to their own small cached JSON artifacts near cache_path
    so a later build() call with unchanged source files skips both."""

    def __init__(
        self,
        diorisis_work: "dict[tuple[str, str], Period]",
        diorisis_author_fallback: "dict[str, Period]",
        frontmatter: "dict[str, Period]",
        tlg_abbreviation_map: "dict[str, set[str]]",
    ) -> None:
        self._diorisis_work = diorisis_work
        self._diorisis_author_fallback = diorisis_author_fallback
        self._frontmatter = frontmatter
        self._tlg_abbreviation_map = tlg_abbreviation_map

    @classmethod
    def build(
        cls,
        tei_xml_dir: Path,
        diorisis_catalog_path: Path,
        cache_path: Path,
        precomputed_tlg_abbreviation_map: "dict[str, set[str]] | None" = None,
    ) -> "LSJPeriodMap":
        """`precomputed_tlg_abbreviation_map`: passed straight through to
        _load_or_build_tlg_map() -- see its own docstring. None (the
        default) leaves this classmethod's existing check-then-scan-if-
        needed behavior completely unchanged."""
        tei_xml_dir = Path(tei_xml_dir)
        diorisis_catalog_path = Path(diorisis_catalog_path)
        cache_path = Path(cache_path)
        return cls(
            diorisis_work=parse_diorisis_catalog(diorisis_catalog_path),
            diorisis_author_fallback=_build_diorisis_author_fallback(diorisis_catalog_path),
            frontmatter=_load_or_parse_frontmatter_authors(
                _frontmatter_file(tei_xml_dir), _frontmatter_cache_path(cache_path)
            ),
            tlg_abbreviation_map=_load_or_build_tlg_map(
                tei_xml_dir, cache_path, precomputed_map=precomputed_tlg_abbreviation_map
            ),
        )

    def period_for_citation(self, citation: "LSJCitation") -> "Period | None":
        """Resolution order: (1) Diorisis work-level, when both
        tlg_author and tlg_work are present and a matching row exists;
        (2) Diorisis author-level fallback (that author's earliest dated
        work), when only tlg_author resolves; (3) LSJ's own front-matter
        table, keyed by an abbreviation -- citation.author_abbreviation
        directly when tlg_author isn't present or when it's already one
        of build_tlg_author_abbreviation_map()'s known candidates for
        that tlg_author (kept as-is, never overridden just because a
        single candidate also exists); otherwise, when tlg_author IS
        present, whichever candidate is unambiguous (exactly one known
        candidate, used even though citation.author_abbreviation itself
        didn't match it -- e.g. missing or a one-off variant) -- a
        multiple-candidate case that citation.author_abbreviation does
        NOT confirm is treated as unresolved at this step, never
        guessed; (4) None, if nothing above resolves. Only reads
        citation.author_abbreviation, .tlg_author, .tlg_work -- .text
        and .dialects are irrelevant here."""
        tlg_author = citation.tlg_author.zfill(4) if citation.tlg_author else None

        if tlg_author and citation.tlg_work:
            period = self._diorisis_work.get((tlg_author, citation.tlg_work.zfill(3)))
            if period is not None:
                return period

        if tlg_author:
            period = self._diorisis_author_fallback.get(tlg_author)
            if period is not None:
                return period

        abbreviation = citation.author_abbreviation
        if tlg_author:
            candidates = self._tlg_abbreviation_map.get(tlg_author)
            if candidates and abbreviation not in candidates:
                if len(candidates) == 1:
                    abbreviation = next(iter(candidates))
                else:
                    abbreviation = None

        if abbreviation is not None:
            return self._frontmatter.get(abbreviation)
        return None
