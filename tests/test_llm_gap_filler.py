import logging
import threading
import time
import unicodedata
from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock, patch

import pytest

from okfbuild.sources.llm_gap_filler import (
    REQUEST_BUDGET_ERROR,
    GapFillCache,
    GapFillerConfig,
    LLMModelConfig,
    SampleStatus,
    fill_gap,
    normalize_form,
)

_LOGGER_NAME = "okfbuild.sources.llm_gap_filler"


def _model(name="model-a", model="gpt-4o-mini", api_key_env="TEST_KEY_A", base_url=None):
    return LLMModelConfig(name=name, model=model, api_key_env=api_key_env, base_url=base_url)


def _mock_backend(forms=frozenset({"form"}), *, raises=None):
    """Returns a construct() callable to patch LLMBackend's side_effect with,
    where every call to LLMBackend(model=, api_key=, base_url=) returns a
    fresh mock instance whose .inflect() always returns `forms` (or raises
    `raises` if given)."""

    def construct(*, model, api_key, base_url, use_cache):
        instance = MagicMock()
        if raises is not None:
            instance.inflect.side_effect = raises
        else:
            instance.inflect.return_value = set(forms)
        return instance

    return construct


# --- Configuration surface ---------------------------------------------------


def test_llm_model_config_constructs_with_all_fields_base_url_defaults_none():
    config = LLMModelConfig(name="a", model="gpt-4o-mini", api_key_env="KEY_A")
    assert config.name == "a"
    assert config.model == "gpt-4o-mini"
    assert config.api_key_env == "KEY_A"
    assert config.base_url is None


def test_gap_filler_config_constructs_with_one_model_samples_per_model_defaults_to_1():
    config = GapFillerConfig(models=(_model(),))
    assert config.samples_per_model == 1


def test_gap_filler_config_empty_models_raises_value_error():
    with pytest.raises(ValueError):
        GapFillerConfig(models=())


def test_gap_filler_config_zero_samples_per_model_raises_value_error():
    with pytest.raises(ValueError):
        GapFillerConfig(models=(_model(),), samples_per_model=0)


def test_gap_filler_config_negative_samples_per_model_raises_value_error():
    with pytest.raises(ValueError):
        GapFillerConfig(models=(_model(),), samples_per_model=-1)


def test_gap_filler_config_non_positive_max_requests_per_run_raises_value_error():
    with pytest.raises(ValueError):
        GapFillerConfig(models=(_model(),), max_requests_per_run=0)
    with pytest.raises(ValueError):
        GapFillerConfig(models=(_model(),), max_requests_per_run=-1)


def test_gap_filler_config_duplicate_model_names_raise_value_error():
    with pytest.raises(ValueError):
        GapFillerConfig(
            models=(
                _model(name="dup", api_key_env="KEY_A"),
                _model(name="dup", api_key_env="KEY_B"),
            )
        )


def test_gap_filler_config_models_is_a_tuple_and_instance_is_frozen():
    config = GapFillerConfig(models=(_model(),))
    assert isinstance(config.models, tuple)
    with pytest.raises(FrozenInstanceError):
        config.models = (_model(),)


# --- normalize_form() ---------------------------------------------------


def test_normalize_form_nfc_nfd_equivalent_forms_normalize_the_same():
    nfc = unicodedata.normalize("NFC", "καλός")
    nfd = unicodedata.normalize("NFD", "καλός")
    assert nfc != nfd  # sanity: genuinely different raw representations
    assert normalize_form(nfc) == normalize_form(nfd)


def test_normalize_form_strips_incidental_whitespace():
    assert normalize_form("  θεός  ") == normalize_form("θεός")


def test_normalize_form_keeps_genuinely_different_forms_distinct():
    assert normalize_form("θεός") != normalize_form("θεοῦ")


# --- fill_gap(): sampling and agreement --------------------------------------


def test_fill_gap_one_model_one_sample_success(monkeypatch):
    monkeypatch.setenv("TEST_KEY_A", "secret")
    config = GapFillerConfig(models=(_model(),), samples_per_model=1)
    cache = GapFillCache()

    with patch(
        "okfbuild.sources.llm_gap_filler.LLMBackend", side_effect=_mock_backend(forms={"θεοῦ"})
    ):
        result = fill_gap("θεός", {"Case": "Gen"}, "noun", "grc", config, cache)

    assert result.forms == {"θεοῦ"}
    assert result.sample_statuses == (SampleStatus.SUCCESS,)


def test_fill_gap_context_reaches_every_sample_call_as_label(monkeypatch):
    monkeypatch.setenv("TEST_KEY_A", "secret")
    config = GapFillerConfig(models=(_model(),), samples_per_model=3)
    cache = GapFillCache()

    lock = threading.Lock()
    received_labels = []

    def construct(*, model, api_key, base_url, use_cache):
        instance = MagicMock()

        def _inflect(*args, **kwargs):
            with lock:
                received_labels.append(kwargs.get("label"))
            return {"θεοῦ"}

        instance.inflect.side_effect = _inflect
        return instance

    with patch("okfbuild.sources.llm_gap_filler.LLMBackend", side_effect=construct):
        fill_gap("θεός", {"Case": "Gen"}, "noun", "grc", config, cache, context="Gen.Sing, period=homeric")

    assert received_labels == ["Gen.Sing, period=homeric"] * 3


def test_fill_gap_one_model_three_samples_agree_after_normalization(monkeypatch):
    monkeypatch.setenv("TEST_KEY_A", "secret")
    config = GapFillerConfig(models=(_model(),), samples_per_model=3)
    cache = GapFillCache()

    raw_variants = [
        {unicodedata.normalize("NFC", "θεοῦ")},
        {unicodedata.normalize("NFD", "θεοῦ")},
        {"  θεοῦ  "},
    ]
    lock = threading.Lock()
    counter = {"n": 0}

    def construct(*, model, api_key, base_url, use_cache):
        instance = MagicMock()

        def _inflect(*args, **kwargs):
            with lock:
                idx = counter["n"]
                counter["n"] += 1
            return raw_variants[idx]

        instance.inflect.side_effect = _inflect
        return instance

    with patch("okfbuild.sources.llm_gap_filler.LLMBackend", side_effect=construct):
        result = fill_gap("θεός", {"Case": "Gen"}, "noun", "grc", config, cache)

    assert result.forms  # accepted -- non-empty
    assert len(result.sample_statuses) == 3
    assert all(status is SampleStatus.SUCCESS for status in result.sample_statuses)


def test_fill_gap_two_models_two_samples_each_equal_weighting(monkeypatch):
    monkeypatch.setenv("TEST_KEY_A", "secret-a")
    monkeypatch.setenv("TEST_KEY_B", "secret-b")
    model_a = _model(name="a", model="model-a", api_key_env="TEST_KEY_A")
    model_b = _model(name="b", model="model-b", api_key_env="TEST_KEY_B")
    config = GapFillerConfig(models=(model_a, model_b), samples_per_model=2)
    cache = GapFillCache()

    lock = threading.Lock()
    constructed_for = []

    def construct(*, model, api_key, base_url, use_cache):
        with lock:
            constructed_for.append(model)
        instance = MagicMock()
        instance.inflect.return_value = {"form"}
        return instance

    with patch("okfbuild.sources.llm_gap_filler.LLMBackend", side_effect=construct):
        fill_gap("lemma", {}, "noun", "grc", config, cache)

    assert constructed_for.count("model-a") == 2
    assert constructed_for.count("model-b") == 2
    assert len(constructed_for) == 4


def test_fill_gap_disagreement_among_success_samples_yields_empty_result(monkeypatch, caplog):
    monkeypatch.setenv("TEST_KEY_A", "secret")
    config = GapFillerConfig(models=(_model(),), samples_per_model=2)
    cache = GapFillCache()

    variants = [{"θεοῦ"}, {"θεοῖο"}]
    lock = threading.Lock()
    counter = {"n": 0}

    def construct(*, model, api_key, base_url, use_cache):
        instance = MagicMock()

        def _inflect(*args, **kwargs):
            with lock:
                idx = counter["n"]
                counter["n"] += 1
            return variants[idx]

        instance.inflect.side_effect = _inflect
        return instance

    with (
        caplog.at_level(logging.WARNING, logger=_LOGGER_NAME),
        patch("okfbuild.sources.llm_gap_filler.LLMBackend", side_effect=construct),
    ):
        result = fill_gap("θεός", {}, "noun", "grc", config, cache)

    assert result.forms == set()
    assert all(status is SampleStatus.SUCCESS for status in result.sample_statuses)
    assert "disagree" in caplog.text.lower()


def test_fill_gap_all_abstained_yields_empty_result_and_distinct_warning(monkeypatch, caplog):
    monkeypatch.setenv("TEST_KEY_A", "secret")
    config = GapFillerConfig(models=(_model(),), samples_per_model=3)
    cache = GapFillCache()

    with (
        caplog.at_level(logging.WARNING, logger=_LOGGER_NAME),
        patch("okfbuild.sources.llm_gap_filler.LLMBackend", side_effect=_mock_backend(forms=set())),
    ):
        result = fill_gap("obscure-lemma", {}, "noun", "grc", config, cache)

    assert result.forms == set()
    assert all(status is SampleStatus.ABSTAINED for status in result.sample_statuses)
    assert "abstain" in caplog.text.lower()


def test_fill_gap_all_call_failed_yields_empty_result_no_raise_distinct_warning(monkeypatch, caplog):
    monkeypatch.setenv("TEST_KEY_A", "secret")
    config = GapFillerConfig(models=(_model(),), samples_per_model=3)
    cache = GapFillCache()

    with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME), patch(
        "okfbuild.sources.llm_gap_filler.LLMBackend",
        side_effect=_mock_backend(raises=RuntimeError("boom")),
    ):
        result = fill_gap("lemma", {}, "noun", "grc", config, cache)  # must not raise

    assert result.forms == set()
    assert all(status is SampleStatus.CALL_FAILED for status in result.sample_statuses)
    assert "failed" in caplog.text.lower()


def test_fill_gap_mixed_success_and_failure_does_not_accept_lone_success(monkeypatch, caplog):
    monkeypatch.setenv("TEST_KEY_A", "secret")
    config = GapFillerConfig(models=(_model(),), samples_per_model=2)
    cache = GapFillCache()

    lock = threading.Lock()
    counter = {"n": 0}

    def construct(*, model, api_key, base_url, use_cache):
        instance = MagicMock()

        def _inflect(*args, **kwargs):
            with lock:
                idx = counter["n"]
                counter["n"] += 1
            if idx == 0:
                return {"θεοῦ"}
            raise RuntimeError("boom")

        instance.inflect.side_effect = _inflect
        return instance

    with (
        caplog.at_level(logging.WARNING, logger=_LOGGER_NAME),
        patch("okfbuild.sources.llm_gap_filler.LLMBackend", side_effect=construct),
    ):
        result = fill_gap("lemma", {}, "noun", "grc", config, cache)

    assert result.forms == set()
    assert "mixed" in caplog.text.lower()


def test_fill_gap_missing_api_key_env_var_surfaces_as_call_failed(monkeypatch, caplog):
    monkeypatch.delenv("TEST_KEY_MISSING", raising=False)
    config = GapFillerConfig(models=(_model(api_key_env="TEST_KEY_MISSING"),), samples_per_model=1)
    cache = GapFillCache()

    with (
        caplog.at_level(logging.WARNING, logger=_LOGGER_NAME),
        patch("okfbuild.sources.llm_gap_filler.LLMBackend") as mock_cls,
    ):
        result = fill_gap("lemma", {}, "noun", "grc", config, cache)

    assert result.sample_statuses == (SampleStatus.CALL_FAILED,)
    mock_cls.assert_not_called()


def test_fill_gap_calls_run_concurrently_not_sequentially(monkeypatch):
    monkeypatch.setenv("TEST_KEY_A", "secret")
    n_samples = 5
    delay_seconds = 0.2
    config = GapFillerConfig(models=(_model(),), samples_per_model=n_samples)
    cache = GapFillCache()

    def construct(*, model, api_key, base_url, use_cache):
        instance = MagicMock()

        def _inflect(*args, **kwargs):
            time.sleep(delay_seconds)
            return {"form"}

        instance.inflect.side_effect = _inflect
        return instance

    start = time.monotonic()
    with patch("okfbuild.sources.llm_gap_filler.LLMBackend", side_effect=construct):
        fill_gap("lemma", {}, "noun", "grc", config, cache)
    elapsed = time.monotonic() - start

    # Sequential execution would take ~n_samples * delay_seconds (1.0s here);
    # concurrent execution should land close to a single delay (~0.2s).
    assert elapsed < n_samples * delay_seconds * 0.6


# --- GapFillCache -------------------------------------------------------


def test_gap_fill_cache_identical_request_twice_issues_only_one_call_batch(monkeypatch):
    monkeypatch.setenv("TEST_KEY_A", "secret")
    config = GapFillerConfig(models=(_model(),), samples_per_model=1)
    cache = GapFillCache()

    constructed = []

    def construct(*, model, api_key, base_url, use_cache):
        constructed.append(1)
        instance = MagicMock()
        instance.inflect.return_value = {"form"}
        return instance

    with patch("okfbuild.sources.llm_gap_filler.LLMBackend", side_effect=construct):
        first = fill_gap("lemma", {"Case": "Gen"}, "noun", "grc", config, cache)
        second = fill_gap("lemma", {"Case": "Gen"}, "noun", "grc", config, cache)

    assert len(constructed) == 1
    assert first == second


def test_gap_fill_cache_negative_result_is_also_cached(monkeypatch):
    monkeypatch.setenv("TEST_KEY_A", "secret")
    config = GapFillerConfig(models=(_model(),), samples_per_model=1)
    cache = GapFillCache()

    constructed = []

    def construct(*, model, api_key, base_url, use_cache):
        constructed.append(1)
        instance = MagicMock()
        instance.inflect.return_value = set()  # abstain -> negative result
        return instance

    with patch("okfbuild.sources.llm_gap_filler.LLMBackend", side_effect=construct):
        fill_gap("lemma", {}, "noun", "grc", config, cache)
        fill_gap("lemma", {}, "noun", "grc", config, cache)

    assert len(constructed) == 1


def test_gap_fill_cache_different_features_dict_order_is_still_a_hit_but_different_content_is_a_miss(monkeypatch):
    monkeypatch.setenv("TEST_KEY_A", "secret")
    config = GapFillerConfig(models=(_model(),), samples_per_model=1)
    cache = GapFillCache()

    constructed = []

    def construct(*, model, api_key, base_url, use_cache):
        constructed.append(1)
        instance = MagicMock()
        instance.inflect.return_value = {"form"}
        return instance

    with patch("okfbuild.sources.llm_gap_filler.LLMBackend", side_effect=construct):
        fill_gap("lemma", {"Case": "Gen", "Number": "Sing"}, "noun", "grc", config, cache)
        fill_gap("lemma", {"Number": "Sing", "Case": "Gen"}, "noun", "grc", config, cache)  # same content, different order
        fill_gap("lemma", {"Case": "Nom", "Number": "Sing"}, "noun", "grc", config, cache)  # genuinely different

    assert len(constructed) == 2


def test_gap_fill_cache_different_model_config_is_a_cache_miss(monkeypatch):
    monkeypatch.setenv("TEST_KEY_A", "secret")
    monkeypatch.setenv("TEST_KEY_B", "secret")
    config_a = GapFillerConfig(models=(_model(name="a", api_key_env="TEST_KEY_A"),), samples_per_model=1)
    config_b = GapFillerConfig(models=(_model(name="b", api_key_env="TEST_KEY_B"),), samples_per_model=1)
    cache = GapFillCache()

    constructed = []

    def construct(*, model, api_key, base_url, use_cache):
        constructed.append(1)
        instance = MagicMock()
        instance.inflect.return_value = {"form"}
        return instance

    with patch("okfbuild.sources.llm_gap_filler.LLMBackend", side_effect=construct):
        fill_gap("lemma", {}, "noun", "grc", config_a, cache)
        fill_gap("lemma", {}, "noun", "grc", config_b, cache)

    assert len(constructed) == 2


def test_gap_fill_cache_different_context_is_a_cache_miss(monkeypatch):
    monkeypatch.setenv("TEST_KEY_A", "secret")
    config = GapFillerConfig(models=(_model(),), samples_per_model=1)
    cache = GapFillCache()

    constructed = []

    def construct(*, model, api_key, base_url, use_cache):
        constructed.append(1)
        instance = MagicMock()
        instance.inflect.return_value = {"form"}
        return instance

    with patch("okfbuild.sources.llm_gap_filler.LLMBackend", side_effect=construct):
        fill_gap("lemma", {}, "noun", "grc", config, cache, context="Gen.Sing")
        fill_gap("lemma", {}, "noun", "grc", config, cache, context="Gen.Sing")  # same context -> hit
        fill_gap("lemma", {}, "noun", "grc", config, cache, context="Gen.Sing, period=attic")  # different -> miss

    assert len(constructed) == 2


def test_gap_fill_cache_miss_return_value_does_not_alias_internal_storage(monkeypatch):
    """A cache MISS returns the exact object fill_gap() just handed to
    cache.set() -- if that return value isn't a copy, a caller mutating
    it in place (result.forms.add(...)) would silently corrupt the
    cache's own stored entry for every future hit on that key."""
    monkeypatch.setenv("TEST_KEY_A", "secret")
    config = GapFillerConfig(models=(_model(),), samples_per_model=1)
    cache = GapFillCache()

    with patch(
        "okfbuild.sources.llm_gap_filler.LLMBackend", side_effect=_mock_backend(forms={"form"})
    ):
        first = fill_gap("lemma", {}, "noun", "grc", config, cache)

    first.forms.add("mutated-in-place")

    key = cache.make_key("lemma", {}, "noun", "grc", config)
    stored = cache.get(key)
    assert "mutated-in-place" not in stored.forms


# --- Request budget -------------------------------------------------------


def test_fill_gap_stops_and_raises_once_budget_exceeded(monkeypatch):
    monkeypatch.setenv("TEST_KEY_A", "secret")
    config = GapFillerConfig(models=(_model(),), samples_per_model=1, max_requests_per_run=1)
    cache = GapFillCache()

    constructed = []

    def construct(*, model, api_key, base_url, use_cache):
        constructed.append(1)
        instance = MagicMock()
        instance.inflect.return_value = {"form"}
        return instance

    with patch("okfbuild.sources.llm_gap_filler.LLMBackend", side_effect=construct):
        fill_gap("lemma-1", {}, "noun", "grc", config, cache)  # consumes the entire budget
        with pytest.raises(RuntimeError, match=REQUEST_BUDGET_ERROR):
            fill_gap("lemma-2", {}, "noun", "grc", config, cache)  # different key -> miss -> budget check fires

    assert len(constructed) == 1
