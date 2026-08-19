"""Reads kaikki.org Wiktextract JSONL dumps (Modern or Ancient Greek edition)
into an in-memory, lemma-keyed lookup index.
"""

import json
import logging
from pathlib import Path

from okfbuild.sources.disk_cache import KeyedJsonCache

logger = logging.getLogger(__name__)


def _load_entries(jsonl_path: Path, lang_code: "str | None" = None) -> dict[str, dict]:
    """Parse one kaikki.org JSONL dump (Modern Greek or Ancient Greek
    edition — see claude-research.md §2.3) into a lemma-keyed dict.

    A kaikki.org dump has one JSONL object per dictionary entry, not per
    word — the same word can recur across multiple lines, both for the
    mundane reason (distinct POS or etymologies within one language) and
    because a single wiktionary edition documents multiple languages' words
    on one headword page (e.g. el.wiktionary entries include both a
    `lang_code: "el"` Modern Greek section and a `lang_code: "grc"` Ancient
    Greek section for the same shared headword, e.g. "νόστος") — confirmed
    directly against the real el-extract.jsonl dump, not assumed.
    `lang_code`, if given, keeps only entries matching that code, so a
    caller wanting "the modern edition's own reading" isn't handed
    whichever language happened to sort last in the dump. Without it (the
    default), only the last entry seen for a given word is kept; earlier
    entries for the same word are discarded."""
    entries: dict[str, dict] = {}
    with Path(jsonl_path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if lang_code is not None and entry.get("lang_code") != lang_code:
                continue
            word = entry.get("word")
            if word:
                entries[word] = entry
    return entries


class WiktextractIndex:
    def __init__(self, entries: dict[str, dict]):
        self._entries = entries

    @classmethod
    def load(cls, jsonl_path: Path, lang_code: str | None = None) -> "WiktextractIndex":
        """Load one kaikki.org JSONL dump entirely into memory. Fine for
        small fixtures (tests); for the real multi-hundred-MB dump, prefer
        `CachedWiktextractIndex`, which only ever resolves the lemmas
        actually looked up."""
        return cls(_load_entries(jsonl_path, lang_code))

    def lookup(self, lemma: str) -> dict | None:
        """Return the raw Wiktextract entry dict for `lemma`, or None."""
        return self._entries.get(lemma)


class CachedWiktextractIndex:
    """Same `lookup(lemma)` contract as `WiktextractIndex`, but backed by a
    small per-lemma disk cache instead of loading the entire multi-hundred-MB
    dump into memory up front (see `references/sources/wiktextract.md`'s
    "known, deliberately-deferred performance limitation").

    Only the lemmas actually looked up ever get resolved and cached — the
    full raw dump is a one-time, local-only, gitignored download needed just
    to resolve a genuinely new lemma; once cached, a lemma's answer (found
    or confirmed absent) never needs the raw dump again. This is the same
    cache-file-per-word shape `MorpheusClient` already uses for the Morpheus
    source, just resolving misses by scanning a local file instead of
    calling a live API.
    """

    def __init__(self, cache_dir: Path, jsonl_path: "Path | None" = None, lang_code: "str | None" = None):
        self._cache = KeyedJsonCache(cache_dir)
        self.cache_dir = self._cache.cache_dir
        self._jsonl_path = jsonl_path
        self._lang_code = lang_code
        self._full_index: "dict[str, dict] | None" = None

    def lookup(self, lemma: str) -> dict | None:
        hit, entry = self._cache.read(lemma)
        if hit:
            return entry

        if self._full_index is None:
            if self._jsonl_path is None or not self._jsonl_path.exists():
                logger.warning(
                    "Wiktextract cache miss for %r and no local dump available to resolve it -- "
                    "not caching, since this isn't a confirmed absence", lemma,
                )
                return None
            self._full_index = _load_entries(self._jsonl_path, self._lang_code)

        entry = self._full_index.get(lemma)
        self._cache.write(lemma, entry)
        return entry
