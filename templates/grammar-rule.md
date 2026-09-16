<!--
Template for a new grammar/<rule-id>.md file.

1. Copy this file to grammar/<rule-id>.md (kebab-case, matching `title:`).
2. Replace every <PLACEHOLDER> below, remove this comment block, and write
   the body -- real claims, each backed by a [^source-id] citation to one
   of the sources: entries below it.
3. Run `uv run greek-knowledge check` (add --fix to let it normalize the
   frontmatter/footnote-definitions block for you -- it never touches
   your prose or your sources: list).

Every sources: entry must be cited at least once via [^id] in the body,
and every [^id] in the body must have a matching sources: entry --
okfbuild/check.py enforces both directions. The footnote-definitions
block at the bottom (one `[^id]: Title, Author (resource)` line per
*cited* source) is mechanical -- `check --fix` derives it from sources:
for you; don't hand-maintain it.
-->
---
type: Grammatical Rule
title: <rule-id, e.g. second-declension-masc-neut>
description: '<one sentence: what this rule covers>'
tags:
- <e.g. morphology>
- <e.g. noun>
level:
- <beginner | advanced>
sources:
- id: <source-id>
  resource: <file path, URL, or a citation like "Author, Title, II.14">
  title: <source title>
  author: <source author>
generated:
  by: human
  at: '<ISO 8601 timestamp, e.g. 2026-09-16T00:00:00+00:00>'
periods_spanned:
  from: <homeric | attic | koine | byzantine | modern>
  to: <homeric | attic | koine | byzantine | modern>
dialect: []
status: draft
verified: []
---
## <A short, descriptive heading>

<Body prose. Bold Greek forms with **asterisks**. Cite every real claim
with a [^source-id] matching an id from sources: above.>[^source-id]
