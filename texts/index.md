# Literary Translation entries

One subdirectory per literary work, each with its own `index.md`. Hand-
authored, not built by `okfbuild/pipeline.py` — there is no live source to
query for a human translation, and no generator step at all: copy
[`templates/literary-translation.md`](../templates/literary-translation.md),
fill it in, and run `uv run greek-knowledge check` to validate it.
`kavafis_ithaki/` is authored this way already; `odyssey/` still has its
own one-off script (`scripts/populate_odyssey_texts.py`) with the text
hardcoded as Python constants, not yet migrated to hand-authored files.

- [odyssey/](odyssey/index.md) — Homer's Odyssey (I.1-21, IX.19-38)
- [kavafis_ithaki/](kavafis_ithaki/index.md) — Cavafy's «Ithaka» (στ. 1-23)
