# LSJ (Liddell-Scott-Jones)

The Liddell-Scott-Jones lexicon, CC BY-SA 4.0 TEI-XML, downloaded once
from
`https://github.com/PerseusDL/lexica/tree/master/CTS_XML_TEI/perseus/pdllex/grc/lsj`
(27 files, ~270MB total). No live REST API exists for LSJ — this is the
correct machine-readable path: download + parse the TEI-XML, don't
screen-scrape a viewer.

Not committed: a one-time, local-only, gitignored download to `data/lsj/`
(see that directory's own README.md) -- matches `data/wiktextract/`'s
pattern, since only a small fraction of the ~116,000 headwords are ever
actually looked up by a given course. Only the headwords actually
resolved get cached, as small per-headword JSON files under
`data/lsj-cache/` (git-tracked, plain).

**Headwords and Greek-tagged body text are Beta Code, not Unicode
Greek** (e.g. `key="no/stos"` for νόστος) -- confirmed only once the real
dump was downloaded and parsed; the small hand-written test fixture
(`tests/fixtures/sources/lsj/`) predates this discovery and uses real
Greek characters directly, which is why it didn't surface the gap
earlier. Converted via the `beta-code` PyPI package (published by
perseids-tools, the same organization as Perseids Morpheus) -- element-
aware, converting only text within a `lang="greek"`-tagged element (or
its descendants), never plain English glosses/bibliographic abbreviations
mixed into the same entry (naive whole-text conversion mangles English,
e.g. "good" -> "γοοδ"). Known, accepted limitation inherent to Beta Code
itself: a literal parenthesis used editorially inside a Greek span (e.g.
a cross-reference like "(ne/omai)") is ambiguous with Beta Code's own
breathing-mark notation and gets misconverted -- not fixed, since
resolving it would need a much deeper, context-aware parser. Also known
(1 of 465 real course-vocabulary lemmas, checked at the time real content
was first generated): LSJ's own editorial bracket notation can
incidentally produce a `[^...]`-shaped substring in extracted entry text,
colliding with OKF markdown's footnote-reference syntax. Cosmetic, not a
correctness issue -- `okf.py`'s `render()` only ever emits a footnote
*definition* for an id matching a real `concept.sources` entry, so a
phantom reference like this simply has no matching definition (an
unresolved link in a markdown viewer), never a duplicated or corrupted
footnote. Not fixed for the same reason as above: a general, root-cause
fix (distinguishing LSJ's own bracket notation from Beta Code artifacts)
needs more of the raw markup's structure than a text-only extraction
preserves.

Parsed by `okfbuild/sources/lsj_index.py` (added in
section-03-source-clients), which must disable XML entity
expansion/external entity resolution even though this specific file comes
from a trusted source -- while still allowing the real files' own DOCTYPE
parameter entities (`_LSJXMLParser`, see its own docstring for the exact
mechanism and why one of the two, `%PersDict`, is actually external, not
internal, yet still safe), which a blanket "forbid all entities" policy
would otherwise reject too.

Attribution: Perseus Digital Library, CC BY-SA 4.0.
