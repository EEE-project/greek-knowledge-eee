"""Tests for okfbuild.wiring.default_source_bundle() and full_source_bundle()."""

from okfbuild.sources.lsj_periods import LSJPeriodMap
from okfbuild.wiring import default_source_bundle, full_source_bundle


def test_default_source_bundle_wires_every_field(repo_root):
    sources = default_source_bundle(repo_root)

    assert sources.eee_engine is not None
    assert sources.morpheus is not None
    assert sources.lsj is not None
    assert sources.wiktextract is not None
    assert sources.wikipedia is not None
    assert isinstance(sources.byzantine_forms, dict)
    assert sources.iecor is not None
    assert len(sources.iecor) == 170


def test_default_source_bundle_iecor_has_real_entries(repo_root):
    sources = default_source_bundle(repo_root)

    entries = sources.iecor["ὕδωρ"]
    assert entries[0].root_language == "Proto-Indo-European"


def test_default_source_bundle_has_no_lsj_period_map(repo_root):
    """The lighter wiring lookup/build use -- full_source_bundle() below
    is the one that adds it."""
    sources = default_source_bundle(repo_root)

    assert sources.lsj_period_map is None


def test_full_source_bundle_matches_default_source_bundle_except_period_map(repo_root):
    default = default_source_bundle(repo_root)
    full = full_source_bundle(repo_root)

    assert full.eee_engine is default.eee_engine
    assert full.wikipedia is default.wikipedia
    assert full.iecor == default.iecor
    # Environment-dependent (needs the real LSJ dump + Diorisis catalog) --
    # gracefully None without them, a real LSJPeriodMap with them, matching
    # how lsj/wiktextract already degrade without their own real dumps.
    assert full.lsj_period_map is None or isinstance(full.lsj_period_map, LSJPeriodMap)
