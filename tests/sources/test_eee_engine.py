from unittest.mock import patch

from okfbuild.sources.eee_engine import inflect_all_attested


class _FakeSlotTemplate:
    def __init__(self, label):
        self.label = label


def test_inflect_all_attested_returns_nonempty_dict_for_known_lemma():
    templates = [_FakeSlotTemplate("Nom.Sing"), _FakeSlotTemplate("Gen.Sing")]
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=templates) as mock_templates,
        patch(
            "okfbuild.sources.eee_engine.eee.inflect_slot",
            side_effect=[{"θεός"}, {"θεοῦ"}],
        ) as mock_inflect,
    ):
        result = inflect_all_attested("θεός", "noun", "grc")

    assert result == {"Nom.Sing": {"θεός"}, "Gen.Sing": {"θεοῦ"}}
    mock_templates.assert_called_once_with("grc", "noun", "en", backend=None)
    mock_inflect.assert_any_call("θεός", templates[0], "noun", language="grc", backend=None)
    mock_inflect.assert_any_call("θεός", templates[1], "noun", language="grc", backend=None)


def test_inflect_all_attested_returns_empty_dict_for_unknown_lemma():
    templates = [_FakeSlotTemplate("Nom.Sing"), _FakeSlotTemplate("Gen.Sing")]
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=templates),
        patch("okfbuild.sources.eee_engine.eee.inflect_slot", return_value=set()),
    ):
        result = inflect_all_attested("not-a-real-lemma", "noun", "grc")

    assert result == {}


def test_inflect_all_attested_passes_backend_through_to_both_calls():
    templates = [_FakeSlotTemplate("Nom.Sing")]
    with (
        patch("okfbuild.sources.eee_engine.eee.get_slot_templates", return_value=templates) as mock_templates,
        patch(
            "okfbuild.sources.eee_engine.eee.inflect_slot", return_value={"νόστος"}
        ) as mock_inflect,
    ):
        result = inflect_all_attested("νόστος", "noun", "grc", backend="homeric")

    assert result == {"Nom.Sing": {"νόστος"}}
    mock_templates.assert_called_once_with("grc", "noun", "en", backend="homeric")
    mock_inflect.assert_called_once_with("νόστος", templates[0], "noun", language="grc", backend="homeric")
