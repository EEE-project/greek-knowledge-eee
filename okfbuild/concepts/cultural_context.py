"""Assembles a Cultural Context ConceptFile from lesson prose plus an
optional Wikipedia summary.
"""

from okfbuild.concepts import GENERATED_BY
from okfbuild.okf import ConceptFile, Source
from okfbuild.sources import SourceBundle

_WIKIPEDIA_SOURCE_ID = "wikipedia"


def build(
    topic_id: str,
    lesson_prose: list[str],
    wiki_title: str | None,
    sources: SourceBundle,
    level: list[str],
    tags: list[str],
    related_words: list[str] | None = None,
    related_lessons: list[str] | None = None,
) -> ConceptFile:
    """Assemble a Cultural Context entry from extracted lesson-notebook
    prose plus, if `wiki_title` is given, a Wikipedia summary via
    wikipedia_client.summary(). Does not call summary() at all when
    wiki_title is None — the body is assembled from lesson_prose alone."""
    body_parts = list(lesson_prose)
    concept_sources: list[Source] = []

    if wiki_title is not None:
        summary = sources.wikipedia.summary(wiki_title)
        if summary is not None:
            page_url = summary.get("content_urls", {}).get("desktop", {}).get("page")
            concept_sources.append(
                Source(
                    id=_WIKIPEDIA_SOURCE_ID,
                    resource=page_url or f"https://en.wikipedia.org/wiki/{wiki_title}",
                    title=summary.get("title", wiki_title),
                    author="Wikipedia",
                )
            )
            extract = summary.get("extract", "")
            body_parts.append(f"{extract}[^{_WIKIPEDIA_SOURCE_ID}]")

    return ConceptFile(
        type="Cultural Context",
        title=topic_id,
        description=f"Cultural context: {topic_id}",
        tags=tags,
        level=level,
        sources=concept_sources,
        generated_by=GENERATED_BY,
        body="\n\n".join(body_parts),
        extra_frontmatter={
            "related_words": related_words or [],
            "related_lessons": related_lessons or [],
        },
    )
