"""Tests for the reading-course lemma-format dispatch case in
_read_vocabulary_candidates() (case 1 in its own docstring): a TSV with
both `lemma` and `pos` columns. Also covers translation_presence.tsv
(case 3), a per-lesson quiz answer key that coincidentally has its own
`lemma` column but must never be read as vocabulary -- see the pipeline
module's docstring for why `pos` is required, not just `lemma`.
"""

import logging

from okfbuild.pipeline import _LexicalCandidate, _read_vocabulary_candidates

from .test_word_translation_candidates import _write_word_translation_tsv as _write_tsv


def test_lemma_and_pos_columns_produce_a_candidate(tmp_path):
    course_dir = tmp_path / "course"
    _write_tsv(
        course_dir,
        "vocab_I_1-21.tsv",
        [{"form": "Ἄνδρα", "lemma": "ἀνήρ", "pos": "noun", "context": "I.1", "meaning": "man"}],
    )

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == [_LexicalCandidate(lemma="ἀνήρ", pos="noun", level=[], tags=[], source_course="course")]


def test_lemma_only_unnamed_file_contributes_zero_candidates_and_logs_warning(tmp_path, caplog):
    """A `lemma`-column file with no `pos` column and no recognized
    filename must not be misread as the reading-course format -- it
    falls through to the generic unrecognized-file warning instead."""
    course_dir = tmp_path / "course"
    _write_tsv(course_dir, "mystery.tsv", [{"lemma": "ἀνήρ", "note": "no pos column here"}])

    with caplog.at_level(logging.WARNING):
        candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == []
    assert "mystery.tsv" in caplog.text


def test_translation_presence_tsv_contributes_zero_candidates(tmp_path):
    """translation_presence.tsv is a per-lesson quiz answer key (see
    translation_presence_SCHEMA.md), not vocabulary -- including a
    comment-prefixed stale row (the file's own convention for a row
    that no longer applies) to confirm the whole file is skipped before
    any row, bogus or not, is ever read."""
    course_dir = tmp_path / "course"
    _write_tsv(
        course_dir,
        "translation_presence.tsv",
        [
            {"lemma": "ἀνήρ", "form": "Ἄνδρα", "stanza_ref": "I.1–5", "translator": "Жуковский", "reflected": "yes"},
            {"lemma": "#ἐγώ", "form": "μοι", "stanza_ref": "I.1–5", "translator": "Жуковский", "reflected": ""},
        ],
    )

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == []


def test_translation_presence_tsv_skip_is_logged_quietly_not_as_a_warning(tmp_path, caplog):
    course_dir = tmp_path / "course"
    _write_tsv(
        course_dir,
        "translation_presence.tsv",
        [{"lemma": "ἀνήρ", "form": "Ἄνδρα", "stanza_ref": "I.1–5", "translator": "Жуковский", "reflected": "yes"}],
    )

    with caplog.at_level(logging.INFO):
        _read_vocabulary_candidates(course_dir)

    assert not any(record.levelno >= logging.WARNING for record in caplog.records)
    assert "translation_presence.tsv" in caplog.text
