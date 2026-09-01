from unittest.mock import Mock, patch

import eee_project as eee
import pytest

from okfbuild.sources.eee_engine import FormSourceType, SlotForms, collect_slot_forms
from okfbuild.sources.llm_gap_filler import GapFillResult, SampleStatus


class _FakeSlotTemplate:
    def __init__(self, label, features=None):
        self.label = label
        self.features = features


def _gap_result(forms):
    return GapFillResult(
        forms=forms,
        method="llm:gpt-4o-mini",
        llm_backend_version="0.2.1",
        sample_statuses=(SampleStatus.SUCCESS,) if forms else (SampleStatus.ABSTAINED,),
    )


# --- Updated pre-existing tests (rename + new return shape) -----------------


def test_collect_slot_forms_returns_rule_based_forms_for_known_lemma():
    templates = [_FakeSlotTemplate("Nom.Sing"), _FakeSlotTemplate("Gen.Sing")]
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=templates) as mock_templates,
        patch(
            "okfbuild.sources.eee_engine.eee.inflect_slot",
            side_effect=[{"θεός"}, {"θεοῦ"}],
        ) as mock_inflect,
    ):
        result = collect_slot_forms("θεός", "noun", "grc")

    assert result == {
        "Nom.Sing": SlotForms(forms={"θεός"}, source_type=FormSourceType.RULE_BASED),
        "Gen.Sing": SlotForms(forms={"θεοῦ"}, source_type=FormSourceType.RULE_BASED),
    }
    mock_templates.assert_called_once_with("grc", "noun", "en", backend=None)
    mock_inflect.assert_any_call("θεός", templates[0], "noun", language="grc", backend=None)
    mock_inflect.assert_any_call("θεός", templates[1], "noun", language="grc", backend=None)


def test_collect_slot_forms_returns_empty_dict_for_unknown_lemma_with_no_gap_filler():
    templates = [_FakeSlotTemplate("Nom.Sing"), _FakeSlotTemplate("Gen.Sing")]
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=templates),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", return_value=set()),
    ):
        result = collect_slot_forms("not-a-real-lemma", "noun", "grc", gap_filler=None)

    assert result == {}


def test_collect_slot_forms_passes_backend_through_to_both_calls():
    templates = [_FakeSlotTemplate("Nom.Sing")]
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=templates) as mock_templates,
        patch(
            "okfbuild.sources.eee_engine.eee.inflect_slot", return_value={"νόστος"}
        ) as mock_inflect,
    ):
        result = collect_slot_forms("νόστος", "noun", "grc", backend="homeric")

    assert result == {"Nom.Sing": SlotForms(forms={"νόστος"}, source_type=FormSourceType.RULE_BASED)}
    mock_templates.assert_called_once_with("grc", "noun", "en", backend="homeric")
    mock_inflect.assert_called_once_with("νόστος", templates[0], "noun", language="grc", backend="homeric")


# --- New tests: the LLM gap-filler fork --------------------------------------


def test_collect_slot_forms_raises_when_gap_filler_set_without_cache():
    gap_filler = Mock()
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates") as mock_templates,
        pytest.raises(ValueError),
    ):
        collect_slot_forms("lemma", "noun", "grc", gap_filler=gap_filler, cache=None)

    mock_templates.assert_not_called()


def test_collect_slot_forms_never_calls_fill_gap_when_rule_based_succeeds():
    templates = [_FakeSlotTemplate("Nom.Sing", features={"Case": "Nom"})]
    gap_filler = Mock()
    cache = Mock()
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=templates),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", return_value={"θεός"}),
        patch("okfbuild.sources.eee_engine.llm_gap_filler.fill_gap") as mock_fill_gap,
    ):
        collect_slot_forms("θεός", "noun", "grc", gap_filler=gap_filler, cache=cache)

    mock_fill_gap.assert_not_called()


def test_collect_slot_forms_calls_fill_gap_on_clean_empty_result():
    template = _FakeSlotTemplate("Nom.Sing", features={"Case": "Nom", "Number": "Sing"})
    gap_filler = Mock()
    cache = Mock()
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=[template]),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", return_value=set()),
        patch(
            "okfbuild.sources.eee_engine.llm_gap_filler.fill_gap",
            return_value=_gap_result({"θεοῦ"}),
        ) as mock_fill_gap,
    ):
        result = collect_slot_forms("θεός", "noun", "grc", gap_filler=gap_filler, cache=cache)

    mock_fill_gap.assert_called_once_with(
        "θεός", template.features, "noun", "grc", gap_filler, cache
    )
    assert result == {
        "Nom.Sing": SlotForms(
            forms={"θεοῦ"},
            source_type=FormSourceType.LLM_INFERRED,
            method="llm:gpt-4o-mini",
            llm_backend_version="0.2.1",
        )
    }


def test_collect_slot_forms_omits_slot_when_fill_gap_produces_no_usable_result():
    template = _FakeSlotTemplate("Nom.Sing", features={"Case": "Nom"})
    gap_filler = Mock()
    cache = Mock()
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=[template]),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", return_value=set()),
        patch(
            "okfbuild.sources.eee_engine.llm_gap_filler.fill_gap",
            return_value=_gap_result(set()),
        ),
    ):
        result = collect_slot_forms("θεός", "noun", "grc", gap_filler=gap_filler, cache=cache)

    assert result == {}


def test_collect_slot_forms_propagates_inflect_slot_exception_without_calling_fill_gap():
    template = _FakeSlotTemplate("Nom.Sing", features={"Case": "Nom"})
    gap_filler = Mock()
    cache = Mock()
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=[template]),
        patch(
            "okfbuild.sources.eee_engine.eee.inflect_slot",
            side_effect=eee.PosNotSupportedError("no data for pos"),
        ),
        patch("okfbuild.sources.eee_engine.llm_gap_filler.fill_gap") as mock_fill_gap,
        pytest.raises(eee.PosNotSupportedError),
    ):
        collect_slot_forms("θεός", "noun", "grc", gap_filler=gap_filler, cache=cache)

    mock_fill_gap.assert_not_called()


def test_collect_slot_forms_never_calls_fill_gap_for_ag_paradigm_shaped_template():
    template = _FakeSlotTemplate("ADV", features=None)
    gap_filler = Mock()
    cache = Mock()
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=[template]),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", return_value=set()),
        patch("okfbuild.sources.eee_engine.llm_gap_filler.fill_gap") as mock_fill_gap,
    ):
        result = collect_slot_forms("καλός", "adj", "grc", gap_filler=gap_filler, cache=cache)

    mock_fill_gap.assert_not_called()
    assert result == {}


def test_collect_slot_forms_threads_same_cache_across_multiple_templates():
    templates = [
        _FakeSlotTemplate("Nom.Sing", features={"Case": "Nom"}),
        _FakeSlotTemplate("Gen.Sing", features={"Case": "Gen"}),
    ]
    gap_filler = Mock()
    cache = Mock()
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=templates),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", return_value=set()),
        patch(
            "okfbuild.sources.eee_engine.llm_gap_filler.fill_gap",
            return_value=_gap_result({"form"}),
        ) as mock_fill_gap,
    ):
        collect_slot_forms("lemma", "noun", "grc", gap_filler=gap_filler, cache=cache)

    assert mock_fill_gap.call_count == 2
    for call in mock_fill_gap.call_args_list:
        assert call.args[4] is gap_filler
        assert call.args[5] is cache
