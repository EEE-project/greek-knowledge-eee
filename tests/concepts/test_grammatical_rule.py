import re

from okfbuild.okf import Source
from okfbuild.concepts.grammatical_rule import build


def test_build_cites_every_source_referenced_in_body():
    concept = build(
        rule_id="osan-imperfect-aorist",
        body=(
            "## The -οσαν ending\n\n"
            "The -οσαν ending replaces -σαν in the 3rd person plural.[^sophocles-1887]\n\n"
            "ἦλθον is replaced by ἤλθοσαν in Byzantine Greek[^sophocles-1887]\n\n"
            "εἶδον is replaced by ἴδοσαν in Byzantine Greek[^sophocles-1887]"
        ),
        sources=[
            Source(
                id="sophocles-1887",
                resource="analisys/sophocles-byzantine-morphology.md",
                title="Greek Lexicon of the Roman and Byzantine Periods (1887)",
                author="E. A. Sophocles",
            )
        ],
        period_from="ancient",
        period_to="byzantine",
        level=["B1"],
        tags=["grammar"],
    )

    assert concept.type == "Grammatical Rule"
    assert concept.extra_frontmatter["periods_spanned"] == {"from": "ancient", "to": "byzantine"}
    assert isinstance(concept.extra_frontmatter["periods_spanned"], dict)
    assert "ἤλθοσαν" in concept.body
    assert "ἴδοσαν" in concept.body

    footnote_ids = set(re.findall(r"\[\^([^\]]+)\]", concept.body))
    assert footnote_ids
    source_ids = {s.id for s in concept.sources}
    assert footnote_ids <= source_ids


def test_build_dialect_defaults_to_empty_list():
    concept = build(
        rule_id="some-rule",
        body="A rule with no dialect scope.",
        sources=[],
        period_from="koine",
        period_to="modern",
        level=[],
        tags=[],
    )

    assert concept.extra_frontmatter["dialect"] == []


def test_build_dialect_passed_through_when_given():
    concept = build(
        rule_id="some-attic-rule",
        body="An Attic-only rule.",
        sources=[],
        period_from="attic",
        period_to="attic",
        level=[],
        tags=[],
        dialect=["attic"],
    )

    assert concept.extra_frontmatter["dialect"] == ["attic"]
