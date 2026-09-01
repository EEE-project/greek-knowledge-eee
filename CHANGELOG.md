# Changelog

## 2026-09-01

- **LLM gap-filler pipeline wiring** (5 sections, branch `feature/llm-gap-filler-pipeline-wiring`, not yet merged) — builds on the earlier `llm-backend-eee` foundation (`fill_gap()`/`GapFillCache`/`LLMModelConfig`, merged separately today) to make LLM-assisted morphology gap-filling actually usable end-to-end, from prompt context through a real pilot run to independent verification.
  - `fill_gap()` now receives a `context` string (the grammatical slot label, plus period/dialect/author/work when known) that reaches both the real LLM prompt — via `llm-backend-eee`'s own `label` mechanism, confirmed against its installed source — and the cache key, so a query under different context is never served from a differently-scoped cache hit. Course-level author/work/dialect metadata (curated in a new, deliberately small `okfbuild/course_context.py`, currently just the Odyssey and Kavafis Ithaki courses) is course-level signal ("this gap comes from the Odyssey course"), never conflated with word-level attestation ("Homer's own text uses this exact form").
  - `GapFillCache` gained `save()`/`load()`: atomic writes (temp file + `os.replace()`), a `format_version` field, exclusion of transient failures from persistence (an all-`CALL_FAILED` entry is never written as a stable negative result — it would wrongly block a legitimate retry), and run-ID-scoped resumability under a caller-supplied `gap_fill_cache_dir` (`<dir>/.gap_fill_runs/<run-id>/cache.json`). `pipeline.run()` shares one cache across every lemma it processes and automatically resumes the most recent incomplete run; a run that completes normally removes its own cache file.
  - A three-layer pytest gate protects any real, billed LLM API test from running by accident: a `paid_llm_api` marker, a `--run-paid-llm-tests` CLI flag (via a custom collection hook, not `addopts`, since `addopts` is trivially overridden by an explicit `-m` on the command line), and a fixture-level double-gate function (`require_paid_llm_gate()`) that re-checks a real API key plus `GREEK_KNOWLEDGE_RUN_PAID_LLM_TESTS=1` every time, regardless of how a test was invoked — the fixture-level check is the actual enforcement boundary, not the marker.
  - A real, two-model `GapFillerConfig` via OpenRouter (`openai/gpt-4o-mini` + `anthropic/claude-3.5-haiku`, one API key: `GREEK_KNOWLEDGE_OPENROUTER_API_KEY`) plus `okfbuild/gap_filler_pilot.py`'s `run_gap_filler_pilot()`: writes to an isolated, gitignored `build/gap-filler-pilot/` directory — never the tracked `words/`/`grammar`/`culture` trees, since an exploratory LLM-gap-filled run shouldn't land in already-reviewed output before a human sees it — plus a JSON "handoff" file recording every individual LLM-inferred form with full structured provenance (lemma/form/slot label/features/pos/language/period/method). Confirmed directly (OpenRouter's own API reference, plus the installed `llm-backend-eee` v0.2.1 source) that a routing provider can silently substitute a different model than requested, and that `llm-backend-eee` discards the response field that would reveal it — so the handoff's `method` field reflects the model *requested*, never confirmed as the one that actually responded. Documented, not fixed (would need a change in that separate package).
  - `okfbuild/morpheus_crosscheck.py`: a standalone tool cross-checking the handoff file's forms against the real Perseids Morpheus service, classifying each into `CONFIRMED` / `DIFFERENT_ANALYSIS` / `UNDERSPECIFIED` / `UNCONFIRMED` / `QUERY_FAILED` via a 7-axis UD-FEATS↔Morpheus vocabulary mapping built from real captured Morpheus responses (full, spelled-out English words like `"genitive"`) — not the abbreviated shape (`"gen"`) this repo's own pre-existing `MorpheusClient` test fixtures happen to use, which would have made the classifier look correct in tests while being silently wrong against every real response. Voice is modeled as match-sets, not a flat lookup: a `mediopassive` reading neither confirms nor contradicts a specifically-requested `Mid`/`Pass`. Purely informational — flags disagreement, blocks nothing, never modifies `words/*.md`.
  - Not yet done: the branch hasn't been merged; the real gated pilot has never actually been run (needs a real API key); no cross-check report exists yet against real output.
  - 215 tests in the suite as of this branch's tip (214 passing, 1 correctly skipped — the real gated pilot test), most of them new across these 5 sections. `ruff check` clean aside from one deliberately-unsuppressed `BLE001` (an intentional broad `except Exception:` converting any Morpheus/JSON/network failure into a documented sentinel, matching an existing pattern already used elsewhere in this codebase).

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
