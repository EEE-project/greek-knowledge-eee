"""Parses Perseus LSJ TEI-XML into a headword-keyed index.

Security: uses defusedxml, not stdlib xml.etree.ElementTree — ElementTree
(backed by expat) is not safe against internal-entity ("billion laughs")
expansion by default. This applies even to trusted sources (Perseus's own
GitHub): parsed external data is treated the same way regardless of
source trust, since trust today isn't a guarantee against a compromised
file or a future different source reusing this same code path.
"""

from pathlib import Path

import defusedxml.ElementTree as ET

_ENTRY_TAGS = {"entryFree", "entry"}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


class LSJIndex:
    def __init__(self, entries: dict[str, str]):
        self._entries = entries

    @classmethod
    def load(cls, tei_xml_dir: Path) -> "LSJIndex":
        """Parse the 27 Perseus LSJ TEI-XML files (see claude-research.md
        §2.2 for the exact source) into a headword-keyed index.

        Security: the XML parser MUST have entity expansion and external
        entity resolution disabled/limited (protect against a "billion
        laughs"-style expansion bomb) even though this specific file comes
        from a trusted source (Perseus's own GitHub) — treat all parsed
        external data the same way regardless of source trust."""
        entries: dict[str, str] = {}
        for xml_file in sorted(Path(tei_xml_dir).glob("*.xml")):
            root = ET.parse(xml_file).getroot()
            for entry_el in root.iter():
                if _local_name(entry_el.tag) not in _ENTRY_TAGS:
                    continue
                headword = entry_el.get("key") or entry_el.get("n")
                if not headword:
                    continue
                text = "".join(entry_el.itertext()).strip()
                if text:
                    entries[headword] = text
        return cls(entries)

    def lookup(self, headword: str) -> str | None:
        """Return the LSJ entry text for `headword`, or None."""
        return self._entries.get(headword)
