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
from functools import lru_cache
from pathlib import Path

import beta_code
import defusedxml.ElementTree as ET

from okfbuild.sources.disk_cache import KeyedJsonCache

logger = logging.getLogger(__name__)

_ENTRY_TAGS = {"entryFree", "entry"}


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


def _load_entries(tei_xml_dir: Path) -> dict[str, str]:
    """Parse the 27 Perseus LSJ TEI-XML files (~270MB, see
    claude-research.md §2.2 for the exact source) into a headword-keyed
    dict.

    Security: the XML parser MUST have entity expansion and external
    entity resolution disabled/limited (protect against a "billion
    laughs"-style expansion bomb) even though this specific file comes
    from a trusted source (Perseus's own GitHub) — treat all parsed
    external data the same way regardless of source trust. Uses
    _LSJXMLParser (see its own docstring), not the bare defused default,
    since the real files' benign parameter-entity DOCTYPE would otherwise
    be rejected too. Headword keys (`key`/`n` attributes) and Greek-tagged
    body text are Beta Code in the real files (e.g. `key="no/stos"` for
    νόστος) -- converted via _beta_code_to_greek() (see its own docstring
    for why it's cached), safely a no-op on already-Unicode input (e.g.
    this module's own small hand-written test fixtures use real Greek
    characters directly, not Beta Code)."""
    entries: dict[str, str] = {}
    for xml_file in sorted(Path(tei_xml_dir).glob("*.xml")):
        root = ET.parse(xml_file, parser=_LSJXMLParser()).getroot()
        for entry_el in root.iter():
            if _local_name(entry_el.tag) not in _ENTRY_TAGS:
                continue
            raw_headword = entry_el.get("key") or entry_el.get("n")
            if not raw_headword:
                continue
            headword = _beta_code_to_greek(raw_headword)
            # The real files' entry markup is indented for human
            # readability, which _extract_text() preserves verbatim as
            # embedded runs of newlines/spaces -- collapsed to single
            # spaces (str.split()'s no-argument form splits on any
            # whitespace run and drops empties) so the result reads as one
            # clean paragraph when embedded in a rendered markdown file.
            text = " ".join(_extract_text(entry_el).split())
            if text:
                entries[headword] = text
    return entries


class LSJIndex:
    def __init__(self, entries: dict[str, str]):
        self._entries = entries

    @classmethod
    def load(cls, tei_xml_dir: Path) -> "LSJIndex":
        """Load all 27 TEI-XML files (~270MB) entirely into memory. Fine
        for small fixtures (tests); for the real dump, prefer
        `CachedLSJIndex`, which only ever resolves the headwords actually
        looked up."""
        return cls(_load_entries(tei_xml_dir))

    def lookup(self, headword: str) -> str | None:
        """Return the LSJ entry text for `headword`, or None."""
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

    def __init__(self, cache_dir: Path, tei_xml_dir: "Path | None" = None):
        self._cache = KeyedJsonCache(cache_dir)
        self.cache_dir = self._cache.cache_dir
        self._tei_xml_dir = tei_xml_dir
        self._full_index: "dict[str, str] | None" = None

    def lookup(self, headword: str) -> str | None:
        hit, entry = self._cache.read(headword)
        if hit:
            return entry

        if self._full_index is None:
            if self._tei_xml_dir is None or not self._tei_xml_dir.is_dir():
                logger.warning(
                    "LSJ cache miss for %r and no local TEI-XML dump available to resolve it -- "
                    "not caching, since this isn't a confirmed absence", headword,
                )
                return None
            self._full_index = _load_entries(self._tei_xml_dir)

        entry = self._full_index.get(headword)
        self._cache.write(headword, entry)
        return entry
