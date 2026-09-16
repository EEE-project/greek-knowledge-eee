<!--
Template for a new culture/<topic-id>.md file.

1. Copy this file to culture/<topic-id>.md (kebab-case, matching `title:`).
2. Replace every <PLACEHOLDER> below, remove this comment block, and write
   the body -- real claims, each backed by a [^source-id] citation to one
   of the sources: entries below it. A Wikipedia summary is just an
   ordinary source now (see the second sources: entry below) -- look one
   up and cite it like any other, there's no automatic fetch anymore.
3. Run `uv run greek-knowledge check` (add --fix to let it normalize the
   frontmatter/footnote-definitions block for you -- it never touches
   your prose or your sources: list).

Every sources: entry must be cited at least once via [^id] in the body,
and every [^id] in the body must have a matching sources: entry --
okfbuild/check.py enforces both directions. The footnote-definitions
block at the bottom is mechanical -- `check --fix` derives it from
sources: for you; don't hand-maintain it.
-->
---
type: Cultural Context
title: <topic-id, e.g. peloponnesian-war-setting>
description: '<one sentence: what this topic covers>'
tags:
- <e.g. history>
- <e.g. athens>
level:
- <beginner | B1 | advanced>
sources:
- id: <source-id>
  resource: <file path, URL, or a citation like "Thucydides, II.14">
  title: <source title>
  author: <source author>
- id: wikipedia
  resource: <https://en.wikipedia.org/wiki/...>
  title: <Wikipedia article title>
  author: Wikipedia
generated:
  by: human
  at: '<ISO 8601 timestamp, e.g. 2026-09-16T00:00:00+00:00>'
related_words:
- <lemma this topic connects to, or remove the list to leave it empty>
related_lessons:
- <course/lesson-slug this topic connects to, or remove the list to leave it empty>
dialect: []
status: draft
verified: []
---
## <A short, descriptive heading>

<Body prose, in one or more `##`-headed sections. Cite every real claim
with a [^source-id] matching an id from sources: above.>[^source-id]
