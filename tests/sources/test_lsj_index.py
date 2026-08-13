from pathlib import Path

import defusedxml.common
import pytest

from okfbuild.sources.lsj_index import LSJIndex

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sources"


def test_load_returns_entry_text_for_known_headword():
    index = LSJIndex.load(FIXTURES_DIR / "lsj")

    text = index.lookup("ἀγαθός")

    assert text is not None
    assert "good" in text


def test_load_rejects_billion_laughs_entity_expansion():
    with pytest.raises(defusedxml.common.EntitiesForbidden):
        LSJIndex.load(FIXTURES_DIR / "lsj_billion_laughs")
