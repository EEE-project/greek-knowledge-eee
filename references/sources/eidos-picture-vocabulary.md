# ΕΙΔΟΣ: Picture vocabulary for ancient Greek (Crowell)

`https://bitbucket.org/ben-crowell/picture-vocab` (git, branch
`master`) — Benjamin Crowell's illustrated Ancient Greek vocabulary
book; the PDF is at `https://lightandmatter.com/vocab.pdf`. The repo
(created 2025-09-08, last updated 2025-11-19, about 1.2 MB) holds the
SVG illustrations and ruby source per topic directory (`animals`,
`arms`, `birds`, `body`, `clothes`, `family`, `household-objects`,
`numbers`, `prepositions`, `ship`, `slavery`, and others), the LaTeX
sources (`vocab.tex`, `vocab.cls`), and `glossary.tex`, a roughly 90 KB
LaTeX glossary of polytonic Greek headwords with short English glosses,
some with English cognates and some marked `[not illustrated]`. The
licence file reads "(c) 2025 Benjamin Crowell, CC-BY-SA"; the bitmap
versions of the illustrations live in a separate mega.nz folder, not in
the repo.

**Status: not integrated.** A candidate as a beginner-level, picture-
linked vocabulary source. The glossary is LaTeX markup
(`\begin{boldgreek}…\end{boldgreek}`, `\cog{…}`), so extraction needs a
small parser; there is no API. CC-BY-SA would require attribution and
share-alike for any data derived from it.
