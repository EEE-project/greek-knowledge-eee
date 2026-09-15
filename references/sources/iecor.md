# IE-CoR (Indo-European Cognate Relationships database)

`https://iecor.clld.org/`, edited by Paul Heggarty, Cormac Anderson, and
Matthew Scarborough; built on the CLLD (Cross-Linguistic Linked Data)
framework. Contains 1,600+ cognate sets across 170 reference meanings,
phylogenetic language trees, and lexical data (orthography, morphology,
phonemic/IPA transcriptions) for languages across the Indo-European
family, contributed by 80+ specialists and cross-checked against
standard PIE reference works (LIV², NIL).

**Status: not integrated, but the strongest access-verified candidate in
this batch.** Unlike the Leiden dictionary series or the toponyms
dataset above, this is genuinely open and machine-readable: the data is
curated at `github.com/lexibank/iecor` in CLDF (Cross-Linguistic Data
Format), with versioned releases archived on Zenodo
(DOI `10.5281/zenodo.8089434`), licensed **CC BY 4.0**. A real candidate
for an `okfbuild/sources/*.py` client alongside `lsj_index.py` /
`wiktextract_index.py` — joining Greek headwords to IE cognate sets /
PIE roots as a citation placed next to (not replacing) Beekes'
hand-curated etymologies (see
[`references/sources/beekes.md`](beekes.md)). Not built yet: no concept
builder currently has a slot for cross-linguistic cognate data, and the
CLDF file layout hasn't been inspected in detail — needs its own scoped
follow-up, the same way Diorisis's full per-word corpus remains a
documented-but-unbuilt candidate (see
[`references/sources/diorisis.md`](diorisis.md)).
