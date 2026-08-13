import json
import shutil
from pathlib import Path
from unittest.mock import patch

from okfbuild.sources.morpheus_client import MorpheusClient

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sources"


def test_analyze_returns_cached_result_without_http_call(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    shutil.copy(FIXTURES_DIR / "morpheus_cache" / "test-word.json", cache_dir / "test-word.json")
    client = MorpheusClient(cache_dir)

    with patch("okfbuild.sources.morpheus_client.urllib.request.urlopen") as mock_urlopen:
        result = client.analyze("test-word")

    mock_urlopen.assert_not_called()
    assert result[0]["lemma"] == "some-lemma"
    assert result[0]["case"] == "gen"
    assert result[0]["dial"] == ["epic"]


def test_analyze_falls_back_to_http_when_no_cache_file_exists(tmp_path):
    cache_dir = tmp_path / "cache"
    client = MorpheusClient(cache_dir)

    raw_response = {
        "RDF": {
            "Annotation": {
                "Body": {
                    "rest": {
                        "entry": {
                            "dict": {"hdwd": {"$": "other-lemma"}, "pofs": "verb"},
                            "infl": {"num": "sing", "dial": ["Doric", "Aeolic"]},
                        }
                    }
                }
            }
        }
    }
    mock_resp = json.dumps(raw_response).encode("utf-8")

    with (
        patch("okfbuild.sources.morpheus_client.urllib.request.urlopen") as mock_urlopen,
        patch("okfbuild.sources.morpheus_client.time.sleep"),
    ):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = mock_resp
        result = client.analyze("other-word")

    mock_urlopen.assert_called_once()
    assert result[0]["lemma"] == "other-lemma"
    assert result[0]["dial"] == ["Doric", "Aeolic"]
    assert (cache_dir / "other-word.json").exists()
