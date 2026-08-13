"""Wikipedia REST API client — GET /api/rest_v1/page/summary/{title}.

No auth required at this project's call volume; every request sets a
descriptive User-Agent (Wikimedia API etiquette for anonymous/no-auth
use — a hard requirement, not a nice-to-have) and retries on 429/5xx
rather than treating them as fatal.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

_USER_AGENT = "EEE-project research (educational, low-volume)"
_MAX_ATTEMPTS = 3
_RETRY_DELAY = 1.0
_RETRYABLE_CODES = {429, 500, 502, 503, 504}


def summary(title: str, lang: str = "en") -> dict | None:
    """Fetch a page summary via the Wikipedia REST API
    (GET https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}).
    No auth required at this project's expected call volume, but every
    request MUST set a descriptive User-Agent identifying this project
    (per Wikimedia API etiquette) and MUST back off and retry on 429/5xx
    responses rather than treating them as fatal — only a 404 (no such
    page) returns None; other errors propagate after retry exhaustion."""
    encoded_title = urllib.parse.quote(title.replace(" ", "_"), safe="")
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})

    last_error = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code not in _RETRYABLE_CODES:
                raise
            last_error = e
            if attempt < _MAX_ATTEMPTS - 1:
                time.sleep(_RETRY_DELAY)
    raise last_error
