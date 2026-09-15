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

import re

import pytest

from okfbuild import okf

pytestmark = pytest.mark.integration

_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def test_pilot_run_produces_all_three_concept_types(pilot_build_report, pilot_output_dir):
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

    found_types = set()
    for type_dir, expected_type in (
        ("words", "Lexical Entry"),
        ("grammar", "Grammatical Rule"),
        ("culture", "Cultural Context"),
    ):
        for path in (pilot_output_dir / type_dir).glob("*.md"):
            if path.name == "index.md":
                continue
            concept = okf.read(path)
            if concept is not None and concept.type == expected_type:
                found_types.add(expected_type)
                break

    assert found_types == {"Lexical Entry", "Grammatical Rule", "Cultural Context"}


def test_grammatical_rule_cites_newly_mined_osan_pattern(pilot_build_report, pilot_output_dir):
    rule_path = pilot_output_dir / "grammar" / "aorist-3pl-osan.md"
    assert rule_path.is_file()

    osan_forms = ("ἤλθοσαν", "ἐξήλθοσαν", "ἴδοσαν", "εἴδοσαν")
    # Each citation is one line ("{lemma} is replaced by {form} in ... Greek[^id]"),
    # not the form immediately adjacent to "[^" — check per-line, not a bare substring,
    # so this actually proves the citation is FOR that form, not merely present somewhere.
    lines = rule_path.read_text(encoding="utf-8").splitlines()
    assert any(form in line and "[^" in line for form in osan_forms for line in lines), lines


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


def test_cross_link_resolves_to_real_file(pilot_build_report, pilot_output_dir):
    culture_path = pilot_output_dir / "culture" / "cavafy.md"
    assert culture_path.is_file()

    text = culture_path.read_text(encoding="utf-8")
    links = _MARKDOWN_LINK_RE.findall(text)
    assert links, "expected at least one markdown link in culture/cavafy.md's body"

    resolved = [(culture_path.parent / target).resolve() for _label, target in links]
    assert any(path.is_file() for path in resolved), (links, resolved)
