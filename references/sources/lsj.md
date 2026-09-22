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
preserves. Also known (found reviewing the real 465-file content batch):
etymological citations sometimes use Latin `v` for digamma (Ϝ) inside a
`lang="greek"` span, e.g. raw `va/stu` in ἄστυ's own entry (confirmed
directly in `grc.lsj.perseus-eng1.xml`) -- standard Beta Code has no
digamma mapping, so `v` isn't part of what `beta_code_to_greek()`
recognizes and passes through unconverted. Not garbled, reads fine as the
`v` scholarly convention already is in print -- not fixed, since treating
it as real Beta Code content would require guessing where digamma
notation starts/ends versus other legitimate uses of Latin letters in
the same span. Also known (found verifying the period/dialect
stratification fix below against real content): the raw Beta Code text
itself occasionally lacks a separating space before its own `*`
capitalization marker, e.g. ἐρύκω's real entry has the single, unsplit
text node `e)ruke/men eu)ru/opa*zh=n` (confirmed directly in
`grc.lsj.perseus-eng5.xml`) -- "εὐρύοπα" and "Ζῆν" (accusative of Ζεύς)
render fused as "εὐρύοπαΖῆν" with no code-visible boundary to hook a fix
onto, since there is no element/token boundary here at all, just one
string with the space missing in Perseus's own digitization. Not fixed,
for the same reason as the other limitations above: inserting a space
before every Beta Code `*` would be wrong in general (e.g. "(*zeu\s)"
correctly has no space after the parenthesis), and distinguishing this
one genuine gap from every legitimate no-space `*` usage isn't possible
from the text alone.

Parsed by [`okfbuild/sources/lsj_index.py`](../../okfbuild/sources/lsj_index.py) (added in
section-03-source-clients), which must disable XML entity
expansion/external entity resolution even though this specific file comes
from a trusted source -- while still allowing the real files' own DOCTYPE
parameter entities (`_LSJXMLParser`, see its own docstring for the exact
mechanism and why one of the two, `%PersDict`, is actually external, not
internal, yet still safe), which a blanket "forbid all entities" policy
would otherwise reject too.

## Period/dialect stratification

Each `LSJCitation` extracted from the dump can carry a resolved historical
period and/or dialect(s), rendered as an inline `**[5th c. BC, Doric]**`-
style tag immediately before the citation's own text (`render_lsj_entry()`
in [`okfbuild/concepts/lexical_entry.py`](../../okfbuild/concepts/lexical_entry.py)) whenever either is known — a
citation with neither renders untagged, exactly as before this capability
existed.

**Period resolution** ([`okfbuild/sources/lsj_periods.py`](../../okfbuild/sources/lsj_periods.py),
`LSJPeriodMap.period_for_citation()`), in order: (1) Diorisis work-level,
when the citation's TLG author+work both resolve and a matching
`data/diorisis/catalog.tsv` row exists; (2) Diorisis author-level fallback
(that author's earliest dated work), when only the author resolves; (3)
LSJ's own front-matter author-date list (`_frontmatter_file()`); (4) no
period. `data/diorisis/catalog.tsv` is Diorisis's own small (821-line)
catalog file, downloaded once from `jtauber/diorisis` on GitHub and
committed directly (unlike the 270MB LSJ dump itself) — not the full
820-file/2.5GB per-word-annotated corpus (see
[[`references/sources/diorisis.md`](diorisis.md)](diorisis.md)), so only Diorisis's
author/work/date metadata is used here, not its morphological analysis.

**Dialect resolution** ([`okfbuild/sources/lsj_index.py`](../../okfbuild/sources/lsj_index.py),
`_resolve_dialect_scope()`) implements a scope-precedence table derived
from directly sampling the real dump, not assumed from the DTD: a
`<gramGrp>` immediately preceding an `<orth>`/`<foreign>` word-form variant
scopes broadly (everything until the next marker or entry/sense boundary);
a `<gramGrp>` between two `<cit>` elements scopes to only the immediately
following citation; a `<gramGrp>` in parentheses right after a
`<foreign>`-quoted form scopes to that one form and its own citation only;
free-standing prose commentary and untagged dialect mentions (e.g. a bare
`<bibl><author>Cypr.</author>` with no `<gram type="dialect">` at all) are
recognized but not attached to a specific citation. `_TRANSPARENT_GRAMMAR_TAGS`
(`{"per", "number", "tns", "itype", "mood", "gen", "pos", "abbr", "pron",
"subc", "pb"}`) lists the bare grammatical markup that can sit between a
dialect `<gramGrp>` and its `<cit>` without breaking Pattern B/C adjacency
— verified against real dump examples one tag at a time, not derived from
the Perseus DTD (not locally available, and fetching it externally was
judged inconsistent with this project's own security stance on untrusted
external XML — see `_LSJXMLParser` above). A non-dialect `<gramGrp>` (e.g.
one carrying only `type="voice"`) is likewise treated as transparent for
adjacency rather than breaking the scope, since its own text still renders
in place. Extending this set is real, measured work, not a guess: the
current set was reached by scanning citation counts on the real dump after
each addition (16,884 → 17,932 dialect-tagged citations across the two
rounds that produced today's set).

**Known, corrected planning error**: this capability's own motivating
example (that λέγω's two homograph `<entryFree>` entries collide to one
dict key after Beta Code conversion) was checked directly against the real
dump and found false — λέγω's real raw keys are `le/gw1`/`le/gw2`, and
`beta_code_to_greek()` happens to preserve the trailing digit for this
word shape, producing two genuinely distinct keys. The real, complete
mechanism (`_load_entries()`'s own docstring in `lsj_index.py`) is 329
other digit-suffixed homograph pairs (e.g. raw keys `a)/atos1`/`a)/atos2`)
where the same conversion inconsistently strips the trailing digit instead
— an internal quirk of that library, not predictable from a word's
spelling. Colliding entries are merged (not overwritten), with an explicit
paragraph break inserted between them.

**Caching**: `LSJPeriodMap.build()` uses two additional, gitignored,
machine-local caches beyond the git-tracked `data/lsj-cache/` above —
`data/lsj-tlg-map-cache.json` (a 27-file mtime-signature cache for the
TLG author/abbreviation join) and
`data/lsj-tlg-map-cache-frontmatter.json` (a single-file mtime cache for
front-matter author parsing) — both rebuilt automatically on a stale or
missing cache, never committed since their validity is tied to local file
mtimes, not content that makes sense to share across clones.

Attribution: Perseus Digital Library, CC BY-SA 4.0.
