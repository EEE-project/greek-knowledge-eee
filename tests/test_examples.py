"""Every script in examples/ is a documented entry point (see the README) that shares okfbuild code (query, wiring, lookup,
lexical_entry); running it for real catches a signature change the unit tests of that code would miss."""

import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pytest

from okfbuild.concepts import lexical_entry
from okfbuild.query import find_concepts
from okfbuild.wiring import default_source_bundle

# A word that is not in the tracked caches in data/ would ask the network: a dead proxy turns that into a logged miss.
_OFFLINE = {
    **{name: "http://127.0.0.1:9" for name in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY")},
    "no_proxy": "", "NO_PROXY": "", "PYTHONIOENCODING": "utf-8",
}
_CASES = {
    "wire": ("wire_sources.py",),
    "lookup": ("lookup_word.py", "ὕδωρ"),
    "lookup_nothing": ("lookup_word.py", "ξξξξξ", "particle"),
    "lookup_usage": ("lookup_word.py",),
    "build": ("build_one_concept.py", "ὕδωρ"),
    "build_homeric": ("build_one_concept.py", "ὕδωρ", "noun", "homeric"),
    "build_nothing": ("build_one_concept.py", "ξξξξξ", "noun", "homeric"),
    "build_usage": ("build_one_concept.py",),
}
_LOOKUP_ORDER = [
    "eee_engine (homeric)", "eee_engine (attic)", "eee_engine (modern)", "morpheus", "lsj", "wiktextract", "byzantine_lexicon", "iecor",
]


def _run_query_example(repo_root, *args):
    result = subprocess.run(
        [sys.executable, str(repo_root / "examples" / "query_knowledge.py"), *args],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.splitlines()


def test_query_example_lists_the_same_concepts_as_find_concepts(repo_root):
    lines = _run_query_example(repo_root, "--type", "grammar", "--period", "modern", "--verified")

    expected = find_concepts(repo_root, type="Grammatical Rule", period="modern", verified=True)
    assert expected
    assert [line.split("  —  ")[0] for line in lines] == [str(path.relative_to(repo_root)) for path, _ in expected]


def test_query_example_prints_a_tally_scoped_by_verified(repo_root):
    lines = _run_query_example(repo_root, "--type", "grammar", "--period", "modern", "--verified", "--level", "list")

    assert lines[0] == "-- level --"
    assert len(lines) > 1 and all(re.fullmatch(r"\S.* \(\d+\)", line) for line in lines[1:])


@pytest.fixture(scope="module")
def example_runs(repo_root):
    """Each case once, 4 at a time: the runs are independent and spend most of their 3-4 s importing."""
    def run(case):
        script, *args = case
        return subprocess.run(
            [sys.executable, str(repo_root / "examples" / script), *args],
            capture_output=True, encoding="utf-8", env={**os.environ, **_OFFLINE}, timeout=120,
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(zip(_CASES, pool.map(run, _CASES.values())))


@pytest.fixture(scope="module")
def example_sources(repo_root):
    return default_source_bundle(repo_root)


@pytest.fixture
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise urllib.error.URLError("offline test")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)


def test_wire_example_reports_what_default_source_bundle_wires(repo_root, example_runs, example_sources):
    run = example_runs["wire"]

    assert run.returncode == 0, run.stderr
    lines = run.stdout.splitlines()
    assert len(lines) == 3
    assert lines[0] == f"SourceBundle wired from {repo_root}"
    assert lines[1].startswith(f"  byzantine_forms: {len(example_sources.byzantine_forms)} lemmas")
    assert lines[2] == f"  iecor: {len(example_sources.iecor)} headwords"


def test_lookup_example_prints_one_section_per_source_that_knows_the_word(example_runs):
    run = example_runs["lookup"]

    assert run.returncode == 0
    assert not re.findall(r"cache miss|request failed", run.stderr)  # ὕδωρ is in every tracked cache: nothing was fetched and nothing was missing
    sections = re.findall(r"^== (.+) ==$", run.stdout, re.M)
    assert sections == [name for name in _LOOKUP_ORDER if name in sections]
    assert {"eee_engine (homeric)", "eee_engine (attic)", "morpheus", "lsj", "iecor"} <= set(sections)
    assert "Proto-Indo-European" in run.stdout


def test_lookup_example_says_so_when_no_source_knows_the_word(example_runs):
    run = example_runs["lookup_nothing"]

    assert run.returncode == 0
    assert run.stdout == "No source has anything for 'ξξξξξ'.\n"


def test_build_example_prints_the_body_that_lexical_entry_builds(example_runs, example_sources, offline):
    expected = lexical_entry.build("ὕδωρ", "noun", ["homeric", "attic", "modern"], example_sources, level=[], tags=[]).body
    run = example_runs["build"]

    assert run.returncode == 0
    assert not re.findall(r"cache miss|request failed", run.stderr)
    assert "## Homeric" in expected and "## Etymology" in expected
    assert run.stdout == expected + "\n"


def test_build_example_builds_only_the_periods_it_is_given(example_runs, example_sources, offline):
    expected = lexical_entry.build("ὕδωρ", "noun", ["homeric"], example_sources, level=[], tags=[]).body
    run = example_runs["build_homeric"]

    assert run.returncode == 0
    assert run.stdout == expected + "\n"
    assert "## Homeric" in run.stdout and "## Attic" not in run.stdout and "## Modern" not in run.stdout


def test_build_example_says_so_when_no_source_has_data_for_the_word(example_runs):
    run = example_runs["build_nothing"]

    assert run.returncode == 0
    assert run.stdout == "No attested data for 'ξξξξξ' in any requested period/source.\n"


@pytest.mark.parametrize("case, script", [("lookup_usage", "lookup_word.py"), ("build_usage", "build_one_concept.py")])
def test_example_without_a_word_prints_its_usage_and_exits_1(example_runs, case, script):
    run = example_runs[case]

    assert run.returncode == 1
    assert run.stdout == ""
    assert f"usage: uv run python examples/{script}" in run.stderr
