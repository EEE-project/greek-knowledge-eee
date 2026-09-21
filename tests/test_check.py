from okfbuild import check


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def test_check_file_accepts_an_editor_added_trailing_newline(tmp_path):
    # Regression guard: a Literary Translation has no footnote-definitions block, so
    # render() ends its body without a newline; an editor saving a final one must not
    # fail the check with a misleading "footnote-definitions block" message.
    path = tmp_path / "texts" / "work" / "translations_el.md"
    _write(path, _LITERARY_TRANSLATION + "\n")

    assert check.check_file(path) == []


def test_check_file_flags_unparseable_frontmatter(tmp_path):
    path = tmp_path / "grammar" / "broken.md"
    _write(path, "---\n---\nno frontmatter fields at all\n")

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
