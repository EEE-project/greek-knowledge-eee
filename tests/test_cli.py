"""Tests for okfbuild.cli's argument parsing and subcommand dispatch.
Both default_source_bundle and the underlying lookup_word/lexical_entry.build
are mocked -- this module tests dispatch and output formatting only, not
real source data (see tests/test_wiring.py / tests/test_lookup.py for that)."""

import sys
from unittest.mock import Mock

from okfbuild import cli


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
        "REPO_ROOT", type="Grammatical Rule", level="advanced", period=None, dialect=None, author="Sophocles",
    )
    out = capsys.readouterr().out
    assert "grammar/aorist-3pl-osan.md" in out
    assert "aorist-3pl-osan" in out


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


def test_cli_query_rejects_unknown_type_shorthand(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["greek-knowledge", "query", "--type", "not-a-real-type"])

    try:
        cli.main()
        assert False, "expected SystemExit"
    except SystemExit as exc:
        assert exc.code == 2
