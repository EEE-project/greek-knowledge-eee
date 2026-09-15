"""Assembles a Grammatical Rule ConceptFile from curated prose plus its
citing sources.

Like cultural_context.build(), this builder is not source-queried live —
body and sources arrive already curated by the caller. Note on body/
footnote shape: `body` must contain ONLY inline `[^id]` references, never
`[^id]: ...` definition lines — okf.py's render() auto-generates the
footnote-definition block from ConceptFile.sources.
"""

from okfbuild.concepts import GENERATED_BY
from okfbuild.okf import ConceptFile, Source


def build(
    rule_id: str,
    body: str,
    sources: list[Source],
    period_from: str,
    period_to: str,
    level: list[str],
    tags: list[str],
    dialect: list[str] | None = None,
) -> ConceptFile:
    """Assemble a Grammatical Rule entry from a curated body of prose plus
    the sources it cites via inline [^id] references."""
    return ConceptFile(
        type="Grammatical Rule",
        title=rule_id,
        description=f"Grammatical rule: {rule_id}",
        tags=tags,
        level=level,
        sources=sources,
        generated_by=GENERATED_BY,
        body=body,
        extra_frontmatter={
            "periods_spanned": {"from": period_from, "to": period_to},
            "dialect": dialect or [],
        },
    )
