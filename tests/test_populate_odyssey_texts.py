"""Tests for scripts/populate_odyssey_texts.py -- the previously-untested,
re-runnable script that assembles texts/odyssey/*.md from hand-extracted
translator sections (see that module's own docstring)."""

from pathlib import Path

import yaml

import eee_project as eee
from scripts import populate_odyssey_texts as script

_GENERATED_FILES = [
    "translations_en.md",
    "translations_ru.md",
    "translations_el.md",
    "interlinear_en.md",
    "interlinear_el.md",
]


def _split(path: Path) -> tuple[dict, str]:
    _, yaml_text, body = path.read_text().split("---\n", 2)
    return yaml.safe_load(yaml_text), body


def _without_generated_at(frontmatter: dict) -> dict:
    fm = dict(frontmatter)
    fm["generated"] = {k: v for k, v in fm["generated"].items() if k != "at"}
    return fm


# --- Full corpus regeneration matches what's committed ---


def test_populate_all_matches_committed_content(tmp_path, monkeypatch):
    """Regenerating the whole corpus into a scratch directory must produce
    content identical to what's committed under texts/odyssey/ -- other
    than the `generated.at` timestamp, which is expected to differ.

    _TEXTS_DIR is read from the module's globals at call time inside each
    populate_*() function, so patching the module attribute (rather than
    passing a directory argument) is enough to redirect every write()
    without any production-code change.
    """
    real_texts_dir = script._TEXTS_DIR
    monkeypatch.setattr(script, "_TEXTS_DIR", tmp_path)

    script.populate_translations_en()
    script.populate_translations_ru()
    script.populate_translations_el()
    script.populate_interlinear()

    for filename in _GENERATED_FILES:
        generated_fm, generated_body = _split(tmp_path / filename)
        committed_fm, committed_body = _split(real_texts_dir / filename)
        assert _without_generated_at(generated_fm) == _without_generated_at(committed_fm), filename
        assert generated_body == committed_body, filename


# --- _strip_header() ---


def test_strip_header_strips_header_comments_and_blank_lines():
    """The exact bug class Task 4 found by hand: a second `## Header`
    section merged under a prior one must have its header line, comment
    line(s), and surrounding blank lines fully stripped, leaving only the
    `### `-prefixed stanza content -- this is the regression test that
    would have caught the original bug."""
    section = (
        "## Header\n"
        "\n"
        "<!-- plain citation line -->\n"
        "<!-- **bold description** -->\n"
        "\n"
        "### Stanza 1\n"
        "\n"
        "line one\n"
        "line two\n"
    )

    result = script._strip_header(section)

    assert result == "### Stanza 1\n\nline one\nline two"


# --- Fix 1 regression: merged Πολυλάς description covers both editions ---


def test_polylas_description_covers_both_editions():
    """_POLYLAS_I's description is the ONE surviving citation line for the
    merged Πολυλάς section (_strip_header drops _POLYLAS_IX's own header) --
    it must name both the 1875 (I.1-21) and 1877 (IX.19-38) editions, since
    4 of the merged section's 8 stanzas are actually from the 1877 edition."""
    body = script._POLYLAS_I.rstrip("\n") + "\n\n" + script._strip_header(script._POLYLAS_IX) + "\n"

    stanzas, descriptions = eee.parse_stanza_translations(body)

    assert len(stanzas["Πολυλάς"]) == 8
    assert "1875" in descriptions["Πολυλάς"]
    assert "1877" in descriptions["Πολυλάς"]
