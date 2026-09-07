from okfbuild.concepts.literary_translation import build
from okfbuild.okf import Source


def test_build_sets_type_and_extra_frontmatter():
    concept = build(
        work="Odyssey",
        passage="IX.19-38",
        language="en",
        translators=["Murray"],
        body="## Murray\n\n### Odyss. IX.19–24\n\nI am Odysseus.",
        sources=[
            Source(id="tr-murray1919", resource="https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0136",
                   title="The Odyssey", author="A. T. Murray"),
        ],
    )

    assert concept.type == "Literary Translation"
    assert concept.extra_frontmatter["work"] == "Odyssey"
    assert concept.extra_frontmatter["passage"] == "IX.19-38"
    assert concept.extra_frontmatter["language"] == "en"
    assert concept.extra_frontmatter["translators"] == ["Murray"]
    assert "Murray" in concept.body
    assert concept.sources[0].id == "tr-murray1919"
    assert concept.generated_by.startswith("process:greek-knowledge-eee-builder/")


def test_build_title_includes_work_and_language():
    concept = build(
        work="Odyssey", passage="I.1-21", language="ru",
        translators=["Жуковский", "Вересаев"],
        body="body", sources=[],
    )
    assert "Odyssey" in concept.title
    assert "ru" in concept.title
