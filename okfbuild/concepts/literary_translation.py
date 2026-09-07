"""Assembles a Literary Translation ConceptFile from already-known,
hand-sourced text -- unlike lexical_entry/grammatical_rule/cultural_context,
there is no live source to query: the human-translated text itself is the
source. Callers pass in the exact body (already in
eee.parse_stanza_translations()-compatible format -- see
okfbuild/okf.py's render() docstring on why the body format is untouched
here) and the Source list for both the translators and the Greek edition(s)
referenced.
"""

from okfbuild.concepts import GENERATED_BY
from okfbuild.okf import ConceptFile, Source


def build(
    work: str,
    passage: str,
    language: str,
    translators: list[str],
    body: str,
    sources: list[Source],
    level: list[str] | None = None,
    tags: list[str] | None = None,
) -> ConceptFile:
    """Assemble a Literary Translation entry.

    body must already be in parse_stanza_translations()-compatible shape:
    `## <translator>` sections, each with an optional `<!-- **desc** -->`
    line and `### <ref>` stanza headings -- unchanged from how
    created_with_eee's translations_{lang}.md files are already written.
    """
    return ConceptFile(
        type="Literary Translation",
        title=f"{work} ({passage}) — {language} translations",
        description=f"{language} translations of {work} {passage}: {', '.join(translators)}.",
        tags=tags or [],
        level=level or [],
        sources=sources,
        generated_by=GENERATED_BY,
        body=body,
        extra_frontmatter={
            "work": work,
            "passage": passage,
            "language": language,
            "translators": translators,
        },
    )
