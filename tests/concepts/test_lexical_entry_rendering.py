"""Tests for render_lsj_entry() itself -- the segments -> markdown step,
decoupled from build()'s wiring (see test_lexical_entry.py for that).
These operate purely on directly-constructed LSJText/LSJCitation/Period
instances -- no XML fixture needed, since render_lsj_entry() takes
already-parsed segments."""

from unittest.mock import Mock

from okfbuild.concepts.lexical_entry import render_lsj_entry
from okfbuild.sources.lsj_index import LSJCitation, LSJText
from okfbuild.sources.lsj_periods import Period


def _period_map_returning(period: "Period | None") -> Mock:
    return Mock(period_for_citation=Mock(return_value=period))


def test_render_citation_with_period_and_dialect_gets_combined_tag():
    period_map = _period_map_returning(Period(centuries=(5,), era="BC"))
    citation = LSJCitation(text="citation text here", dialects=("Doric",))

    result = render_lsj_entry([citation], period_map)

    assert result == "**[5th c. BC, Doric]** citation text here"


def test_render_citation_with_only_period_known():
    period_map = _period_map_returning(Period(centuries=(5,), era="BC"))
    citation = LSJCitation(text="citation text")

    result = render_lsj_entry([citation], period_map)

    assert result == "**[5th c. BC]** citation text"


def test_render_citation_with_only_dialect_known():
    period_map = _period_map_returning(None)
    citation = LSJCitation(text="citation text", dialects=("Doric",))

    result = render_lsj_entry([citation], period_map)

    assert result == "**[Doric]** citation text"


def test_render_citation_with_neither_period_nor_dialect_known():
    period_map = _period_map_returning(None)
    citation = LSJCitation(text="citation text")

    result = render_lsj_entry([citation], period_map)

    assert result == "citation text"


def test_render_citation_with_multiple_dialects_joins_with_slash():
    citation = LSJCitation(text="citation text", dialects=("Ionic", "Attic"))

    result = render_lsj_entry([citation], _period_map_returning(None))
    assert result == "**[Ionic / Attic]** citation text"

    result_with_period = render_lsj_entry([citation], _period_map_returning(Period(centuries=(5,), era="BC")))
    assert result_with_period == "**[5th c. BC, Ionic / Attic]** citation text"


def test_render_multiple_citations_in_one_run_get_independent_tags():
    period_map = Mock(
        period_for_citation=Mock(
            side_effect=lambda c: Period(centuries=(5,), era="BC") if c.text == "first" else None
        )
    )
    segments = [
        LSJText("prefix "),
        LSJCitation(text="first", dialects=("Doric",)),
        LSJText(" middle "),
        LSJCitation(text="second", dialects=("Ionic",)),
    ]

    result = render_lsj_entry(segments, period_map)

    assert result == "prefix **[5th c. BC, Doric]** first middle **[Ionic]** second"


def test_render_consecutive_text_segments_join_as_continuous_prose():
    segments = [LSJText("one, "), LSJText("two, "), LSJText("three.")]

    result = render_lsj_entry(segments, _period_map_returning(None))

    assert result == "one, two, three."


def test_render_full_entry_end_to_end_matches_expected_markdown():
    """A realistic fixture entry modeled loosely on the real νόστος
    shape: multiple citations, multiple eras, at least one dialect tag."""
    period_map = Mock(
        period_for_citation=Mock(
            side_effect=lambda c: {
                "Il.": Period(centuries=(8,), era="BC"),
                "Hdt.": Period(centuries=(5,), era="BC"),
            }.get(c.author_abbreviation)
        )
    )
    segments = [
        LSJText("return, homecoming; a coming back, "),
        LSJCitation(text="νόστος Il. 1.1", author_abbreviation="Il."),
        LSJText(", "),
        LSJCitation(text="νόστου Hdt. 1.5", author_abbreviation="Hdt.", dialects=("Ion.",)),
        LSJText(", also of a return by sea, "),
        LSJCitation(text="πλόος νόστιμος", author_abbreviation="Unattested-in-frontmatter"),
        LSJText("."),
    ]

    result = render_lsj_entry(segments, period_map)

    assert result == (
        "return, homecoming; a coming back, "
        "**[8th c. BC]** νόστος Il. 1.1, "
        "**[5th c. BC, Ion.]** νόστου Hdt. 1.5, also of a return by sea, "
        "πλόος νόστιμος."
    )


def test_render_with_no_period_map_still_renders_dialect_only_tags():
    """period_map=None (the documented common case -- an LSJPeriodMap
    wasn't built, or wasn't passed) must not crash; dialect-only tags
    still render, period-dependent tags simply never appear."""
    segments = [
        LSJCitation(text="tagged", dialects=("Doric",)),
        LSJText(", "),
        LSJCitation(text="untagged"),
    ]

    result = render_lsj_entry(segments)

    assert result == "**[Doric]** tagged, untagged"
