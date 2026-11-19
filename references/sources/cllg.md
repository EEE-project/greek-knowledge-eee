# CLLG (Corpus Liberatum Linguae Graecae)

The Corpus Liberatum Linguae Graecae (dir. Thibault Clérice; https://cllg-project.github.io/) releases Greek texts
as open TEI P5 files. Its Freed corpus holds the TLG E texts: the corpus that the TLG once distributed on CD-ROM,
about 6,600 works from Homer to the Byzantine period, in the editions that the TLG used. The corpus is a git
repository, `https://gitlab.inria.fr/almanach/cllg/freed-corpus.git`, with one file per work at
`data/tlgAAAA/tlgWWW/tlgAAAA.tlgWWW.cllg-grc1.xml`. The `refsDecl` of each file declares how the work is cited:
by book and line (Homer), by book, chapter and section (Strabo, Polybius), or by the pages of a printed edition
(Eustathius, Stallbaum's pages). The index page https://freed-corpus-bae861.gitlabpages.inria.fr/ lists the works
with their ids. The GitLab web pages refuse automated reads; git works.

**Status: integrated as an opt-in, local-only source.** `greek-knowledge cllg TEXT_ID REF` prints the text of one
citation (`10.510`: book 10, line 510; `10`: all of book 10; `209`: one page). `greek-knowledge cllg TEXT_ID --find
PHRASE` lists every place of a phrase, with its citation. Case, accents and breathings are ignored, and the words
may stand on two lines. The code is `okfbuild/sources/cllg.py`. The texts are a sparse clone in
`data/cllg/freed-corpus`, fetched by hand (see `data/cllg/README.md`) and gitignored. CLLG is not part of
`SourceBundle` or `lookup`, because a text corpus is not lemma-keyed.

Use it to check a quoted Greek passage, or a citation, against the TLG text. Examples: a scholion (`tlg5026.tlg007`,
the Odyssey scholia, ed. Dindorf; `1.75` holds Silenus of Chios on the name of Odysseus), Eustathius on the
Odyssey (`tlg4083.tlg003`), Athenaeus (`tlg0008.tlg001`, cited by Kaibel's book and paragraph, not by Casaubon's
pages), or the Odyssey itself (`tlg0012.tlg002`).

**Licence.** The header of each file says that the text is CC0 1.0: "under French law, the text of a critical
edition is not protected by copyright (CA Paris, Pôle 5, 2ème Ch., 9 June 2017, no. 16/00005)". The citation
structure and the metadata are CC-BY 4.0, with attribution to the Corpus Liberatum Linguae Graecae. The legal
question is not closed. On 19 March 2026 the Court of Justice of the EU held (C-649/23, *Institutul G. Călinescu*)
that a critical edition of a public-domain work can be protected by copyright when it reflects the free and creative
choices of its editor. So this repo commits no CLLG text and no cache of passages. The tests use small fixtures
made from `texts/odyssey/text.md`.

**Editions.** The texts are those of the TLG E disk. They are often older than the current critical editions. The
CLLG Odyssey is von der Mühll's edition (Basel, 1962); `texts/odyssey/text.md` is Murray's (1919), as the Perseus Digital Library gives it, except three lines that follow the Odyssey
lessons (its description names them). A CLLG passage
shows what the TLG edition prints, not the latest reading.
