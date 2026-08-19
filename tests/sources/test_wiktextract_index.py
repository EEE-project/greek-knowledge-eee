from pathlib import Path

from okfbuild.sources.wiktextract_index import CachedWiktextractIndex, WiktextractIndex

FIXTURE = Path(__file__).parent.parent / "fixtures" / "sources" / "wiktextract_sample.jsonl"


def _seeded_index(cache_dir: Path) -> CachedWiktextractIndex:
    return CachedWiktextractIndex(cache_dir, jsonl_path=FIXTURE, lang_code="el")


def test_load_builds_lookup_index_from_jsonl():
    index = WiktextractIndex.load(FIXTURE)

    entry = index.lookup("λόγος")

    assert entry["pos"] == "noun"
    assert entry["senses"][0]["glosses"] == ["word, speech"]


def test_lookup_returns_none_for_lemma_not_in_fixture():
    index = WiktextractIndex.load(FIXTURE)

    assert index.lookup("not-in-fixture") is None


def test_load_without_lang_code_keeps_whichever_entry_sorts_last():
    index = WiktextractIndex.load(FIXTURE)

    assert index.lookup("νόστος")["senses"][0]["glosses"] == ["journey (Ancient)"]


def test_load_with_lang_code_filters_out_other_languages_same_headword():
    index = WiktextractIndex.load(FIXTURE, lang_code="el")

    assert index.lookup("νόστος")["senses"][0]["glosses"] == ["return home (Modern)"]
    assert index.lookup("λόγος") is not None


def test_cached_index_resolves_from_dump_on_first_lookup(tmp_path):
    index = _seeded_index(tmp_path / "cache")

    entry = index.lookup("λόγος")

    assert entry["senses"][0]["glosses"] == ["word, speech"]


def test_cached_index_persists_across_instances_without_the_dump(tmp_path):
    cache_dir = tmp_path / "cache"
    _seeded_index(cache_dir).lookup("λόγος")

    # A fresh instance, no jsonl_path at all -- the previous lookup's answer
    # must already be on disk, not just held in the first instance's memory.
    reopened = CachedWiktextractIndex(cache_dir)

    assert reopened.lookup("λόγος")["senses"][0]["glosses"] == ["word, speech"]


def test_cached_index_caches_confirmed_absence(tmp_path):
    cache_dir = tmp_path / "cache"
    first = _seeded_index(cache_dir)

    assert first.lookup("not-in-fixture") is None
    assert (cache_dir / "not-in-fixture.json").exists()

    # Confirmed-absent lemmas must stay resolvable with no dump available.
    reopened = CachedWiktextractIndex(cache_dir)
    assert reopened.lookup("not-in-fixture") is None


def test_cached_index_miss_without_dump_available_is_not_cached(tmp_path):
    cache_dir = tmp_path / "cache"
    index = CachedWiktextractIndex(cache_dir)  # no jsonl_path -- dump unavailable

    assert index.lookup("λόγος") is None
    assert list(cache_dir.iterdir()) == []
