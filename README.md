# greek-knowledge-eee

A Greek language & culture knowledge base in Google's Open Knowledge
Format (OKF v0.2) for the Ελληνικά Εκπαιδευτικά Εργαλεία (EEE) — Greek
Language Educational Tools project. Built by a batch pipeline that reads
this project's own lesson materials (starting with the Odyssey and
Kavafis Ithaki courses; the remaining EEE courses are future work) and
queries the EEE morphology engine plus several external linguistic
sources, producing plain, checked-in markdown files with YAML-frontmatter
provenance/citation metadata that a person or an AI agent can read
directly — the same way this org's other repos are already read via their
own README/CLAUDE.md/docs.

🔓 Open source:
- prod — https://github.com/EEE-project/greek-knowledge-eee
- prod mirror — https://gitlab.com/EEE-project/greek-knowledge-eee
- dev — https://codeberg.org/EEE-project/greek-knowledge-eee

💬 Community: https://telegram.me/eee_greek


## Installation

This repo is not a library other packages import — it's cloned and run
directly to (re)generate the knowledge base content:

```bash
git clone https://codeberg.org/EEE-project/greek-knowledge-eee.git
cd greek-knowledge-eee
uv sync --dev
```


## Usage

*(Filled in once `okfbuild/pipeline.py` exists — section-05-pipeline. Until
then, this repo's code is a Python API (`from okfbuild.pipeline import
run`), not yet a CLI wrapper.)*


## Content model

Three OKF concept types, each one markdown file with YAML frontmatter:
**Lexical Entry** (one file per word, with a section per attested
historical period), **Grammatical Rule** (one file per documented
period-to-period morphological change), and **Cultural Context** (one
file per person/theme/work). Every claim in a file's body is
footnote-cited back to a `sources[]` frontmatter entry. See
`okfbuild/okf.py` (added in section-02-okf-writer) for the exact schema.


## Sources

| Source | What it covers | Doc |
|---|---|---|
| EEE morphology engine (`eee_project`) | Homeric/Attic/Modern inflected forms, already installed | [`references/sources/eee-engine.md`](references/sources/eee-engine.md) |
| Morpheus | Classical/Koine Ancient Greek morphological analysis | [`references/sources/morpheus.md`](references/sources/morpheus.md) |
| Byzantine verb lexicon | Byzantine-period attested verb forms | [`references/sources/byzantine-lexicon.md`](references/sources/byzantine-lexicon.md) |
| LSJ (Liddell-Scott-Jones) | Classical Ancient Greek definitions/etymology | [`references/sources/lsj.md`](references/sources/lsj.md) |
| Wiktextract (kaikki.org) | Modern + Ancient Greek dictionary data | [`references/sources/wiktextract.md`](references/sources/wiktextract.md) |
| Wikipedia | Cultural/biographical context | [`references/sources/wikipedia.md`](references/sources/wikipedia.md) |
| Beekes' EDG | Indo-European etymology, word families (hand-curated, no bulk access) | [`references/sources/beekes.md`](references/sources/beekes.md) |
| Thesaurus Linguae Graecae (TLG) | Canonical Greek text library, Homer–Byzantine (subscription-only, not integrated) | [`references/sources/tlg.md`](references/sources/tlg.md) |
| Patrologia Graeca corpus (GREgORI/Calfa) | Late-antique/Byzantine Greek text, ~6M words, ~1% CER (not yet integrated) | [`references/sources/patrologia-graeca.md`](references/sources/patrologia-graeca.md) |
| ancientrome.ru | Greek author index + Dvoretsky Greek-Russian dictionary listing (finding aid, not integrated) | [`references/sources/ancientrome-ru.md`](references/sources/ancientrome-ru.md) |


## Development

```bash
uv sync --dev
uv run pytest
```

If `uv sync --dev` alone doesn't populate `pytest` into the venv, fall
back to:
```bash
uv run --all-extras --dev python -m pytest
```

`uv run pytest` with no flags also runs the pilot's real acceptance suite
(`tests/test_pilot_acceptance.py`, marked `integration`) — it needs a
sibling `created_with_eee` checkout and live network access (Perseids
Morpheus, Wikipedia). A downloaded Wiktextract dump
(`data/wiktextract/README.md`) is only needed the first time, or when a
course adds a lemma not already in `data/wiktextract-cache/` (git-tracked,
covers everything the current pilot's 2 courses use) — with a warm cache,
a run takes seconds; a cold one (resolving new lemmas against the full raw
dump) takes several minutes. For a fast unit-test-only run:
```bash
uv run pytest -m "not integration"
```
To run only the pilot acceptance suite:
```bash
uv run pytest -m integration
```
