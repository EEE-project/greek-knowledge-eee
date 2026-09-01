"""Tests for the section-04 gap-filler pilot: the real OpenRouter-backed
fixture chain and run_gap_filler_pilot()'s own orchestration logic.

Per-test markers, not a module-level pytestmark -- most tests here are
ordinary, mocked, no-network unit tests that must stay in the default
`-m "not integration"` suite; only the one real end-to-end test at the
bottom is marked integration + paid_llm_api.
"""

import dataclasses
import json
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from okfbuild.concepts.lexical_entry import GapFillRecord
from okfbuild.gap_filler_pilot import run_gap_filler_pilot
from okfbuild.pipeline import BuildReport
from okfbuild.sources import SourceBundle
from okfbuild.sources.llm_gap_filler import GapFillerConfig, LLMModelConfig
from tests import conftest

# --- Fixture-construction unit tests (mocked, no network) -------------------


def test_build_real_gap_filler_config_has_two_models_sharing_key_and_base_url():
    config = conftest._build_real_gap_filler_config()

    assert len(config.models) == 2
    assert {m.name for m in config.models} == {"gpt-4o-mini", "claude-3.5-haiku"}
    assert {m.model for m in config.models} == {"openai/gpt-4o-mini", "anthropic/claude-3.5-haiku"}
    api_key_envs = {m.api_key_env for m in config.models}
    base_urls = {m.base_url for m in config.models}
    assert len(api_key_envs) == 1  # both models share one OpenRouter key
    assert len(base_urls) == 1  # both models share one OpenRouter endpoint


def test_source_bundle_replace_with_gap_filler_preserves_every_other_field():
    """Verifies the exact mechanism real_source_bundle_with_gap_filler uses
    (dataclasses.replace(), never in-place mutation) against a
    representative fake SourceBundle -- confirms no field is accidentally
    altered besides llm_gap_filler, without needing the real fixture
    chain's live Morpheus/Wiktextract/etc clients."""
    fake_bundle = SourceBundle(
        eee_engine=Mock(),
        morpheus=Mock(),
        byzantine_forms={"lemma": {}},
        wiktextract=Mock(),
        lsj=Mock(),
        wikipedia=Mock(),
    )
    fake_config = GapFillerConfig(models=(LLMModelConfig(name="a", model="m", api_key_env="KEY"),))

    replaced = dataclasses.replace(fake_bundle, llm_gap_filler=fake_config)

    assert replaced.eee_engine is fake_bundle.eee_engine
    assert replaced.morpheus is fake_bundle.morpheus
    assert replaced.byzantine_forms is fake_bundle.byzantine_forms
    assert replaced.wiktextract is fake_bundle.wiktextract
    assert replaced.lsj is fake_bundle.lsj
    assert replaced.wikipedia is fake_bundle.wikipedia
    assert replaced.llm_gap_filler is fake_config
    assert fake_bundle.llm_gap_filler is None  # original untouched


# --- run_gap_filler_pilot() orchestration unit tests (mocked, no network) ---


def _fake_build_report():
    return BuildReport(written=3, unchanged=1, failed=0, errors=[])


def test_run_gap_filler_pilot_writes_output_to_given_out_dir(tmp_path):
    out_dir = tmp_path / "isolated-out"
    handoff_path = tmp_path / "handoff.json"
    course_paths = [tmp_path / "course-a"]
    sources = Mock()

    with patch("okfbuild.gap_filler_pilot.pipeline.run", return_value=_fake_build_report()) as mock_run:
        run_gap_filler_pilot(sources, course_paths, out_dir, handoff_path)

    call = mock_run.call_args
    assert call.args[0] == course_paths
    assert call.args[1] == out_dir
    assert call.args[2] is sources


def test_run_gap_filler_pilot_passes_gap_fill_cache_dir_through(tmp_path):
    out_dir = tmp_path / "isolated-out"
    handoff_path = tmp_path / "handoff.json"

    with patch("okfbuild.gap_filler_pilot.pipeline.run", return_value=_fake_build_report()) as mock_run:
        run_gap_filler_pilot(Mock(), [tmp_path / "course"], out_dir, handoff_path)

    assert mock_run.call_args.kwargs["gap_fill_cache_dir"] == out_dir


def test_run_gap_filler_pilot_writes_handoff_matching_schema(tmp_path):
    out_dir = tmp_path / "isolated-out"
    handoff_path = tmp_path / "nested" / "handoff.json"  # also proves parent dirs get created
    record = GapFillRecord(
        lemma="νόστος",
        form="νόστου",
        slot_label="Gen.Sing",
        features={"Case": "Gen", "Number": "Sing"},
        pos="noun",
        language="grc",
        period="homeric",
        method="llm:openai/gpt-4o-mini",
        llm_backend_version="0.2.1",
    )

    def fake_run(course_paths, out_dir_arg, sources, **kwargs):
        kwargs["on_llm_inferred"](record)
        return _fake_build_report()

    with patch("okfbuild.gap_filler_pilot.pipeline.run", side_effect=fake_run):
        report = run_gap_filler_pilot(Mock(), [tmp_path / "course"], out_dir, handoff_path)

    assert report.written == 3
    assert handoff_path.exists()
    data = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert data["format_version"] == 1
    assert isinstance(data["run_timestamp"], str) and data["run_timestamp"]
    assert data["entries"] == [
        {
            "lemma": "νόστος",
            "form": "νόστου",
            "slot_label": "Gen.Sing",
            "features": {"Case": "Gen", "Number": "Sing"},
            "pos": "noun",
            "language": "grc",
            "period": "homeric",
            "method": "llm:openai/gpt-4o-mini",
            "llm_backend_version": "0.2.1",
        }
    ]


def test_run_gap_filler_pilot_handoff_faithfully_forwards_whatever_it_is_given(tmp_path):
    """run_gap_filler_pilot() has no filtering logic of its own -- RULE_BASED
    vs LLM_INFERRED filtering already happened upstream, in
    lexical_entry.build()'s own on_llm_inferred hook (see
    test_build_on_llm_inferred_fires_once_per_form_for_llm_inferred_slots_only
    in tests/concepts/test_lexical_entry.py). This proves the handoff file
    contains exactly, and only, the records the on_llm_inferred callback
    actually received -- no separate path could leak anything else in."""
    out_dir = tmp_path / "isolated-out"
    handoff_path = tmp_path / "handoff.json"
    records = [
        GapFillRecord("νόστος", "νόστου", "Gen.Sing", {}, "noun", "grc", "homeric", "llm:a", "0.2.1"),
        GapFillRecord("φίλος", "φίλου", "Gen.Sing", {}, "noun", "grc", "attic", "llm:a", "0.2.1"),
    ]

    def fake_run(course_paths, out_dir_arg, sources, **kwargs):
        for record in records:
            kwargs["on_llm_inferred"](record)
        return _fake_build_report()

    with patch("okfbuild.gap_filler_pilot.pipeline.run", side_effect=fake_run):
        run_gap_filler_pilot(Mock(), [tmp_path / "course"], out_dir, handoff_path)

    data = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert [entry["form"] for entry in data["entries"]] == ["νόστου", "φίλου"]


# --- The one real, gated end-to-end test ------------------------------------


@pytest.mark.integration
@pytest.mark.paid_llm_api
def test_real_gated_pilot_run_produces_valid_handoff(
    repo_root, created_with_eee_root, real_source_bundle_with_gap_filler
):
    """Never run in this section's own verification pass -- requires
    --run-paid-llm-tests, a real GREEK_KNOWLEDGE_OPENROUTER_API_KEY, and
    GREEK_KNOWLEDGE_RUN_PAID_LLM_TESTS=1 (see require_paid_llm_gate() via
    the real_gap_filler_config fixture this one transitively depends on).
    Exercised only via the separate manual step:
    uv run pytest -m "integration and paid_llm_api" --run-paid-llm-tests tests/test_gap_filler_pilot.py

    Structural assertions only (both plan reviews flagged a content-based
    assertion like "at least one dagger marker" as brittle, unrelated to
    whether the integration itself works) -- the run completes without
    raising, produces zero failures, and the handoff file is well-formed.
    Content correctness is section-05's Morpheus cross-check's job, not
    this test's."""
    out_dir = repo_root / "build" / "gap-filler-pilot"
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
    handoff_path = out_dir / f"handoff-{run_id}.json"
    course_paths = [
        created_with_eee_root / "ancient_greek" / "odyssey",
        created_with_eee_root / "modern_greek" / "b1greeklanguageandculture" / "kavafis_ithaki",
    ]

    report = run_gap_filler_pilot(real_source_bundle_with_gap_filler, course_paths, out_dir, handoff_path)

    assert report.failed == 0
    assert handoff_path.exists()
    data = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert data["format_version"] == 1
    assert isinstance(data["entries"], list)
    for entry in data["entries"]:
        assert entry.keys() == {
            "lemma", "form", "slot_label", "features", "pos", "language", "period", "method", "llm_backend_version",
        }
