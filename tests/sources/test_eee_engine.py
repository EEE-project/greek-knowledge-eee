import logging
from unittest.mock import Mock, patch

import eee_project as eee
import pytest
from modern_greek_inflexion_eee.exceptions import (
    NotInGreekException,
    NotLegalAdjectiveException,
    NotLegalPronounException,
    NotLegalVerbException,
)

from okfbuild.sources.eee_engine import FormSourceType, SlotForms, collect_slot_forms
from okfbuild.sources.llm_gap_filler import GapFillResult, SampleStatus

_LOGGER_NAME = "okfbuild.sources.eee_engine"


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
        "θεός", template.features, "noun", "grc", gap_filler, cache, context="Nom.Sing"
    )
    assert result == {
        "Nom.Sing": SlotForms(
            forms={"θεοῦ"},
            source_type=FormSourceType.LLM_INFERRED,
            method="llm:gpt-4o-mini",
            llm_backend_version="0.2.1",
            features=template.features,
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


# --- New tests: context string built for the LLM gap-filler -----------------


def test_collect_slot_forms_context_is_just_the_label_with_no_backend_or_course():
    template = _FakeSlotTemplate("Nom.Sing", features={"Case": "Nom"})
    gap_filler = Mock()
    cache = Mock()
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=[template]),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", return_value=set()),
        patch(
            "okfbuild.sources.eee_engine.llm_gap_filler.fill_gap",
            return_value=_gap_result({"θεός"}),
        ) as mock_fill_gap,
    ):
        collect_slot_forms("θεός", "noun", "grc", gap_filler=gap_filler, cache=cache)

    assert mock_fill_gap.call_args.kwargs["context"] == "Nom.Sing"


def test_collect_slot_forms_context_includes_period_when_backend_set():
    template = _FakeSlotTemplate("Gen.Sing", features={"Case": "Gen"})
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
        collect_slot_forms("θεός", "noun", "grc", backend="homeric", gap_filler=gap_filler, cache=cache)

    assert mock_fill_gap.call_args.kwargs["context"] == "Gen.Sing, period=homeric"


def test_collect_slot_forms_context_has_no_period_fragment_when_backend_unset():
    template = _FakeSlotTemplate("Gen.Sing", features={"Case": "Gen"})
    gap_filler = Mock()
    cache = Mock()
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=[template]),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", return_value=set()),
        patch(
            "okfbuild.sources.eee_engine.llm_gap_filler.fill_gap",
            return_value=_gap_result({"form"}),
        ) as mock_fill_gap,
    ):
        collect_slot_forms("word", "noun", "el", gap_filler=gap_filler, cache=cache)

    assert "period=" not in mock_fill_gap.call_args.kwargs["context"]


def test_collect_slot_forms_context_includes_full_course_metadata_for_odyssey():
    template = _FakeSlotTemplate("Gen.Sing", features={"Case": "Gen"})
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
        collect_slot_forms(
            "θεός", "noun", "grc", backend="homeric", gap_filler=gap_filler, cache=cache,
            source_course="odyssey",
        )

    context = mock_fill_gap.call_args.kwargs["context"]
    assert context == "Gen.Sing, period=homeric, author=Homer, work=Odyssey, dialect=Epic/Ionic"


def test_collect_slot_forms_context_omits_dialect_when_course_has_none():
    template = _FakeSlotTemplate("Nom.Sing", features={"Case": "Nom"})
    gap_filler = Mock()
    cache = Mock()
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=[template]),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", return_value=set()),
        patch(
            "okfbuild.sources.eee_engine.llm_gap_filler.fill_gap",
            return_value=_gap_result({"form"}),
        ) as mock_fill_gap,
    ):
        collect_slot_forms(
            "word", "noun", "el", gap_filler=gap_filler, cache=cache, source_course="kavafis_ithaki"
        )

    context = mock_fill_gap.call_args.kwargs["context"]
    assert context == "Nom.Sing, author=Constantine P. Cavafy, work=Ithaka"


def test_collect_slot_forms_context_ignores_unmapped_or_missing_course():
    """The second call (explicit source_course=None) also doubles as this
    file's coverage that omitting source_course entirely (see
    test_collect_slot_forms_context_is_just_the_label_with_no_backend_or_course)
    behaves identically to passing None explicitly -- the parameter's
    default -- so a separate dedicated test for that isn't needed."""
    template = _FakeSlotTemplate("Nom.Sing", features={"Case": "Nom"})
    gap_filler = Mock()
    cache = Mock()
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=[template]),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", return_value=set()),
        patch(
            "okfbuild.sources.eee_engine.llm_gap_filler.fill_gap",
            return_value=_gap_result({"form"}),
        ) as mock_fill_gap,
    ):
        collect_slot_forms(
            "word", "noun", "el", gap_filler=gap_filler, cache=cache, source_course="unmapped-course"
        )
        collect_slot_forms("word", "noun", "el", gap_filler=gap_filler, cache=cache, source_course=None)

    for call in mock_fill_gap.call_args_list:
        assert call.kwargs["context"] == "Nom.Sing"


# --- New tests: pronoun PronType cross-family filter -------------------------


def test_collect_slot_forms_skips_fill_gap_for_cross_family_pronoun_template():
    """ἐγώ (PronType=Prs) has no demonstrative form -- an empty rule-based
    result on a Dem-tagged template is a category error, not a gap, and
    must never reach the LLM."""
    prs_template = _FakeSlotTemplate("Nom.Sing.Prs", features={"Case": "Nom", "Number": "Sing", "PronType": "Prs"})
    dem_template = _FakeSlotTemplate("Nom.Sing.Dem", features={"Case": "Nom", "Number": "Sing", "PronType": "Dem"})
    gap_filler = Mock()
    cache = Mock()
    with (
        patch(
            "okfbuild.sources.eee_engine.eee.get_slot_templates",
            return_value=[prs_template, dem_template],
        ),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", side_effect=[{"ἐγώ"}, set()]),
        patch("okfbuild.sources.eee_engine.llm_gap_filler.fill_gap") as mock_fill_gap,
    ):
        result = collect_slot_forms("ἐγώ", "pronoun", "grc", gap_filler=gap_filler, cache=cache)

    mock_fill_gap.assert_not_called()
    assert result == {
        "Nom.Sing.Prs": SlotForms(
            forms={"ἐγώ"}, source_type=FormSourceType.RULE_BASED, features=prs_template.features
        )
    }


def test_collect_slot_forms_calls_fill_gap_for_same_family_pronoun_gap():
    """A genuine within-family gap (both templates share PronType=Prs)
    must still reach the LLM -- the filter only blocks cross-family
    cells, not real gaps."""
    known_template = _FakeSlotTemplate("Nom.Sing.Prs", features={"Case": "Nom", "Number": "Sing", "PronType": "Prs"})
    gap_template = _FakeSlotTemplate("Dat.Dual.Prs", features={"Case": "Dat", "Number": "Dual", "PronType": "Prs"})
    gap_filler = Mock()
    cache = Mock()
    with (
        patch(
            "okfbuild.sources.eee_engine.eee.get_slot_templates",
            return_value=[known_template, gap_template],
        ),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", side_effect=[{"ἐγώ"}, set()]),
        patch(
            "okfbuild.sources.eee_engine.llm_gap_filler.fill_gap",
            return_value=_gap_result({"νῶϊν"}),
        ) as mock_fill_gap,
    ):
        result = collect_slot_forms("ἐγώ", "pronoun", "grc", gap_filler=gap_filler, cache=cache)

    mock_fill_gap.assert_called_once_with(
        "ἐγώ", gap_template.features, "pronoun", "grc", gap_filler, cache, context="Dat.Dual.Prs"
    )
    assert result["Dat.Dual.Prs"] == SlotForms(
        forms={"νῶϊν"},
        source_type=FormSourceType.LLM_INFERRED,
        method="llm:gpt-4o-mini",
        llm_backend_version="0.2.1",
        features=gap_template.features,
    )


def test_collect_slot_forms_skips_all_pronoun_gap_fill_when_family_undetermined():
    """If rule-based inflection has zero successes for this lemma, its
    PronType family is unknowable -- guessing which of the mixed
    templates apply would be exactly the wasteful cross-product this
    filter exists to prevent, so skip gap-filling entirely rather than
    querying every family."""
    templates = [
        _FakeSlotTemplate("Nom.Sing.Prs", features={"Case": "Nom", "Number": "Sing", "PronType": "Prs"}),
        _FakeSlotTemplate("Nom.Sing.Dem", features={"Case": "Nom", "Number": "Sing", "PronType": "Dem"}),
    ]
    gap_filler = Mock()
    cache = Mock()
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=templates),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", return_value=set()),
        patch("okfbuild.sources.eee_engine.llm_gap_filler.fill_gap") as mock_fill_gap,
    ):
        result = collect_slot_forms("unknown-pronoun", "pronoun", "grc", gap_filler=gap_filler, cache=cache)

    mock_fill_gap.assert_not_called()
    assert result == {}


def test_collect_slot_forms_warns_once_when_pronoun_family_undetermined(caplog):
    templates = [
        _FakeSlotTemplate("Nom.Sing.Prs", features={"Case": "Nom", "Number": "Sing", "PronType": "Prs"}),
        _FakeSlotTemplate("Nom.Sing.Dem", features={"Case": "Nom", "Number": "Sing", "PronType": "Dem"}),
    ]
    gap_filler = Mock()
    cache = Mock()
    with (
        caplog.at_level(logging.WARNING, logger=_LOGGER_NAME),
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=templates),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", return_value=set()),
        patch("okfbuild.sources.eee_engine.llm_gap_filler.fill_gap"),
    ):
        collect_slot_forms("unknown-pronoun", "pronoun", "grc", gap_filler=gap_filler, cache=cache)

    assert caplog.text.lower().count("skipping llm gap-fill entirely") == 1
    assert "unknown-pronoun" in caplog.text


def test_collect_slot_forms_pronoun_filter_does_not_apply_to_other_pos():
    """A non-pronoun POS must never trigger the PronType filter, even if a
    template's features dict happens to contain a PronType-like key --
    the gate is pos == "pronoun", not the presence of any specific
    feature."""
    template = _FakeSlotTemplate("Nom.Sing", features={"Case": "Nom", "PronType": "Dem"})
    gap_filler = Mock()
    cache = Mock()
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=[template]),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", return_value=set()),
        patch(
            "okfbuild.sources.eee_engine.llm_gap_filler.fill_gap",
            return_value=_gap_result({"form"}),
        ) as mock_fill_gap,
    ):
        result = collect_slot_forms("word", "noun", "grc", gap_filler=gap_filler, cache=cache)

    mock_fill_gap.assert_called_once()
    assert result["Nom.Sing"].source_type == FormSourceType.LLM_INFERRED


# --- New tests: "not a word in this language" exceptions --------------------


@pytest.mark.parametrize(
    "exception_cls",
    [NotInGreekException, NotLegalAdjectiveException, NotLegalPronounException, NotLegalVerbException],
)
def test_collect_slot_forms_catches_not_a_modern_greek_word_exceptions(exception_cls):
    """modern_greek_backend_eee raises one of these four types (never
    returns a clean empty result) when a lemma simply isn't a word in the
    target language -- must be treated like "no rule-based form", not let
    the whole call blow up. Parametrized so a regression on any one of
    the four is individually named, not lost in "somewhere". Covers every
    ancient-only pronoun (σύ, τίς, μιν, ὅδε, ...), which used to need its
    own separate, deliberately-broader-net test here because
    modern_greek_inflexion_eee's pronoun path raised a bare `ValueError`
    -- now NotLegalPronounException, an unambiguous signal like the other
    three (see modern-greek-inflexion-eee's CHANGELOG, 2.1.10)."""
    templates = [_FakeSlotTemplate("Nom.Sing"), _FakeSlotTemplate("Gen.Sing")]
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=templates),
        patch(
            "okfbuild.sources.eee_engine.eee.inflect_slot", side_effect=exception_cls()
        ) as mock_inflect,
    ):
        result = collect_slot_forms("not-a-real-word", "noun", "el")

    mock_inflect.assert_called_once()
    assert result == {}


def test_collect_slot_forms_not_a_word_exception_short_circuits_remaining_templates_and_gap_fill():
    templates = [
        _FakeSlotTemplate("Nom.Sing", features={"Case": "Nom"}),
        _FakeSlotTemplate("Gen.Sing", features={"Case": "Gen"}),
        _FakeSlotTemplate("Dat.Sing", features={"Case": "Dat"}),
    ]
    gap_filler = Mock()
    cache = Mock()
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=templates),
        patch(
            "okfbuild.sources.eee_engine.eee.inflect_slot", side_effect=NotInGreekException()
        ) as mock_inflect,
        patch("okfbuild.sources.eee_engine.llm_gap_filler.fill_gap") as mock_fill_gap,
    ):
        result = collect_slot_forms("ξένη-λέξη", "noun", "el", gap_filler=gap_filler, cache=cache)

    mock_inflect.assert_called_once()  # only the first template is ever attempted
    mock_fill_gap.assert_not_called()
    assert result == {}


def test_collect_slot_forms_not_a_word_exception_is_logged(caplog):
    templates = [_FakeSlotTemplate("Nom.Sing")]
    with (
        caplog.at_level(logging.INFO, logger=_LOGGER_NAME),
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=templates),
        patch(
            "okfbuild.sources.eee_engine.eee.inflect_slot", side_effect=NotLegalVerbException()
        ),
    ):
        collect_slot_forms("ξένη-λέξη", "verb", "el")

    assert "ξένη-λέξη" in caplog.text
    assert "NotLegalVerbException" in caplog.text
