# Thesaurus Linguae Graecae (TLG)

The standard digital library of Greek texts from Homer through the
Byzantine period, maintained by the University of California, Irvine
(`https://stephanus.tlg.uci.edu/`). Its canon of author/work numbers is
the citation standard used throughout classical scholarship.

**Status: not integrated, and not a source this KB reads full text
from.** Full-text access is primarily via institutional/individual
subscription — there is no open bulk-download or free REST API, unlike
this KB's other sources (LSJ/Wiktextract are openly licensed downloads,
Morpheus is a free REST service). See
[`references/sources/patrologia-graeca.md`](patrologia-graeca.md) for a
corpus built specifically to cover PG volumes TLG lacks (late-antique/
Byzantine texts) — a coverage gap independent of the access question.

TLG's canonical author/work *numbering convention* (not the service
itself) is used internally as a join key by
`okfbuild/sources/lsj_periods.py`, matching LSJ citations against
Diorisis's catalog and LSJ's own front matter to resolve a historical
period — see
[`references/sources/lsj.md`](lsj.md#perioddialect-stratification). This
doesn't change the status above: no TLG text or data is read, only the
numbering scheme every one of these sources already publishes citations
against.
