# Changelog

## 2026-08-19
- Replaced the vendored 1.4GB `data/wiktextract/el-extract.jsonl` (committed
  via Git LFS) with `CachedWiktextractIndex`: a lazy, per-lemma disk cache
  under `data/wiktextract-cache/` (569 small JSON files, 3.2MB total),
  matching the plain-tracked pattern `data/morpheus-cache/` already uses.
  Only lemmas actually looked up during a build get resolved and cached —
  the full raw dump is now a one-time, gitignored, local-only download,
  needed only to resolve a genuinely new lemma; once cached, an answer
  (found or confirmed absent) never needs the raw dump again. Verified live
  against the real dump: first run resolves normally (93s, matching the
  original pilot), a second consecutive run completes in 9s with the raw
  dump untouched, confirming the cache is actually load-bearing and not
  just smaller. `WiktextractIndex` (eager, in-memory) is unchanged and
  still used by existing unit tests against small fixtures; the shared
  JSONL-parsing logic was extracted into `_load_entries()` so both classes
  use identical parsing. `CachedWiktextractIndex`'s cache-file mechanics
  (dir init, quote-based path, read, write) duplicated `MorpheusClient`'s
  near-verbatim, so both now share a `KeyedJsonCache` in new
  `okfbuild/sources/disk_cache.py`; also deduped 3 near-identical test
  constructions behind one `_seeded_index()` helper. `el-extract.jsonl`
  untracked going forward
  (`git rm --cached`) but its prior commit (`b63dd696`) still holds the
  full 1.4GB LFS object in history — a separate decision, not yet made,
  on whether to purge it via a history rewrite.
