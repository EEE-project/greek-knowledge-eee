"""Parses Perseus LSJ TEI-XML into a headword-keyed index.

The real files' headwords and Greek-tagged body text are Beta Code (e.g.
"no/stos" for νόστος), not Unicode Greek -- converted via the `beta_code`
package. See _extract_text()'s docstring for why this must be
element-aware (entries mix Beta Code Greek with plain English prose).

Security: uses defusedxml, not stdlib xml.etree.ElementTree — ElementTree
(backed by expat) is not safe against internal-entity ("billion laughs")
expansion by default. This applies even to trusted sources (Perseus's own
GitHub): parsed external data is treated the same way regardless of
source trust, since trust today isn't a guarantee against a compromised
file or a future different source reusing this same code path. See
_LSJXMLParser's docstring for why the real files need a narrower policy
than defusedxml's own default (their benign DTD-internal parameter
entities would otherwise be rejected too).
"""

import logging
import re
from dataclasses import asdict, dataclass, replace
from functools import lru_cache
from pathlib import Path

import beta_code
import defusedxml.ElementTree as ET

from okfbuild.sources.disk_cache import KeyedJsonCache

logger = logging.getLogger(__name__)

_ENTRY_TAGS = {"entryFree", "entry"}


@dataclass(frozen=True)
class LSJText:
    """A run of plain prose -- never carries citation metadata."""

    text: str


@dataclass(frozen=True)
class LSJCitation:
    """One citable unit (a <cit>, or an equivalent bare <bibl>-only
    reference -- see the scope-precedence table in
    _resolve_dialect_scope()'s docstring, from section-01's structural
    investigation). `dialects` is a tuple, not a single optional value:
    kept defensively for a citation that could in principle carry more
    than one dialect tag, though section-01's investigation found no
    confirmed real case of that actually happening for a genuine
    citation (as opposed to free-standing prose commentary, which never
    becomes an LSJCitation at all -- see below). `tlg_author`/`tlg_work`
    are the raw IDs parsed from a CTS URN when present (colon-delimited
    passage format, not the CTS spec's own period-delimited form --
    verified directly against the real dump); `author_abbreviation` is
    the bare <author> text. period is resolved later, by
    okfbuild.sources.lsj_periods.LSJPeriodMap, not during extraction."""

    text: str
    author_abbreviation: "str | None" = None
    tlg_author: "str | None" = None
    tlg_work: "str | None" = None
    dialects: "tuple[str, ...]" = ()


LSJSegment = LSJText | LSJCitation


@lru_cache(maxsize=None)
def _beta_code_to_greek(text: str) -> str:
    """Cached wrapper around beta_code.beta_code_to_greek() -- pure for
    every call site in this module (always called with one positional
    argument, no custom_map), and the same short fragments (case endings,
    particles, punctuation runs) recur constantly across the real ~270MB
    dump: measured 36.9% of all calls during a real full-dump load were on
    a string already seen earlier in the same run, and beta_code's own
    implementation rebuilds its translation table and recompiles a regex
    on every call regardless of input. Unbounded cache is safe here --
    _load_entries() runs at most once per process (memoized by
    CachedLSJIndex._full_index), bounded by the same order of magnitude of
    short strings the process already retains for its lifetime either
    way."""
    return beta_code.beta_code_to_greek(text)


class _LSJXMLParser(ET.DefusedXMLParser):
    """The real Perseus TEI files' DOCTYPE declares 2 parameter entities:
    `%TEI.XML "INCLUDE"` (genuinely internal, a plain string value) and
    `%PersDict PUBLIC "..." "http://www.perseus.tufts.edu/DTD/1.0/PersDict.dtd"`
    (an EXTERNAL parameter entity, actually referenced via `%PersDict;` in
    the internal subset -- verified directly against the real downloaded
    files, not assumed). Neither can be exploited for a "billion
    laughs"-style body-expansion attack regardless: parameter entities
    (`%name;`) are usable only within the DTD itself, never in document
    body content, unlike general entities (`&name;`, referenced from the
    document body -- exactly what a real attack payload uses). Safe from
    the external reference specifically because Python's expat parser is
    non-validating by default and never resolves a parameter entity's
    content beyond its declaration -- `%PersDict;` is never actually
    fetched or expanded (verified empirically: parsing a real file with
    this override does not touch the network) -- with `forbid_external`
    (inherited, unchanged) as a second line of defense should that ever
    stop being true. DefusedXMLParser.defused_entity_decl forbids ALL
    entity declarations unconditionally, parameter or general; this
    override narrows that to general entities only, preserving the actual
    security boundary instead of widening it."""

    def defused_entity_decl(self, name, is_parameter_entity, value, base, sysid, pubid, notation_name):
        if is_parameter_entity:
            return
        super().defused_entity_decl(name, is_parameter_entity, value, base, sysid, pubid, notation_name)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _extract_text(el, in_greek: bool = False) -> str:
    """Concatenate `el`'s full text content, converting Beta Code to
    Unicode Greek only within an element (or a descendant of one) with
    `lang="greek"` -- entries mix Beta Code Greek quotations/orthography
    with plain English glosses and bibliographic abbreviations in the same
    entry (e.g. `<orth lang="greek">no/st-os</orth>, <tr>return home,</tr>
    <bibl><author>Hom.</author></bibl>`), and beta_code_to_greek() mangles
    plain English (e.g. "good" -> "γοοδ") if applied unconditionally.
    `child.tail` (text after a child's closing tag, before the next
    sibling) belongs to the PARENT's language context, not the child's --
    handled via the passed-down `in_greek`, not the child's own.

    Known limitation, inherent to Beta Code itself, not fixed: a literal
    parenthesis used editorially inside a `lang="greek"` span (e.g. a
    cross-reference like "(ne/omai)") is ambiguous with Beta Code's own
    breathing-mark notation ("(" = rough breathing) and gets misconverted
    -- a real, accepted imprecision in the source format, not a bug in
    this conversion step."""
    this_greek = in_greek or el.get("lang") == "greek"
    parts = []
    if el.text:
        parts.append(_beta_code_to_greek(el.text) if this_greek else el.text)
    for child in el:
        parts.append(_extract_text(child, this_greek))
        if child.tail:
            parts.append(_beta_code_to_greek(child.tail) if this_greek else child.tail)
    return "".join(parts)


_CTS_URN_RE = re.compile(r"^urn:cts:greekLit:tlg(?P<author>\d{4})(?:\.tlg(?P<work>\d{3}))?")


def _build_citation(el, in_greek: bool) -> LSJCitation:
    """Extract one LSJCitation's metadata from `el` (a <cit>, or a bare
    <bibl> standing on its own). `text` reuses _extract_text()'s existing
    Beta-Code-aware flattening, scoped to just this element -- the
    citation/prose text-rendering logic itself is unchanged by the
    dialect-scoping rewrite. `author_abbreviation`/`tlg_author`/
    `tlg_work` come from the first <bibl> descendant (or `el` itself, if
    it IS the <bibl>) -- verified directly against the full real dump
    (not assumed from a few samples): 0 of 159,473 real <cit> elements
    have 2+ <bibl> descendants, so "first" and "only" are equivalent in
    practice. `dialects` always
    starts empty here; _resolve_dialect_scope() fills it in afterward,
    since this element-local extraction has no visibility into the
    surrounding context a dialect tag's scope depends on."""
    text = " ".join(_extract_text(el, in_greek).split())
    bibl_el = el if _local_name(el.tag) == "bibl" else next(
        (d for d in el.iter() if _local_name(d.tag) == "bibl"), None
    )
    author_abbreviation = None
    tlg_author = None
    tlg_work = None
    if bibl_el is not None:
        author_el = next((c for c in bibl_el if _local_name(c.tag) == "author"), None)
        if author_el is not None:
            author_abbreviation = "".join(author_el.itertext()).strip() or None
        n_attr = bibl_el.get("n")
        if n_attr:
            urn_match = _CTS_URN_RE.match(n_attr)
            if urn_match:
                tlg_author = urn_match.group("author")
                tlg_work = urn_match.group("work")
    return LSJCitation(text=text, author_abbreviation=author_abbreviation, tlg_author=tlg_author, tlg_work=tlg_work)


@dataclass(frozen=True)
class _DialectMarker:
    """Phase-1 token: a <gramGrp> containing >=1 <gram type="dialect">.
    `raw_text` is that gramGrp's own flattened text (e.g. "Dor.") --
    needed only if Phase 2 decides this marker doesn't attach to
    anything (the free-standing-commentary case) and has to render it as
    plain prose instead of structured metadata."""

    dialects: "tuple[str, ...]"
    raw_text: str


@dataclass(frozen=True)
class _TransparentText:
    """Phase-1 token for text belonging to one of _TRANSPARENT_GRAMMAR_TAGS
    -- section-01's table (row 2/3) explicitly documents that Pattern B
    tolerates "intervening bare grammatical markup -- <per>/<number>/
    <tns>, etc." between a dialect marker and the citation it targets,
    with a real, directly-quoted corroborating example (e)fi/hmi's
    <gramGrp>Ion.</gramGrp> <per>3</per><number>pl.</number> <cit>...Hdt.
    ...</cit>). Unlike a plain str token, this NEVER counts as "real
    prose" for Phase 2's word-character adjacency check, regardless of
    its own content -- a person marker's text ("3") or a number marker's
    text ("pl.") would otherwise trip that check exactly like real prose
    would (both contain \\w characters), incorrectly flushing a pending
    dialect marker before it ever reaches its target citation."""

    text: str


_WORD_FORM_MARKER = object()  # Phase-1 token marking an <orth>/<foreign> position (a headword
# spelling or word-form variant) -- only ever compared by identity in Phase 2, same as _CACHE_MISS below.
_SENSE_BOUNDARY = object()  # Phase-1 token marking a <sense> position -- Pattern A's broad
# dialect inheritance resets here, per section-01's table.

# The tags section-01's investigation directly verified can appear
# between a dialect marker and its target citation without breaking
# adjacency. Not exhaustive by section-01's own account ("etc.") --
# these are only the ones with real, confirmed evidence; extend this set
# if a future real example needs another one, rather than guessing ahead
# of the evidence.
_TRANSPARENT_GRAMMAR_TAGS = {"per", "number", "tns"}


def _flatten_for_dialect_scope(el, in_greek: bool = False) -> list:
    """Phase 1 of dialect-aware extraction: walk `el`'s subtree in
    document order, producing a FLAT list mixing plain text (str),
    _DialectMarker instances, the _WORD_FORM_MARKER/_SENSE_BOUNDARY
    sentinels, and already-built LSJCitation objects (dialects=() for
    now -- Phase 2 fills them in) for each <cit> or bare <bibl>. A
    <cit>'s own internal <quote>/<bibl>
    structure is deliberately NOT flattened further -- the whole subtree
    collapses to one LSJCitation token, matching the invariant that
    every citable unit becomes exactly one LSJCitation.

    Keeping this a flat, single-level list (rather than preserving tree
    structure) is what makes Phase 2's left-to-right scope resolution
    tractable: the dialect-scoping rules in
    _resolve_dialect_scope()'s docstring are fundamentally about
    adjacency in the linearized token stream, not XML nesting depth --
    e.g. Pattern A's broad inheritance needs to flow from a dialect
    marker at one nesting level, through a <sense> element's opening,
    into that <sense>'s own children, which a purely tree-shaped
    recursive walk (each level blind to its siblings' state) can't
    express as simply as one linear scan can."""
    this_greek = in_greek or el.get("lang") == "greek"
    tokens: list = []
    if el.text:
        tokens.append(_beta_code_to_greek(el.text) if this_greek else el.text)
    for child in el:
        tag = _local_name(child.tag)
        if tag == "gramGrp":
            dialects = tuple(
                "".join(gram.itertext()).strip()
                for gram in child
                if _local_name(gram.tag) == "gram" and gram.get("type") == "dialect"
            )
            if dialects:
                raw_text = " ".join(_extract_text(child, this_greek).split())
                tokens.append(_DialectMarker(dialects, raw_text))
            else:
                tokens.extend(_flatten_for_dialect_scope(child, this_greek))
        elif tag in ("cit", "bibl"):
            tokens.append(_build_citation(child, this_greek))
        elif tag in ("orth", "foreign"):
            tokens.append(_WORD_FORM_MARKER)
            tokens.extend(_flatten_for_dialect_scope(child, this_greek))
        elif tag == "sense":
            tokens.append(_SENSE_BOUNDARY)
            tokens.extend(_flatten_for_dialect_scope(child, this_greek))
        elif tag in _TRANSPARENT_GRAMMAR_TAGS:
            text = _extract_text(child, this_greek)
            if text:
                tokens.append(_TransparentText(text))
        else:
            tokens.extend(_flatten_for_dialect_scope(child, this_greek))
        if child.tail:
            tokens.append(_beta_code_to_greek(child.tail) if this_greek else child.tail)
    return tokens


_WORD_CHAR_RE = re.compile(r"\w")


def _resolve_dialect_scope(tokens: list) -> "list[LSJSegment]":
    r"""Phase 2: a single left-to-right scan over Phase 1's flat token
    list, implementing section-01's verified scope-precedence table for
    <gram type="dialect"> (from this project's
    sections/section-01-structural-investigation.md, reproduced here as
    the required code comment documenting it):

      1. A <gramGrp> immediately (no intervening real prose) followed by
         an <orth>/<foreign> word-form marker: the dialect(s) describe
         that variant, and everything that follows inherits them (broad
         scope) until the next dialect marker or a <sense> boundary.
      2/3. A <gramGrp> immediately followed by a <cit>/bare <bibl>
         (directly, or through intervening bare grammatical markup --
         nothing "real" in between, e.g. <per>/<number>/<tns>, or a
         parenthetical wrapping right after a <foreign>-quoted form):
         the dialect(s) apply to ONLY that one citation, not persisted
         further -- these two real narrative shapes (a marker between
         two <cit>s; a marker in parens right after a quoted form)
         resolve identically here, since both are "adjacent-forward to
         exactly one citable unit."
      4. A <gramGrp> NOT immediately followed by a word-form marker or a
         citation (i.e. followed by real prose text instead) is free-
         standing lexicographic commentary, not attached to any citation
         or form -- its own text becomes part of the surrounding plain
         prose instead of structured metadata (the genuine inconsistency
         section-01 documented, with this as the chosen defensible
         default).
      5. Dialect abbreviations with no <gram type="dialect"> wrapper at
         all (plain prose, or inside a bare <bibl>'s <author> text) are
         out of structural scope by construction -- never specially
         recognized; they just pass through as ordinary text/citation
         content, same as before this section's changes.

    "Immediately"/"real prose" is decided by whether the text
    immediately following a dialect marker contains a word character
    (`\w`) -- pure whitespace or light punctuation (parens, commas)
    between the marker and the next structural element doesn't count as
    "real prose" and doesn't break adjacency (needed for the real
    parenthetical shape in rule 2/3, where a closing paren sits between
    the marker and its target). Two or more consecutive adjacent dialect
    markers (no resolution target in between) merge into one combined
    dialects tuple for whichever pattern ends up applying to them
    jointly -- covers the rare, real case of >1 dialect marker applying
    to one target, without a separate code path for it; the one directly
    verified real instance of this turned out to be case 4 (prose
    commentary), not a genuine multi-dialect citation, but the
    possibility isn't ruled out for markers this scan hasn't seen.

    Known limitation, not fixed (same spirit as _extract_text()'s own
    documented Beta-Code parenthesis-ambiguity limitation): case 1's
    broad inheritance is a mechanical "until the next marker/sense"
    rule, and real entries occasionally list several alternate dialectal
    forms/mentions in a row without a fresh <sense> between them (e.g.
    θεός's real entry: Boeot./Lacon. orth variants, then a bare,
    untagged <bibl>Cypr.</bibl> mention with nothing resetting scope in
    between) -- in that shape, the LAST active dialect can end up
    attached to a citation whose own text already names a *different*
    dialect. Measured directly against the full real dump: 15 of 14,939
    real dialect-tagged citations (0.1%) show this exact signature (the
    citation's own author_abbreviation or bare text is itself one of the
    10 known dialect abbreviations) -- rare enough, and not backed by
    section-01's own verified evidence for a more specific rule, that
    this is left as a documented imprecision rather than adding an
    unverified heuristic (e.g. "an untagged bare dialect-name mention
    resets scope") to guess around it."""
    segments: "list[LSJSegment]" = []
    text_parts: list[str] = []
    active_dialect: "tuple[str, ...]" = ()
    pending: "list[_DialectMarker]" = []

    def flush_text() -> None:
        if text_parts:
            combined = " ".join("".join(text_parts).split())
            if combined:
                segments.append(LSJText(combined))
            text_parts.clear()

    def flush_pending_as_prose() -> None:
        nonlocal pending
        for marker in pending:
            text_parts.append(marker.raw_text)
            text_parts.append(" ")
        pending = []

    def pending_dialects() -> "tuple[str, ...]":
        result: list[str] = []
        for marker in pending:
            result.extend(marker.dialects)
        return tuple(result)

    for token in tokens:
        if isinstance(token, _DialectMarker):
            pending.append(token)
        elif token is _WORD_FORM_MARKER:
            if pending:
                active_dialect = pending_dialects()
                pending = []
        elif token is _SENSE_BOUNDARY:
            flush_pending_as_prose()
            active_dialect = ()
        elif isinstance(token, LSJCitation):
            dialects = pending_dialects() if pending else active_dialect
            pending = []
            flush_text()
            segments.append(replace(token, dialects=dialects) if dialects else token)
        elif isinstance(token, _TransparentText):
            # Bare grammatical markup (<per>/<number>/<tns>) -- its text
            # still renders normally, but it never counts as "real
            # prose" for adjacency, unlike a plain str token.
            text_parts.append(token.text)
        else:  # plain text (str)
            if pending and _WORD_CHAR_RE.search(token):
                flush_pending_as_prose()
            text_parts.append(token)

    flush_pending_as_prose()
    flush_text()
    return segments


def _extract_segments(el, in_greek: bool = False) -> "list[LSJSegment]":
    """Entry-body extraction, replacing the old flat-string
    _extract_text() for that purpose (which is retained -- see its own
    docstring -- as the citation/prose-level text flattener
    _build_citation() and the dialect-marker prose fallback both still
    use). Flattens `el`'s subtree (Phase 1: _flatten_for_dialect_scope())
    then resolves dialect scope over the flattened stream (Phase 2:
    _resolve_dialect_scope()) -- see that function's docstring for the
    actual scope-precedence rules being implemented."""
    return _resolve_dialect_scope(_flatten_for_dialect_scope(el, in_greek))


def _load_entries(
    tei_xml_dir: Path,
    tlg_abbreviation_collector: "dict[str, set[str]] | None" = None,
) -> "dict[str, list[LSJSegment]]":
    """Parse the 27 Perseus LSJ TEI-XML files (~270MB, see
    claude-research.md §2.2 for the exact source) into a headword-keyed
    dict of segment lists.

    Security: the XML parser MUST have entity expansion and external
    entity resolution disabled/limited (protect against a "billion
    laughs"-style expansion bomb) even though this specific file comes
    from a trusted source (Perseus's own GitHub) — treat all parsed
    external data the same way regardless of source trust. Uses
    _LSJXMLParser (see its own docstring), not the bare defused default,
    since the real files' benign parameter-entity DOCTYPE would otherwise
    be rejected too. Headword keys (`key`/`n` attributes) are Beta Code
    in the real files (e.g. `key="no/stos"` for νόστος) -- converted via
    _beta_code_to_greek() (see its own docstring for why it's cached),
    safely a no-op on already-Unicode input (e.g. this module's own small
    hand-written test fixtures use real Greek characters directly, not
    Beta Code).

    Streaming: defusedxml.ElementTree.iterparse() does exist and was
    verified directly to correctly preserve _LSJXMLParser's security
    semantics (still rejects a billion-laughs payload when passed as its
    `parser=`) -- but iterparse() alone doesn't reduce peak memory unless
    the caller also explicitly elem.clear()s finished subtrees as it
    goes, which adds real complexity and correctness risk (accidentally
    clearing something still needed) for a code path that runs at most
    ONCE per process (CachedLSJIndex's whole design means a real course
    build only ever hits this on the very first genuinely new headword,
    if any). Not worth that tradeoff here -- kept as ET.parse()'s normal
    full-tree build, documented per this section's own requirement to
    investigate rather than assume.

    Real, confirmed bug this function fixes -- verified directly against
    the live dump, and NOT what the plan this section implements
    originally assumed: the plan's own motivating example was λέγω,
    reasoning that LSJ's real >=2 separate <entryFree> elements for it
    (distinct senses/etymologies, standard practice for a major
    polysemous verb) would collapse onto the identical post-Beta-Code-
    conversion dict key. Checked directly: this is false for λέγω
    specifically -- its real raw keys are "le/gw1"/"le/gw2" (LSJ's own
    homograph-numbering convention, a literal digit suffix in the XML's
    own `key` attribute), and beta_code.beta_code_to_greek() happens to
    PRESERVE that trailing digit for this particular word shape
    ("le/gw1" -> "λέγω1", "le/gw2" -> "λέγω2" -- verified directly, two
    distinct keys, no collision at all). A full scan of the real dump
    found the actual mechanism: 329 other digit-suffixed homograph pairs
    (e.g. raw keys "a)/atos1"/"a)/atos2") where beta_code_to_greek()
    inconsistently STRIPS the trailing digit instead ("ἄατος" both
    times) -- an internal quirk of that library, not of LSJ's own
    encoding, and not predictable from the word's spelling alone. 329 is
    exactly the "116,497 raw entries vs 116,168 previously-reported
    headwords" gap this project's own earlier research had already
    measured, confirming this -- not λέγω -- is the real, complete
    explanation for it. The fix itself doesn't depend on which of these
    two causes produced a given collision -- it merges whatever two (or
    more) entries land on an identical post-conversion key, regardless
    of why -- so this correction only changes the documented example,
    not any code behavior.

    Merges colliding entries instead of overwriting, inserting an
    explicit LSJText("\\n\\n") boundary between one homograph entry's
    final segment and the next one's first, so two genuinely distinct
    entries never run together without a break if a reader (or a later
    renderer) needs to tell where one ends and the next begins. The
    existing sorted-file-then-document-order iteration (unchanged)
    already gives this merge deterministic, stable ordering across the
    27 source files.

    If `tlg_abbreviation_collector` is given (a plain dict), it's
    populated in-place with {tlgAuthor: {abbreviation, ...}} pairs
    collected from the SAME per-file parse this function already does
    for entry extraction -- satisfies
    okfbuild.sources.lsj_periods.build_tlg_author_abbreviation_map()'s
    single-pass requirement (one read+parse per file, not two) for any
    caller that wants both products from one scan; existing callers
    (LSJIndex.load(), CachedLSJIndex, neither of which pass this) are
    completely unaffected and pay nothing extra for it. Nothing in this
    plan's scope currently constructs such a caller (that's SourceBundle
    wiring, a later section's job) -- this only makes the capability
    exist and directly tested."""
    entries: "dict[str, list[LSJSegment]]" = {}
    for xml_file in sorted(Path(tei_xml_dir).glob("*.xml")):
        root = ET.parse(xml_file, parser=_LSJXMLParser()).getroot()
        if tlg_abbreviation_collector is not None:
            # Deferred, function-level import -- NOT module-level: this
            # module's _LSJXMLParser is itself imported at module level
            # by lsj_periods.py, so a module-level import back here would
            # be a genuine circular import (both modules importing each
            # other at load time), not a hypothetical one.
            from okfbuild.sources.lsj_periods import collect_bibl_author_pairs_from_root

            for tlg_author, abbreviation in collect_bibl_author_pairs_from_root(root, str(xml_file)):
                tlg_abbreviation_collector.setdefault(tlg_author, set()).add(abbreviation)
        for entry_el in root.iter():
            if _local_name(entry_el.tag) not in _ENTRY_TAGS:
                continue
            raw_headword = entry_el.get("key") or entry_el.get("n")
            if not raw_headword:
                continue
            headword = _beta_code_to_greek(raw_headword)
            segments = _extract_segments(entry_el)
            if not segments:
                continue
            if headword in entries:
                entries[headword] = [*entries[headword], LSJText("\n\n"), *segments]
            else:
                entries[headword] = segments
    return entries


_CACHE_FORMAT_VERSION = 2
_CACHE_MISS = object()


def _encode_cached_entry(segments: "list[LSJSegment] | None") -> object:
    """A plain dataclass isn't automatically JSON-serializable -- convert
    explicitly on write, with a `kind` key per segment (not inferred from
    which fields are present) so decoding never has to guess, and a
    top-level `format_version` so a future format change -- or the old
    per-headword cache files' bare-string format, from before this
    section -- is detected explicitly rather than silently misread. A
    confirmed-absent lookup (segments is None) stays a bare `None` --
    already a clean, unambiguous round-trip through json.dumps/loads,
    no wrapping needed."""
    if segments is None:
        return None
    encoded_segments = []
    for segment in segments:
        if isinstance(segment, LSJText):
            encoded_segments.append({"kind": "text", "text": segment.text})
        else:
            encoded_segments.append({"kind": "citation", **asdict(segment)})
    return {"format_version": _CACHE_FORMAT_VERSION, "segments": encoded_segments}


def _decode_cached_entry(cached: object) -> "list[LSJSegment] | None | object":
    """Inverse of _encode_cached_entry(). Returns _CACHE_MISS (a private
    sentinel, distinct from a real None) for anything that isn't a
    None-or-current-format-version value -- an old bare-string cache
    entry (from before this section) or a future/unrecognized format --
    so the caller treats it exactly like a genuine cache miss (fresh
    lookup, then overwrite in the current format) instead of either
    crashing or silently returning wrong data shaped like the old
    format."""
    if cached is None:
        return None
    if not isinstance(cached, dict) or cached.get("format_version") != _CACHE_FORMAT_VERSION:
        return _CACHE_MISS
    segments: "list[LSJSegment]" = []
    for item in cached["segments"]:
        if item["kind"] == "text":
            segments.append(LSJText(text=item["text"]))
        else:
            segments.append(
                LSJCitation(
                    text=item["text"],
                    author_abbreviation=item["author_abbreviation"],
                    tlg_author=item["tlg_author"],
                    tlg_work=item["tlg_work"],
                    dialects=tuple(item["dialects"]),
                )
            )
    return segments


class LSJIndex:
    def __init__(self, entries: "dict[str, list[LSJSegment]]"):
        self._entries = entries

    @classmethod
    def load(cls, tei_xml_dir: Path) -> "LSJIndex":
        """Load all 27 TEI-XML files (~270MB) entirely into memory. Fine
        for small fixtures (tests); for the real dump, prefer
        `CachedLSJIndex`, which only ever resolves the headwords actually
        looked up."""
        return cls(_load_entries(tei_xml_dir))

    def lookup(self, headword: str) -> "list[LSJSegment] | None":
        """Return the LSJ entry's segments for `headword`, or None."""
        return self._entries.get(headword)


class CachedLSJIndex:
    """Same `lookup(headword)` contract as `LSJIndex`, but backed by a
    small per-headword disk cache instead of parsing all 27 TEI-XML files
    (~270MB) into memory up front. Mirrors `CachedWiktextractIndex`
    exactly -- same shape of problem (a large, rarely-changing bulk dump
    where a real course only ever touches a small fraction of headwords),
    same fix.

    Only the headwords actually looked up ever get resolved and cached --
    the full raw dump is a one-time, local-only, gitignored download
    needed just to resolve a genuinely new headword; once cached, a
    headword's answer (found or confirmed absent) never needs the raw
    dump again."""

    def __init__(
        self,
        cache_dir: Path,
        tei_xml_dir: "Path | None" = None,
        preloaded_index: "dict[str, list[LSJSegment]] | None" = None,
    ):
        """`preloaded_index`: for a caller that already scanned
        `tei_xml_dir` for another purpose (see _load_entries()'s own
        `tlg_abbreviation_collector` parameter) and wants THIS instance
        to reuse that result instead of doing its own, otherwise-
        independent lazy scan on first miss. None (the default) leaves
        the normal lazy behavior completely unchanged -- every existing
        caller is unaffected."""
        self._cache = KeyedJsonCache(cache_dir)
        self.cache_dir = self._cache.cache_dir
        self._tei_xml_dir = tei_xml_dir
        self._full_index: "dict[str, list[LSJSegment]] | None" = preloaded_index

    def lookup(self, headword: str) -> "list[LSJSegment] | None":
        hit, cached = self._cache.read(headword)
        if hit:
            decoded = _decode_cached_entry(cached)
            if decoded is not _CACHE_MISS:
                return decoded
            # Old-format or unrecognized cache entry -- fall through and
            # re-resolve exactly as if this had been a genuine miss.

        if self._full_index is None:
            if self._tei_xml_dir is None or not self._tei_xml_dir.is_dir():
                logger.warning(
                    "LSJ cache miss for %r and no local TEI-XML dump available to resolve it -- "
                    "not caching, since this isn't a confirmed absence", headword,
                )
                return None
            self._full_index = _load_entries(self._tei_xml_dir)

        segments = self._full_index.get(headword)
        self._cache.write(headword, _encode_cached_entry(segments))
        return segments
