# Diorisis Ancient Greek Corpus

A large, structured, word-level annotated corpus of Ancient Greek: 820
TEI-XML files (~2.5GB uncompressed), one per work, spanning authors from
Achilles Tatius through Xenophon, keyed by TLG canonical author/work
numbers (e.g. `Aeschylus (0085) - Persians (002)`).

Each word carries a `<lemma>` with `entry` (dictionary headword), `POS`,
and one or more `<analysis morph="...">` candidates — pre-computed
morphological analysis, comparable in kind to a live Morpheus query but
offline and pre-annotated for the whole corpus (disambiguation between
multiple analysis candidates is not always resolved — several sampled
words carry `disambiguated="n/a"`).

Built from Perseus Digital Library source texts
(`PerseusDL/canonical-greekLit` on GitHub) by Alessandro Vatri (corpus
conversion and automatic annotation) and Barbara McGillivray (principal
investigator), The Alan Turing Institute / University of Oxford /
University of Cambridge, funded by EPSRC grant EP/N510129/1. Licensed
CC BY-SA 3.0 (US).

**Status: partially integrated.** [`okfbuild/sources/lsj_periods.py`](../../okfbuild/sources/lsj_periods.py) uses
Diorisis's own small `catalog.tsv` (821 lines: author, title, TLG
author/work numbers, date, genre — downloaded once from `jtauber/diorisis`
on GitHub and committed to `data/diorisis/catalog.tsv`) to resolve a
historical period for LSJ citations, joined via TLG author/work numbers
(see [[`references/sources/lsj.md`](lsj.md)](lsj.md#perioddialect-stratification)).
This is metadata-only: the full 820-file/2.5GB per-word-annotated corpus
described above, with its pre-computed lemma/POS/morphology, is **still
not integrated** — remains a strong candidate for the reasons below,
independent of the period-mapping use already made of its catalog.
