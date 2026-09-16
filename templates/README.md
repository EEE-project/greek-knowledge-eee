# Templates

One starting point per OKF concept type, for hand-authoring a new entry
directly:

- [`grammar-rule.md`](grammar-rule.md) → `grammar/<rule-id>.md`
- [`cultural-context.md`](cultural-context.md) → `culture/<topic-id>.md`
- [`literary-translation.md`](literary-translation.md) → `texts/<work-slug>/translations_<lang>.md`
- [`lexical-entry.md`](lexical-entry.md) → `words/<lemma>.md` (rare -- see
  that template's own comment for when a manual entry makes sense instead
  of `regenerate --write`)

## Workflow

1. Copy the relevant template to its real path.
2. Fill in every `<PLACEHOLDER>`, remove the leading HTML comment, and
   write the body -- real prose you (or Claude) author directly, citing
   sources with `[^id]` as you go.
3. Run `uv run greek-knowledge check` (add `--fix` to let it mechanically
   normalize frontmatter shape and the footnote-definitions block -- it
   never invents or edits your prose or your `sources:` list). Pass a
   file or directory to scope it (e.g. `uv run greek-knowledge check
   grammar/my-new-rule.md`) instead of checking everything.

grammar/, culture/, and texts/ content is hand-authored and validated,
not generated -- see `okfbuild/check.py`'s module docstring for exactly
what it checks. words/ is the one type still built by a real pipeline
(`okfbuild/pipeline.py`, wired through `greek-knowledge regenerate`) from
external sources (LSJ, Wiktextract, Morpheus, IE-CoR...), since those
entries are genuine data derivation, not curated prose.
