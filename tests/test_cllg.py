"""okfbuild.sources.cllg against three small TEI fixtures in the shapes of the CLLG files -- book/line,
book/chapter/section, pages (tests/fixtures/sources/cllg; their Greek is cut from texts/odyssey/text.md, not taken
from CLLG). No network. The expected texts come from the fixtures by plain regexes, not from the module."""

import re
import unicodedata
from pathlib import Path

import pytest

from okfbuild.sources import cllg

CORPUS = Path(__file__).parent / "fixtures" / "sources" / "cllg"
LINES, SECTIONS, PAGES = (cllg.text_path(CORPUS, i) for i in ("tlg0012.tlg002", "tlg0000.tlg001", "tlg0000.tlg002"))


def _line(n: str) -> str:
    return re.search(rf'<l n="{n}">(.*?)</l>', LINES.read_text(encoding="utf-8")).group(1)


def _paragraphs(path: Path) -> list[str]:
    body = path.read_text(encoding="utf-8").split("<body>")[1]
    return [re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", p)).strip() for p in re.findall(r"<p>(.*?)</p>", body)]


def _bare(s: str) -> str:
    """s in capitals without accents and breathings, as a reader may type it."""
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c)).upper()


def test_text_path_maps_an_id_and_rejects_anything_else():
    assert cllg.text_path(Path("c"), "tlg0012.tlg002") == Path("c/data/tlg0012/tlg002/tlg0012.tlg002.cllg-grc1.xml")
    for bad in ("../tlg0012.tlg002", "tlg12.tlg2", "tlg0012/tlg002", "tlg0012.tlg002/../x"):
        with pytest.raises(ValueError):
            cllg.text_path(Path("c"), bad)


def test_passage_of_a_line_and_of_a_book():
    assert cllg.passage(LINES, "9.157") == _line("157")
    assert cllg.passage(LINES, "9") == " ".join(_line(str(n)) for n in range(152, 158))
    with pytest.raises(KeyError):
        cllg.passage(LINES, "9.158")


def test_find_ignores_case_accents_and_breathings_and_crosses_a_line_end():
    last, first = _line("156").split()[-1], _line("157").split()[0]
    hits = cllg.find(LINES, _bare(f"{last} {first}"))
    assert [hit.ref for hit in hits] == ["9.156"]
    assert hits[0].text.startswith(f"{last} {first}")


def test_find_gives_every_place_but_none_in_the_header_or_in_a_tag():
    assert [hit.ref for hit in cllg.find(LINES, _line("4").split()[0])] == ["1.1", "1.4"]
    for word in ("book", "Odyssey", "fixture"):  # in the header and in type="book" only
        assert cllg.find(LINES, word) == []
    with pytest.raises(ValueError):
        cllg.find(LINES, " ")


def test_book_chapter_section_and_an_uncited_page_break():
    first, second, third = _paragraphs(SECTIONS)
    assert cllg.passage(SECTIONS, "1.1.2") == second
    assert cllg.passage(SECTIONS, "1.1") == f"{first} {second}"
    assert cllg.passage(SECTIONS, "1.2.1") == third
    assert [hit.ref for hit in cllg.find(SECTIONS, second.split()[-1])] == ["1.1.2"]  # after the <pb />, which has no n


def test_pages_run_from_one_page_break_to_the_next_and_a_volume_milestone_is_no_page():
    page1, page2 = _paragraphs(PAGES)
    assert cllg.passage(PAGES, "1") == page1
    assert cllg.passage(PAGES, "2") == page2  # not from <milestone n="2"/>, which the refsDecl does not cite
    assert [hit.ref for hit in cllg.find(PAGES, page2.split()[-1])] == ["2"]
    assert [hit.ref for hit in cllg.find(PAGES, page1.split()[0])] == ["1"]
