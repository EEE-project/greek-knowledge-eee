"""Client for the Perseids Morpheus Ancient Greek morphological analysis service.

Vendored from greek-inflexion-eee/tools/morpheus/query_morpheus.py — that
script lives under that repo's tools/ directory, not its installable
package, so importing it directly would mean depending on another repo's
internal layout rather than its public API.
"""

# TODO: extract to a shared library, see query_morpheus.py in greek-inflexion-eee

import json
import logging
import time
import urllib.parse
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_URL = "https://services.perseids.org/bsp/morphologyservice/analysis/word"
_USER_AGENT = "EEE-project research (educational, low-volume)"
_ENGINE = "morpheusgrc"
_REQUEST_DELAY = 0.4


def _as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def _text_of(x):
    return x.get("$") if isinstance(x, dict) else x


class MorpheusClient:
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, word: str) -> Path:
        safe = urllib.parse.quote(word, safe="")
        return self.cache_dir / f"{safe}.json"

    def analyze(self, word: str, lang: str = "grc") -> list[dict]:
        """Query (or read from local cache) Morpheus's analysis for `word`.
        Reuses the existing cache-file-per-word convention and error
        shape from query_morpheus.py.

        Decision: a request failure (network error, timeout, non-2xx
        response) is logged and treated as "no analysis found" (empty
        list), rather than raising or returning the original tool's
        {"error": str} sentinel — this keeps the return type strictly
        list[dict] as declared, and callers (section-04 concept builders)
        can treat a Morpheus miss uniformly whether it's "no entry" or
        "request failed" for what is enrichment data, not a hard
        dependency."""
        cache_file = self._cache_path(word)
        if cache_file.exists():
            raw = json.loads(cache_file.read_text(encoding="utf-8"))
        else:
            encoded = urllib.parse.quote(word)
            url = f"{BASE_URL}?word={encoded}&lang={lang}&engine={_ENGINE}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw = json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                logger.warning("Morpheus request failed for %r: %s", word, e)
                return []
            cache_file.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            time.sleep(_REQUEST_DELAY)

        return self._parse_entries(raw)

    @staticmethod
    def _parse_entries(raw: dict) -> list[dict]:
        try:
            body = raw["RDF"]["Annotation"]["Body"]
        except (KeyError, TypeError):
            return []
        results = []
        for b in _as_list(body):
            if not isinstance(b, dict):
                continue
            rest = b.get("rest")
            entry = rest.get("entry") if isinstance(rest, dict) else None
            for e in _as_list(entry):
                if not isinstance(e, dict):
                    continue
                dict_ = e.get("dict", {})
                infl = e.get("infl", {})
                for inf in _as_list(infl) or [{}]:
                    results.append(
                        {
                            "lemma": _text_of(dict_.get("hdwd")),
                            "pofs": _text_of(dict_.get("pofs")) or _text_of(inf.get("pofs")),
                            "case": _text_of(inf.get("case")),
                            "number": _text_of(inf.get("num")),
                            "gender": _text_of(inf.get("gend")),
                            "person": _text_of(inf.get("pers")),
                            "tense": _text_of(inf.get("tense")),
                            "mood": _text_of(inf.get("mood")),
                            "voice": _text_of(inf.get("voice")),
                            "stemtype": _text_of(inf.get("stemtype")),
                            "decl": _text_of(dict_.get("decl")) or _text_of(inf.get("decl")),
                            "dial": [_text_of(d) for d in _as_list(inf.get("dial"))],
                        }
                    )
        return results
