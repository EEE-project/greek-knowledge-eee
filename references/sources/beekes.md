# Beekes' Etymological Dictionary of Greek (EDG)

Robert S. P. Beekes, *Etymological Dictionary of Greek* (Brill, 2010, 2
vols.) — the standard modern etymological reference for Ancient Greek:
Proto-Indo-European root reconstructions, cognate word families, and
(where Beekes judges a word non-Indo-European) Pre-Greek substrate
etymologies. Volume 10 of Brill's
[Leiden Indo-European Etymological Dictionary Series](leiden-ie-dictionary-series.md)
— see that doc for sibling volumes covering other IE branches.

Already used, uncredited, as a hand-curated citation source in existing
EEE lesson content (Palaestra lesson notes cite specific EDG page numbers
for word-family/IE-root data).

**No bulk/programmatic access exists.** Unlike LSJ (CC BY-SA TEI-XML on
Perseus's GitHub) or Wiktextract (CC BY-SA/GFDL bulk JSONL dumps), EDG is
a copyrighted academic publication with no open digital edition or API —
and unlike the Byzantine verb lexicon (see
[`references/sources/byzantine-lexicon.md`](byzantine-lexicon.md)), which still has a real
[`okfbuild/sources/byzantine_lexicon.py`](../../okfbuild/sources/byzantine_lexicon.py) client loading a merged YAML file at
build time, Beekes has **no `okfbuild/sources/*.py` client at all**. A human
(or an LLM with access to the actual text) reads the relevant entry and
transcribes a page-cited quote — word family, IE root, competing
etymologies — directly as curated input to a concept builder.

[`okfbuild/concepts/lexical_entry.py`](../../okfbuild/concepts/lexical_entry.py) (added in section-04-concept-builders)
accepts this curated citation as optional input -- the Lexical Entry
equivalent of how [`grammar/aorist-3pl-osan.md`](../../grammar/aorist-3pl-osan.md) cites its own curated
Sophocles excerpt directly, hand-authored rather than built. When no
curated Beekes citation is supplied for a given lemma, the Lexical Entry
is built without an etymology section from Beekes — this is never a
blocking dependency. The "## Etymology" section can also be populated
automatically, independent of a curated Beekes citation, from
[IE-CoR](iecor.md)'s ~170-word cognate-set extract when `sources.iecor`
has an entry for the lemma — the two can appear together, each with its
own footnote, since IE-CoR covers a fixed core vocabulary rather than
Beekes' full headword range.

Always cite by page number (e.g. `Beekes p. 128`).
