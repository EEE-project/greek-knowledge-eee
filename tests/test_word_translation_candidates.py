import csv
from pathlib import Path

from okfbuild.pipeline import (
    _collect_lexical_candidates,
    _LexicalCandidate,
    _read_vocabulary_candidates,
    run,
)


def _write_word_translation_tsv(course_dir: Path, filename: str, rows: list[dict]) -> None:
    """Writes rows to course_dir/filename as a tab-separated file. fieldnames
    are taken from the first row's keys -- callers pass a consistent key set
    per call (e.g. all rows {"Word", "Translation"}, or all rows including
    "Type"), matching how one real TSV file has exactly one fixed header."""
    course_dir.mkdir(parents=True, exist_ok=True)
    with (course_dir / filename).open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


# --- 5.1 Filename -> part-of-speech mapping ---------------------------------


def test_nouns_tsv_row_with_article_strips_to_noun_candidate(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(course_dir, "nouns.tsv", [{"Word": "το μήνυμα", "Translation": "message"}])

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == [_LexicalCandidate(lemma="μήνυμα", pos="noun", level=[], tags=[], source_course="course")]


def test_verbs_tsv_produces_verb_candidate(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(course_dir, "verbs.tsv", [{"Word": "ακούω", "Translation": "to hear"}])

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == [_LexicalCandidate(lemma="ακούω", pos="verb", level=[], tags=[], source_course="course")]


def test_adjectives_tsv_produces_adj_candidate(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(course_dir, "adjectives.tsv", [{"Word": "μεγάλος", "Translation": "big"}])

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == [_LexicalCandidate(lemma="μεγάλος", pos="adj", level=[], tags=[], source_course="course")]


def test_pronouns_tsv_produces_pronoun_candidate(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(course_dir, "pronouns.tsv", [{"Word": "εγώ", "Translation": "I"}])

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == [_LexicalCandidate(lemma="εγώ", pos="pronoun", level=[], tags=[], source_course="course")]


def test_particles_tsv_produces_particle_candidate(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(course_dir, "particles.tsv", [{"Word": "μεν", "Translation": "on the one hand"}])

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == [_LexicalCandidate(lemma="μεν", pos="particle", level=[], tags=[], source_course="course")]


def test_verbs_plus_tsv_maps_to_same_pos_as_verbs_tsv(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(course_dir, "verbs+.tsv", [{"Word": "λέγω", "Translation": "to say"}])

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == [_LexicalCandidate(lemma="λέγω", pos="verb", level=[], tags=[], source_course="course")]


def test_adjs_tsv_maps_to_same_pos_as_adjectives_tsv(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(course_dir, "adjs.tsv", [{"Word": "καλός", "Translation": "good"}])

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == [_LexicalCandidate(lemma="καλός", pos="adj", level=[], tags=[], source_course="course")]


def test_ru_suffixed_filename_contributes_zero_candidates(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(course_dir, "nouns_ru.tsv", [{"Word": "το μήνυμα", "Translation": "сообщение"}])

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == []


def test_other_two_letter_language_suffix_filename_contributes_zero_candidates(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(course_dir, "nouns_fr.tsv", [{"Word": "το μήνυμα", "Translation": "message"}])

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == []


def test_unrecognized_filename_contributes_zero_candidates_and_does_not_raise(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(course_dir, "numbers.tsv", [{"Word": "ένα", "Translation": "one"}])

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == []


# --- 5.2 vocabulary.tsv: POS from its own Type column -----------------------


def test_vocabulary_tsv_type_column_maps_each_representative_row_per_table(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(
        course_dir,
        "vocabulary.tsv",
        [
            {"Word": "το μήνυμα", "Translation": "message", "Type": "noun"},
            {"Word": "ακούω", "Translation": "to hear", "Type": "verb"},
            {"Word": "μεγάλος", "Translation": "big", "Type": "adjective"},
            {"Word": "γρήγορα", "Translation": "quickly", "Type": "adverb"},
            {"Word": "εγώ", "Translation": "I", "Type": "pronoun"},
            {"Word": "βρέχει", "Translation": "it rains", "Type": "verb (impersonal)"},
            {"Word": "έχω έναν στόχο", "Translation": "I have a goal", "Type": "phrase"},
            {"Word": "κάτι", "Translation": "something", "Type": ""},
        ],
    )

    candidates = _read_vocabulary_candidates(course_dir)

    by_lemma = {c.lemma: c.pos for c in candidates}
    assert by_lemma == {
        "μήνυμα": "noun",
        "ακούω": "verb",
        "μεγάλος": "adj",
        "γρήγορα": "adv",
        "εγώ": "pronoun",
        "βρέχει": "verb",
    }
    assert "έχω έναν στόχο" not in by_lemma
    assert "κάτι" not in by_lemma


def test_vocabulary_tsv_unrecognized_type_value_skips_only_that_row(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(
        course_dir,
        "vocabulary.tsv",
        [
            {"Word": "ακούω", "Translation": "to hear", "Type": "verb"},
            {"Word": "κάτι παράξενο", "Translation": "something strange", "Type": "idiom"},
        ],
    )

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == [_LexicalCandidate(lemma="ακούω", pos="verb", level=[], tags=[], source_course="course")]


def test_vocabulary_ru_tsv_contributes_zero_candidates(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(
        course_dir, "vocabulary_ru.tsv", [{"Word": "το μήνυμα", "Translation": "сообщение", "Type": "noun"}]
    )

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == []


# --- 5.3 Article stripping (noun-typed rows) --------------------------------


def test_nouns_tsv_monotonic_singular_article_stripped(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(
        course_dir,
        "nouns.tsv",
        [
            {"Word": "ο φίλος", "Translation": "friend"},
            {"Word": "η πρόσκληση", "Translation": "invitation"},
            {"Word": "το μήνυμα", "Translation": "message"},
        ],
    )

    candidates = _read_vocabulary_candidates(course_dir)

    assert {c.lemma for c in candidates} == {"φίλος", "πρόσκληση", "μήνυμα"}
    assert all(c.pos == "noun" for c in candidates)


def test_nouns_tsv_polytonic_singular_article_stripped(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(
        course_dir,
        "nouns.tsv",
        [
            {"Word": "ὁ βοῦς", "Translation": "ox"},
            {"Word": "ἡ ῥάβδος", "Translation": "rod"},
            {"Word": "τό ἄροτρον", "Translation": "plow"},
            {"Word": "τὸ δένδρον", "Translation": "tree"},
        ],
    )

    candidates = _read_vocabulary_candidates(course_dir)

    assert {c.lemma for c in candidates} == {"βοῦς", "ῥάβδος", "ἄροτρον", "δένδρον"}


def test_nouns_tsv_plural_article_row_skipped(tmp_path):
    """τα σκουπίδια (pluralia tantum -- "garbage", no natural singular) must
    be skipped entirely, never stripped down to a fabricated singular
    lemma. Confirmed real data: created_with_eee's ellinika_b chapter_07
    nouns.tsv has this exact row."""
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(course_dir, "nouns.tsv", [{"Word": "τα σκουπίδια", "Translation": "garbage"}])

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == []


def test_nouns_tsv_bare_word_no_article_used_as_lemma_directly(tmp_path):
    """παροιμία ("proverb") is cited with no article at all in real course
    data. This must NOT be collapsed into the plural-article skip case --
    it is a normal, valid bare lemma and must produce a candidate."""
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(course_dir, "nouns.tsv", [{"Word": "παροιμία", "Translation": "proverb"}])

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == [_LexicalCandidate(lemma="παροιμία", pos="noun", level=[], tags=[], source_course="course")]


def test_vocabulary_tsv_type_noun_row_shares_article_stripping_with_nouns_tsv(tmp_path):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(
        course_dir, "vocabulary.tsv", [{"Word": "ο φίλος", "Translation": "friend", "Type": "noun"}]
    )

    candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == [_LexicalCandidate(lemma="φίλος", pos="noun", level=[], tags=[], source_course="course")]


# --- 5.5 Logging (skip visibility) ------------------------------------------


def test_unrecognized_filename_logs_warning_with_filename(tmp_path, caplog):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(course_dir, "numbers.tsv", [{"Word": "ένα", "Translation": "one"}])

    with caplog.at_level("WARNING"):
        _read_vocabulary_candidates(course_dir)

    assert "numbers.tsv" in caplog.text


def test_vocabulary_tsv_known_skip_type_values_do_not_log_warning(tmp_path, caplog):
    """phrase/adverb phrase/literary term are catalogued, confirmed-skip
    Type values (see section-01-word-translation-tsv.md's survey table),
    not unrecognized ones -- must not trigger the same warning as a
    genuinely novel Type value like "idiom"."""
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(
        course_dir,
        "vocabulary.tsv",
        [
            {"Word": "έχω έναν στόχο", "Translation": "I have a goal", "Type": "phrase"},
            {"Word": "εν τω μεταξύ", "Translation": "in the meantime", "Type": "adverb phrase"},
            {"Word": "ρήμα", "Translation": "verb (grammar term)", "Type": "literary term"},
        ],
    )

    with caplog.at_level("WARNING"):
        candidates = _read_vocabulary_candidates(course_dir)

    assert candidates == []
    assert caplog.text == ""


def test_vocabulary_tsv_unrecognized_type_value_logs_warning_with_value(tmp_path, caplog):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(
        course_dir, "vocabulary.tsv", [{"Word": "κάτι παράξενο", "Translation": "something strange", "Type": "idiom"}]
    )

    with caplog.at_level("WARNING"):
        _read_vocabulary_candidates(course_dir)

    assert "idiom" in caplog.text


def test_nouns_tsv_plural_article_row_logs_warning_with_skipped_word(tmp_path, caplog):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(course_dir, "nouns.tsv", [{"Word": "τα σκουπίδια", "Translation": "garbage"}])

    with caplog.at_level("WARNING"):
        _read_vocabulary_candidates(course_dir)

    assert "τα σκουπίδια" in caplog.text


def test_collect_lexical_candidates_dedup_preserves_source_course_of_winning_candidate(tmp_path):
    course_a = tmp_path / "odyssey"
    course_b = tmp_path / "other-course"
    _write_word_translation_tsv(course_a, "nouns.tsv", [{"Word": "ο φίλος", "Translation": "friend"}])
    _write_word_translation_tsv(course_b, "nouns.tsv", [{"Word": "ο φίλος", "Translation": "friend"}])

    forward = _collect_lexical_candidates([course_a, course_b])
    assert len(forward) == 1
    assert forward[0].source_course == "odyssey"

    reversed_order = _collect_lexical_candidates([course_b, course_a])
    assert len(reversed_order) == 1
    assert reversed_order[0].source_course == "other-course"


# --- 5.6 End-to-end integration (via run()) ---------------------------------


def test_run_dedupes_candidate_shared_between_lemma_pos_tsv_and_word_translation_tsv(tmp_path, make_source_bundle):
    course_dir = tmp_path / "course"
    course_dir.mkdir(parents=True, exist_ok=True)
    with (course_dir / "vocab_test.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["lemma", "pos", "level", "tags"], delimiter="\t")
        writer.writeheader()
        writer.writerow({"lemma": "νόστος", "pos": "noun", "level": "", "tags": ""})
    _write_word_translation_tsv(course_dir, "nouns.tsv", [{"Word": "ο νόστος", "Translation": "homecoming"}])
    out_dir = tmp_path / "out"
    sources = make_source_bundle(attested_lemmas={"νόστος"})

    report = run([course_dir], out_dir, sources)

    assert (out_dir / "words" / "νόστος.md").exists()
    assert report.written == 1


def test_run_builds_concepts_from_word_translation_tsvs_only(tmp_path, make_source_bundle):
    course_dir = tmp_path / "course"
    _write_word_translation_tsv(course_dir, "nouns.tsv", [{"Word": "ο φίλος", "Translation": "friend"}])
    out_dir = tmp_path / "out"
    sources = make_source_bundle(attested_lemmas={"φίλος"})

    report = run([course_dir], out_dir, sources)

    assert (out_dir / "words" / "φίλος.md").exists()
    assert report.written == 1
