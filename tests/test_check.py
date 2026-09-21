from datetime import date

import pytest
import yaml

from okfbuild import check, okf


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


_UNPARSEABLE = "---\n---\nno frontmatter fields at all\n"

_GOOD_RULE = """\
---
type: Grammatical Rule
title: test-rule
description: 'Grammatical rule: test-rule'
tags: []
level: []
sources:
- id: src
  resource: somewhere
  title: A Source
  author: Someone
generated:
  by: process:greek-knowledge-eee-builder/0.2.0
  at: '2026-01-01T00:00:00+00:00'
periods_spanned:
  from: attic
  to: attic
dialect: []
status: draft
verified: []
---
## A test rule

Some claim.[^src]

[^src]: A Source, Someone (somewhere)
"""


def test_check_file_passes_a_well_formed_file(tmp_path):
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _GOOD_RULE)

    assert check.check_file(path) == []


def test_check_file_flags_unresolved_footnote_reference(tmp_path):
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _GOOD_RULE.replace("Some claim.[^src]", "Some claim.[^src][^ghost]"))

    issues = check.check_file(path)

    assert any("ghost" in issue.message and "no matching sources" in issue.message for issue in issues)


def test_check_file_flags_uncited_source(tmp_path):
    path = tmp_path / "grammar" / "test-rule.md"
    two_sources = _GOOD_RULE.replace(
        "sources:\n- id: src\n  resource: somewhere\n  title: A Source\n  author: Someone\n",
        "sources:\n- id: src\n  resource: somewhere\n  title: A Source\n  author: Someone\n"
        "- id: unused\n  resource: elsewhere\n  title: Another Source\n  author: Someone Else\n",
    )
    _write(path, two_sources)

    issues = check.check_file(path)

    assert any("unused" in issue.message and "never cited" in issue.message for issue in issues)


def test_check_file_ignores_a_non_slug_bracket_caret_substring_in_raw_source_text(tmp_path):
    # Regression guard: raw dictionary text (e.g. LSJ) can contain literal
    # "[^—]"-shaped editorial notation that isn't a real citation at all --
    # found live in words/ὄϊς.md. A real id is always a lowercase slug, so
    # this must not be mistaken for an unresolved reference.
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _GOOD_RULE.replace("Some claim.[^src]", "Some claim.[^src] Ion. dat. ὀΐ [^—] more text."))

    issues = check.check_file(path)

    assert issues == []


_LITERARY_TRANSLATION = """\
---
type: Literary Translation
title: work (1) — el translations
description: el translations of work 1
tags: []
level: []
sources:
- id: unused
  resource: somewhere
  title: A Source
  author: Someone
generated:
  by: process:greek-knowledge-eee-builder/0.2.0
  at: '2026-01-01T00:00:00+00:00'
work: work
passage: '1'
language: el
translators:
- πρωτότυπο
status: draft
verified: []
---
## πρωτότυπο

Plain poem text, no inline citations."""


def test_check_file_skips_citation_checks_for_literary_translation(tmp_path):
    path = tmp_path / "texts" / "work" / "translations_el.md"
    _write(path, _LITERARY_TRANSLATION)

    assert check.check_file(path) == []


def test_check_file_accepts_a_literary_text_without_citations_or_translators(tmp_path):
    path = tmp_path / "texts" / "work" / "text.md"
    text = _LITERARY_TRANSLATION.replace("type: Literary Translation", "type: Literary Text")
    text = text.replace("translators:\n- πρωτότυπο\n", "")
    assert "Literary Text" in text and "translators" not in text
    _write(path, text)

    assert check.check_file(path) == []


def test_check_file_accepts_an_editor_added_trailing_newline(tmp_path):
    # Regression guard: a Literary Translation has no footnote-definitions block, so
    # render() ends its body without a newline; an editor saving a final one must not
    # fail the check with a misleading "footnote-definitions block" message.
    path = tmp_path / "texts" / "work" / "translations_el.md"
    _write(path, _LITERARY_TRANSLATION + "\n")

    assert check.check_file(path) == []


def test_check_file_flags_unparseable_frontmatter(tmp_path):
    path = tmp_path / "grammar" / "broken.md"
    _write(path, _UNPARSEABLE)

    issues = check.check_file(path)

    assert len(issues) == 1
    assert "cannot parse" in issues[0].message


def test_check_file_flags_stale_footnote_definitions_and_fix_file_repairs_it(tmp_path):
    path = tmp_path / "grammar" / "test-rule.md"
    stale = _GOOD_RULE.replace(
        "[^src]: A Source, Someone (somewhere)",
        "[^src]: A Stale Title That Doesn't Match Sources Anymore (somewhere)",
    )
    _write(path, stale)

    assert check.check_file(path) != []

    changed = check.fix_file(path)

    assert changed
    assert check.check_file(path) == []


def test_check_file_flags_frontmatter_that_is_not_canonical_and_fix_file_repairs_it(tmp_path):
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _GOOD_RULE.replace("verified: []\n", ""))

    assert any("canonical rendering" in issue.message for issue in check.check_file(path))

    assert check.fix_file(path) is True
    assert check.check_file(path) == []


def test_fix_file_leaves_a_file_it_cannot_parse_alone(tmp_path):
    path = tmp_path / "grammar" / "broken.md"
    _write(path, _UNPARSEABLE)
    before = path.read_bytes()

    assert check.fix_file(path) is False
    assert path.read_bytes() == before


def test_check_corpus_skips_index_files_and_dirs_outside_the_checked_set(tmp_path):
    _write(tmp_path / "grammar" / "test-rule.md", _GOOD_RULE)
    _write(tmp_path / "grammar" / "index.md", "not OKF markdown at all")
    _write(tmp_path / "references" / "not-a-concept.md", "not OKF markdown at all")

    issues = check.check_corpus(tmp_path)

    assert issues == []


def test_resolve_targets_with_no_paths_checks_everything(tmp_path):
    _write(tmp_path / "grammar" / "test-rule.md", _GOOD_RULE)

    assert check.resolve_targets(tmp_path, []) == check.iter_checked_files(tmp_path)


def test_resolve_targets_with_a_single_file_scopes_to_just_that_file(tmp_path):
    _write(tmp_path / "grammar" / "test-rule.md", _GOOD_RULE)
    _write(tmp_path / "culture" / "other-topic.md", _GOOD_RULE.replace("test-rule", "other-topic"))

    targets = check.resolve_targets(tmp_path, [str(tmp_path / "grammar" / "test-rule.md")])

    assert targets == [tmp_path / "grammar" / "test-rule.md"]


def test_resolve_targets_with_a_directory_walks_just_that_directory(tmp_path):
    _write(tmp_path / "grammar" / "test-rule.md", _GOOD_RULE)
    _write(tmp_path / "grammar" / "index.md", "not OKF markdown at all")
    _write(tmp_path / "culture" / "other-topic.md", _GOOD_RULE.replace("test-rule", "other-topic"))

    targets = check.resolve_targets(tmp_path, [str(tmp_path / "grammar")])

    assert targets == [tmp_path / "grammar" / "test-rule.md"]


def test_check_corpus_against_real_repo_content_is_clean(repo_root):
    issues = check.check_corpus(repo_root)

    assert issues == [], [str(issue) for issue in issues]


# --- verification records ---


def _current_entry():
    return {
        "by": "tester",
        "at": "2026-09-21",
        "against": ["a source"],
        "body_sha256": okf.body_digest(_GOOD_RULE.split("---\n", 2)[2]),
    }


def _rule_with_verified(entries):
    return _GOOD_RULE.replace("verified: []\n", yaml.safe_dump({"verified": entries}, allow_unicode=True, sort_keys=False))


def test_check_file_accepts_a_verification_pinned_to_the_current_text(tmp_path):
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _rule_with_verified([_current_entry()]))

    assert check.check_file(path) == []


def test_check_file_flags_a_verification_of_older_text_as_stale(tmp_path):
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _rule_with_verified([_current_entry()]).replace("Some claim.", "Another claim."))

    issues = check.check_file(path)

    assert any("stale" in issue.message for issue in issues), [str(issue) for issue in issues]


@pytest.mark.parametrize(
    "change",
    [{"by": ""}, {"by": None}, {"at": "yesterday"}, {"against": []}, {"against": [""]}, {"body_sha256": "abc"}],
)
def test_check_file_flags_a_malformed_verification(tmp_path, change):
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _rule_with_verified([{**_current_entry(), **change}]))

    issues = check.check_file(path)

    assert any("verified entry" in issue.message for issue in issues), [str(issue) for issue in issues]


@pytest.mark.parametrize("missing", ["by", "at", "against", "body_sha256"])
def test_check_file_flags_a_verification_missing_a_field(tmp_path, missing):
    entry = _current_entry()
    del entry[missing]
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _rule_with_verified([entry]))

    issues = check.check_file(path)

    assert any("verified entry" in issue.message and missing in issue.message for issue in issues)


def test_check_file_flags_a_verified_field_that_is_not_a_list(tmp_path):
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _GOOD_RULE.replace("verified: []", "verified: yes"))

    issues = check.check_file(path)

    assert any("verified" in issue.message for issue in issues)


def test_record_verification_pins_a_record_to_the_current_text(tmp_path):
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _GOOD_RULE)

    issues = check.record_verification(path, by="tester", against=["a source", "the corpus"], on=date(2026, 9, 21))

    assert issues == []
    concept = okf.read(path)
    assert concept.verified == [
        {"by": "tester", "at": "2026-09-21", "against": ["a source", "the corpus"], "body_sha256": okf.body_digest(concept.body)}
    ]
    assert okf.current_verification(concept) is not None
    assert check.check_file(path) == []


def test_record_verification_dates_the_record_today_by_default(tmp_path):
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _GOOD_RULE)

    check.record_verification(path, by="tester", against=["a source"])

    assert okf.read(path).verified[0]["at"] == date.today().isoformat()


def test_record_verification_replaces_the_record_of_older_text(tmp_path):
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _GOOD_RULE)
    check.record_verification(path, by="first", against=["x"], on=date(2026, 9, 1))
    path.write_text(path.read_text(encoding="utf-8").replace("Some claim.", "Another claim."), encoding="utf-8")
    assert any("stale" in issue.message for issue in check.check_file(path))

    issues = check.record_verification(path, by="second", against=["y"], on=date(2026, 9, 21))

    assert issues == []
    assert [entry["by"] for entry in okf.read(path).verified] == ["second"]
    assert check.check_file(path) == []


def test_record_verification_refuses_a_file_that_fails_the_structural_check(tmp_path):
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _GOOD_RULE.replace("Some claim.[^src]", "Some claim.[^src][^ghost]"))
    before = path.read_bytes()

    issues = check.record_verification(path, by="tester", against=["a source"])

    assert any("ghost" in issue.message for issue in issues)
    assert path.read_bytes() == before


def test_fix_file_leaves_a_current_verification_alone(tmp_path):
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _GOOD_RULE)
    check.record_verification(path, by="tester", against=["a source"], on=date(2026, 9, 21))
    before = path.read_bytes()

    assert check.fix_file(path) is False

    assert path.read_bytes() == before


def test_check_file_flags_a_verification_entry_that_is_not_a_mapping(tmp_path):
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _rule_with_verified(["checked by someone"]))

    issues = check.check_file(path)

    assert any("verified entry 1 is not a mapping" in issue.message for issue in issues)


def test_check_structure_ignores_a_stale_record_but_still_flags_a_broken_file(tmp_path):
    stale = tmp_path / "grammar" / "stale.md"
    _write(stale, _rule_with_verified([_current_entry()]).replace("Some claim.", "Another claim."))
    broken = tmp_path / "grammar" / "broken.md"
    _write(broken, _UNPARSEABLE)

    assert check.check_structure(stale) == []
    assert [issue.message for issue in check.check_structure(broken)] == [
        "cannot parse as OKF markdown, or missing a required common field"
    ]


def test_record_verification_refuses_a_file_that_cannot_be_parsed(tmp_path):
    path = tmp_path / "grammar" / "broken.md"
    _write(path, _UNPARSEABLE)
    before = path.read_bytes()

    issues = check.record_verification(path, by="tester", against=["a source"])

    assert len(issues) == 1 and "cannot parse" in issues[0].message
    assert path.read_bytes() == before


@pytest.mark.parametrize("kwargs", [{"by": "", "against": ["a source"]}, {"by": "tester", "against": []}])
def test_record_verification_will_not_record_an_anonymous_or_unfounded_check(tmp_path, kwargs):
    path = tmp_path / "grammar" / "test-rule.md"
    _write(path, _GOOD_RULE)
    before = path.read_bytes()

    with pytest.raises(ValueError, match="cannot record a verification"):
        check.record_verification(path, **kwargs)

    assert path.read_bytes() == before
