# Patrologia Graeca Corpus (GREgORI / Calfa)

A roughly 6-million-word Ancient Greek corpus built from *Patrologia
Graeca* (Migne), produced jointly by the GREgORI project (UCLouvain,
`https://uclouvain.be/fr/instituts-recherche/incal/ciol/gregori-project`)
and Calfa (`https://calfa.fr/`), a company specializing in automatic
transcription of rare-language texts.

It covers PG volumes missing from the Thesaurus Linguae Graecae
(`https://stephanus.tlg.uci.edu/`) — chiefly late-antique and Byzantine
texts, a period this KB's other sources (Morpheus for Classical/Koine,
the Byzantine verb lexicon for attested verb forms only) don't cover as
running text.

Reported CER (character error rate) ~1%. Released in several formats,
including lemmatized and POS-tagged versions — usable for full-text
search, text analysis, and as silver data for LLM training.

- GitHub: `https://github.com/calfa-co/Patrologia-Graeca`
- Paper: "The Patrologia Graeca Corpus: OCR, Annotation, and Open Release
  of Noisy Nineteenth-Century Polytonic Greek Editions"
  (`https://aclanthology.org/2026.lrec-1.517/`)

**Status: not yet integrated.** No `okfbuild/sources/` client exists for
this corpus yet — documented here as a candidate source for late-antique/
Byzantine running-text coverage, not something the current pipeline reads
from.
