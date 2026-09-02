from dataclasses import replace

import pytest
import yaml

from okfbuild.okf import (
    ConceptFile,
    Source,
    read,
    render,
    resolve_slug,
    validate_frontmatter,
    write,
)


def _minimal_common_fields() -> dict:
    return {
        "title": "Test Concept",
        "description": "A test concept.",
        "tags": ["test"],
        "level": ["B1"],
        "sources": [
            {"id": "src-1", "resource": "https://example.com", "title": "Example", "author": "test"}
        ],
        "generated": {"by": "process:test", "at": "2026-01-01T00:00:00+00:00"},
        "verified": [],
        "status": "draft",
    }


def _minimal_lexical_entry() -> dict:
    fm = _minimal_common_fields()
    fm["type"] = "Lexical Entry"
    fm["lemma"] = "test"
    fm["periods"] = ["modern"]
    return fm


def _minimal_grammatical_rule() -> dict:
    fm = _minimal_common_fields()
    fm["type"] = "Grammatical Rule"
    fm["periods_spanned"] = {"from": "attic", "to": "byzantine"}
    return fm


def _minimal_cultural_context() -> dict:
    fm = _minimal_common_fields()
    fm["type"] = "Cultural Context"
    fm["related_words"] = ["test"]
    fm["related_lessons"] = ["course/1"]
    return fm


def _minimal_concept(**overrides) -> ConceptFile:
    defaults = dict(
        type="Lexical Entry",
        title="test",
        description="test",
        tags=[],
        level=["B1"],
        sources=[],
        generated_by="process:test",
        body="body text",
        extra_frontmatter={"lemma": "test", "periods": ["modern"]},
    )
    defaults.update(overrides)
    return ConceptFile(**defaults)


# --- Frontmatter validation ---


def test_validate_accepts_minimal_lexical_entry():
    validate_frontmatter(_minimal_lexical_entry())


def test_validate_accepts_minimal_grammatical_rule():
    validate_frontmatter(_minimal_grammatical_rule())


def test_validate_rejects_list_shaped_periods_spanned():
    fm = _minimal_grammatical_rule()
    fm["periods_spanned"] = [{"from": "attic", "to": "byzantine"}]
    with pytest.raises(ValueError):
        validate_frontmatter(fm)


def test_validate_accepts_minimal_cultural_context():
    validate_frontmatter(_minimal_cultural_context())


def test_validate_rejects_missing_type():
    fm = _minimal_lexical_entry()
    del fm["type"]
    with pytest.raises(ValueError):
        validate_frontmatter(fm)


def test_validate_rejects_level_as_bare_string():
    fm = _minimal_lexical_entry()
    fm["level"] = "B1"
    with pytest.raises(ValueError):
        validate_frontmatter(fm)


# --- render() ---


def test_render_produces_valid_frontmatter_and_body():
    concept = _minimal_concept(
        title="νόστος",
        description="Return, homecoming.",
        body="## Homeric\n\nAttested in the Odyssey.",
    )
    rendered = render(concept)
    assert rendered.startswith("---\n")
    _, yaml_text, _ = rendered.split("---\n", 2)
    frontmatter = yaml.safe_load(yaml_text)
    assert frontmatter["type"] == "Lexical Entry"
    assert "Attested in the Odyssey" in rendered


def test_render_includes_footnote_block_per_source():
    concept = _minimal_concept(
        sources=[Source(id="src-1", resource="https://example.com", title="Example Source", author="test")],
        body="A claim here[^src-1]",
    )
    rendered = render(concept)
    assert "[^src-1]:" in rendered


def test_render_does_not_duplicate_footnote_when_body_already_has_one():
    """A body already ending with a footnote-definitions block (e.g. from
    read() reconstructing a ConceptFile that was rendered once before) must
    not get a second block appended on top -- the real-world trigger is
    pipeline.py's pruning step: read() an existing file, flip `status`, and
    write() it back unchanged otherwise."""
    concept = _minimal_concept(
        sources=[Source(id="src-1", resource="https://example.com", title="Example Source", author="test")],
        body="A claim here[^src-1]\n\n[^src-1]: Example Source, test (https://example.com)\n",
    )
    rendered = render(concept)
    assert rendered.count("[^src-1]:") == 1


# --- write() ---


def test_write_creates_new_file_returns_true(tmp_path):
    concept = _minimal_concept(body="body text")
    path = tmp_path / "test.md"

    result = write(concept, path)

    assert result is True
    assert path.exists()
    assert "body text" in path.read_text()


def test_write_twice_unchanged_returns_false_second_time(tmp_path):
    concept = _minimal_concept(body="body text")
    path = tmp_path / "test.md"
    write(concept, path)
    mtime_before = path.stat().st_mtime_ns
    content_before = path.read_text()

    result = write(concept, path)

    assert result is False
    assert path.stat().st_mtime_ns == mtime_before
    assert path.read_text() == content_before


def test_write_handles_malformed_existing_file_gracefully(tmp_path):
    """A malformed existing file at the target path (e.g. a broken `---`
    fence from a bad human edit, or an unrelated file) must not crash
    write() — it should be treated as if no valid existing file was there."""
    path = tmp_path / "test.md"
    path.write_text("not a valid OKF file at all, no frontmatter fence here")

    concept = _minimal_concept(body="new body")
    result = write(concept, path)

    assert result is True
    assert "new body" in path.read_text()


def test_write_rewrite_via_read_does_not_duplicate_footnote(tmp_path):
    """End-to-end regression for the real pipeline.py pruning path: build a
    concept with a real citation, write it, read() it back, change an
    unrelated field (mirroring the status flip _prune() does), and write()
    again -- the footnote must still appear exactly once, not twice."""
    concept = _minimal_concept(
        sources=[Source(id="src-1", resource="https://example.com", title="Example Source", author="test")],
        body="A claim here[^src-1]",
    )
    path = tmp_path / "test.md"
    write(concept, path)
    assert path.read_text().count("[^src-1]:") == 1

    reread = read(path)
    modified = replace(reread, extra_frontmatter={**reread.extra_frontmatter, "status": "deprecated"})
    write(modified, path)

    assert path.read_text().count("[^src-1]:") == 1


def test_write_preserves_manually_added_verified_entry(tmp_path):
    concept = _minimal_concept(body="original body")
    path = tmp_path / "test.md"
    write(concept, path)

    text = path.read_text()
    _, yaml_text, body_text = text.split("---\n", 2)
    frontmatter = yaml.safe_load(yaml_text)
    frontmatter["verified"] = [{"by": "human:x", "at": "2026-01-01T00:00:00+00:00"}]
    new_text = "---\n" + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False) + "---\n" + body_text
    path.write_text(new_text)

    concept2 = _minimal_concept(body="CHANGED body")
    write(concept2, path)

    final_text = path.read_text()
    _, final_yaml, _ = final_text.split("---\n", 2)
    final_frontmatter = yaml.safe_load(final_yaml)
    assert final_frontmatter["verified"] == [{"by": "human:x", "at": "2026-01-01T00:00:00+00:00"}]


# --- resolve_slug() ---


def test_resolve_slug_disambiguates_on_collision(tmp_path):
    concept = _minimal_concept(extra_frontmatter={"lemma": "lemma A", "periods": ["modern"]})
    write(concept, tmp_path / "slug.md")

    resolved = resolve_slug(tmp_path, "slug", lemma="lemma B")

    assert resolved != "slug"


def test_resolve_slug_unchanged_for_same_lemma_rewrite(tmp_path):
    concept = _minimal_concept(extra_frontmatter={"lemma": "lemma A", "periods": ["modern"]})
    write(concept, tmp_path / "slug.md")

    resolved = resolve_slug(tmp_path, "slug", lemma="lemma A")

    assert resolved == "slug"


# --- read() ---


def test_read_roundtrips_a_written_concept(tmp_path):
    path = tmp_path / "test.md"
    concept = _minimal_concept(body="original body")
    write(concept, path)

    result = read(path)

    assert result.type == "Lexical Entry"
    assert result.body == "original body"
    assert result.extra_frontmatter["lemma"] == "test"
    assert result.sources == []


def test_read_returns_none_for_missing_file(tmp_path):
    assert read(tmp_path / "does-not-exist.md") is None


def test_read_returns_none_for_malformed_existing_file(tmp_path):
    path = tmp_path / "test.md"
    path.write_text("not a valid OKF file at all, no frontmatter fence here")

    assert read(path) is None


def test_read_returns_none_for_empty_frontmatter_block(tmp_path):
    """A file whose frontmatter fence is present but empty (`---\\n---\\nbody`)
    parses as YAML `None`, not a dict — read() must treat this the same as
    any other unparseable existing file, not crash on the missing keys."""
    path = tmp_path / "test.md"
    path.write_text("---\n---\nbody\n")

    assert read(path) is None


def test_read_returns_none_for_frontmatter_missing_a_required_field(tmp_path):
    """A valid-YAML frontmatter block that's missing a field every concept
    requires (e.g. a human hand-edit deleted `sources:`) must not crash."""
    path = tmp_path / "test.md"
    path.write_text("---\ntitle: test\n---\nbody\n")

    assert read(path) is None
