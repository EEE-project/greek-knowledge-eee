"""Section-07 pilot acceptance tests: run the real pipeline against the
real Odyssey/Kavafis Ithaki course content, not fixtures — see
plans/sections/section-07-pilot.md. Writes to pilot_output_dir, a scratch
directory (see that fixture's docstring in conftest.py) -- NOT this
repo's own words/, grammar/, culture/. To actually refresh those, use
`greek-knowledge regenerate --write` (okfbuild/cli.py) instead, and
review the resulting `git diff` before committing.

Excluded from the default `uv run pytest` gate for the same reason
eee-project excludes its own "integration" marker: this module needs real
network access, a real sibling-repo checkout, and real multi-hundred-MB
local data. Run explicitly: `uv run pytest -m integration`.
"""

import pytest

from okfbuild import okf

pytestmark = pytest.mark.integration


def test_pilot_run_produces_lexical_entries(pilot_build_report, pilot_output_dir):
    # pipeline.run()'s own contract is per-candidate isolation, not
    # zero-failure: a handful of the 500+ auto-extracted real-course
    # candidates are expected to fail (rare/dialectal Homeric words with
    # no coverage in any lexicon; a known modern_greek_inflexion_eee
    # IndexError on certain short pronoun lemmas queried against the
    # modern-period backend — see section-07-pilot.md's doc update for the
    # full breakdown). A large-scale failure (e.g. a wiring bug breaking
    # every candidate) would blow well past this ratio.
    total = pilot_build_report.written + pilot_build_report.unchanged + pilot_build_report.failed
    assert pilot_build_report.failed < total * 0.1, pilot_build_report.errors

    found = False
    for path in (pilot_output_dir / "words").glob("*.md"):
        if path.name == "index.md":
            continue
        concept = okf.read(path)
        if concept is not None and concept.type == "Lexical Entry":
            found = True
            break

    assert found


def test_wiktextract_lookups_are_cached_not_just_in_memory(pilot_build_report, repo_root):
    # Proves the real fixture wiring uses CachedWiktextractIndex (not
    # WiktextractIndex.load(), which never touches disk) -- a regression
    # here wouldn't be caught by wiktextract_index.py's own unit tests,
    # which construct CachedWiktextractIndex directly, not via conftest.py.
    cache_dir = repo_root / "data" / "wiktextract-cache"
    assert cache_dir.is_dir() and any(cache_dir.glob("*.json")), (
        "expected data/wiktextract-cache/ to hold at least one resolved lemma "
        "after a real pilot run"
    )
