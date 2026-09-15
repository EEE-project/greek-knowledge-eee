from pathlib import Path
from typing import Any

from okfbuild import okf
from okfbuild.okf import ConceptFile, Source
from okfbuild.query import find_concepts


def _write(repo_root: Path, subdir: str, slug: str, **overrides: Any) -> Path:
    defaults = dict(
        type="Grammatical Rule",
        title=slug,
        description=f"Grammatical rule: {slug}",
        tags=[],
        level=["beginner"],
        sources=[Source(id="src", resource="somewhere", title="A Source", author="Jane Doe")],
        generated_by="process:test/0.1.0",
        body=f"## {slug}\n\nSome claim.[^src]",
        extra_frontmatter={"periods_spanned": {"from": "attic", "to": "attic"}, "dialect": ["attic"]},
    )
    defaults.update(overrides)
    concept = ConceptFile(**defaults)
    path = repo_root / subdir / f"{slug}.md"
    okf.write(concept, path)
    return path


def test_find_concepts_with_no_filters_returns_everything(tmp_path):
    _write(tmp_path, "grammar", "rule-a")
    _write(tmp_path, "culture", "topic-a", type="Cultural Context", extra_frontmatter={"related_words": [], "related_lessons": [], "dialect": []})

    results = find_concepts(tmp_path)

    assert len(results) == 2


def test_find_concepts_filters_by_type(tmp_path):
    _write(tmp_path, "grammar", "rule-a")
    _write(tmp_path, "culture", "topic-a", type="Cultural Context", extra_frontmatter={"related_words": [], "related_lessons": [], "dialect": []})

    results = find_concepts(tmp_path, type="Grammatical Rule")

    assert [c.title for _, c in results] == ["rule-a"]


def test_find_concepts_filters_by_level(tmp_path):
    _write(tmp_path, "grammar", "rule-beginner", level=["beginner"])
    _write(tmp_path, "grammar", "rule-advanced", level=["advanced"])

    results = find_concepts(tmp_path, level="advanced")

    assert [c.title for _, c in results] == ["rule-advanced"]


def test_find_concepts_filters_by_author_case_insensitive_substring(tmp_path):
    _write(tmp_path, "grammar", "sophocles-rule", sources=[Source(id="s", resource="r", title="t", author="E. A. Sophocles")])
    _write(tmp_path, "grammar", "other-rule", sources=[Source(id="s", resource="r", title="t", author="Jane Doe")])

    results = find_concepts(tmp_path, author="sophocles")

    assert [c.title for _, c in results] == ["sophocles-rule"]


def test_find_concepts_filters_by_author_matches_any_source(tmp_path):
    _write(tmp_path, "grammar", "multi-source-rule", sources=[
        Source(id="s1", resource="r1", title="t1", author="Jane Doe"),
        Source(id="s2", resource="r2", title="t2", author="E. A. Sophocles"),
    ])
    _write(tmp_path, "grammar", "other-rule", sources=[Source(id="s", resource="r", title="t", author="Homer")])

    results = find_concepts(tmp_path, author="sophocles")

    assert [c.title for _, c in results] == ["multi-source-rule"]


def test_find_concepts_skips_index_files(tmp_path):
    (tmp_path / "grammar").mkdir(parents=True)
    (tmp_path / "grammar" / "index.md").write_text("# Grammatical Rules\n")
    _write(tmp_path, "grammar", "rule-a")

    results = find_concepts(tmp_path)

    assert len(results) == 1


def test_find_concepts_results_sorted_by_path(tmp_path):
    _write(tmp_path, "grammar", "z-rule")
    _write(tmp_path, "grammar", "a-rule")

    results = find_concepts(tmp_path)

    assert [path.name for path, _ in results] == ["a-rule.md", "z-rule.md"]
