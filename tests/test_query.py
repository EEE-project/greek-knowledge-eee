from pathlib import Path
from typing import Any

import yaml

from okfbuild import okf
from okfbuild.okf import ConceptFile, Source
from okfbuild.query import TYPE_BY_DIR, find_concepts, list_mode_report, list_values

_CULTURE_DEFAULTS = {"related_words": [], "related_lessons": [], "dialect": []}


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
    _write(tmp_path, "culture", "topic-a", type="Cultural Context", extra_frontmatter=_CULTURE_DEFAULTS)

    results = find_concepts(tmp_path)

    assert len(results) == 2


def test_find_concepts_filters_by_type(tmp_path):
    _write(tmp_path, "grammar", "rule-a")
    _write(tmp_path, "culture", "topic-a", type="Cultural Context", extra_frontmatter=_CULTURE_DEFAULTS)

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


def test_find_concepts_period_range_containment_on_grammatical_rule(tmp_path):
    _write(tmp_path, "grammar", "spans-attic-to-byzantine", extra_frontmatter={"periods_spanned": {"from": "attic", "to": "byzantine"}, "dialect": []})
    _write(tmp_path, "grammar", "modern-only", extra_frontmatter={"periods_spanned": {"from": "modern", "to": "modern"}, "dialect": []})

    results = find_concepts(tmp_path, period="koine")

    assert [c.title for _, c in results] == ["spans-attic-to-byzantine"]


def test_find_concepts_period_membership_on_lexical_entry(tmp_path):
    _write(
        tmp_path, "words", "attested-homeric-and-modern",
        type="Lexical Entry",
        extra_frontmatter={"lemma": "νόστος", "periods": ["homeric", "modern"]},
    )
    _write(
        tmp_path, "words", "attested-attic-only",
        type="Lexical Entry",
        extra_frontmatter={"lemma": "ἄνθρωπος", "periods": ["attic"]},
    )

    results = find_concepts(tmp_path, period="homeric")

    assert [c.title for _, c in results] == ["attested-homeric-and-modern"]


def test_find_concepts_period_filter_never_matches_concept_with_no_period_data(tmp_path):
    _write(
        tmp_path, "culture", "timeless-topic",
        type="Cultural Context",
        extra_frontmatter=_CULTURE_DEFAULTS,
    )

    results = find_concepts(tmp_path, period="attic")

    assert results == []


def test_find_concepts_unknown_period_value_matches_nothing(tmp_path):
    _write(tmp_path, "grammar", "rule-a", extra_frontmatter={"periods_spanned": {"from": "attic", "to": "byzantine"}, "dialect": []})

    results = find_concepts(tmp_path, period="not-a-real-period")

    assert results == []


def test_find_concepts_level_filter_ignores_hand_edited_scalar_level(tmp_path):
    path = _write(tmp_path, "grammar", "hand-edited-rule", level=["beginner"])
    text = path.read_text()
    _, yaml_text, body_text = text.split("---\n", 2)
    frontmatter = yaml.safe_load(yaml_text)
    frontmatter["level"] = "beginner"
    path.write_text("---\n" + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False) + "---\n" + body_text)

    results = find_concepts(tmp_path, level="beg")

    assert results == []


def test_find_concepts_dialect_filter_ignores_hand_edited_scalar_dialect(tmp_path):
    _write(
        tmp_path, "grammar", "hand-edited-dialect-rule",
        extra_frontmatter={"periods_spanned": {"from": "attic", "to": "attic"}, "dialect": "attic"},
    )

    results = find_concepts(tmp_path, dialect="atti")

    assert results == []


def test_find_concepts_with_type_filter_only_reads_matching_directory(tmp_path, monkeypatch):
    _write(tmp_path, "grammar", "rule-a")
    _write(tmp_path, "culture", "topic-a", type="Cultural Context", extra_frontmatter=_CULTURE_DEFAULTS)

    read_dirs = []
    original_read = okf.read

    def spy_read(path):
        read_dirs.append(path.parent.name)
        return original_read(path)

    monkeypatch.setattr(okf, "read", spy_read)

    results = find_concepts(tmp_path, type="Grammatical Rule")

    assert read_dirs == ["grammar"]
    assert [c.title for _, c in results] == ["rule-a"]


def test_find_concepts_filters_by_dialect(tmp_path):
    _write(tmp_path, "grammar", "attic-rule", extra_frontmatter={"periods_spanned": {"from": "attic", "to": "attic"}, "dialect": ["attic"]})
    _write(tmp_path, "grammar", "koine-bridging-rule", extra_frontmatter={"periods_spanned": {"from": "koine", "to": "modern"}, "dialect": []})

    results = find_concepts(tmp_path, dialect="attic")

    assert [c.title for _, c in results] == ["attic-rule"]


def test_find_concepts_combines_all_filters_with_and(tmp_path):
    _write(
        tmp_path, "grammar", "matches-everything",
        level=["beginner"],
        sources=[Source(id="s", resource="r", title="t", author="E. A. Sophocles")],
        extra_frontmatter={"periods_spanned": {"from": "attic", "to": "byzantine"}, "dialect": ["attic"]},
    )
    _write(
        tmp_path, "grammar", "wrong-level",
        level=["advanced"],
        sources=[Source(id="s", resource="r", title="t", author="E. A. Sophocles")],
        extra_frontmatter={"periods_spanned": {"from": "attic", "to": "byzantine"}, "dialect": ["attic"]},
    )

    results = find_concepts(
        tmp_path,
        type="Grammatical Rule",
        level="beginner",
        period="koine",
        dialect="attic",
        author="Sophocles",
    )

    assert [c.title for _, c in results] == ["matches-everything"]


def test_list_values_counts_distinct_level_values(tmp_path):
    _write(tmp_path, "grammar", "rule-a", level=["beginner"])
    _write(tmp_path, "grammar", "rule-b", level=["beginner"])
    _write(tmp_path, "grammar", "rule-c", level=["advanced"])

    results = list_values(tmp_path, "level")

    assert dict(results) == {"beginner": 2, "advanced": 1}


def test_list_values_sorted_by_count_desc_then_value(tmp_path):
    _write(tmp_path, "grammar", "rule-a", level=["beginner"])
    _write(tmp_path, "grammar", "rule-b", level=["beginner"])
    _write(tmp_path, "grammar", "rule-c", level=["beginner"])
    _write(tmp_path, "grammar", "rule-d", level=["advanced"])
    _write(tmp_path, "grammar", "rule-e", level=["b1"])

    results = list_values(tmp_path, "level")

    assert results == [("beginner", 3), ("advanced", 1), ("b1", 1)]


def test_list_values_scoped_by_other_filter(tmp_path):
    _write(tmp_path, "grammar", "grammar-beginner", level=["beginner"])
    _write(tmp_path, "culture", "culture-advanced", type="Cultural Context", level=["advanced"], extra_frontmatter=_CULTURE_DEFAULTS)

    results = list_values(tmp_path, "level", type="Grammatical Rule")

    assert dict(results) == {"beginner": 1}


def test_list_values_ignores_a_filter_matching_its_own_field(tmp_path):
    _write(tmp_path, "grammar", "rule-a", level=["beginner"])
    _write(tmp_path, "grammar", "rule-b", level=["advanced"])

    results = list_values(tmp_path, "level", level="nonexistent-value")

    assert dict(results) == {"beginner": 1, "advanced": 1}


def test_list_values_for_period_counts_every_period_a_range_spans(tmp_path):
    _write(tmp_path, "grammar", "wide-span", extra_frontmatter={"periods_spanned": {"from": "attic", "to": "byzantine"}, "dialect": []})
    _write(tmp_path, "grammar", "narrow-span", extra_frontmatter={"periods_spanned": {"from": "attic", "to": "attic"}, "dialect": []})

    results = list_values(tmp_path, "period")

    assert dict(results) == {"attic": 2, "koine": 1, "byzantine": 1}


def test_list_values_for_author_counts_each_source_on_multi_source_concepts(tmp_path):
    _write(tmp_path, "grammar", "multi-source-rule", sources=[
        Source(id="s1", resource="r1", title="t1", author="Jane Doe"),
        Source(id="s2", resource="r2", title="t2", author="Homer"),
    ])
    _write(tmp_path, "grammar", "single-source-rule", sources=[Source(id="s", resource="r", title="t", author="Homer")])

    results = list_values(tmp_path, "author")

    assert dict(results) == {"Jane Doe": 1, "Homer": 2}


def test_list_values_for_dialect_ignores_hand_edited_scalar_dialect(tmp_path):
    _write(
        tmp_path, "grammar", "hand-edited-dialect-rule",
        extra_frontmatter={"periods_spanned": {"from": "attic", "to": "attic"}, "dialect": "attic"},
    )

    results = list_values(tmp_path, "dialect")

    assert results == []


def test_list_mode_report_returns_none_when_no_field_is_list(tmp_path):
    _write(tmp_path, "grammar", "rule-a")

    assert list_mode_report(tmp_path, {"type": None, "level": "beginner", "period": None, "dialect": None, "author": None}) is None


def test_list_mode_report_type_values_are_short_form_round_trippable(tmp_path):
    _write(tmp_path, "grammar", "rule-a")
    _write(tmp_path, "culture", "topic-a", type="Cultural Context", extra_frontmatter=_CULTURE_DEFAULTS)

    report = list_mode_report(tmp_path, {"type": "list", "level": None, "period": None, "dialect": None, "author": None})

    values = dict(report["type"])
    assert values == {"grammar": 1, "culture": 1}
    # every returned value must be valid --type input, i.e. a TYPE_BY_DIR key -- not the
    # ConceptFile.type long form ("Grammatical Rule") argparse's --type choices reject.
    assert set(values) <= set(TYPE_BY_DIR)


def test_list_mode_report_scopes_multiple_listed_fields_from_one_shared_scan(tmp_path, monkeypatch):
    _write(tmp_path, "grammar", "rule-a", level=["beginner"])
    _write(tmp_path, "grammar", "rule-b", level=["advanced"])
    _write(tmp_path, "culture", "topic-a", type="Cultural Context", level=["beginner"], extra_frontmatter=_CULTURE_DEFAULTS)

    read_count = 0
    original_read = okf.read

    def counting_read(path):
        nonlocal read_count
        read_count += 1
        return original_read(path)

    monkeypatch.setattr(okf, "read", counting_read)

    report = list_mode_report(tmp_path, {"type": "grammar", "level": "list", "period": "list", "dialect": None, "author": None})

    # exactly one find_concepts() scan shared across both listed fields (2 grammar
    # files), not one scan per field (which would read 2 files twice = 4 reads).
    assert read_count == 2
    assert dict(report["level"]) == {"beginner": 1, "advanced": 1}
    # both rule-a and rule-b keep _write()'s default periods_spanned attic->attic.
    assert dict(report["period"]) == {"attic": 2}
