# Beekes' Etymological Dictionary of Greek (EDG)

Robert S. P. Beekes, *Etymological Dictionary of Greek* (Brill, 2010, 2
vols.) — the standard modern etymological reference for Ancient Greek:
Proto-Indo-European root reconstructions, cognate word families, and
(where Beekes judges a word non-Indo-European) Pre-Greek substrate
etymologies.

Already used, uncredited, as a hand-curated citation source in existing
EEE lesson content (Palaestra lesson notes cite specific EDG page numbers
for word-family/IE-root data).

**No bulk/programmatic access exists.** Unlike LSJ (CC BY-SA TEI-XML on
Perseus's GitHub) or Wiktextract (CC BY-SA/GFDL bulk JSONL dumps), EDG is
a copyrighted academic publication with no open digital edition or API —
and unlike the Byzantine verb lexicon (see
`references/sources/byzantine-lexicon.md`), which still has a real
`build/sources/byzantine_lexicon.py` client loading a merged YAML file at
build time, Beekes has **no `build/sources/*.py` client at all**. A human
(or an LLM with access to the actual text) reads the relevant entry and
transcribes a page-cited quote — word family, IE root, competing
etymologies — directly as curated input to a concept builder.

`build/concepts/lexical_entry.py` (added in section-04-concept-builders)
accepts this curated citation as optional input, the same mechanism
`grammatical_rule.py` uses for its curated Sophocles excerpts. When no
curated Beekes citation is supplied for a given lemma, the Lexical Entry
is built without an etymology section — this is never a blocking
dependency.

Always cite by page number (e.g. `Beekes p. 128`).
