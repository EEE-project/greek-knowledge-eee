# arXiv Complete Corpus (Hugging Face)

`https://huggingface.co/datasets/secemp9/arxiv-complete` — a one-off
snapshot of arXiv: metadata (from arXiv's OAI-PMH `arXivRaw` interface),
version history, submission files and rendered documents for 3,148,796
papers, with file contents, paths, sizes and SHA-256 digests; a PDF is
held for 99.47% of papers. The dataset is public and not gated. Its
configs are `sample` (26 MB), `metadata`, `versions`, `files`,
`paper_text` (one resolved TeX string per paper), `latex`, `source`,
`pdf` and `ps`. The repo holds about 3,700 files and roughly 16 TB
(Hugging Face's reported `usedStorage`). Licences vary by paper
(`license: other`, "mixed-arxiv-author-licenses"); only the compilation
carries a CC0 dedication. Created 2026-09-10 (checked 2026-09-21).

**Status: not integrated, and not Greek-specific** — a general
scientific-preprint corpus, English-language per its card. It could
only serve as a pool to search for papers on Greek linguistics,
computational philology or classics (for example by filtering
`metadata`), not as a source to cite from directly. The card's own
caveats apply: `paper_text` keeps LaTeX syntax, comments and macros and
needs filtering, some rows are withdrawal stubs, and large binary rows
need substantial memory. Per-paper licences must be checked before any
quotation.
