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

**Status: not integrated**, but a strong candidate — unlike most other
not-yet-integrated sources in this list, it's already structured,
offline (no rate limits or live-service dependency), and covers a huge
span of Classical prose and poetry with pre-computed lemma/POS/morphology,
directly comparable to this KB's Morpheus and EEE-engine sources.
