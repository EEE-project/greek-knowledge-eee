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

This repo's code is a Python API, not a CLI. Run it with `uv run python`
(a script, or a REPL) from inside this directory — not a bare `python` or
any other environment, even another EEE repo's venv. This repo has one
dependency (`llm-backend-eee`) not on PyPI at all, pinned via a Codeberg
git tag; only `uv`'s own project-managed `.venv/` here has it installed.
Two entry points cover most needs, both taking a `SourceBundle` -- wire one
first (this is the same wiring `tests/conftest.py`'s `real_source_bundle`
fixture uses):
```python
from pathlib import Path
from okfbuild.sources import SourceBundle, eee_engine, wikipedia_client
from okfbuild.sources.morpheus_client import MorpheusClient
from okfbuild.sources.wiktextract_index import CachedWiktextractIndex
from okfbuild.sources.lsj_index import CachedLSJIndex
from okfbuild.sources.byzantine_lexicon import load_byzantine_forms

import eee_project as eee
from ancient_greek_backend_eee import AncientGreekBackend
from modern_greek_backend_eee import ModernGreekBackend

# Backend registration is the caller's responsibility, once per process
# (see eee_engine.py's own module docstring).
eee.register_backend("grc", AncientGreekBackend.for_period("epic"), backend="homeric")
eee.register_backend("grc", AncientGreekBackend.for_period("attic"), backend="attic")
eee.register_backend("el", ModernGreekBackend())

sources = SourceBundle(
    eee_engine=eee_engine,
    morpheus=MorpheusClient(cache_dir=Path("data/morpheus-cache")),
    # Ships in the sibling greek-inflexion-eee checkout, not this repo --
    # adjust the path to wherever yours lives.
    byzantine_forms=load_byzantine_forms(
        Path("../greek-inflexion-eee/src/greek_inflexion_eee/data/byzantine_verbs_lexicon.yaml")
    ),
    wiktextract=CachedWiktextractIndex(
        cache_dir=Path("data/wiktextract-cache"), jsonl_path=None, lang_code="el"
    ),
    lsj=CachedLSJIndex(cache_dir=Path("data/lsj-cache"), tei_xml_dir=None),
    wikipedia=wikipedia_client,
)
```

**Build and write one concept file** (continues in the same session as the
`sources` wiring above -- both examples below need that `sources` object
to already exist, they don't redefine it):
```python
from okfbuild.concepts import lexical_entry
from okfbuild.okf import write

concept = lexical_entry.build(
    "νόστος", "noun", ["homeric", "attic", "byzantine", "modern"], sources,
    level=[], tags=[],
)
write(concept, Path("words/νόστος.md"))
```
Expect `write()` to return `True` (a new file, or content that changed) or
`False` (the file already had this exact content) -- both are success, it
never raises for a normal build. `concept` itself is a `ConceptFile`, not
yet written to disk until `write()` is called.

**Or run the full pipeline over one or more courses** (extracts vocabulary
from each course's TSVs, builds every concept, prunes stale files no longer
touched) -- an alternative to the single-concept example above, not a
continuation of it, but it still needs the same `sources` from the wiring
step. Unlike that example, `out_dir` here is not a safe default to point at
this repo's own root: anything under `out_dir/{words,grammar,culture}` not
touched by *this specific call* gets pruned (`status` flipped to
`deprecated`) -- including this repo's own real `grammar/`/`culture/`
content, since this example doesn't pass `grammar_rules=`/
`cultural_topics=` (see `okfbuild/pilot_content.py`'s `GRAMMAR_RULES`/
`CULTURAL_TOPICS`, and `tests/conftest.py`'s `pilot_build_report` fixture
for how the real pilot run passes those correctly). Use a scratch
directory, as below, unless you mean to regenerate this repo's own tracked
content and are passing everything the real pilot run does:
```python
from okfbuild import pipeline

report = pipeline.run([Path("path/to/a/course")], Path("/tmp/okf-output"), sources)
print(report.written, report.unchanged, report.failed)
```
`Path(...)` does not expand a leading `~` to your home directory on its
own (that needs `Path(...).expanduser()`) -- a literal `~` in the string
is just a nonexistent directory named `~`, so course_paths silently finds
zero vocabulary files and `report` comes back `(0, 0, 0)` with nothing
written, no error raised, and `out_dir` never even created.

Expect `written + unchanged` to equal the course's total vocabulary size,
and `report.failed` to be `0` on a course with no coverage gaps -- if it's
not, `report.errors` has one string per failure, worth reading before
assuming the pipeline itself is broken (a handful of genuinely rare or
unattested words failing is expected on a large real course, not a bug --
see "Development" below for how large that number gets on this repo's own
two pilot courses).

To also fill morphology gaps via a real LLM, pass a `GapFillerConfig` as
`sources.llm_gap_filler` and a `gap_fill_cache_dir` to `run()` — see
`okfbuild/gap_filler_pilot.py`'s `run_gap_filler_pilot()` for the reference
wiring, and "Development" below for the paid-test gating this same
mechanism uses.

LSJ citations also get an inline `**[5th c. BC, Doric]**`-style period/
dialect marker when `sources.lsj_period_map` is set to an
`okfbuild.sources.lsj_periods.LSJPeriodMap`
(`LSJPeriodMap.build(tei_xml_dir, diorisis_catalog_path, cache_path)` —
needs the real LSJ dump and `data/diorisis/catalog.tsv`, the latter
already git-tracked in this repo). Optional: `None` (the default) still
renders every citation correctly, just without period tags — see
`tests/conftest.py`'s `real_source_bundle` fixture, which wires this the
same conditionally-available way it wires `lsj` itself, for the
reference wiring.


## Content model

Four OKF concept types, each one markdown file with YAML frontmatter:
**Lexical Entry** (one file per word, with a section per attested
historical period), **Grammatical Rule** (one file per documented
period-to-period morphological change), **Cultural Context** (one
file per person/theme/work), and **Literary Translation** (one file
per work/passage/language, gathering every translator's rendering of
that passage). Every claim in a Lexical Entry/Grammatical Rule/
Cultural Context file's body is footnote-cited back to a `sources[]`
frontmatter entry; a Literary Translation file instead cites inline,
via an HTML-comment description line under each translator's `##`
heading. See `okfbuild/okf.py` (added in section-02-okf-writer) for
the exact schema.


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
| Diorisis Ancient Greek Corpus | 820 works, per-word lemma/POS/morphology, TLG-numbered, CC BY-SA (catalog integrated for LSJ period mapping; full per-word morphology not yet integrated) | [`references/sources/diorisis.md`](references/sources/diorisis.md) |
| Homer/Odyssey scholarship | Commentary/scholarship on Homer (Голинкевич, Гордезиани, Lord, Сахарный, Тахо-Годи; not integrated) | [`references/sources/homer-scholarship.md`](references/sources/homer-scholarship.md) |
| Greek alphabet origins | Papers on the Greek alphabet's formation and pre-alphabetic antecedents (not integrated) | [`references/sources/greek-alphabet-origins.md`](references/sources/greek-alphabet-origins.md) |
| Pre-Greek substrate overview (Hieber) | Blog/newsletter survey of ~1,000 non-IE Ancient Greek words (orientation citation, not integrated) | [`references/sources/pre-greek-substrate-overview.md`](references/sources/pre-greek-substrate-overview.md) |
| Verhasselt (2009), Pre-Greek substratum survey | Open-access literature review of Pre-Greek substrate scholarship (not integrated) | [`references/sources/verhasselt-pre-greek-substratum.md`](references/sources/verhasselt-pre-greek-substratum.md) |
| Pre-Greek toponyms dataset (Hieber) | Pre-Greek place names ranked by certainty (view-only, not integrated) | [`references/sources/pre-greek-toponyms.md`](references/sources/pre-greek-toponyms.md) |
| Leiden IE Etymological Dictionary Series (Brill) | ~12-volume IE-branch dictionary series incl. Beekes' Greek volume (subscription-only, not integrated beyond Beekes) | [`references/sources/leiden-ie-dictionary-series.md`](references/sources/leiden-ie-dictionary-series.md) |
| IE-CoR | 1,600+ IE cognate sets + language trees, CC BY 4.0 CLDF data (not integrated, strong tool candidate) | [`references/sources/iecor.md`](references/sources/iecor.md) |
| CLARIN Virtual Language Observatory | Meta-catalog of ~975k language-resource records (discovery tool, not integrated) | [`references/sources/clarin-vlo.md`](references/sources/clarin-vlo.md) |
| European Language Grid catalogue | Meta-catalog of language resources/tools (discovery tool, not integrated) | [`references/sources/european-language-grid.md`](references/sources/european-language-grid.md) |
| Greek For Euclid (Calvert) | 26-lesson course on mathematical Greek for reading Euclid's *Elements* (legacy SPIonic font, not integrated) | [`references/sources/greek-for-euclid.md`](references/sources/greek-for-euclid.md) |
| Textkit | Open CC BY-SA library of 180+ public-domain Ancient Greek/Latin textbooks (PDFs, not integrated) | [`references/sources/textkit.md`](references/sources/textkit.md) |
| Irby (2017), scientific-Greek reading anthology | Annotated Greek passages across 8+ scientific disciplines incl. an Euclid excerpt, CC BY 3.0 (not integrated) | [`references/sources/irby-scientific-greek.md`](references/sources/irby-scientific-greek.md) |


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
The one such test today (`tests/test_gap_filler_pilot.py`) reads its API key
from `GREEK_KNOWLEDGE_OPENROUTER_API_KEY` — a real
[OpenRouter](https://openrouter.ai/) key, used to query two models
(`openai/gpt-4o-mini`, `anthropic/claude-3.5-haiku`) through one endpoint. It
does not attempt full completion of a course scan — a real, zero-cost
measurement found that needs on the order of 90,000 real LLM requests, far
more than any single run should attempt. Instead it verifies the mechanism
cheaply (a handful of real requests): a small real budget stops the run
cleanly, its cache is preserved, and a second real run against that cache
genuinely resumes. Output goes to an isolated `tmp_path`, discarded after the
test.

To actually (re)generate real content with the gap-filler, run it directly —
`okfbuild.gap_filler_pilot.run_gap_filler_pilot()` — rather than via this
test. Output goes to the gitignored `build/gap-filler-pilot/`, never the
tracked `words/`/`grammar`/`culture` trees — review and selectively copy from
there by hand.
