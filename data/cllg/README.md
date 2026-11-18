# data/cllg/

The Freed corpus of the Corpus Liberatum Linguae Graecae (CLLG): the TLG E texts as TEI files. It is an opt-in,
**local-only** sparse git clone in `freed-corpus/`, which is gitignored (see `.gitignore`). Nothing from it is
committed, and no cache of its passages is kept either. `greek-knowledge cllg` reads it; see
`references/sources/cllg.md`.

Fetch only the texts you need. Take their ids from the corpus index page
https://freed-corpus-bae861.gitlabpages.inria.fr/. The id `tlg0012.tlg002` (the Odyssey) is the folder
`data/tlg0012/tlg002`. From the repo root:

```bash
git clone --depth 1 --filter=blob:none --sparse https://gitlab.inria.fr/almanach/cllg/freed-corpus.git data/cllg/freed-corpus
git -C data/cllg/freed-corpus sparse-checkout set data/tlg0012/tlg002 data/tlg5026/tlg007   # the Odyssey, the Odyssey scholia (Dindorf)
git -C data/cllg/freed-corpus sparse-checkout add data/tlg4083/tlg003                      # later: one more text (Eustathius on the Odyssey)
uv run greek-knowledge cllg tlg0012.tlg002 10.510
```

The GitLab web pages of the corpus refuse automated reads; git works. Checked with corpus commit `281049a`
(2026-10-06). Licence: the texts are CC0 1.0. The citation structure and the metadata are CC-BY 4.0: attribute the
Corpus Liberatum Linguae Graecae (dir. Thibault Clérice).
