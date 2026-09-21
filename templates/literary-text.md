<!--
Template for a work's original text: texts/<work-slug>/text.md (one file per
work and passage, in the language the work was written in).

1. Copy this file to texts/<work-slug>/text.md.
2. Replace every <PLACEHOLDER> below, remove this comment block, and add
   the text under `###` headings, one per stanza/section.
3. Run `uv run greek-knowledge check` (add --fix to normalize the
   frontmatter -- it never touches your body text).

This is a Literary Text, not a Literary Translation: it holds the original
itself, so there is no `translators` field. For renderings into other
languages, and for interlinear glosses, use templates/literary-translation.md.

sources: here is plain provenance for the whole passage (which edition the
text was copied from, what it was checked against), and the body normally has
no inline [^id] markers, so okfbuild/check.py requires none.

Only reproduce a text that is actually public domain (EU/Greek rule: author
dead 70+ years; US rule: published before 1929) or that you have explicit
permission to use.
-->
---
type: Literary Text
title: <Work, Passage> — original text (<language>)
description: <one sentence: what this file covers, the edition used, and its copyright status>
tags: []
level: []
sources:
- id: <source-id>
  resource: <file path or URL of the edition this text was copied from or checked against>
  title: <source title>
  author: <source author>
generated:
  by: human
  at: '<ISO 8601 timestamp, e.g. 2026-09-16T00:00:00+00:00>'
work: <Work name, e.g. Kavafis, Ithaka>
passage: <passage locator, e.g. 1-36>
language: <ISO 639 code of the original language, e.g. el, grc>
status: draft
verified: []
---
## <Work title>

<!-- One line of context: the edition, and any variant readings you had to choose between. -->

### <Work>, l. 1–N

<the text itself, one stanza/section per `###` heading>
