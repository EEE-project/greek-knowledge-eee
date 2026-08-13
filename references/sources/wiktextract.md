# Wiktextract (kaikki.org)

kaikki.org's Wiktextract JSONL dumps (fully-expanded Wiktionary
templates), two relevant editions: Modern Greek (`kaikki.org/elwiktionary/`)
and Ancient Greek (`kaikki.org/dictionary/Ancient%20Greek/`), CC
BY-SA/GFDL dual license, updated every few days.

Parsed by `okfbuild/sources/wiktextract_index.py` (added in
section-03-source-clients) into a lemma-keyed index, loaded once per
pipeline run — a known, deliberately-deferred performance limitation at
full six-course scale (not a concern at this pilot's scale).
