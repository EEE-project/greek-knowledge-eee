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
    extra_sources: list[Source] | None = None,
    periods_spanned: dict | None = None,
    dialect: list[str] | None = None,
) -> ConceptFile:
    """Assemble a Cultural Context entry from extracted lesson-notebook
    prose plus, if `wiki_title` is given, a Wikipedia summary via
    wikipedia_client.summary(). Does not call summary() at all when
    wiki_title is None — the body is assembled from lesson_prose alone.
    extra_sources (e.g. a primary-text citation like Thucydides) are
    listed ahead of the Wikipedia source, since they're the caller's
    deliberately-chosen primary citations rather than an automatic
    enrichment."""
    body_parts = list(lesson_prose)
    concept_sources: list[Source] = list(extra_sources or [])

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

    extra_frontmatter = {
        "related_words": related_words or [],
        "related_lessons": related_lessons or [],
        "dialect": dialect or [],
    }
    if periods_spanned is not None:
        extra_frontmatter["periods_spanned"] = periods_spanned

    return ConceptFile(
        type="Cultural Context",
        title=topic_id,
        description=f"Cultural context: {topic_id}",
        tags=tags,
        level=level,
        sources=concept_sources,
        generated_by=GENERATED_BY,
        body="\n\n".join(body_parts),
        extra_frontmatter=extra_frontmatter,
    )
