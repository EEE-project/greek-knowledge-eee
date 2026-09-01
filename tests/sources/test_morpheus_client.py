import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

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


def test_analyze_raise_on_error_true_reraises_the_underlying_exception(tmp_path):
    client = MorpheusClient(tmp_path / "cache")

    with (
        patch("okfbuild.sources.morpheus_client.urllib.request.urlopen", side_effect=OSError("network down")),
        pytest.raises(OSError, match="network down"),
    ):
        client.analyze("failing-word", raise_on_error=True)


def test_analyze_default_and_explicit_false_preserve_swallow_to_empty_list(tmp_path):
    """Every existing caller (lexical_entry.build()'s citation lookup) omits
    raise_on_error entirely -- both the implicit default and an explicit
    False must preserve today's exact log-and-return-[] behavior."""
    client = MorpheusClient(tmp_path / "cache")

    with patch("okfbuild.sources.morpheus_client.urllib.request.urlopen", side_effect=OSError("network down")):
        default_result = client.analyze("failing-word-a")
        explicit_false_result = client.analyze("failing-word-b", raise_on_error=False)

    assert default_result == []
    assert explicit_false_result == []
