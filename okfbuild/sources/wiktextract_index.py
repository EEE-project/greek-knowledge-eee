"""Reads kaikki.org Wiktextract JSONL dumps (Modern or Ancient Greek edition)
into an in-memory, lemma-keyed lookup index.
"""

import json
from pathlib import Path


class WiktextractIndex:
    def __init__(self, entries: dict[str, dict]):
        self._entries = entries

    @classmethod
    def load(cls, jsonl_path: Path, lang_code: str | None = None) -> "WiktextractIndex":
        """Load one kaikki.org JSONL dump (Modern Greek or Ancient Greek
        edition — see claude-research.md §2.3) into a lemma-keyed index.

        A kaikki.org dump has one JSONL object per dictionary entry, not
        per word — the same word can recur across multiple lines, both for
        the mundane reason (distinct POS or etymologies within one
        language) and because a single wiktionary edition documents
        multiple languages' words on one headword page (e.g. el.wiktionary
        entries include both a `lang_code: "el"` Modern Greek section and
        a `lang_code: "grc"` Ancient Greek section for the same shared
        headword, e.g. "νόστος") — confirmed directly against the real
        el-extract.jsonl dump, not assumed. `lang_code`, if given, keeps
        only entries matching that code, so a caller wanting "the modern
        edition's own reading" isn't handed whichever language happened to
        sort last in the dump. Without it (the default), this index keeps
        only the last entry seen for a given word, matching lookup()'s
        single-dict return type; earlier entries for the same word are
        discarded."""
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
        return cls(entries)

    def lookup(self, lemma: str) -> dict | None:
        """Return the raw Wiktextract entry dict for `lemma`, or None."""
        return self._entries.get(lemma)
