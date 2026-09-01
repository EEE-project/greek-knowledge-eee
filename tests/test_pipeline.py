import csv
import logging
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from okfbuild.concepts import GENERATED_BY
from okfbuild.okf import ConceptFile
from okfbuild.pipeline import run
from okfbuild.sources.llm_gap_filler import (
    GapFillCache,
    GapFillerConfig,
    LLMModelConfig,
)


def _write_vocabulary_tsv(course_dir: Path, rows: list[dict]) -> None:
    course_dir.mkdir(parents=True, exist_ok=True)
    with (course_dir / "vocabulary.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["lemma", "pos", "level", "tags"], delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _read_frontmatter(path: Path) -> dict:
    _, yaml_text, _ = path.read_text().split("---\n", 2)
    return yaml.safe_load(yaml_text)


def test_run_writes_expected_concept_files(tmp_path, make_source_bundle):
    course_dir = tmp_path / "course"
    _write_vocabulary_tsv(course_dir, [{"lemma": "νόστος", "pos": "noun", "level": "B1", "tags": "epic"}])
    out_dir = tmp_path / "out"
    sources = make_source_bundle(attested_lemmas={"νόστος"})

    report = run([course_dir], out_dir, sources)

    concept_path = out_dir / "words" / "νόστος.md"
    assert concept_path.exists()
    frontmatter = _read_frontmatter(concept_path)
    assert frontmatter["type"] == "Lexical Entry"
    assert frontmatter["lemma"] == "νόστος"
    assert report.written == 1
    assert report.failed == 0


def test_run_pruning_marks_removed_word_deprecated_not_deleted(tmp_path, make_source_bundle):
    course_dir = tmp_path / "course"
    _write_vocabulary_tsv(
        course_dir,
        [
            {"lemma": "νόστος", "pos": "noun", "level": "B1", "tags": ""},
            {"lemma": "ἄνθρωπος", "pos": "noun", "level": "B1", "tags": ""},
        ],
    )
    out_dir = tmp_path / "out"
    sources = make_source_bundle(attested_lemmas={"νόστος", "ἄνθρωπος"})

    run([course_dir], out_dir, sources)
    removed_path = out_dir / "words" / "ἄνθρωπος.md"
    assert removed_path.exists()
    assert _read_frontmatter(removed_path)["status"] == "draft"

    _write_vocabulary_tsv(course_dir, [{"lemma": "νόστος", "pos": "noun", "level": "B1", "tags": ""}])
    report = run([course_dir], out_dir, sources)

    assert removed_path.exists()
    frontmatter = _read_frontmatter(removed_path)
    assert frontmatter["status"] == "deprecated"
    assert report.written == 1  # only the now-deprecated file changed; νόστος is unchanged
    assert report.unchanged == 1


def test_run_prune_isolates_malformed_existing_file(tmp_path, make_source_bundle):
    """A pre-existing, hand-corrupted concept file under words/ that isn't
    touched this run must not crash the whole pipeline during pruning — an
    empty frontmatter block parses as YAML None, not a dict, which must be
    recorded as a failure rather than raising out of run()."""
    course_dir = tmp_path / "course"
    _write_vocabulary_tsv(course_dir, [{"lemma": "νόστος", "pos": "noun", "level": "B1", "tags": ""}])
    out_dir = tmp_path / "out"
    words_dir = out_dir / "words"
    words_dir.mkdir(parents=True)
    (words_dir / "broken.md").write_text("---\n---\nempty frontmatter block\n")
    sources = make_source_bundle(attested_lemmas={"νόστος"})

    report = run([course_dir], out_dir, sources)

    assert (out_dir / "words" / "νόστος.md").exists()
    assert report.failed == 1
    assert "broken.md" in report.errors[0]


def test_run_build_report_counts_and_isolates_failures(tmp_path, make_source_bundle):
    course_dir = tmp_path / "course"
    _write_vocabulary_tsv(
        course_dir,
        [
            {"lemma": "νόστος", "pos": "noun", "level": "B1", "tags": ""},
            {"lemma": "ἄγνωστος", "pos": "adj", "level": "B1", "tags": ""},
        ],
    )
    out_dir = tmp_path / "out"
    sources = make_source_bundle(attested_lemmas={"νόστος"})  # ἄγνωστος gets no data anywhere

    report = run([course_dir], out_dir, sources)

    assert report.written == 1
    assert report.failed == 1
    assert len(report.errors) == 1
    assert not (out_dir / "words" / "ἄγνωστος.md").exists()


def test_run_passes_each_candidates_source_course_to_lexical_entry_build(tmp_path, make_source_bundle):
    course_a = tmp_path / "odyssey"
    course_b = tmp_path / "other-course"
    _write_vocabulary_tsv(course_a, [{"lemma": "νόστος", "pos": "noun", "level": "", "tags": ""}])
    _write_vocabulary_tsv(course_b, [{"lemma": "φίλος", "pos": "noun", "level": "", "tags": ""}])
    out_dir = tmp_path / "out"
    sources = make_source_bundle(attested_lemmas={"νόστος", "φίλος"})

    def fake_build(lemma, pos, periods, sources, level, tags, beekes_citation=None, source_course=None):
        return ConceptFile(
            type="Lexical Entry",
            title=lemma,
            description="",
            tags=tags,
            level=level,
            sources=[],
            generated_by=GENERATED_BY,
            body="",
            extra_frontmatter={"lemma": lemma, "periods": ["homeric"]},
        )

    with patch("okfbuild.pipeline.lexical_entry.build", side_effect=fake_build) as mock_build:
        run([course_a, course_b], out_dir, sources)

    passed_source_courses = {call.kwargs["source_course"] for call in mock_build.call_args_list}
    assert passed_source_courses == {"odyssey", "other-course"}


def _gap_filler():
    return GapFillerConfig(models=(LLMModelConfig(name="a", model="gpt-4o-mini", api_key_env="TEST_LLM_KEY"),))


def test_run_shares_one_gap_fill_cache_across_all_candidates(tmp_path, make_source_bundle):
    course_a = tmp_path / "odyssey"
    course_b = tmp_path / "other-course"
    _write_vocabulary_tsv(course_a, [{"lemma": "νόστος", "pos": "noun", "level": "", "tags": ""}])
    _write_vocabulary_tsv(course_b, [{"lemma": "φίλος", "pos": "noun", "level": "", "tags": ""}])
    out_dir = tmp_path / "out"
    sources = make_source_bundle(attested_lemmas={"νόστος", "φίλος"}, llm_gap_filler=_gap_filler())

    def fake_build(lemma, pos, periods, sources, level, tags, beekes_citation=None, source_course=None, cache=None):
        return ConceptFile(
            type="Lexical Entry",
            title=lemma,
            description="",
            tags=tags,
            level=level,
            sources=[],
            generated_by=GENERATED_BY,
            body="",
            extra_frontmatter={"lemma": lemma, "periods": ["homeric"]},
        )

    with patch("okfbuild.pipeline.lexical_entry.build", side_effect=fake_build) as mock_build:
        run([course_a, course_b], out_dir, sources)

    cache_args = [call.kwargs["cache"] for call in mock_build.call_args_list]
    assert len(cache_args) == 2
    assert cache_args[0] is not None
    assert cache_args[0] is cache_args[1]


def test_run_never_constructs_gap_fill_cache_when_llm_gap_filler_unset(tmp_path, make_source_bundle):
    course_dir = tmp_path / "course"
    _write_vocabulary_tsv(course_dir, [{"lemma": "νόστος", "pos": "noun", "level": "", "tags": ""}])
    out_dir = tmp_path / "out"
    sources = make_source_bundle(attested_lemmas={"νόστος"})  # llm_gap_filler=None (default)

    with patch("okfbuild.pipeline.GapFillCache", wraps=GapFillCache) as mock_cache_cls:
        run([course_dir], out_dir, sources)

    mock_cache_cls.assert_not_called()


def test_run_with_llm_gap_filler_but_no_cache_dir_never_persists(tmp_path, make_source_bundle):
    course_dir = tmp_path / "course"
    _write_vocabulary_tsv(course_dir, [{"lemma": "νόστος", "pos": "noun", "level": "", "tags": ""}])
    out_dir = tmp_path / "out"
    sources = make_source_bundle(attested_lemmas={"νόστος"}, llm_gap_filler=_gap_filler())

    with (
        patch.object(GapFillCache, "load") as mock_load,
        patch.object(GapFillCache, "save") as mock_save,
    ):
        run([course_dir], out_dir, sources)  # gap_fill_cache_dir omitted

    mock_load.assert_not_called()
    mock_save.assert_not_called()


def test_run_with_cache_dir_and_no_prior_run_uses_a_fresh_run_id(tmp_path, make_source_bundle):
    course_dir = tmp_path / "course"
    _write_vocabulary_tsv(course_dir, [{"lemma": "νόστος", "pos": "noun", "level": "", "tags": ""}])
    out_dir = tmp_path / "out"
    cache_dir = tmp_path / "cache-dir"
    sources = make_source_bundle(attested_lemmas={"νόστος"}, llm_gap_filler=_gap_filler())

    assert not (cache_dir / ".gap_fill_runs").exists()  # nothing to resume before the call

    with patch("okfbuild.pipeline.GapFillCache.load", wraps=GapFillCache.load) as mock_load:
        run([course_dir], out_dir, sources, gap_fill_cache_dir=cache_dir)

    mock_load.assert_called_once()
    (loaded_path,) = mock_load.call_args.args
    assert loaded_path.parent.parent == cache_dir / ".gap_fill_runs"


def test_run_with_cache_dir_resumes_existing_incomplete_run(tmp_path, make_source_bundle):
    course_dir = tmp_path / "course"
    _write_vocabulary_tsv(course_dir, [{"lemma": "νόστος", "pos": "noun", "level": "", "tags": ""}])
    out_dir = tmp_path / "out"
    cache_dir = tmp_path / "cache-dir"
    sources = make_source_bundle(attested_lemmas={"νόστος"}, llm_gap_filler=_gap_filler())

    existing_run_dir = cache_dir / ".gap_fill_runs" / "existing-run-id"
    existing_run_dir.mkdir(parents=True)
    seed_cache = GapFillCache()
    seed_cache.request_count = 5
    seed_cache.save(existing_run_dir / "cache.json")

    with patch("okfbuild.pipeline.GapFillCache.load", wraps=GapFillCache.load) as mock_load:
        run([course_dir], out_dir, sources, gap_fill_cache_dir=cache_dir)

    mock_load.assert_called_once()
    (loaded_path,) = mock_load.call_args.args
    assert loaded_path == existing_run_dir / "cache.json"


def test_run_with_cache_dir_removes_cache_file_on_success(tmp_path, make_source_bundle):
    course_dir = tmp_path / "course"
    _write_vocabulary_tsv(course_dir, [{"lemma": "νόστος", "pos": "noun", "level": "", "tags": ""}])
    out_dir = tmp_path / "out"
    cache_dir = tmp_path / "cache-dir"
    sources = make_source_bundle(attested_lemmas={"νόστος"}, llm_gap_filler=_gap_filler())

    run([course_dir], out_dir, sources, gap_fill_cache_dir=cache_dir)

    runs_dir = cache_dir / ".gap_fill_runs"
    assert list(runs_dir.rglob("cache.json")) == []


def test_run_two_successive_successful_runs_use_different_run_ids(tmp_path, make_source_bundle):
    course_dir = tmp_path / "course"
    _write_vocabulary_tsv(course_dir, [{"lemma": "νόστος", "pos": "noun", "level": "", "tags": ""}])
    out_dir = tmp_path / "out"
    cache_dir = tmp_path / "cache-dir"
    sources = make_source_bundle(attested_lemmas={"νόστος"}, llm_gap_filler=_gap_filler())

    with patch("okfbuild.pipeline.GapFillCache.load", wraps=GapFillCache.load) as mock_load:
        run([course_dir], out_dir, sources, gap_fill_cache_dir=cache_dir)
        first_path = mock_load.call_args.args[0]

        run([course_dir], out_dir, sources, gap_fill_cache_dir=cache_dir)
        second_path = mock_load.call_args.args[0]

    assert first_path != second_path
    assert first_path.parent != second_path.parent


def test_run_exception_propagates_and_leaves_final_checkpoint_for_resume(tmp_path, make_source_bundle):
    course_dir = tmp_path / "course"
    _write_vocabulary_tsv(course_dir, [{"lemma": "νόστος", "pos": "noun", "level": "", "tags": ""}])
    out_dir = tmp_path / "out"
    cache_dir = tmp_path / "cache-dir"
    sources = make_source_bundle(attested_lemmas={"νόστος"}, llm_gap_filler=_gap_filler())

    with (
        patch("okfbuild.pipeline._collect_lexical_candidates", side_effect=RuntimeError("boom")),
        pytest.raises(RuntimeError, match="boom"),
    ):
        run([course_dir], out_dir, sources, gap_fill_cache_dir=cache_dir)

    # The exception propagated out of run() rather than being swallowed by
    # the finally-block save -- and because run() never reached its own
    # success-path cleanup, the run's cache file is left in place for a
    # future resume, not deleted.
    cache_files = list((cache_dir / ".gap_fill_runs").rglob("cache.json"))
    assert len(cache_files) == 1


def test_run_final_save_failure_does_not_mask_original_exception(tmp_path, make_source_bundle, caplog):
    course_dir = tmp_path / "course"
    _write_vocabulary_tsv(course_dir, [{"lemma": "νόστος", "pos": "noun", "level": "", "tags": ""}])
    out_dir = tmp_path / "out"
    cache_dir = tmp_path / "cache-dir"
    sources = make_source_bundle(attested_lemmas={"νόστος"}, llm_gap_filler=_gap_filler())

    with (
        caplog.at_level(logging.ERROR, logger="okfbuild.pipeline"),
        patch("okfbuild.pipeline._collect_lexical_candidates", side_effect=RuntimeError("boom")),
        patch.object(GapFillCache, "save", side_effect=OSError("disk full")),
        pytest.raises(RuntimeError, match="boom"),
    ):
        run([course_dir], out_dir, sources, gap_fill_cache_dir=cache_dir)

    assert "disk full" in caplog.text  # the save failure itself was logged, not silently dropped
