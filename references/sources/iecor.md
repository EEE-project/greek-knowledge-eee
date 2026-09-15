# IE-CoR (Indo-European Cognate Relationships database)

`https://iecor.clld.org/`, edited by Paul Heggarty, Cormac Anderson, and
Matthew Scarborough; built on the CLLD (Cross-Linguistic Linked Data)
framework. Contains 1,600+ cognate sets across 170 reference meanings,
phylogenetic language trees, and lexical data (orthography, morphology,
phonemic/IPA transcriptions) for languages across the Indo-European
family, contributed by 80+ specialists and cross-checked against
standard PIE reference works (LIV², NIL).

**Status: integrated (Ancient Greek only).** Unlike the Leiden
dictionary series or the toponyms dataset above, this is genuinely open
and machine-readable: the data is curated at `github.com/lexibank/iecor`
in CLDF (Cross-Linguistic Data Format), with versioned releases archived
on Zenodo (DOI `10.5281/zenodo.8089434`), licensed **CC BY 4.0**.

`okfbuild/sources/iecor_client.py`'s `load_iecor_cognates()` loads
`data/iecor/ancient_greek_cognates.tsv` — a small, committed extract of
IE-CoR's 172 "Greek: Ancient" (Language_ID 110) forms, joined through
its `cognates.csv`/`cognatesets.csv` to each headword's root and the
editors' own justification prose (extraction is a one-off, not a
checked-in script — the TSV itself is the committed artifact, same as
[`references/sources/diorisis.md`](diorisis.md)'s `catalog.tsv`). Wired
into `SourceBundle.iecor` and consumed by
`okfbuild/concepts/lexical_entry.py`'s `_etymology_section()`, which
cites it in the "## Etymology" section alongside (never replacing) a
hand-curated Beekes citation — see
[`references/sources/beekes.md`](beekes.md). Coverage is real but
narrow: IE-CoR's own wordlist is a fixed ~170-word comparative-linguistics
core vocabulary (body parts, numbers, colors, common verbs), not a
general lexicon — checked against this KB's 634 built `words/*.md`
files at integration time: 43 exact headword matches. The other 7 Greek
varieties IE-CoR carries (Modern, Mycenaean, New Testament/Koine,
Cypriot, Italiot, Cappadocian, Pontic) are not extracted or wired —
Ancient Greek is the one that pairs naturally with Beekes' etymology
section; extending to the others would need its own scoped follow-up.
