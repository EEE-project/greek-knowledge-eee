import os
import shutil
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from okfbuild.sources.lsj_periods import (
    LSJPeriodMap,
    Period,
    build_tlg_author_abbreviation_map,
    parse_date_text,
    parse_diorisis_catalog,
    parse_lsj_frontmatter_authors,
    tlg_map_cache_is_fresh,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sources" / "lsj_periods"
CATALOG_PATH = FIXTURES_DIR / "diorisis_catalog.tsv"


def _citation(tlg_author=None, tlg_work=None, author_abbreviation=None):
    """A plain stand-in for LSJCitation -- deliberately not importing the
    real class (owned by section-03, which lsj_periods.py must not depend
    on to avoid a circular import). period_for_citation() only ever reads
    these three attributes."""
    return SimpleNamespace(tlg_author=tlg_author, tlg_work=tlg_work, author_abbreviation=author_abbreviation)


# --- parse_date_text ---


def test_parse_date_text_single_century_bc():
    period = parse_date_text("v B.C.")
    assert period == Period(centuries=(5,), era="BC", uncertain=False)
    assert period.label == "5th c. BC"


def test_parse_date_text_century_span_ad():
    period = parse_date_text("i/ii A.D.")
    assert period == Period(centuries=(1, 2), era="AD", uncertain=False)
    assert period.label == "1st/2nd c. AD"


def test_parse_date_text_century_span_ad_other_real_examples():
    # "ii/iii A.D." and "v/vi A.D." are both named directly in
    # claude-plan-tdd.md as real, confirmed occurrences worth their own
    # dedicated check, not just coverage via the general real-format scan.
    assert parse_date_text("ii/iii A.D.") == Period(centuries=(2, 3), era="AD", uncertain=False)
    assert parse_date_text("v/vi A.D.") == Period(centuries=(5, 6), era="AD", uncertain=False)


def test_parse_date_text_uncertain_alternative_reading():
    period = parse_date_text("iii or ii B.C.")
    assert period.centuries == (3, 2)
    assert period.era == "BC"
    assert period.uncertain is True
    # ascending in the label even though centuries preserves the source's own order
    assert period.label == "2nd or 3rd c. BC"


def test_parse_date_text_era_spanning():
    period = parse_date_text("i B.C./i A.D.")
    assert period == Period(centuries=(1,), era="BC/AD", uncertain=False)
    assert period.label == "1st c. BC/AD"


def test_parse_date_text_era_spanning_uncertain():
    period = parse_date_text("i B.C./i A.D. (?)")
    assert period == Period(centuries=(1,), era="BC/AD", uncertain=True)


def test_parse_date_text_tolerates_real_punctuation_irregularity():
    # real LSJ front matter has "A D." (space, no period after A) at
    # least once -- must not be treated as unparseable.
    period = parse_date_text("ii A D. (?)")
    assert period == Period(centuries=(2,), era="AD", uncertain=True)


def test_parse_date_text_unrecognized_format_returns_none_and_warns(caplog):
    with caplog.at_level("WARNING"):
        result = parse_date_text("sometime, probably")
    assert result is None
    assert "sometime, probably" in caplog.text


def test_parse_date_text_covers_every_real_frontmatter_format():
    """Every distinct real date-string format actually found in the live
    LSJ front matter's List I ("Authors and Works") items either parses
    to a sensible Period or is a documented None case -- the test that
    proves parser coverage against real data, not just the hand-picked
    seed examples above. Skips cleanly when the real (gitignored,
    local-only) dump isn't present.

    Deliberately mirrors parse_lsj_frontmatter_authors()'s own
    List-I-scoping and "first <date> child per item" logic rather than
    grepping every <date> element in the whole file -- a first version of
    this test did that and surfaced ~70 "unparsed" formats that turned
    out to be a red herring: <date> is reused elsewhere in this document
    for unrelated things a person's lifespan appearing outside List I,
    modern edition-publication years, a specific inscription's own date
    deep in the dictionary body -- none of which parse_date_text() is
    ever actually asked to parse in production."""
    real_dump = Path(__file__).parent.parent.parent / "data" / "lsj" / "grc.lsj.perseus-eng1.xml"
    if not real_dump.is_file():
        pytest.skip("real LSJ dump not present locally")

    import defusedxml.ElementTree as ET

    from okfbuild.sources.lsj_index import _LSJXMLParser, _local_name

    root = ET.parse(real_dump, parser=_LSJXMLParser()).getroot()
    target_div1 = None
    for div1 in root.iter():
        if _local_name(div1.tag) != "div1":
            continue
        head = next((child for child in div1 if _local_name(child.tag) == "head"), None)
        if head is not None and "".join(head.itertext()).strip() == "I. Authors and Works":
            target_div1 = div1
            break
    assert target_div1 is not None, "expected to find the 'I. Authors and Works' div1 in the real front matter"

    date_texts = set()
    for item in target_div1.iter():
        if _local_name(item.tag) != "item":
            continue
        date_el = next((child for child in item.iter() if _local_name(child.tag) == "date"), None)
        if date_el is not None:
            date_texts.add("".join(date_el.itertext()).strip())

    assert date_texts, "expected to find at least one dated item in List I"

    # 3 isolated real data defects, not systematic formats -- see
    # parse_date_text()'s own docstring for why these stay unparsed
    # (Melanthius's truncated "iv B", a bare "B.C." with no numeral
    # attached to any author, and Eunapius's corrupted "<*>v/v A.D.",
    # which every other "iv/v A.D."-dated item in this same file shows
    # is what it was clearly meant to say).
    expected_unparseable = {"iv B", "B.C.", "<*>v/v A.D."}

    unparsed = {d for d in date_texts if parse_date_text(d) is None}
    assert unparsed == expected_unparseable, (
        f"unparsed real List-I date formats changed: "
        f"new/unexpected={sorted(unparsed - expected_unparseable)}, "
        f"now-parseable (remove from allowlist)={sorted(expected_unparseable - unparsed)}"
    )


# --- parse_diorisis_catalog ---


def test_parse_diorisis_catalog_work_level():
    catalog = parse_diorisis_catalog(CATALOG_PATH)
    assert catalog[("0012", "001")] == Period(centuries=(8,), era="BC", uncertain=False)
    assert catalog[("0059", "030")].label == "4th c. BC"


def test_parse_diorisis_catalog_bc_and_ad_eras():
    catalog = parse_diorisis_catalog(CATALOG_PATH)
    assert catalog[("0012", "001")].era == "BC"
    assert catalog[("2165", "001")].era == "AD"
    assert catalog[("2165", "001")].label == "5th c. AD"


def test_parse_diorisis_catalog_preserves_leading_zeros():
    catalog = parse_diorisis_catalog(CATALOG_PATH)
    assert ("0012", "001") in catalog
    assert (12, 1) not in catalog  # a naive int() cast would produce this key shape instead


# --- parse_lsj_frontmatter_authors ---


def test_parse_lsj_frontmatter_authors_basic():
    authors = parse_lsj_frontmatter_authors(FIXTURES_DIR / "grc.lsj.perseus-eng1.xml")
    assert authors["Hdt."] == Period(centuries=(5,), era="BC", uncertain=False)
    assert authors["Pl."].centuries == (5, 4)
    assert authors["Pl."].era == "BC"


def test_parse_lsj_frontmatter_authors_no_date_item_is_absent_not_error():
    authors = parse_lsj_frontmatter_authors(FIXTURES_DIR / "grc.lsj.perseus-eng1.xml")
    assert "Hom." not in authors


def test_parse_lsj_frontmatter_authors_bracket_only_skips_unbracketed_continuations():
    # Homer's own item continues with unbracketed "Il. = Ilias", "Od. =
    # Odyssea" -- must not be misparsed as separate author entries.
    authors = parse_lsj_frontmatter_authors(FIXTURES_DIR / "grc.lsj.perseus-eng1.xml")
    assert "Il." not in authors
    assert "Od." not in authors


def test_parse_lsj_frontmatter_authors_malformed_split_bracket_skipped_not_crashed():
    authors = parse_lsj_frontmatter_authors(FIXTURES_DIR / "grc.lsj.perseus-eng1.xml")
    assert "Misc" not in authors
    assert "Cont." not in authors


def test_parse_lsj_frontmatter_authors_scoped_to_list_i_only():
    authors = parse_lsj_frontmatter_authors(FIXTURES_DIR / "grc.lsj.perseus-eng1.xml")
    assert "Not.An Author" not in authors


# --- build_tlg_author_abbreviation_map ---


def test_build_tlg_author_abbreviation_map_single_abbreviation():
    result = build_tlg_author_abbreviation_map(FIXTURES_DIR)
    assert result["0016"] == {"Hdt."}


def test_build_tlg_author_abbreviation_map_multiple_abbreviations_not_overwritten():
    result = build_tlg_author_abbreviation_map(FIXTURES_DIR)
    assert result["0059"] == {"Pl.", "Id."}
    assert result["0085"] == {"A.", "Aesch."}


def test_build_tlg_author_abbreviation_map_bibl_without_author_child_skipped(caplog):
    # DEBUG, not WARNING: verified against the real full dump that this
    # is the ordinary case for a citation continuing the same work as a
    # preceding one (72,567 real occurrences), not an anomaly worth
    # warning about.
    with caplog.at_level("DEBUG"):
        result = build_tlg_author_abbreviation_map(FIXTURES_DIR)
    assert "9999" not in result


def test_build_tlg_author_abbreviation_map_non_urn_n_attribute_ignored():
    result = build_tlg_author_abbreviation_map(FIXTURES_DIR)
    assert all("E." not in abbrevs for abbrevs in result.values())


def test_build_tlg_author_abbreviation_map_aggregates_across_multiple_files():
    result = build_tlg_author_abbreviation_map(FIXTURES_DIR)
    assert result["0012"] == {"Il."}  # only present in grc.lsj.perseus-eng2.xml


# --- LSJPeriodMap ---


def test_period_map_resolves_via_diorisis_work_level(tmp_path):
    period_map = LSJPeriodMap.build(FIXTURES_DIR, CATALOG_PATH, tmp_path / "tlg-map.json")
    citation = _citation(tlg_author="0012", tlg_work="001")
    assert period_map.period_for_citation(citation) == Period(centuries=(8,), era="BC", uncertain=False)


def test_period_map_falls_back_to_diorisis_author_level(tmp_path):
    period_map = LSJPeriodMap.build(FIXTURES_DIR, CATALOG_PATH, tmp_path / "tlg-map.json")
    # tlg_work "999" isn't in the Diorisis fixture for author 0012 -- must
    # fall back to that author's EARLIEST work (001, -800 -> 8th c. BC),
    # not the later 002 (-700 -> 7th c. BC), proving "earliest" is really
    # computed, not just "some work of this author".
    citation = _citation(tlg_author="0012", tlg_work="999")
    assert period_map.period_for_citation(citation) == Period(centuries=(8,), era="BC", uncertain=False)


def test_period_map_resolves_via_frontmatter_when_no_tlg_info(tmp_path):
    period_map = LSJPeriodMap.build(FIXTURES_DIR, CATALOG_PATH, tmp_path / "tlg-map.json")
    citation = _citation(author_abbreviation="Pl.")
    period = period_map.period_for_citation(citation)
    assert period.centuries == (5, 4)
    assert period.era == "BC"


def test_period_map_diorisis_wins_over_frontmatter_when_both_have_a_date(tmp_path):
    """Herodotus fixture data deliberately disagrees between sources
    (Diorisis: 4th c. BC via a constructed test row; front matter: 5th
    c. BC, "v B.C.") specifically so this test distinguishes real
    priority-respecting code from code that would pass either way."""
    period_map = LSJPeriodMap.build(FIXTURES_DIR, CATALOG_PATH, tmp_path / "tlg-map.json")
    citation = _citation(tlg_author="0016", tlg_work="001")
    period = period_map.period_for_citation(citation)
    assert period.era == "BC"
    assert period.centuries == (4,)  # Diorisis's value, not front matter's "v B.C." (5th c.)


def test_period_map_disambiguates_multi_candidate_via_citation_abbreviation_match(tmp_path):
    # tlg0085 has NO Diorisis rows at all and maps to 2 abbreviations
    # ({"A.", "Aesch."}) -- only the citation's own author_abbreviation
    # can disambiguate which one to resolve against front matter.
    period_map = LSJPeriodMap.build(FIXTURES_DIR, CATALOG_PATH, tmp_path / "tlg-map.json")
    citation = _citation(tlg_author="0085", author_abbreviation="A.")
    period = period_map.period_for_citation(citation)
    assert period.centuries == (6, 5)
    assert period.era == "BC"


def test_period_map_ambiguous_multi_candidate_no_match_returns_none_not_a_guess(tmp_path):
    period_map = LSJPeriodMap.build(FIXTURES_DIR, CATALOG_PATH, tmp_path / "tlg-map.json")
    citation = _citation(tlg_author="0085", author_abbreviation="X.")  # matches neither candidate
    assert period_map.period_for_citation(citation) is None


def test_period_map_single_candidate_wins_over_a_differing_citation_abbreviation(tmp_path):
    """tlg0261 has NO Diorisis rows at all and exactly ONE known
    abbreviation candidate ("Simon."). A citation whose own
    author_abbreviation is something else entirely -- even a real,
    independently-valid frontmatter key like "Hdt." -- must still
    resolve via the map's single confident candidate ("Simon.", 6th/5th
    c. BC), not via the citation's own (here: wrong-author) text. This
    is the case a first version of period_for_citation() got backwards
    (it unconditionally overrode with the single candidate) without a
    test distinguishing it from "citation's own abbreviation IS the
    single candidate" (same outcome either way, not a real test)."""
    period_map = LSJPeriodMap.build(FIXTURES_DIR, CATALOG_PATH, tmp_path / "tlg-map.json")
    citation = _citation(tlg_author="0261", author_abbreviation="Hdt.")
    period = period_map.period_for_citation(citation)
    assert period.centuries == (6, 5)
    assert period.era == "BC"


def test_period_map_unresolvable_citation_returns_none(tmp_path):
    period_map = LSJPeriodMap.build(FIXTURES_DIR, CATALOG_PATH, tmp_path / "tlg-map.json")
    citation = _citation(tlg_author="9999", author_abbreviation="Ghost.")
    assert period_map.period_for_citation(citation) is None


# --- caching ---


def test_period_map_build_caches_tlg_map_across_calls(tmp_path):
    cache_path = tmp_path / "tlg-map.json"
    with patch(
        "okfbuild.sources.lsj_periods.build_tlg_author_abbreviation_map",
        wraps=build_tlg_author_abbreviation_map,
    ) as spy:
        LSJPeriodMap.build(FIXTURES_DIR, CATALOG_PATH, cache_path)
        second = LSJPeriodMap.build(FIXTURES_DIR, CATALOG_PATH, cache_path)

    assert spy.call_count == 1
    # the second build must have loaded real, correctly round-tripped
    # data from the cache file, not an empty/corrupt map.
    citation = _citation(tlg_author="0085", author_abbreviation="A.")
    period = second.period_for_citation(citation)
    assert period is not None
    assert period.centuries == (6, 5)


def test_period_map_build_rebuilds_when_a_source_file_changes(tmp_path):
    fixture_copy = tmp_path / "lsj_periods_fixture"
    shutil.copytree(FIXTURES_DIR, fixture_copy)
    cache_path = tmp_path / "tlg-map.json"

    with patch(
        "okfbuild.sources.lsj_periods.build_tlg_author_abbreviation_map",
        wraps=build_tlg_author_abbreviation_map,
    ) as spy:
        LSJPeriodMap.build(fixture_copy, fixture_copy / "diorisis_catalog.tsv", cache_path)

        xml_file = fixture_copy / "grc.lsj.perseus-eng1.xml"
        new_time = xml_file.stat().st_mtime + 5
        os.utime(xml_file, (new_time, new_time))

        LSJPeriodMap.build(fixture_copy, fixture_copy / "diorisis_catalog.tsv", cache_path)

    assert spy.call_count == 2


def test_tlg_map_cache_is_fresh_false_when_no_cache_yet(tmp_path):
    assert tlg_map_cache_is_fresh(FIXTURES_DIR, tmp_path / "does-not-exist.json") is False


def test_tlg_map_cache_is_fresh_true_after_a_real_build(tmp_path):
    cache_path = tmp_path / "tlg-map.json"
    LSJPeriodMap.build(FIXTURES_DIR, CATALOG_PATH, cache_path)
    assert tlg_map_cache_is_fresh(FIXTURES_DIR, cache_path) is True


def test_tlg_map_cache_is_fresh_false_after_a_source_file_changes(tmp_path):
    fixture_copy = tmp_path / "lsj_periods_fixture"
    shutil.copytree(FIXTURES_DIR, fixture_copy)
    cache_path = tmp_path / "tlg-map.json"
    LSJPeriodMap.build(fixture_copy, fixture_copy / "diorisis_catalog.tsv", cache_path)

    xml_file = fixture_copy / "grc.lsj.perseus-eng1.xml"
    new_time = xml_file.stat().st_mtime + 5
    os.utime(xml_file, (new_time, new_time))

    assert tlg_map_cache_is_fresh(fixture_copy, cache_path) is False


def test_period_map_build_with_precomputed_tlg_map_skips_its_own_scan(tmp_path):
    """A caller that already scanned the dump for another purpose (e.g.
    _load_entries()'s own collector) can hand LSJPeriodMap.build() the
    result directly -- it must persist and use that, never call
    build_tlg_author_abbreviation_map() itself."""
    cache_path = tmp_path / "tlg-map.json"
    precomputed = {"0085": {"A.", "Aesch."}}

    with patch(
        "okfbuild.sources.lsj_periods.build_tlg_author_abbreviation_map",
        wraps=build_tlg_author_abbreviation_map,
    ) as spy:
        period_map = LSJPeriodMap.build(
            FIXTURES_DIR, CATALOG_PATH, cache_path, precomputed_tlg_abbreviation_map=precomputed
        )

    spy.assert_not_called()
    citation = _citation(tlg_author="0085", author_abbreviation="A.")
    assert period_map.period_for_citation(citation) == Period(centuries=(6, 5), era="BC", uncertain=False)
    # and it was genuinely persisted -- a later plain build() (no
    # precomputed_map) must read it back from the cache, not rescan.
    assert tlg_map_cache_is_fresh(FIXTURES_DIR, cache_path) is True


def test_period_map_build_caches_frontmatter_authors_across_calls(tmp_path):
    cache_path = tmp_path / "tlg-map.json"
    with patch(
        "okfbuild.sources.lsj_periods.parse_lsj_frontmatter_authors",
        wraps=parse_lsj_frontmatter_authors,
    ) as spy:
        LSJPeriodMap.build(FIXTURES_DIR, CATALOG_PATH, cache_path)
        second = LSJPeriodMap.build(FIXTURES_DIR, CATALOG_PATH, cache_path)

    assert spy.call_count == 1
    # the second build must have loaded real, correctly round-tripped
    # data from the cache file (Period reconstructed via __post_init__,
    # not just some raw dict), not an empty/corrupt map.
    citation = _citation(author_abbreviation="Hdt.")
    period = second.period_for_citation(citation)
    assert period == Period(centuries=(5,), era="BC", uncertain=False)


def test_period_map_build_rebuilds_frontmatter_authors_when_source_file_changes(tmp_path):
    fixture_copy = tmp_path / "lsj_periods_fixture"
    shutil.copytree(FIXTURES_DIR, fixture_copy)
    cache_path = tmp_path / "tlg-map.json"

    with patch(
        "okfbuild.sources.lsj_periods.parse_lsj_frontmatter_authors",
        wraps=parse_lsj_frontmatter_authors,
    ) as spy:
        LSJPeriodMap.build(fixture_copy, fixture_copy / "diorisis_catalog.tsv", cache_path)

        # grc.lsj.perseus-eng1.xml serves as both the TLG-map scan's
        # source and the front-matter parse's own source -- touching it
        # must independently invalidate this cache too.
        xml_file = fixture_copy / "grc.lsj.perseus-eng1.xml"
        new_time = xml_file.stat().st_mtime + 5
        os.utime(xml_file, (new_time, new_time))

        LSJPeriodMap.build(fixture_copy, fixture_copy / "diorisis_catalog.tsv", cache_path)

    assert spy.call_count == 2
