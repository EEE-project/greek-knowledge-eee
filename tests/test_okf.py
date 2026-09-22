from dataclasses import replace

import pytest
import yaml

from okfbuild.okf import (
    ConceptFile,
    Source,
    body_digest,
    current_verification,
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


def _minimal_literary_translation() -> dict:
    fm = _minimal_common_fields()
    fm["type"] = "Literary Translation"
    fm["work"] = "Odyssey"
    fm["passage"] = "IX.19-38"
    fm["language"] = "en"
    fm["translators"] = ["Murray"]
    return fm


def _minimal_literary_text() -> dict:
    fm = _minimal_common_fields()
    fm["type"] = "Literary Text"
    fm["work"] = "Kavafis, Ithaka"
    fm["passage"] = "1-36"
    fm["language"] = "el"
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


def test_validate_accepts_minimal_literary_translation():
    validate_frontmatter(_minimal_literary_translation())


def test_validate_rejects_literary_translation_missing_translators():
    fm = _minimal_literary_translation()
    del fm["translators"]
    with pytest.raises(ValueError):
        validate_frontmatter(fm)


def test_validate_rejects_literary_translation_missing_work():
    fm = _minimal_literary_translation()
    del fm["work"]
    with pytest.raises(ValueError):
        validate_frontmatter(fm)


def test_validate_accepts_minimal_literary_text_without_translators():
    fm = _minimal_literary_text()
    assert "translators" not in fm

    validate_frontmatter(fm)


@pytest.mark.parametrize("field", ["work", "passage", "language"])
def test_validate_rejects_literary_text_missing_a_required_field(field):
    fm = _minimal_literary_text()
    del fm[field]
    with pytest.raises(ValueError, match="Literary Text requires"):
        validate_frontmatter(fm)


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


def test_render_leaves_a_resource_plain_when_no_path_is_given():
    """The default, path-less call every existing caller (and this test file)
    already makes must render exactly as before -- linking is opt-in."""
    concept = _minimal_concept(
        sources=[Source(id="src-1", resource="texts/kavafis_ithaki/text.md", title="Example", author="test")],
        body="A claim here[^src-1]",
    )
    rendered = render(concept)
    assert "[^src-1]: Example, test (texts/kavafis_ithaki/text.md)" in rendered


def _fake_repo(tmp_path):
    """A tmp_path with a pyproject.toml marker -- what render()'s repo-root
    detection looks for, matching this repo's own layout."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname = \"fake\"\n")
    return tmp_path


def test_render_links_an_internal_resource_that_exists_in_the_repo(tmp_path):
    repo_root = _fake_repo(tmp_path)
    (repo_root / "texts" / "kavafis_ithaki").mkdir(parents=True)
    (repo_root / "texts" / "kavafis_ithaki" / "text.md").write_text("the target file")
    path = repo_root / "culture" / "cavafy.md"
    path.parent.mkdir()
    concept = _minimal_concept(
        sources=[Source(id="src-1", resource="texts/kavafis_ithaki/text.md", title="Example", author="test")],
        body="A claim here[^src-1]",
    )

    rendered = render(concept, path=path)

    assert "[^src-1]: Example, test ([texts/kavafis_ithaki/text.md](../texts/kavafis_ithaki/text.md))" in rendered


def test_render_leaves_an_external_url_resource_plain_even_with_a_path(tmp_path):
    repo_root = _fake_repo(tmp_path)
    path = repo_root / "culture" / "cavafy.md"
    path.parent.mkdir()
    concept = _minimal_concept(
        sources=[Source(id="src-1", resource="https://example.com/page", title="Example", author="test")],
        body="A claim here[^src-1]",
    )

    rendered = render(concept, path=path)

    assert "[^src-1]: Example, test (https://example.com/page)" in rendered
    assert "[https://example.com/page]" not in rendered


def test_render_leaves_a_resource_plain_when_it_matches_no_real_file_in_the_repo(tmp_path):
    repo_root = _fake_repo(tmp_path)
    path = repo_root / "culture" / "cavafy.md"
    path.parent.mkdir()
    concept = _minimal_concept(
        sources=[Source(id="src-1", resource="lectures/Palaestra/nonexistent.md", title="Example", author="test")],
        body="A claim here[^src-1]",
    )

    rendered = render(concept, path=path)

    assert "[^src-1]: Example, test (lectures/Palaestra/nonexistent.md)" in rendered


def test_render_leaves_an_absolute_path_resource_plain_even_if_it_exists(tmp_path):
    """A citation to a file outside the repo (e.g. a private local lecture
    copy) must never become a link -- it wouldn't resolve for anyone else,
    or in the repo's own published rendering."""
    repo_root = _fake_repo(tmp_path)
    path = repo_root / "culture" / "cavafy.md"
    path.parent.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("exists, but outside the repo")
    concept = _minimal_concept(
        sources=[Source(id="src-1", resource=str(outside), title="Example", author="test")],
        body="A claim here[^src-1]",
    )

    rendered = render(concept, path=path)

    assert f"[^src-1]: Example, test ({outside})" in rendered


def test_render_computes_a_correct_relative_path_across_sibling_directories(tmp_path):
    repo_root = _fake_repo(tmp_path)
    (repo_root / "words").mkdir()
    (repo_root / "words" / "νόστος.md").write_text("the target file")
    path = repo_root / "grammar" / "some-rule.md"
    path.parent.mkdir()
    concept = _minimal_concept(
        sources=[Source(id="src-1", resource="words/νόστος.md", title="Example", author="test")],
        body="A claim here[^src-1]",
    )

    rendered = render(concept, path=path)

    assert "([words/νόστος.md](../words/νόστος.md))" in rendered


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


def _set_verified(path, entries):
    """Rewrite `path`'s frontmatter with a hand-edited `verified:` list, as a human editing the file would."""
    _, yaml_text, body_text = path.read_text().split("---\n", 2)
    frontmatter = yaml.safe_load(yaml_text)
    frontmatter["verified"] = entries
    path.write_text("---\n" + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False) + "---\n" + body_text)


def test_write_preserves_manually_added_verified_entry(tmp_path):
    concept = _minimal_concept(body="original body")
    path = tmp_path / "test.md"
    write(concept, path)

    _set_verified(path, [{"by": "human:x", "at": "2026-01-01T00:00:00+00:00"}])

    concept2 = _minimal_concept(body="CHANGED body")
    write(concept2, path)

    final_text = path.read_text()
    _, final_yaml, _ = final_text.split("---\n", 2)
    final_frontmatter = yaml.safe_load(final_yaml)
    assert final_frontmatter["verified"] == [{"by": "human:x", "at": "2026-01-01T00:00:00+00:00"}]


# --- verification records: pinned to the text they were recorded for ---


def _verification_entry(body: str) -> dict:
    return {"by": "tester", "at": "2026-09-21", "against": ["a source"], "body_sha256": body_digest(body)}


def test_body_digest_is_a_sha256_that_ignores_only_trailing_newlines():
    assert len(body_digest("## A\n\ntext")) == 64
    assert body_digest("## A\n\ntext\n\n") == body_digest("## A\n\ntext")
    assert body_digest("## A\n\ntext") != body_digest("## A\n\ntext!")


def test_read_returns_the_verified_entries_of_a_file(tmp_path):
    path = tmp_path / "test.md"
    write(_minimal_concept(body="claim"), path)
    entry = _verification_entry("claim")
    _set_verified(path, [entry])

    assert read(path).verified == [entry]


def test_read_of_a_file_without_verified_entries_returns_an_empty_list(tmp_path):
    path = tmp_path / "test.md"
    write(_minimal_concept(), path)

    assert read(path).verified == []


def test_render_writes_the_verified_entries_a_concept_carries():
    entry = _verification_entry("claim")

    text = render(_minimal_concept(body="claim", verified=[entry]))

    assert yaml.safe_load(text.split("---\n", 2)[1])["verified"] == [entry]


def test_current_verification_matches_only_the_text_it_was_recorded_for():
    concept = _minimal_concept(body="claim")
    entry = _verification_entry("claim")

    assert current_verification(concept) is None
    assert current_verification(replace(concept, verified=[entry])) == entry
    assert current_verification(replace(concept, body="claim\n", verified=[entry])) == entry
    assert current_verification(replace(concept, body="a different claim", verified=[entry])) is None


def test_current_verification_ignores_entries_that_are_not_mappings():
    concept = _minimal_concept(body="claim", verified=["human:x", {"by": "old", "at": "2026-01-01"}])

    assert current_verification(concept) is None


def test_validate_rejects_a_verified_field_that_is_not_a_list():
    frontmatter = _minimal_grammatical_rule()
    frontmatter["verified"] = "yes"

    with pytest.raises(ValueError, match="verified"):
        validate_frontmatter(frontmatter)


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
