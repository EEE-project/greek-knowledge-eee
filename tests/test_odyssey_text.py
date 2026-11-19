"""texts/odyssey/text.md against itself and against the Greek echoes of the interlinear translations: every
`### Odyss. <book>.<first>–<last>` section holds exactly the verses its heading names, and every `<!-- grc: ... -->`
echo in translations_{el,en,ru}.md equals the text.md line of the same verse (the k-th echo of a section is verse first+k)."""

import re
import unicodedata
from pathlib import Path

import pytest

_ODYSSEY = Path(__file__).parent.parent / "texts" / "odyssey"
_HEADER = re.compile(r"^### Odyss\. ([IVX]+)\.(\d+)(?:[–-](\d+))?")
_ECHO = re.compile(r"^<!-- grc: (.*) -->$")
_BOOKS = {"I": 1, "IX": 9}


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text).strip()


def _sections() -> list[tuple[str, int, int, list[str]]]:
    out: list[tuple[str, int, int, list[str]]] = []
    for raw in (_ODYSSEY / "text.md").read_text(encoding="utf-8").splitlines():
        if match := _HEADER.match(raw):
            first = int(match.group(2))
            out.append((raw, first, int(match.group(3) or first), []))
        elif out and raw.strip() and not raw.startswith(("#", "<!--")):
            out[-1][3].append(_nfc(raw))
    return out


_SECTIONS = _sections()


def test_text_has_sections():
    assert len(_SECTIONS) >= 2


@pytest.mark.parametrize(("heading", "first", "last", "verses"), _SECTIONS, ids=[s[0] for s in _SECTIONS])
def test_section_holds_the_verses_of_its_heading(heading, first, last, verses):
    assert len(verses) == last - first + 1


def test_greek_lines_hold_no_colon():
    # Beta Code writes the raised dot as a colon; a colon in a Greek line is a leftover of a conversion.
    assert [line for _, _, _, verses in _SECTIONS for line in verses if ":" in line] == []


@pytest.mark.parametrize("lang", ["el", "en", "ru"])
def test_interlinear_echoes_equal_the_text(lang):
    text = {}
    for heading, first, _, verses in _SECTIONS:
        book = _BOOKS[_HEADER.match(heading).group(1)]
        text.update({(book, first + k): line for k, line in enumerate(verses)})
    book, verse, echoes, wrong = None, None, 0, []
    for raw in (_ODYSSEY / f"translations_{lang}.md").read_text(encoding="utf-8").splitlines():
        if match := _HEADER.match(raw):
            book, verse = _BOOKS[match.group(1)], int(match.group(2))
        elif book and (match := _ECHO.match(raw)):
            echoes += 1
            if text.get((book, verse)) != _nfc(match.group(1)):
                wrong.append(f"{book}.{verse}")
            verse += 1
    assert echoes > 0
    assert wrong == []
