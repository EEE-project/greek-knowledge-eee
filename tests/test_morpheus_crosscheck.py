"""Tests for the Morpheus cross-check tool. Morpheus interface mocked
throughout -- no real network calls anywhere in this file. Uses the REAL,
full-word Morpheus vocabulary confirmed against real captured responses
(e.g. case="genitive", mood="participle") -- NOT the abbreviated shape
this repo's own pre-existing MorpheusClient test fixtures happen to use.
"""

import json
from unittest.mock import Mock

import pytest

from okfbuild.morpheus_crosscheck import (
    CrosscheckCategory,
    CrosscheckReport,
    CrosscheckResult,
    _classify_readings,
    _query_morpheus_or_none,
    crosscheck_handoff_file,
    render_report,
)


def _reading(**kwargs) -> dict:
    base = {
        "lemma": None,
        "pofs": None,
        "case": None,
        "number": None,
        "gender": None,
        "person": None,
        "tense": None,
        "mood": None,
        "voice": None,
        "stemtype": None,
        "decl": None,
        "dial": [],
    }
    base.update(kwargs)
    return base


def _entry(
    lemma,
    form,
    slot_label="Gen.Sing",
    features=None,
    pos="noun",
    language="grc",
    period=None,
    method="llm:openai/gpt-4o-mini",
) -> dict:
    return {
        "lemma": lemma,
        "form": form,
        "slot_label": slot_label,
        "features": features or {"Case": "Gen", "Number": "Sing"},
        "pos": pos,
        "language": language,
        "period": period,
        "method": method,
        "llm_backend_version": "0.2.1",
    }


# --- _classify_readings() (pure classification logic, no I/O) ---------------


def test_classify_readings_full_match_is_confirmed():
    features = {"Case": "Gen", "Number": "Plur", "Gender": "Neut", "VerbForm": "Part", "Voice": "Act"}
    reading = _reading(
        lemma="πονέω", case="genitive", number="plural", gender="neuter", mood="participle", voice="active"
    )

    category, _ = _classify_readings("πονέω", features, [reading])

    assert category == CrosscheckCategory.CONFIRMED


def test_classify_readings_any_reading_matches_not_first_only():
    """The real πονούντων example: masculine reading first, neuter reading
    matches -- a classifier that only inspects the first reading returned
    would wrongly report DIFFERENT_ANALYSIS."""
    features = {"Case": "Gen", "Number": "Plur", "Gender": "Neut", "VerbForm": "Part", "Voice": "Act"}
    masculine_reading = _reading(
        lemma="πονέω", case="genitive", number="plural", gender="masculine", mood="participle", voice="active"
    )
    neuter_reading = _reading(
        lemma="πονέω", case="genitive", number="plural", gender="neuter", mood="participle", voice="active"
    )
    unrelated_reading = _reading(
        lemma="πονέω", case="genitive", number="plural", gender="masculine", mood="imperative", voice="active"
    )

    category, _ = _classify_readings(
        "πονέω", features, [masculine_reading, neuter_reading, unrelated_reading]
    )

    assert category == CrosscheckCategory.CONFIRMED


def test_classify_readings_no_matching_reading_is_different_analysis():
    features = {"Case": "Gen", "Number": "Plur", "Gender": "Neut", "VerbForm": "Part", "Voice": "Act"}
    reading = _reading(
        lemma="πονέω", case="nominative", number="singular", gender="masculine", mood="participle", voice="active"
    )

    category, _ = _classify_readings("πονέω", features, [reading])

    assert category == CrosscheckCategory.DIFFERENT_ANALYSIS


def test_classify_readings_absent_lemma_is_unconfirmed_with_softened_phrase():
    category, detail = _classify_readings("νόστος", {"Case": "Gen", "Number": "Sing"}, [])

    assert category == CrosscheckCategory.UNCONFIRMED
    assert detail == "not confirmed by queried Morpheus source"


@pytest.mark.parametrize("requested_voice", ["Mid", "Pass"])
def test_classify_readings_mid_or_pass_voice_against_mediopassive_reading_is_underspecified(requested_voice):
    reading = _reading(lemma="λύω", voice="mediopassive")

    category, _ = _classify_readings("λύω", {"Voice": requested_voice}, [reading])

    assert category == CrosscheckCategory.UNDERSPECIFIED


@pytest.mark.parametrize("reading_voice", ["middle", "passive", "mediopassive"])
def test_classify_readings_mid_pass_voice_confirmed_by_any_of_three_reading_voices(reading_voice):
    reading = _reading(lemma="λύω", voice=reading_voice)

    category, _ = _classify_readings("λύω", {"Voice": "Mid,Pass"}, [reading])

    assert category == CrosscheckCategory.CONFIRMED


def test_classify_readings_none_readings_is_query_failed():
    category, _ = _classify_readings("νόστος", {"Case": "Gen"}, None)

    assert category == CrosscheckCategory.QUERY_FAILED


def test_classify_readings_wrong_lemma_reading_never_counts_as_match():
    """A real captured response for the surface form ἔωθεν reports readings
    under lemma ἔθω, not ἔωθεν itself -- Morpheus analyzes a FORM and can
    report readings under an unrelated homograph lemma that must never be
    mistaken for confirmation of a different requested lemma."""
    wrong_lemma_reading = _reading(lemma="ἔθω", case="genitive", number="singular")

    category, _ = _classify_readings("ἔωθεν", {"Case": "Gen", "Number": "Sing"}, [wrong_lemma_reading])

    assert category == CrosscheckCategory.UNCONFIRMED


def test_classify_readings_verbform_fin_is_a_structural_pass_through():
    """VerbForm=='Fin' must contribute a pass-through MATCH on its own --
    the real check is carried by the separate Mood key. This is the most
    common real-world case (any finite verb: indicative/subjunctive/
    optative/imperative) and had no coverage at all before this test."""
    features = {"Tense": "Pres", "Voice": "Act", "Mood": "Ind", "Person": "3", "Number": "Sing", "VerbForm": "Fin"}
    reading = _reading(
        lemma="λύω", tense="present", voice="active", mood="indicative", person="3rd", number="singular"
    )

    category, _ = _classify_readings("λύω", features, [reading])

    assert category == CrosscheckCategory.CONFIRMED


def test_classify_readings_verbform_fin_does_not_mask_a_mood_mismatch():
    """Proves VerbForm=='Fin' is a true no-op contribution, not a shortcut
    that skips checking the rest of the reading."""
    features = {"Mood": "Ind", "VerbForm": "Fin"}
    reading = _reading(lemma="λύω", mood="subjunctive")

    category, _ = _classify_readings("λύω", features, [reading])

    assert category == CrosscheckCategory.DIFFERENT_ANALYSIS


# --- _query_morpheus_or_none() -----------------------------------------------


def test_query_morpheus_or_none_returns_none_when_analyze_raises():
    morpheus = Mock()
    morpheus.analyze.side_effect = RuntimeError("network down")

    result = _query_morpheus_or_none(morpheus, "νόστου")

    assert result is None
    morpheus.analyze.assert_called_once_with("νόστου", raise_on_error=True)


# --- render_report() ----------------------------------------------------------


def test_render_report_never_uses_bare_unconfirmed_label():
    report = CrosscheckReport(
        results=[
            CrosscheckResult(
                lemma="νόστος",
                form="νόστου",
                slot_label="Gen.Sing",
                features={"Case": "Gen", "Number": "Sing"},
                pos="noun",
                language="grc",
                period="homeric",
                method="llm:a",
                category=CrosscheckCategory.UNCONFIRMED,
                detail="not confirmed by queried Morpheus source",
            )
        ],
        skipped_non_grc=[],
    )

    rendered = render_report(report, "2026-09-01T00:00:00+00:00")

    assert "not confirmed by queried Morpheus source" in rendered
    assert "unconfirmed" not in rendered.lower()


# --- crosscheck_handoff_file() (end-to-end, Morpheus mocked) -----------------


def test_crosscheck_handoff_file_dedups_query_but_keeps_both_report_rows(tmp_path):
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text(
        json.dumps(
            {
                "format_version": 1,
                "run_timestamp": "2026-09-01T00:00:00+00:00",
                "entries": [
                    _entry("νόστος", "νόστου", period="homeric"),
                    _entry("νόστος", "νόστου", period="attic"),
                ],
            }
        ),
        encoding="utf-8",
    )
    report_path = tmp_path / "report.md"
    morpheus = Mock()
    morpheus.analyze.return_value = [_reading(lemma="νόστος", case="genitive", number="singular")]

    report = crosscheck_handoff_file(handoff_path, report_path, morpheus)

    assert morpheus.analyze.call_count == 1
    assert len(report.results) == 2
    assert {r.period for r in report.results} == {"homeric", "attic"}


def test_crosscheck_handoff_file_skips_non_grc_entries(tmp_path):
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text(
        json.dumps(
            {
                "format_version": 1,
                "run_timestamp": "2026-09-01T00:00:00+00:00",
                "entries": [_entry("word", "form", language="el")],
            }
        ),
        encoding="utf-8",
    )
    report_path = tmp_path / "report.md"
    morpheus = Mock()

    report = crosscheck_handoff_file(handoff_path, report_path, morpheus)

    morpheus.analyze.assert_not_called()
    assert report.results == []
    assert len(report.skipped_non_grc) == 1
    assert report.skipped_non_grc[0]["language"] == "el"


def test_crosscheck_handoff_file_query_failure_produces_query_failed_category(tmp_path):
    """Exercises the actual composition inside crosscheck_handoff_file()
    end-to-end, not just its two halves in isolation
    (_query_morpheus_or_none's raise->None conversion, and
    _classify_readings' None->QUERY_FAILED classification)."""
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text(
        json.dumps(
            {
                "format_version": 1,
                "run_timestamp": "2026-09-01T00:00:00+00:00",
                "entries": [_entry("νόστος", "νόστου")],
            }
        ),
        encoding="utf-8",
    )
    report_path = tmp_path / "report.md"
    morpheus = Mock()
    morpheus.analyze.side_effect = RuntimeError("network down")

    report = crosscheck_handoff_file(handoff_path, report_path, morpheus)

    assert len(report.results) == 1
    assert report.results[0].category == CrosscheckCategory.QUERY_FAILED


def test_crosscheck_handoff_file_empty_entries_produces_well_formed_empty_report(tmp_path):
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text(
        json.dumps({"format_version": 1, "run_timestamp": "2026-09-01T00:00:00+00:00", "entries": []}),
        encoding="utf-8",
    )
    report_path = tmp_path / "report.md"
    morpheus = Mock()

    report = crosscheck_handoff_file(handoff_path, report_path, morpheus)

    assert report.results == []
    assert report.skipped_non_grc == []
    assert report_path.exists()
    assert "Morpheus Cross-Check Report" in report_path.read_text(encoding="utf-8")


def test_crosscheck_handoff_file_end_to_end_mixed_classification(tmp_path):
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text(
        json.dumps(
            {
                "format_version": 1,
                "run_timestamp": "2026-09-01T00:00:00+00:00",
                "entries": [
                    _entry("νόστος", "νόστου", features={"Case": "Gen", "Number": "Sing"}),
                    _entry("ἄγνωστος", "ἀγνώστου", features={"Case": "Gen", "Number": "Sing"}),
                    _entry("μῦθος", "μύθου", features={"Case": "Gen", "Number": "Sing"}),
                ],
            }
        ),
        encoding="utf-8",
    )
    report_path = tmp_path / "report.md"
    morpheus = Mock()

    def fake_analyze(form, raise_on_error=False):
        if form == "νόστου":
            return [_reading(lemma="νόστος", case="genitive", number="singular")]
        if form == "ἀγνώστου":
            return [_reading(lemma="ἄγνωστος", case="nominative", number="singular")]  # wrong case
        return []  # μύθου: no readings at all

    morpheus.analyze.side_effect = fake_analyze

    report = crosscheck_handoff_file(handoff_path, report_path, morpheus)

    categories_by_lemma = {r.lemma: r.category for r in report.results}
    assert categories_by_lemma["νόστος"] == CrosscheckCategory.CONFIRMED
    assert categories_by_lemma["ἄγνωστος"] == CrosscheckCategory.DIFFERENT_ANALYSIS
    assert categories_by_lemma["μῦθος"] == CrosscheckCategory.UNCONFIRMED


def test_crosscheck_handoff_file_wrong_format_version_raises(tmp_path):
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text(
        json.dumps({"format_version": 999, "run_timestamp": "...", "entries": []}), encoding="utf-8"
    )
    report_path = tmp_path / "report.md"

    with pytest.raises(ValueError, match="format_version"):
        crosscheck_handoff_file(handoff_path, report_path, Mock())


def test_crosscheck_handoff_file_corrupt_json_raises_naming_path(tmp_path):
    """A handoff file truncated by an interrupted pilot run should fail
    loudly with a clear, path-naming error -- not a raw JSONDecodeError,
    and distinguishable from the wrong-format_version case above."""
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text("{not valid json", encoding="utf-8")
    report_path = tmp_path / "report.md"

    with pytest.raises(ValueError, match="corrupt") as exc_info:
        crosscheck_handoff_file(handoff_path, report_path, Mock())
    assert str(handoff_path) in str(exc_info.value)
