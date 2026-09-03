from pathlib import Path

import defusedxml.common
import pytest

from okfbuild.sources.lsj_index import CachedLSJIndex, LSJIndex

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sources"
LSJ_FIXTURE_DIR = FIXTURES_DIR / "lsj"


def _seeded_index(cache_dir: Path) -> CachedLSJIndex:
    return CachedLSJIndex(cache_dir, tei_xml_dir=LSJ_FIXTURE_DIR)


def _assert_agathos_entry(text: "str | None") -> None:
    assert text is not None
    assert "good" in text


def test_load_returns_entry_text_for_known_headword():
    index = LSJIndex.load(FIXTURES_DIR / "lsj")

    text = index.lookup("ἀγαθός")

    _assert_agathos_entry(text)


def test_load_rejects_billion_laughs_entity_expansion():
    with pytest.raises(defusedxml.common.EntitiesForbidden):
        LSJIndex.load(FIXTURES_DIR / "lsj_billion_laughs")


def test_cached_index_resolves_from_dump_on_first_lookup(tmp_path):
    index = _seeded_index(tmp_path / "cache")

    text = index.lookup("ἀγαθός")

    _assert_agathos_entry(text)


def test_cached_index_persists_across_instances_without_the_dump(tmp_path):
    cache_dir = tmp_path / "cache"
    _seeded_index(cache_dir).lookup("ἀγαθός")

    # A fresh instance, no tei_xml_dir at all -- the previous lookup's
    # answer must already be on disk, not just held in the first
    # instance's memory.
    reopened = CachedLSJIndex(cache_dir)

    text = reopened.lookup("ἀγαθός")
    _assert_agathos_entry(text)


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
