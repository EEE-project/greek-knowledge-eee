# Wiktextract (kaikki.org)

kaikki.org's Wiktextract JSONL dumps (fully-expanded Wiktionary
templates), two relevant editions: Modern Greek (`kaikki.org/elwiktionary/`)
and Ancient Greek (`kaikki.org/dictionary/Ancient%20Greek/`), CC
BY-SA/GFDL dual license, updated every few days.

Parsed by [`okfbuild/sources/wiktextract_index.py`](../../okfbuild/sources/wiktextract_index.py) (added in
section-03-source-clients) into a lemma-keyed index. `CachedWiktextractIndex`
(added 2026-08-19, closing the "loaded once per pipeline run" limitation
flagged here at pilot time) only resolves lemmas actually looked up,
persisting each answer as a small per-lemma file under
`data/wiktextract-cache/` — a rebuild against already-seen course vocabulary
never needs the full multi-hundred-MB dump at all, only a genuinely new
lemma does. The raw dump itself is gitignored, not committed (see
`data/wiktextract/README.md`).
