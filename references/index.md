# References

How this knowledge base uses each of its external and internal sources —
see `sources/` for one doc per source.

## Source authority (optional)

A source doc in `sources/` may optionally carry YAML frontmatter with an
`authority` field — a curator's assessment of how much weight to give
that source, filed by perspective (e.g. `linguistic`, `historical`,
`archaeological`). Lazy and sparse by design: most sources have no
`authority` frontmatter at all until someone actually needs one for a
specific purpose, and a scored source typically carries only the one or
two perspectives it's actually relevant to, never all of them by default.

Each perspective's value is either a single integer 1-5 (5 = highest —
e.g. a careful, self-consciously methodical primary source; 1 = minimal,
essentially unverifiable) or a `{min, max}` range of the same scale, for
a source whose reliability genuinely depends on what it's being cited
to support (see `sources/pseudo-xenophon.md` for a worked example of
when a range is the honest answer and a single number would overstate
certainty). **Always pair a score with a short inline `#` comment saying
why** — a bare number six months from now tells nobody, including its
own author, whether it was a careful judgment or a placeholder guess.
The comment is a one-line pointer, not a replacement for the fuller
rationale each source doc's own "Authority:" paragraph gives below its
frontmatter.

```yaml
---
authority:
  linguistic: 4  # mainstream, checkable grammar; no named author caps it below 5
  historical: {min: 2, max: 4}  # primary but polemical — depends what it's cited for
---
```

This is documentation only — nothing in this codebase reads or queries
`authority` yet. It exists so a scored judgment, once made, is recorded
somewhere a later query feature (or a human) can find it, not lost as a
one-off remark in a chat or commit message.
