<!--
Template for a new words/<lemma>.md file.

words/ is normally pipeline-generated -- `uv run greek-knowledge regenerate
--write` builds one Lexical Entry per lemma found in a course's vocabulary
TSV, querying every real source (LSJ, Wiktextract, Morpheus, IE-CoR...)
automatically. Reach for this template only for the rare manual/edge case:
a word worth an entry that isn't in any course's vocabulary TSV, or one
needing curated enrichment regenerate has no field for (see
okfbuild/pilot_content.py's enrich_nostos_with_beekes for a real example
of the latter -- a Beekes etymology citation).

1. Copy this file to words/<lemma>.md.
2. Replace every <PLACEHOLDER> below. periods: lists which of
   homeric/attic/koine/byzantine/modern this lemma is attested in --
   normally regenerate discovers this per-source; fill in only what
   you've actually verified.
3. Run `uv run greek-knowledge check` -- note this only covers
   grammar/culture/texts today, not words/, so a hand-added Lexical Entry
   gets no automatic footnote/frontmatter validation yet.
-->
---
type: Lexical Entry
title: <lemma>
description: Lexical entry for <lemma>.
tags: []
level: []
sources:
- id: <source-id>
  resource: <file path, URL, or citation>
  title: <source title>
  author: <source author>
generated:
  by: human
  at: '<ISO 8601 timestamp, e.g. 2026-09-16T00:00:00+00:00>'
lemma: <lemma>
periods:
- <homeric | attic | koine | byzantine | modern>
status: draft
verified: []
---
## <Period, e.g. Modern>

<Body prose: attested forms, glosses, etymology -- cite every real claim
with a [^source-id] matching an id from sources: above.>[^source-id]
