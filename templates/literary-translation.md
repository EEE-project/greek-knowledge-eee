<!--
Template for a new texts/<work-slug>/translations_<lang>.md file (one file
per language covering the same work+passage).

1. Copy this file to texts/<work-slug>/translations_<lang>.md.
2. Replace every <PLACEHOLDER> below, remove this comment block, and add
   the real text under one `## <translator>` heading per translator.
3. Run `uv run greek-knowledge check` (add --fix to normalize the
   frontmatter -- it never touches your body text).

The work's original text does not belong here: it goes in
texts/<work-slug>/text.md (templates/literary-text.md).

Unlike Grammatical Rule/Cultural Context, sources: here is plain
provenance for the whole passage (where the text came from, what it was
verified against) -- the body is the translated text itself, not prose
making citable claims, so it normally has no inline [^id] markers and
okfbuild/check.py doesn't require any.

Before reproducing a translation's full text: confirm it's actually
public domain (EU/Greek rule: author dead 70+ years; US rule: published
before 1929) or you have explicit permission. If it isn't, add a
"### <translator> (reference only, not reproduced)" section instead --
name, publication, and a real URL, no text -- see any existing
texts/*/translations_*.md for the pattern.
-->
---
type: Literary Translation
title: <Work, Passage> — <language> translations
description: <one sentence: what this file covers and its copyright status>
tags: []
level: []
sources:
- id: <source-id>
  resource: <file path or URL this text/edition was verified against>
  title: <source title>
  author: <source author>
generated:
  by: human
  at: '<ISO 8601 timestamp, e.g. 2026-09-16T00:00:00+00:00>'
work: <Work name, e.g. Kavafis, Ithaka>
passage: <passage locator, e.g. 1-23>
language: <ISO 639-1 code, e.g. el, en, ru>
translators:
- <translator name>
status: draft
verified: []
---
## <translator name>

<!-- One line of context: edition, date, whether this is an original,
a full translation, or an interlinear gloss. -->

### <Work>, l. 1–N

<the text itself, one stanza/section per `###` heading>
