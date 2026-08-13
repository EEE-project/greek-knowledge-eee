"""Assembles a Grammatical Rule ConceptFile from curated Sophocles input.

Unlike lexical_entry and cultural_context, this builder is not
source-queried live — sophocles_excerpt and example_forms arrive already
curated by the caller (for the pilot, section-07 reading
analisys/sophocles-byzantine-morphology.md directly).

Note on body/footnote shape: `body` must contain ONLY inline `[^id]`
references, never `[^id]: ...` definition lines — okf.py's render()
(section-02) auto-generates the footnote-definition block from
ConceptFile.sources. This module's own plan text illustrates the final
*rendered* output with both lines together, which can misread as an
instruction to embed the definition line into `sophocles_excerpt` itself
— don't: that would duplicate what render() already emits. This is the
highest-risk module for that mistake, since sophocles_excerpt is
caller-supplied free text passed straight into body.
"""

from okfbuild.concepts import GENERATED_BY
from okfbuild.okf import ConceptFile, Source

_SOPHOCLES_SOURCE_ID = "sophocles-1887"


def build(
    rule_id: str,
    sophocles_excerpt: str,
    example_forms: list[tuple[str, str]],
    period_from: str,
    period_to: str,
    level: list[str],
    tags: list[str],
) -> ConceptFile:
    """Assemble a Grammatical Rule entry from a curated excerpt of the
    Sophocles transcription plus its cited example lemma->form pairs."""
    source = Source(
        id=_SOPHOCLES_SOURCE_ID,
        resource="analisys/sophocles-byzantine-morphology.md",
        title="Greek Lexicon of the Roman and Byzantine Periods (1887)",
        author="E. A. Sophocles",
    )

    example_lines = [
        f"{lemma} is replaced by {form} in {period_to.capitalize()} Greek[^{_SOPHOCLES_SOURCE_ID}]"
        for lemma, form in example_forms
    ]

    return ConceptFile(
        type="Grammatical Rule",
        title=rule_id,
        description=f"Grammatical rule: {rule_id}",
        tags=tags,
        level=level,
        sources=[source],
        generated_by=GENERATED_BY,
        body="\n\n".join([sophocles_excerpt, *example_lines]),
        extra_frontmatter={"periods_spanned": {"from": period_from, "to": period_to}},
    )
