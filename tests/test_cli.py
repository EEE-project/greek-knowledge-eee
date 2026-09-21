"""Tests for okfbuild.cli's argument parsing and subcommand dispatch.
Both default_source_bundle and the underlying lookup_word/lexical_entry.build
are mocked -- this module tests dispatch and output formatting only, not
real source data (see tests/test_wiring.py / tests/test_lookup.py for that)."""

import sys
from unittest.mock import Mock

import pytest

from okfbuild import cli, okf
from okfbuild.okf import ConceptFile, Source


def test_cli_lookup_dispatches_and_prints_results(monkeypatch, capsys):
    monkeypatch.setattr(cli, "default_source_bundle", Mock(return_value="SOURCES"))
    monkeypatch.setattr(cli, "lookup_word", Mock(return_value={"morpheus": ["a reading"]}))
    monkeypatch.setattr(sys, "argv", ["greek-knowledge", "lookup", "νόστος"])

    cli.main()

    cli.lookup_word.assert_called_once_with("νόστος", "SOURCES", pos="noun")
    out = capsys.readouterr().out
    assert "== morpheus ==" in out
    assert "a reading" in out


def test_cli_lookup_reports_when_nothing_found(monkeypatch, capsys):
    monkeypatch.setattr(cli, "default_source_bundle", Mock(return_value="SOURCES"))
    monkeypatch.setattr(cli, "lookup_word", Mock(return_value={}))
    monkeypatch.setattr(sys, "argv", ["greek-knowledge", "lookup", "ἄγνωστος"])

    cli.main()

    assert "No source has anything for 'ἄγνωστος'" in capsys.readouterr().out


def test_cli_build_dispatches_and_prints_body(monkeypatch, capsys):
    concept = Mock(body="## Homeric\n\nsome body", extra_frontmatter={"periods": ["homeric"]})
    monkeypatch.setattr(cli, "default_source_bundle", Mock(return_value="SOURCES"))
    monkeypatch.setattr(cli.lexical_entry, "build", Mock(return_value=concept))
    monkeypatch.setattr(sys, "argv", ["greek-knowledge", "build", "νόστος", "--period", "homeric"])

    cli.main()

    cli.lexical_entry.build.assert_called_once_with("νόστος", "noun", ["homeric"], "SOURCES", level=[], tags=[])
    assert "some body" in capsys.readouterr().out


def test_cli_build_reports_when_no_periods_attested(monkeypatch, capsys):
    concept = Mock(extra_frontmatter={"periods": []})
    monkeypatch.setattr(cli, "default_source_bundle", Mock(return_value="SOURCES"))
    monkeypatch.setattr(cli.lexical_entry, "build", Mock(return_value=concept))
    monkeypatch.setattr(sys, "argv", ["greek-knowledge", "build", "ἄγνωστος"])

    cli.main()

    assert "No attested data for 'ἄγνωστος'" in capsys.readouterr().out


def test_cli_regenerate_without_write_refuses_and_never_touches_pipeline(monkeypatch, capsys):
    """The core safety property: `regenerate` alone (no --write) must be a
    complete no-op -- pipeline.run() is never called, so no accidental
    corpus mutation is possible without the explicit flag."""
    run_mock = Mock()
    monkeypatch.setattr("okfbuild.pipeline.run", run_mock)
    monkeypatch.setattr(sys, "argv", ["greek-knowledge", "regenerate"])

    try:
        cli.main()
        assert False, "expected SystemExit"
    except SystemExit as exc:
        assert exc.code == 1

    run_mock.assert_not_called()
    assert "Refusing to regenerate without --write" in capsys.readouterr().err


def test_cli_regenerate_with_write_but_no_created_with_eee_checkout_fails_cleanly(monkeypatch, capsys, tmp_path):
    run_mock = Mock()
    monkeypatch.setattr("okfbuild.pipeline.run", run_mock)
    monkeypatch.delenv("CREATED_WITH_EEE_PATH", raising=False)
    monkeypatch.setattr(cli, "_repo_root", Mock(return_value=tmp_path / "nonexistent-repo-root"))
    monkeypatch.setattr(sys, "argv", ["greek-knowledge", "regenerate", "--write"])

    try:
        cli.main()
        assert False, "expected SystemExit"
    except SystemExit as exc:
        assert exc.code == 1

    run_mock.assert_not_called()
    assert "created_with_eee checkout not found" in capsys.readouterr().err


def test_cli_regenerate_with_write_and_real_checkout_calls_pipeline_run(monkeypatch, capsys, tmp_path):
    created_with_eee = tmp_path / "created_with_eee"
    created_with_eee.mkdir()
    repo_root = tmp_path / "greek-knowledge-eee"
    repo_root.mkdir()

    report = Mock(written=5, unchanged=2, failed=0, errors=[])
    run_mock = Mock(return_value=report)
    enrich_mock = Mock()
    monkeypatch.setattr("okfbuild.pipeline.run", run_mock)
    monkeypatch.setattr("okfbuild.pilot_content.enrich_nostos_with_beekes", enrich_mock)
    monkeypatch.setattr(cli, "_repo_root", Mock(return_value=repo_root))
    monkeypatch.setattr(cli, "full_source_bundle", Mock(return_value="SOURCES"))
    monkeypatch.setenv("CREATED_WITH_EEE_PATH", str(created_with_eee))
    monkeypatch.setattr(sys, "argv", ["greek-knowledge", "regenerate", "--write"])

    cli.main()

    run_mock.assert_called_once()
    assert run_mock.call_args.kwargs["out_dir"] == repo_root
    assert run_mock.call_args.kwargs["sources"] == "SOURCES"
    enrich_mock.assert_called_once_with(repo_root, "SOURCES")
    assert "written=5 unchanged=2 failed=0" in capsys.readouterr().out


def test_cli_query_dispatches_with_translated_type_and_prints_matches(monkeypatch, capsys):
    concept = Mock(title="aorist-3pl-osan")
    path = Mock()
    path.relative_to.return_value = "grammar/aorist-3pl-osan.md"
    find_mock = Mock(return_value=[(path, concept)])
    monkeypatch.setattr(cli, "find_concepts", find_mock)
    monkeypatch.setattr(cli, "_repo_root", Mock(return_value="REPO_ROOT"))
    monkeypatch.setattr(
        sys, "argv",
        ["greek-knowledge", "query", "--type", "grammar", "--level", "advanced", "--author", "Sophocles"],
    )

    cli.main()

    find_mock.assert_called_once_with(
        "REPO_ROOT", type={"Grammatical Rule"}, level=["advanced"], period=None, dialect=None, author=["Sophocles"],
        work=None, language=None, verified=False,
    )
    out = capsys.readouterr().out
    assert "grammar/aorist-3pl-osan.md" in out
    assert "aorist-3pl-osan" in out


def _run_cli(monkeypatch, repo_root, *argv):
    monkeypatch.setattr(cli, "_repo_root", Mock(return_value=repo_root))
    monkeypatch.setattr(sys, "argv", ["greek-knowledge", *argv])
    cli.main()


def _query_kwargs(monkeypatch, *argv):
    """The keyword arguments `greek-knowledge query <argv>` hands to find_concepts()."""
    find_mock = Mock(return_value=[])
    monkeypatch.setattr(cli, "find_concepts", find_mock)
    _run_cli(monkeypatch, "REPO_ROOT", "query", *argv)
    return find_mock.call_args.kwargs


def test_cli_query_type_texts_covers_originals_and_translations(monkeypatch):
    assert _query_kwargs(monkeypatch, "--type", "texts")["type"] == {"Literary Text", "Literary Translation"}


def test_cli_query_passes_the_work_and_language_filters(monkeypatch):
    kwargs = _query_kwargs(monkeypatch, "--type", "texts", "--work", "ithaka", "--language", "ru", "--full")

    assert kwargs["work"] == ["ithaka"]
    assert kwargs["language"] == ["ru"]


@pytest.mark.parametrize(
    "argv, expected",
    [
        (["--language", "ru,en"], ["ru", "en"]),
        (["--language", "ru", "--language", "en"], ["ru", "en"]),
        (["--language", "ru,en", "--language", "el"], ["ru", "en", "el"]),
    ],
)
def test_cli_query_takes_several_values_by_comma_or_by_repeating_the_flag(monkeypatch, argv, expected):
    assert _query_kwargs(monkeypatch, *argv)["language"] == expected


def test_cli_query_takes_several_values_for_every_filter(monkeypatch):
    kwargs = _query_kwargs(
        monkeypatch,
        "--type", "grammar,texts", "--level", "A2", "--level", "B1", "--period", "homeric..attic,modern",
        "--dialect", "attic,ionic", "--author", "Murray,Pope", "--work", "ithaka,odyssey", "--language", "ru,en",
    )

    assert kwargs["type"] == {"Grammatical Rule", "Literary Translation", "Literary Text"}
    assert kwargs["level"] == ["A2", "B1"]
    assert kwargs["period"] == ["homeric..attic", "modern"]
    assert kwargs["dialect"] == ["attic", "ionic"]
    assert kwargs["author"] == ["Murray", "Pope"]
    assert kwargs["work"] == ["ithaka", "odyssey"]
    assert kwargs["language"] == ["ru", "en"]


def test_cli_query_keeps_a_comma_followed_by_a_space_inside_one_value(monkeypatch):
    kwargs = _query_kwargs(monkeypatch, "--work", "Kavafis, Ithaka", "--author", "Sophocles (1887), curated")

    assert kwargs["work"] == ["Kavafis, Ithaka"]
    assert kwargs["author"] == ["Sophocles (1887), curated"]


def test_cli_query_rejects_an_unknown_type_inside_a_list(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["greek-knowledge", "query", "--type", "grammar,not-a-real-type"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2
    assert "not-a-real-type" in capsys.readouterr().err


def test_cli_query_reports_when_nothing_found(monkeypatch, capsys):
    monkeypatch.setattr(cli, "find_concepts", Mock(return_value=[]))
    monkeypatch.setattr(cli, "_repo_root", Mock(return_value="REPO_ROOT"))
    monkeypatch.setattr(sys, "argv", ["greek-knowledge", "query", "--level", "C2"])

    cli.main()

    assert "No concepts match" in capsys.readouterr().out


def test_cli_query_full_flag_prints_bodies(monkeypatch, capsys):
    concept = Mock(title="aorist-3pl-osan", body="## The rule\n\nSome text.")
    path = Mock()
    path.relative_to.return_value = "grammar/aorist-3pl-osan.md"
    monkeypatch.setattr(cli, "find_concepts", Mock(return_value=[(path, concept)]))
    monkeypatch.setattr(cli, "_repo_root", Mock(return_value="REPO_ROOT"))
    monkeypatch.setattr(sys, "argv", ["greek-knowledge", "query", "--full"])

    cli.main()

    out = capsys.readouterr().out
    assert "Some text." in out


def test_cli_query_list_mode_prints_report_and_skips_find_concepts(monkeypatch, capsys):
    report = {"level": [("beginner", 15), ("advanced", 1)]}
    monkeypatch.setattr(cli, "list_mode_report", Mock(return_value=report))
    find_mock = Mock()
    monkeypatch.setattr(cli, "find_concepts", find_mock)
    monkeypatch.setattr(cli, "_repo_root", Mock(return_value="REPO_ROOT"))
    monkeypatch.setattr(sys, "argv", ["greek-knowledge", "query", "--level", "list"])

    cli.main()

    cli.list_mode_report.assert_called_once_with(
        "REPO_ROOT",
        {"type": None, "level": ["list"], "period": None, "dialect": None, "author": None, "work": None, "language": None},
        verified=False,
    )
    find_mock.assert_not_called()
    out = capsys.readouterr().out
    assert "-- level --" in out
    assert "beginner (15)" in out
    assert "advanced (1)" in out


def test_cli_query_rejects_unknown_type_shorthand(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["greek-knowledge", "query", "--type", "not-a-real-type"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_cli_query_verified_switch_reaches_find_concepts_and_defaults_to_off(monkeypatch):
    assert _query_kwargs(monkeypatch, "--type", "grammar", "--verified")["verified"] is True
    assert _query_kwargs(monkeypatch, "--type", "grammar")["verified"] is False


def test_cli_query_list_mode_passes_the_verified_scope(monkeypatch, capsys):
    monkeypatch.setattr(cli, "list_mode_report", Mock(return_value={"level": [("A2", 27)]}))
    monkeypatch.setattr(cli, "_repo_root", Mock(return_value="REPO_ROOT"))
    monkeypatch.setattr(sys, "argv", ["greek-knowledge", "query", "--level", "list", "--verified"])

    cli.main()

    assert cli.list_mode_report.call_args.kwargs == {"verified": True}
    assert "A2 (27)" in capsys.readouterr().out


def _write_rule(repo_root, slug="rule", body="## A rule\n\nA claim.[^src]"):
    concept = ConceptFile(
        type="Grammatical Rule",
        title=slug,
        description=f"Grammatical rule: {slug}",
        tags=[],
        level=["A2"],
        sources=[Source(id="src", resource="somewhere", title="A Source", author="Someone")],
        generated_by="human",
        body=body,
        extra_frontmatter={"periods_spanned": {"from": "modern", "to": "modern"}, "dialect": []},
    )
    path = repo_root / "grammar" / f"{slug}.md"
    okf.write(concept, path)
    return path


def test_cli_verify_pins_a_record_to_each_file_it_is_given(monkeypatch, capsys, tmp_path):
    first, second = _write_rule(tmp_path, "first"), _write_rule(tmp_path, "second")

    _run_cli(monkeypatch, tmp_path, "verify", str(first), str(second), "--by", "tester", "--against", "a source", "--against", "the corpus")

    for path in (first, second):
        concept = okf.read(path)
        assert [(entry["by"], entry["against"]) for entry in concept.verified] == [("tester", ["a source", "the corpus"])]
        assert okf.current_verification(concept) is not None
    assert capsys.readouterr().out.count("verified ") == 2


def test_cli_verify_accepts_a_directory(monkeypatch, tmp_path):
    _write_rule(tmp_path, "first")
    _write_rule(tmp_path, "second")

    _run_cli(monkeypatch, tmp_path, "verify", str(tmp_path / "grammar"), "--by", "tester", "--against", "a source")

    assert all(okf.read(tmp_path / "grammar" / f"{slug}.md").verified for slug in ("first", "second"))


def test_cli_verify_writes_nothing_when_any_file_fails_the_check(monkeypatch, capsys, tmp_path):
    good = _write_rule(tmp_path, "good")
    broken = _write_rule(tmp_path, "broken", body="## A rule\n\nA claim.[^src][^ghost]")

    with pytest.raises(SystemExit) as exc_info:
        _run_cli(monkeypatch, tmp_path, "verify", str(good), str(broken), "--by", "tester", "--against", "a source")

    assert exc_info.value.code == 1
    assert "ghost" in capsys.readouterr().out
    assert okf.read(good).verified == []
    assert okf.read(broken).verified == []


@pytest.mark.parametrize("missing", [["--against", "a source"], ["--by", "tester"]])
def test_cli_verify_requires_by_and_at_least_one_against(monkeypatch, tmp_path, missing):
    rule = _write_rule(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        _run_cli(monkeypatch, tmp_path, "verify", str(rule), *missing)

    assert exc_info.value.code == 2


def test_cli_check_is_silent_on_a_clean_corpus(monkeypatch, capsys, tmp_path):
    _write_rule(tmp_path)

    _run_cli(monkeypatch, tmp_path, "check")

    assert capsys.readouterr().out == ""


def test_cli_check_reports_a_stale_verification_and_exits_1(monkeypatch, capsys, tmp_path):
    rule = _write_rule(tmp_path)
    _run_cli(monkeypatch, tmp_path, "verify", str(rule), "--by", "tester", "--against", "a source")
    capsys.readouterr()
    rule.write_text(rule.read_text(encoding="utf-8").replace("A claim.", "Another claim."), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        _run_cli(monkeypatch, tmp_path, "check")

    assert exc_info.value.code == 1
    assert "grammar/rule.md: verified record is stale" in capsys.readouterr().out


def test_cli_check_fix_repairs_a_footnote_block_and_then_passes(monkeypatch, capsys, tmp_path):
    rule = _write_rule(tmp_path)
    rule.write_text(rule.read_text(encoding="utf-8").replace("[^src]: A Source", "[^src]: A Stale Title"), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        _run_cli(monkeypatch, tmp_path, "check")
    assert exc_info.value.code == 1
    capsys.readouterr()

    _run_cli(monkeypatch, tmp_path, "check", "--fix")

    assert capsys.readouterr().out == ""
    assert "A Stale Title" not in rule.read_text(encoding="utf-8")


def test_cli_check_can_be_scoped_to_one_file(monkeypatch, capsys, tmp_path):
    good = _write_rule(tmp_path, "good")
    broken = _write_rule(tmp_path, "broken", body="## A rule\n\nA claim.[^src][^ghost]")

    _run_cli(monkeypatch, tmp_path, "check", str(good))
    assert capsys.readouterr().out == ""

    with pytest.raises(SystemExit):
        _run_cli(monkeypatch, tmp_path, "check", str(broken))
    assert "ghost" in capsys.readouterr().out
