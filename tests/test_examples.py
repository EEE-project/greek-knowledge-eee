"""examples/query_knowledge.py is a documented entry point (see the README) that shares okfbuild.query's
argument and filter code; running it for real catches a signature change the unit tests of that code would miss."""

import re
import subprocess
import sys

from okfbuild.query import find_concepts


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
