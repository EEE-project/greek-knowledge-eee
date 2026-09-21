from datetime import date
from pathlib import Path
from typing import Any

import yaml

from okfbuild import check, okf
from okfbuild.okf import ConceptFile, Source
from okfbuild.periods import PERIOD_ORDER
from okfbuild.query import (
    TYPES_BY_DIR,
    concept_types,
    find_concepts,
    list_mode_report,
    list_values,
    split_values,
)

_CULTURE_DEFAULTS = {"related_words": [], "related_lessons": [], "dialect": []}
_LITERARY_TEXT_FIELDS = {"work": "Work", "passage": "1", "language": "el"}
_LITERARY_TRANSLATION_FIELDS = {**_LITERARY_TEXT_FIELDS, "translators": ["Someone"]}


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


def test_period_queries_ignore_a_span_that_names_an_unknown_period(tmp_path):
    _write(tmp_path, "grammar", "misspelled-span", extra_frontmatter={"periods_spanned": {"from": "attik", "to": "modern"}, "dialect": []})

    assert find_concepts(tmp_path, period="modern") == []
    assert list_values(tmp_path, "period") == []


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
    # every returned value must be valid --type input, i.e. a TYPES_BY_DIR key -- not the
    # ConceptFile.type long form ("Grammatical Rule") argparse's --type choices reject.
    assert set(values) <= set(TYPES_BY_DIR)


def _write_a_text_and_a_translation(tmp_path):
    _write(tmp_path, "texts/work", "text", type="Literary Text", extra_frontmatter=_LITERARY_TEXT_FIELDS)
    _write(tmp_path, "texts/work", "translations_en", type="Literary Translation", extra_frontmatter=_LITERARY_TRANSLATION_FIELDS)


def test_the_texts_type_spans_originals_and_translations(tmp_path):
    _write_a_text_and_a_translation(tmp_path)
    _write(tmp_path, "grammar", "rule-a")

    results = find_concepts(tmp_path, type=TYPES_BY_DIR["texts"])

    assert sorted(c.title for _, c in results) == ["text", "translations_en"]


def test_find_concepts_type_literary_text_excludes_translations(tmp_path):
    _write_a_text_and_a_translation(tmp_path)

    results = find_concepts(tmp_path, type="Literary Text")

    assert [c.title for _, c in results] == ["text"]


def test_list_mode_report_merges_both_texts_types_under_the_short_form(tmp_path):
    _write_a_text_and_a_translation(tmp_path)
    _write(tmp_path, "grammar", "rule-a")

    report = list_mode_report(tmp_path, {"type": "list", "level": None, "period": None, "dialect": None, "author": None})

    assert dict(report["type"]) == {"texts": 2, "grammar": 1}


def _write_translation(tmp_path, slug, *, work, language):
    fields = {**_LITERARY_TRANSLATION_FIELDS, "work": work, "language": language}
    return _write(tmp_path, "texts/work", slug, type="Literary Translation", extra_frontmatter=fields)


def test_find_concepts_filters_by_work_case_insensitive_substring(tmp_path):
    _write_translation(tmp_path, "ithaka-ru", work="Kavafis, Ithaka", language="ru")
    _write_translation(tmp_path, "odyssey-ru", work="Odyssey", language="ru")

    results = find_concepts(tmp_path, work="ITHAKA")

    assert [c.title for _, c in results] == ["ithaka-ru"]


def test_find_concepts_filters_by_language_as_an_exact_case_insensitive_code(tmp_path):
    _write_translation(tmp_path, "work-el", work="Work", language="el")
    _write_translation(tmp_path, "work-en", work="Work", language="en")

    assert [c.title for _, c in find_concepts(tmp_path, language="EL")] == ["work-el"]
    # a code, not a substring: "e" is the start of both "el" and "en" yet matches neither
    assert find_concepts(tmp_path, language="e") == []


def test_find_concepts_combines_the_work_and_language_filters(tmp_path):
    _write_translation(tmp_path, "ithaka-ru", work="Kavafis, Ithaka", language="ru")
    _write_translation(tmp_path, "ithaka-en", work="Kavafis, Ithaka", language="en")
    _write_translation(tmp_path, "odyssey-ru", work="Odyssey", language="ru")

    results = find_concepts(tmp_path, type=TYPES_BY_DIR["texts"], work="ithaka", language="ru")

    assert [c.title for _, c in results] == ["ithaka-ru"]


def test_find_concepts_work_and_language_never_match_a_concept_without_them(tmp_path):
    _write(tmp_path, "grammar", "rule-a")

    assert find_concepts(tmp_path, work="a") == []
    assert find_concepts(tmp_path, language="el") == []


def test_list_mode_report_lists_the_works_and_languages_in_use(tmp_path):
    _write_translation(tmp_path, "ithaka-ru", work="Kavafis, Ithaka", language="ru")
    _write_translation(tmp_path, "ithaka-en", work="Kavafis, Ithaka", language="en")
    _write_translation(tmp_path, "odyssey-ru", work="Odyssey", language="ru")
    _write(tmp_path, "grammar", "rule-a")

    report = list_mode_report(tmp_path, {"work": "list", "language": "list"})

    assert dict(report["work"]) == {"Kavafis, Ithaka": 2, "Odyssey": 1}
    assert dict(report["language"]) == {"ru": 2, "en": 1}


def test_list_values_for_work_is_scoped_by_language(tmp_path):
    _write_translation(tmp_path, "ithaka-ru", work="Kavafis, Ithaka", language="ru")
    _write_translation(tmp_path, "ithaka-en", work="Kavafis, Ithaka", language="en")
    _write_translation(tmp_path, "odyssey-ru", work="Odyssey", language="ru")

    assert dict(list_values(tmp_path, "work", language="ru")) == {"Kavafis, Ithaka": 1, "Odyssey": 1}


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


def test_split_values_splits_at_a_comma_not_followed_by_whitespace():
    assert split_values("ru,en") == ["ru", "en"]
    assert split_values("ru") == ["ru"]
    assert split_values(",ru,,en,") == ["ru", "en"]
    assert split_values("") == []


def test_split_values_keeps_a_comma_followed_by_whitespace_inside_one_value():
    # `--work list` prints "Kavafis, Ithaka" and `--author list` prints "Sophocles (1887), curated":
    # a printed value has to stay valid input, so a comma-then-space belongs to the value
    assert split_values("Kavafis, Ithaka") == ["Kavafis, Ithaka"]
    assert split_values("Kavafis, Ithaka,Odyssey") == ["Kavafis, Ithaka", "Odyssey"]


def test_concept_types_unions_the_types_behind_each_shorthand():
    assert concept_types(None) is None
    assert concept_types([]) is None
    assert concept_types("words") == {"Lexical Entry"}
    assert concept_types(["grammar", "texts"]) == {"Grammatical Rule", "Literary Translation", "Literary Text"}


def test_find_concepts_matches_any_of_several_levels(tmp_path):
    _write(tmp_path, "grammar", "rule-beginner", level=["beginner"])
    _write(tmp_path, "grammar", "rule-advanced", level=["advanced"])
    _write(tmp_path, "grammar", "rule-b1", level=["B1"])

    results = find_concepts(tmp_path, level=["beginner", "advanced"])

    assert [c.title for _, c in results] == ["rule-advanced", "rule-beginner"]


def test_find_concepts_matches_any_of_several_dialects(tmp_path):
    _write(tmp_path, "grammar", "attic-rule", extra_frontmatter={"periods_spanned": {"from": "attic", "to": "attic"}, "dialect": ["attic"]})
    _write(tmp_path, "grammar", "ionic-rule", extra_frontmatter={"periods_spanned": {"from": "homeric", "to": "homeric"}, "dialect": ["ionic"]})
    _write(tmp_path, "grammar", "koine-rule", extra_frontmatter={"periods_spanned": {"from": "koine", "to": "koine"}, "dialect": ["koine"]})

    results = find_concepts(tmp_path, dialect=("attic", "ionic"))

    assert [c.title for _, c in results] == ["attic-rule", "ionic-rule"]


def test_find_concepts_matches_any_of_several_authors_by_substring(tmp_path):
    _write(tmp_path, "grammar", "by-sophocles", sources=[Source(id="s", resource="r", title="t", author="E. A. Sophocles")])
    _write(tmp_path, "grammar", "by-murray", sources=[Source(id="s", resource="r", title="t", author="A. T. Murray")])
    _write(tmp_path, "grammar", "by-pope", sources=[Source(id="s", resource="r", title="t", author="Alexander Pope")])

    results = find_concepts(tmp_path, author=["sophocles", "MURRAY"])

    assert [c.title for _, c in results] == ["by-murray", "by-sophocles"]


def test_find_concepts_matches_any_of_several_works_and_languages(tmp_path):
    _write_translation(tmp_path, "ithaka-ru", work="Kavafis, Ithaka", language="ru")
    _write_translation(tmp_path, "ithaka-en", work="Kavafis, Ithaka", language="en")
    _write_translation(tmp_path, "ithaka-el", work="Kavafis, Ithaka", language="el")
    _write_translation(tmp_path, "odyssey-ru", work="Odyssey", language="ru")

    assert [c.title for _, c in find_concepts(tmp_path, work="ithaka", language=["ru", "EN"])] == ["ithaka-en", "ithaka-ru"]
    assert [c.title for _, c in find_concepts(tmp_path, work=["ithaka", "odyssey"], language="ru")] == ["ithaka-ru", "odyssey-ru"]


def _write_one_rule_per_period(tmp_path):
    for period in PERIOD_ORDER:
        _write(tmp_path, "grammar", f"{period}-rule", extra_frontmatter={"periods_spanned": {"from": period, "to": period}, "dialect": []})


def test_find_concepts_matches_any_of_several_periods(tmp_path):
    _write_one_rule_per_period(tmp_path)

    results = find_concepts(tmp_path, period=["homeric", "modern"])

    assert [c.title for _, c in results] == ["homeric-rule", "modern-rule"]


def test_find_concepts_period_range_includes_both_ends_and_everything_between(tmp_path):
    _write_one_rule_per_period(tmp_path)

    results = find_concepts(tmp_path, period="attic..byzantine")

    assert [c.title for _, c in results] == ["attic-rule", "byzantine-rule", "koine-rule"]


def test_find_concepts_period_range_combines_with_single_periods(tmp_path):
    _write_one_rule_per_period(tmp_path)

    results = find_concepts(tmp_path, period=["homeric..attic", "modern"])

    assert [c.title for _, c in results] == ["attic-rule", "homeric-rule", "modern-rule"]


def test_find_concepts_period_range_with_a_reversed_or_unknown_end_matches_nothing(tmp_path):
    _write_one_rule_per_period(tmp_path)

    assert find_concepts(tmp_path, period="attic..homeric") == []
    assert find_concepts(tmp_path, period="attic..nonsense") == []
    assert find_concepts(tmp_path, period="..attic") == []


def test_find_concepts_treats_an_empty_selection_as_no_filter(tmp_path):
    _write(tmp_path, "grammar", "rule-a", level=["beginner"])
    _write(tmp_path, "grammar", "rule-b", level=["advanced"])

    assert len(find_concepts(tmp_path, type=set(), level=[], period=(), work=[])) == 2


def test_find_concepts_ors_the_values_within_a_filter_and_ands_the_filters(tmp_path):
    attic = {"periods_spanned": {"from": "attic", "to": "attic"}, "dialect": ["attic"]}
    ionic = {"periods_spanned": {"from": "homeric", "to": "homeric"}, "dialect": ["ionic"]}
    _write(tmp_path, "grammar", "beginner-attic", level=["beginner"], extra_frontmatter=attic)
    _write(tmp_path, "grammar", "advanced-attic", level=["advanced"], extra_frontmatter=attic)
    _write(tmp_path, "grammar", "b1-attic", level=["B1"], extra_frontmatter=attic)
    _write(tmp_path, "grammar", "beginner-ionic", level=["beginner"], extra_frontmatter=ionic)

    results = find_concepts(tmp_path, level=["beginner", "advanced"], dialect="attic")

    assert [c.title for _, c in results] == ["advanced-attic", "beginner-attic"]


def test_list_mode_report_takes_list_valued_filters_as_the_command_line_gives_them(tmp_path):
    _write_translation(tmp_path, "ithaka-ru", work="Kavafis, Ithaka", language="ru")
    _write_translation(tmp_path, "ithaka-en", work="Kavafis, Ithaka", language="en")
    _write_translation(tmp_path, "odyssey-ru", work="Odyssey", language="ru")
    _write_translation(tmp_path, "odyssey-el", work="Odyssey", language="el")

    report = list_mode_report(tmp_path, {"work": ["list"], "language": ["ru", "en"]})

    assert dict(report["work"]) == {"Kavafis, Ithaka": 2, "Odyssey": 1}


def test_list_mode_report_is_none_unless_a_filter_is_exactly_list(tmp_path):
    _write(tmp_path, "grammar", "rule-a")

    assert list_mode_report(tmp_path, {"level": ["beginner", "advanced"], "work": None}) is None
    assert list_mode_report(tmp_path, {"level": ["list", "advanced"]}) is None


def test_list_mode_report_scopes_by_several_types(tmp_path):
    _write(tmp_path, "grammar", "rule-a", level=["beginner"])
    _write(tmp_path, "culture", "topic-a", type="Cultural Context", level=["advanced"], extra_frontmatter=_CULTURE_DEFAULTS)
    _write(tmp_path, "words", "word-a", type="Lexical Entry", level=["B1"], extra_frontmatter={"lemma": "x", "periods": ["attic"]})

    report = list_mode_report(tmp_path, {"type": ["grammar", "culture"], "level": ["list"]})

    assert dict(report["level"]) == {"beginner": 1, "advanced": 1}


def _verify(path: Path, *, of_current_text: bool = True) -> Path:
    check.record_verification(path, by="tester", against=["a source"], on=date(2026, 9, 21))
    if not of_current_text:
        path.write_text(path.read_text(encoding="utf-8").replace("Some claim.", "Another claim."), encoding="utf-8")
    return path


def test_find_concepts_verified_keeps_only_concepts_verified_for_their_current_text(tmp_path):
    _verify(_write(tmp_path, "grammar", "checked"))
    _write(tmp_path, "grammar", "unchecked")
    _verify(_write(tmp_path, "grammar", "edited-since"), of_current_text=False)

    assert [c.title for _, c in find_concepts(tmp_path, verified=True)] == ["checked"]
    assert len(find_concepts(tmp_path)) == 3
    assert len(find_concepts(tmp_path, verified=False)) == 3


def test_find_concepts_verified_combines_with_the_other_filters(tmp_path):
    _verify(_write(tmp_path, "grammar", "beginner-checked", level=["beginner"]))
    _verify(_write(tmp_path, "grammar", "advanced-checked", level=["advanced"]))
    _write(tmp_path, "grammar", "beginner-unchecked", level=["beginner"])

    results = find_concepts(tmp_path, level="beginner", verified=True)

    assert [c.title for _, c in results] == ["beginner-checked"]


def test_find_concepts_verified_ignores_a_hand_edited_scalar_verified_field(tmp_path):
    path = _write(tmp_path, "grammar", "hand-edited")
    path.write_text(path.read_text(encoding="utf-8").replace("verified: []", "verified: yes"), encoding="utf-8")

    assert find_concepts(tmp_path, verified=True) == []


def test_list_values_can_be_scoped_to_verified_concepts(tmp_path):
    _verify(_write(tmp_path, "grammar", "checked", level=["A2"]))
    _write(tmp_path, "grammar", "unchecked", level=["B1"])

    assert dict(list_values(tmp_path, "level", verified=True)) == {"A2": 1}
    assert dict(list_values(tmp_path, "level")) == {"A2": 1, "B1": 1}


def test_list_mode_report_scopes_a_listing_to_verified_concepts(tmp_path):
    _verify(_write(tmp_path, "grammar", "checked", level=["A2"]))
    _write(tmp_path, "grammar", "unchecked", level=["B1"])

    scoped = list_mode_report(tmp_path, {"level": ["list"]}, verified=True)
    unscoped = list_mode_report(tmp_path, {"level": ["list"]})

    assert dict(scoped["level"]) == {"A2": 1}
    assert dict(unscoped["level"]) == {"A2": 1, "B1": 1}


def test_list_mode_report_is_none_when_only_verified_is_given(tmp_path):
    _write(tmp_path, "grammar", "rule-a")

    assert list_mode_report(tmp_path, {"level": ["A2"]}, verified=True) is None


def test_find_concepts_skips_a_file_that_is_not_a_concept(tmp_path):
    _write(tmp_path, "grammar", "rule-a")
    (tmp_path / "grammar" / "notes.md").write_text("just some notes, no frontmatter\n", encoding="utf-8")

    assert [c.title for _, c in find_concepts(tmp_path)] == ["rule-a"]
