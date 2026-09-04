from pathlib import Path
from unittest.mock import patch

import defusedxml.common
import defusedxml.ElementTree as ET
import pytest

from okfbuild.sources.lsj_index import (
    CachedLSJIndex,
    LSJCitation,
    LSJIndex,
    LSJText,
    _extract_segments,
    _load_entries,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sources"
LSJ_FIXTURE_DIR = FIXTURES_DIR / "lsj"


def _seeded_index(cache_dir: Path) -> CachedLSJIndex:
    return CachedLSJIndex(cache_dir, tei_xml_dir=LSJ_FIXTURE_DIR)


def _joined_text(segments) -> str:
    return " ".join(s.text for s in segments)


def _assert_agathos_entry(segments) -> None:
    assert segments is not None
    assert "good" in _joined_text(segments)


# --- migrated from the flat-string era (existing 7 tests, adapted) ---


def test_load_returns_entry_text_for_known_headword():
    index = LSJIndex.load(FIXTURES_DIR / "lsj")
    segments = index.lookup("ἀγαθός")
    _assert_agathos_entry(segments)


def test_load_rejects_billion_laughs_entity_expansion():
    with pytest.raises(defusedxml.common.EntitiesForbidden):
        LSJIndex.load(FIXTURES_DIR / "lsj_billion_laughs")


def test_cached_index_resolves_from_dump_on_first_lookup(tmp_path):
    index = _seeded_index(tmp_path / "cache")
    segments = index.lookup("ἀγαθός")
    _assert_agathos_entry(segments)


def test_cached_index_persists_across_instances_without_the_dump(tmp_path):
    cache_dir = tmp_path / "cache"
    _seeded_index(cache_dir).lookup("ἀγαθός")

    # A fresh instance, no tei_xml_dir at all -- the previous lookup's
    # answer must already be on disk, not just held in the first
    # instance's memory.
    reopened = CachedLSJIndex(cache_dir)

    segments = reopened.lookup("ἀγαθός")
    _assert_agathos_entry(segments)


def test_cached_index_caches_confirmed_absence(tmp_path):
    cache_dir = tmp_path / "cache"
    first = _seeded_index(cache_dir)

    assert first.lookup("not-in-fixture") is None
    assert (cache_dir / "not-in-fixture.json").exists()

    # Confirmed-absent headwords must stay resolvable with no dump available.
    reopened = CachedLSJIndex(cache_dir)
    assert reopened.lookup("not-in-fixture") is None


def test_cached_index_miss_without_dump_available_is_not_cached(tmp_path):
    cache_dir = tmp_path / "cache"
    index = CachedLSJIndex(cache_dir)  # no tei_xml_dir -- dump unavailable

    assert index.lookup("ἀγαθός") is None
    assert list(cache_dir.iterdir()) == []


def test_cached_index_rejects_billion_laughs_entity_expansion(tmp_path):
    index = CachedLSJIndex(tmp_path / "cache", tei_xml_dir=FIXTURES_DIR / "lsj_billion_laughs")

    with pytest.raises(defusedxml.common.EntitiesForbidden):
        index.lookup("ἀγαθός")


# --- core segmentation invariant ---


def test_two_citations_in_one_run_produce_independent_citations():
    index = LSJIndex.load(FIXTURES_DIR / "lsj")
    segments = index.lookup("ἄατος")

    citations = [s for s in segments if isinstance(s, LSJCitation)]
    # entry f3 alone has 3 citable units (Il., Pi., Pl.); entry f3b (the
    # homograph, merged in) adds 2 more (Od., Id.) -- at least the first
    # 3 must each be independent objects with their own metadata, not one
    # shared segment for the whole run.
    il_citation = next(c for c in citations if c.author_abbreviation == "Il.")
    pi_citation = next(c for c in citations if c.author_abbreviation == "Pi.")
    assert il_citation is not pi_citation
    assert il_citation.dialects == ()
    assert pi_citation.dialects == ("Dor.",)
    assert il_citation.tlg_author == "0012"
    assert pi_citation.tlg_author == "0033"


def test_no_text_segment_contains_citation_content():
    """Checked across the WHOLE fixture's parsed output (every headword,
    every real citation abbreviation actually present), not spot-checked
    against a couple of hardcoded strings on one or two entries -- a
    narrower version of this test wouldn't catch a leak of an
    abbreviation it didn't happen to name."""
    entries = _load_entries(FIXTURES_DIR / "lsj")
    all_citations = [s for segs in entries.values() for s in segs if isinstance(s, LSJCitation)]
    real_abbreviations = {c.author_abbreviation for c in all_citations if c.author_abbreviation}
    assert real_abbreviations, "expected the fixture to contain at least one real abbreviation"

    for segments in entries.values():
        for segment in segments:
            if isinstance(segment, LSJText):
                for abbreviation in real_abbreviations:
                    assert abbreviation not in segment.text, (
                        f"citation abbreviation {abbreviation!r} leaked into plain text {segment.text!r}"
                    )


def test_untagged_citation_still_produces_citation_object():
    index = LSJIndex.load(FIXTURES_DIR / "lsj")
    segments = index.lookup("θιός")
    citations = [s for s in segments if isinstance(s, LSJCitation)]
    # The second bibl in entry f2 (biblScope 5.1, no <author> at all) is
    # still its own untagged citable unit, distinguishable from prose.
    untagged = [c for c in citations if c.author_abbreviation is None]
    assert len(untagged) == 1
    assert "5.1" in untagged[0].text


# --- dialect-tag scoping (per section-01's verified table) ---


def test_dialect_pattern_a_broad_inheritance_across_multiple_citations():
    """Boeot. precedes the sio/s orth variant (Pattern A) with NO <sense>
    boundary before either citation that follows -- both must inherit
    it."""
    index = LSJIndex.load(FIXTURES_DIR / "lsj")
    segments = index.lookup("θιός")
    citations = [s for s in segments if isinstance(s, LSJCitation)]
    assert len(citations) == 2
    assert all(c.dialects == ("Boeot.",) for c in citations)


def test_dialect_pattern_b_applies_only_to_the_immediately_following_citation():
    """Dor. sits directly between two <cit> elements in entry f3 -- only
    the second (Pi.) gets it; the first (Il., before the marker) and the
    third (Pl., a bare <bibl> after a comma with real intervening prose
    "cf.") must not."""
    index = LSJIndex.load(FIXTURES_DIR / "lsj")
    segments = index.lookup("ἄατος")
    citations = [s for s in segments if isinstance(s, LSJCitation)]
    by_abbrev = {c.author_abbreviation: c for c in citations}
    assert by_abbrev["Il."].dialects == ()
    assert by_abbrev["Pi."].dialects == ("Dor.",)
    assert by_abbrev["Pl."].dialects == ()


def test_dialect_pattern_c_parenthetical_after_foreign_quote():
    """The other real, directly-quoted shape from section-01's table
    (row 2/3): a <gramGrp> in parentheses immediately after a
    <foreign>-quoted form, immediately before that form's own <bibl> --
    scoped to just that one citation, matching Pattern B's outcome
    exactly (this project's own real example: e)fi/hmi's "thnei\\ ga\\r
    e)fi/sdei (Dor.) Theoc. 5.97"). No fixture entry exercises this
    shape, so constructed directly."""
    xml = """<entryFree key="test">
        <sense><foreign lang="greek">quoted form</foreign> (<gramGrp><gram type="dialect">Dor.</gram></gramGrp>)
        <bibl n="urn:cts:greekLit:tlg0005.tlg001.perseus-grc1:5:97"><author>Theoc.</author></bibl>.</sense>
    </entryFree>"""
    root = ET.fromstring(xml)
    citations = [s for s in _extract_segments(root) if isinstance(s, LSJCitation)]
    assert len(citations) == 1
    assert citations[0].author_abbreviation == "Theoc."
    assert citations[0].dialects == ("Dor.",)


def test_dialect_transparent_grammar_markup_does_not_break_pattern_b():
    """Real, directly-quoted example from section-01's table (row 2/3):
    a dialect marker separated from its target <cit> only by <per>/
    <number> -- must still attach, not fall through to prose (a
    regression test for a real bug this section's own code review
    caught: <per>3</per>/<number>pl.</number>'s own text contains word
    characters, which a naive "real prose breaks adjacency" check
    mistook for real intervening prose)."""
    xml = """<entryFree key="test">
        <sense><cit><quote lang="greek">e)fi/hti</quote>
        <bibl n="urn:cts:greekLit:tlg0033.tlg004.perseus-grc1:2:9"><author>Pi.</author></bibl></cit>,
        <gramGrp><gram type="dialect">Ion.</gram></gramGrp> <per>3</per><number>pl.</number>
        <cit><quote lang="greek">e)piei=si</quote>
        <bibl n="urn:cts:greekLit:tlg0016.tlg001.perseus-grc1:4:30"><author>Hdt.</author></bibl></cit>.</sense>
    </entryFree>"""
    root = ET.fromstring(xml)
    citations = [s for s in _extract_segments(root) if isinstance(s, LSJCitation)]
    by_abbrev = {c.author_abbreviation: c for c in citations}
    assert by_abbrev["Pi."].dialects == ()
    assert by_abbrev["Hdt."].dialects == ("Ion.",)


def test_dialect_untagged_mention_out_of_structural_scope():
    """Row 5 of section-01's table: a dialect abbreviation with no <gram
    type="dialect"> wrapper at all (real example: θεός's bare
    <bibl><author>Cypr.</author></bibl>) is never specially recognized --
    it's just an ordinary citation whose own text happens to look like a
    dialect name, with an empty dialects tuple like any other untagged
    citation."""
    xml = """<entryFree key="test">
        <sense><tr>form</tr>, <bibl><author>Cypr.</author></bibl>.</sense>
    </entryFree>"""
    root = ET.fromstring(xml)
    citations = [s for s in _extract_segments(root) if isinstance(s, LSJCitation)]
    assert len(citations) == 1
    assert citations[0].author_abbreviation == "Cypr."
    assert citations[0].dialects == ()


def test_dialect_sense_boundary_resets_active_dialect():
    """A dialect set via Pattern A must not bleed across a <sense>
    boundary into unrelated citations -- constructed directly against
    _extract_segments() rather than the fixture file, to isolate this
    one rule without depending on the fixture's own entry shapes."""
    xml = """<entryFree key="test">
        <orth lang="greek">form</orth>, <gramGrp><gram type="dialect">Dor.</gram></gramGrp>
        <orth lang="greek">variant</orth>, <sense><tr>meaning</tr>,
        <bibl n="urn:cts:greekLit:tlg0001.tlg001:1"><author>X.</author></bibl>.</sense>
    </entryFree>"""
    root = ET.fromstring(xml)
    segments = _extract_segments(root)
    citations = [s for s in segments if isinstance(s, LSJCitation)]
    assert len(citations) == 1
    assert citations[0].dialects == (), "dialect must not survive a <sense> boundary"


def test_dialect_consecutive_adjacent_markers_merge_for_one_target():
    """Two consecutive dialect markers with nothing but whitespace
    between them (and between the second and its target) merge into one
    combined dialects tuple, per the plan's own tuple design -- a
    real, confirmed dump-wide pattern (4 occurrences), though section-01
    found the one directly-verified instance was case 4 (prose
    commentary), not a genuine multi-dialect citation. No real fixture
    entry exercises the genuine-citation case, so this constructs one
    directly to verify the merge mechanism itself works, independent of
    whether real data happens to hit it."""
    xml = """<entryFree key="test">
        <orth lang="greek">form</orth>, <gramGrp><gram type="dialect">Aeol.</gram></gramGrp>
        <gramGrp><gram type="dialect">Dor.</gram></gramGrp>
        <cit TEIform="cit"><quote lang="greek">quo</quote>
        <bibl n="urn:cts:greekLit:tlg0001.tlg001:1"><author>X.</author></bibl></cit>.
    </entryFree>"""
    root = ET.fromstring(xml)
    citations = [s for s in _extract_segments(root) if isinstance(s, LSJCitation)]
    assert len(citations) == 1
    assert citations[0].dialects == ("Aeol.", "Dor.")


def test_dialect_prose_commentary_not_attached_to_any_citation():
    """Aeol. in entry f4 (ἄγαν) is followed by real prose ("and Trag.,
    not in") before the next <bibl> -- free-standing commentary, not
    Pattern A/B. The Hom. citation right after it must be untagged, and
    "Aeol." must still appear as plain rendered text."""
    index = LSJIndex.load(FIXTURES_DIR / "lsj")
    segments = index.lookup("ἄγαν")
    citations = [s for s in segments if isinstance(s, LSJCitation)]
    assert len(citations) == 1
    assert citations[0].dialects == ()
    assert citations[0].author_abbreviation == "Hom."
    assert "Aeol." in _joined_text(segments)


# --- _load_entries() merge/collision fix (a real, verified homograph
# collision -- see _load_entries()'s own docstring for why this uses
# ἄατος rather than the plan's original λέγω example, which turned out
# not to actually collide when checked directly) ---


def test_homograph_entries_merge_not_overwrite():
    entries = _load_entries(FIXTURES_DIR / "lsj")
    segments = entries["ἄατος"]
    citations = [s for s in segments if isinstance(s, LSJCitation)]
    abbreviations = {c.author_abbreviation for c in citations}
    # f3's citations (Il., Pi., Pl.) AND f3b's citations (Od., Id.) must
    # both be present -- last-one-wins would drop f3's entirely.
    assert {"Il.", "Pi.", "Pl."} <= abbreviations
    assert {"Od.", "Id."} <= abbreviations


def test_homograph_merge_inserts_boundary_separator():
    entries = _load_entries(FIXTURES_DIR / "lsj")
    segments = entries["ἄατος"]
    # f3 ends with the bare "Pl." citation's own text ("Ap."-ish, no
    # trailing space); f3b immediately starts with "unwearied,
    # insatiable in battle," -- concatenated with no separator this
    # would read "...Ap.unwearied" run together. Assert the merge
    # boundary (an LSJText("\n\n")) is genuinely present between them,
    # and that no word-run-together artifact appears in the fully
    # joined text.
    assert any(isinstance(s, LSJText) and s.text == "\n\n" for s in segments)
    joined = _joined_text(segments)
    assert "Ap.unwearied" not in joined.replace(" ", "").replace("\n", "")


def test_homograph_fix_does_not_affect_non_colliding_headwords():
    entries = _load_entries(FIXTURES_DIR / "lsj")
    assert "ἀγαθός" in entries
    assert not any(isinstance(s, LSJText) and s.text == "\n\n" for s in entries["ἀγαθός"])


# --- single-pass scanning ---


def test_load_entries_single_pass_when_collector_given():
    """_load_entries() and the TLG-abbreviation-map collection touch each
    source XML file's content exactly once -- verified via a call-count
    spy on ET.parse(), which is the one genuinely expensive step (XML
    parsing); the tlg_abbreviation_collector's own second `.iter()` over
    the already-parsed tree costs nothing extra there."""
    import okfbuild.sources.lsj_index as lsj_index_module

    with patch.object(lsj_index_module.ET, "parse", wraps=lsj_index_module.ET.parse) as spy:
        collector: "dict[str, set[str]]" = {}
        _load_entries(FIXTURES_DIR / "lsj", tlg_abbreviation_collector=collector)

    xml_file_count = len(list((FIXTURES_DIR / "lsj").glob("*.xml")))
    assert spy.call_count == xml_file_count
    # and the collector was genuinely populated, not left empty
    assert collector.get("0012") == {"Il.", "Od."}
    assert collector.get("0059") == {"Pl.", "Id."}


def test_load_entries_collector_matches_independent_lsj_periods_build():
    """The collector-populated map must be identical to what
    lsj_periods.build_tlg_author_abbreviation_map() would independently
    compute over the same directory -- proves the shared single-pass
    path and the standalone path agree, not just that each looks
    internally consistent."""
    from okfbuild.sources.lsj_periods import build_tlg_author_abbreviation_map

    collector: "dict[str, set[str]]" = {}
    _load_entries(FIXTURES_DIR / "lsj", tlg_abbreviation_collector=collector)
    independent = build_tlg_author_abbreviation_map(FIXTURES_DIR / "lsj")
    assert collector == independent


# --- LSJIndex/CachedLSJIndex.lookup() ---


def test_cold_lookup_returns_segment_list(tmp_path):
    index = _seeded_index(tmp_path / "cache")
    segments = index.lookup("ἀγαθός")
    assert isinstance(segments, list)
    assert all(isinstance(s, (LSJText, LSJCitation)) for s in segments)


def test_cache_file_on_disk_has_the_new_versioned_format(tmp_path):
    import json
    import urllib.parse

    cache_dir = tmp_path / "cache"
    _seeded_index(cache_dir).lookup("ἀγαθός")

    cache_file = cache_dir / f"{urllib.parse.quote('ἀγαθός', safe='')}.json"
    raw = json.loads(cache_file.read_text(encoding="utf-8"))
    assert raw["format_version"] == 2
    assert raw["segments"][0]["kind"] in ("text", "citation")


def test_warm_lookup_matches_cold_lookup_type_and_shape(tmp_path):
    cache_dir = tmp_path / "cache"
    cold = _seeded_index(cache_dir).lookup("ἄατος")

    reopened = CachedLSJIndex(cache_dir)  # no tei_xml_dir -- forces the cache path
    warm = reopened.lookup("ἄατος")

    assert type(cold) is type(warm)
    assert cold == warm  # structural equality on the dataclasses, not just "both non-empty"


def test_cache_round_trip_preserves_dialects_and_tlg_ids(tmp_path):
    cache_dir = tmp_path / "cache"
    _seeded_index(cache_dir).lookup("θιός")

    reopened = CachedLSJIndex(cache_dir)
    segments = reopened.lookup("θιός")
    citation = next(s for s in segments if isinstance(s, LSJCitation) and s.author_abbreviation == "Hdt.")
    assert citation.dialects == ("Boeot.",)
    assert citation.tlg_author == "0016"
    assert citation.tlg_work == "001"


def test_old_format_cache_entry_treated_as_miss_not_crash(tmp_path):
    """A leftover bare-string cache file from before this section (the
    format every real data/lsj-cache/ file was in) must not crash --
    treated exactly like a fresh miss, re-resolved and rewritten in the
    current format. Written at the exact path KeyedJsonCache itself
    would use for "ἀγαθός", so the lookup below genuinely hits it."""
    import urllib.parse

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    stale_path = cache_dir / f"{urllib.parse.quote('ἀγαθός', safe='')}.json"
    stale_path.write_text('"an old flat-string cache entry, not a dict"', encoding="utf-8")

    index = _seeded_index(cache_dir)
    _assert_agathos_entry(index.lookup("ἀγαθός"))

    # and the stale file was genuinely overwritten in the new format,
    # not left as-is alongside a duplicate:
    reopened = CachedLSJIndex(cache_dir)  # no tei_xml_dir -- forces the cache path
    _assert_agathos_entry(reopened.lookup("ἀγαθός"))
