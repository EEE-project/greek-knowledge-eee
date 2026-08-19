"""Shared cache-file-per-key mechanics for source clients that resolve one
key at a time and want to persist each answer as its own small JSON file
(`MorpheusClient`: HTTP-resolved; `CachedWiktextractIndex`: local-dump-resolved).
"""

import json
import urllib.parse
from pathlib import Path


class KeyedJsonCache:
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        safe = urllib.parse.quote(key, safe="")
        return self.cache_dir / f"{safe}.json"

    def read(self, key: str) -> "tuple[bool, object]":
        """Returns (True, value) on a cache hit, (False, None) on a miss."""
        path = self._path_for(key)
        if not path.exists():
            return False, None
        return True, json.loads(path.read_text(encoding="utf-8"))

    def write(self, key: str, value) -> None:
        self._path_for(key).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
