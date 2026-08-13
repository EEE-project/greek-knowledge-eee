import json
import urllib.error
from unittest.mock import MagicMock, patch

from okfbuild.sources.wikipedia_client import summary


def _mock_response(payload: dict) -> MagicMock:
    mock = MagicMock()
    mock.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    return mock


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://en.wikipedia.org/x", code, "error", {}, None)


def test_summary_returns_parsed_dict_on_200():
    payload = {"title": "Odyssey", "extract": "An epic poem."}
    with patch(
        "okfbuild.sources.wikipedia_client.urllib.request.urlopen",
        return_value=_mock_response(payload),
    ):
        result = summary("Odyssey")

    assert result == payload


def test_summary_returns_none_on_404():
    with patch(
        "okfbuild.sources.wikipedia_client.urllib.request.urlopen",
        side_effect=_http_error(404),
    ):
        result = summary("No_Such_Page")

    assert result is None


def test_summary_retries_on_429_then_succeeds():
    payload = {"title": "Retried"}
    with (
        patch(
            "okfbuild.sources.wikipedia_client.urllib.request.urlopen",
            side_effect=[_http_error(429), _mock_response(payload)],
        ),
        patch("okfbuild.sources.wikipedia_client.time.sleep"),
    ):
        result = summary("Retried")

    assert result == payload


def test_summary_sends_descriptive_user_agent():
    payload = {"title": "X"}
    with patch(
        "okfbuild.sources.wikipedia_client.urllib.request.urlopen",
        return_value=_mock_response(payload),
    ) as mock_urlopen:
        summary("X")

    request_obj = mock_urlopen.call_args[0][0]
    user_agent = request_obj.get_header("User-agent")
    assert user_agent
    assert "python-urllib" not in user_agent.lower()
