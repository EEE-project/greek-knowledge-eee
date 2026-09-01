# greek-knowledge-eee

A Greek language & culture knowledge base in Google's Open Knowledge
Format (OKF v0.2), built on the Ελληνικά Εκπαιδευτικά Εργαλεία (EEE) —
Greek Language Educational Tools — morphology engine. A standalone
personal/research project, not (yet) part of the EEE-project org. Built
by a batch pipeline that reads EEE course lesson materials (starting
with the Odyssey and Kavafis Ithaki courses) and queries the EEE
morphology engine plus several external linguistic sources, producing
plain, checked-in markdown files with YAML-frontmatter
provenance/citation metadata that a person or an AI agent can read
directly.

🔓 Open source: https://codeberg.org/sadov/greek-knowledge-eee

💬 Community: https://telegram.me/eee_greek


## Installation

This repo is not a library other packages import — it's cloned and run
directly to (re)generate the knowledge base content:

```bash
git clone https://codeberg.org/sadov/greek-knowledge-eee.git
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
| Digital Encyclopedia of Atticism (DEA) | Atticist lexica — prescriptive "correct Attic usage" commentary (not integrated) | [`references/sources/atticism-eu.md`](references/sources/atticism-eu.md) |
| Grammar references (Kühner, Gildersleeve, Sobolevsky, Kozarzhevsky, Wolf, Chantraine) | Citation sources for Grammatical Rule entries (print works, not integrated) | [`references/sources/grammar-references.md`](references/sources/grammar-references.md) |
| Diorisis Ancient Greek Corpus | 820 works, per-word lemma/POS/morphology, TLG-numbered, CC BY-SA (not yet integrated) | [`references/sources/diorisis.md`](references/sources/diorisis.md) |
| Homer/Odyssey scholarship | Commentary/scholarship on Homer (Голинкевич, Гордезиани, Lord, Сахарный, Тахо-Годи; not integrated) | [`references/sources/homer-scholarship.md`](references/sources/homer-scholarship.md) |
| Greek alphabet origins | Papers on the Greek alphabet's formation and pre-alphabetic antecedents (not integrated) | [`references/sources/greek-alphabet-origins.md`](references/sources/greek-alphabet-origins.md) |


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

Some tests under `integration` additionally call a real, billed LLM API
and are further gated behind their own `paid_llm_api` marker — running
them requires all of: the `--run-paid-llm-tests` flag, a real API key set
in the environment variable the test names, AND
`GREEK_KNOWLEDGE_RUN_PAID_LLM_TESTS=1` set exactly (not `"0"`/`"true"`/
anything else). Any one of these missing causes a clean skip, never a
silent real charge:
```bash
uv run pytest --run-paid-llm-tests -m "integration and paid_llm_api"
```
