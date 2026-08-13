import re

from okfbuild.concepts.grammatical_rule import build


def test_build_cites_every_example_pair():
    concept = build(
        rule_id="osan-imperfect-aorist",
        sophocles_excerpt="The -οσαν ending replaces -σαν in the 3rd person plural.",
        example_forms=[("ἦλθον", "ἤλθοσαν"), ("εἶδον", "ἴδοσαν")],
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
