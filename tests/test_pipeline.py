import csv
from pathlib import Path

import yaml

from okfbuild.pipeline import run


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
