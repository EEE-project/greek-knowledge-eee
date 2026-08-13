from unittest.mock import Mock

from okfbuild.concepts.cultural_context import build


def test_build_without_wiki_title_never_calls_wikipedia():
    wikipedia = Mock()
    sources = Mock(wikipedia=wikipedia)

    concept = build(
        topic_id="ithaka-symbol",
        lesson_prose=["Ithaca symbolizes the journey itself, not just the destination."],
        wiki_title=None,
        sources=sources,
        level=["B1"],
        tags=["culture"],
    )

    wikipedia.summary.assert_not_called()
    assert concept.type == "Cultural Context"
    assert "journey itself" in concept.body


def test_build_with_wiki_title_cites_wikipedia_summary():
    wikipedia = Mock()
    wikipedia.summary.return_value = {
        "title": "Constantine P. Cavafy",
        "extract": "Cavafy was a Greek poet who lived in Alexandria.",
    }
    sources = Mock(wikipedia=wikipedia)

    concept = build(
        topic_id="cavafy",
        lesson_prose=["Cavafy wrote Ithaka in 1911."],
        wiki_title="Constantine_P._Cavafy",
        sources=sources,
        level=["B1"],
        tags=["culture"],
        related_words=["ιθάκη"],
        related_lessons=["ancient_greek/odyssey/kavafis-ithaki"],
    )

    wikipedia.summary.assert_called_once_with("Constantine_P._Cavafy")
    assert "Cavafy was a Greek poet" in concept.body
    assert "[^wikipedia]" in concept.body
    wiki_source = next(s for s in concept.sources if s.id == "wikipedia")
    assert wiki_source.author == "Wikipedia"
    assert concept.extra_frontmatter["related_words"] == ["ιθάκη"]


def test_build_with_wiki_title_but_no_matching_page_falls_back_to_prose_only():
    """wikipedia_client.summary() returns None on a 404 (no such page) —
    build() must not crash or fabricate a citation, just fall back to
    lesson_prose alone, same as the no-wiki_title case."""
    wikipedia = Mock()
    wikipedia.summary.return_value = None
    sources = Mock(wikipedia=wikipedia)

    concept = build(
        topic_id="obscure-topic",
        lesson_prose=["A topic with no matching Wikipedia page."],
        wiki_title="ThisPageDoesNotExist12345",
        sources=sources,
        level=["B1"],
        tags=["culture"],
    )

    wikipedia.summary.assert_called_once_with("ThisPageDoesNotExist12345")
    assert concept.sources == []
    assert "[^wikipedia]" not in concept.body
    assert "A topic with no matching Wikipedia page." in concept.body
