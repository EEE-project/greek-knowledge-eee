from pathlib import Path

from okfbuild.sources.wiktextract_index import WiktextractIndex

FIXTURE = Path(__file__).parent.parent / "fixtures" / "sources" / "wiktextract_sample.jsonl"


def test_load_builds_lookup_index_from_jsonl():
    index = WiktextractIndex.load(FIXTURE)

    entry = index.lookup("λόγος")

    assert entry["pos"] == "noun"
    assert entry["senses"][0]["glosses"] == ["word, speech"]


def test_lookup_returns_none_for_lemma_not_in_fixture():
    index = WiktextractIndex.load(FIXTURE)

    assert index.lookup("not-in-fixture") is None
