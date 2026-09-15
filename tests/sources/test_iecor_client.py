from pathlib import Path

from okfbuild.sources.iecor_client import load_iecor_cognates

FIXTURE = Path(__file__).parent.parent / "fixtures" / "sources" / "iecor_sample.tsv"


def test_load_iecor_cognates_returns_headword_keyed_dict_of_entries():
    result = load_iecor_cognates(FIXTURE)

    assert len(result["νόστος"]) == 1
    entry = result["νόστος"][0]
    assert entry.gloss == "return, homecoming"
    assert entry.root_form == "*nes-"
    assert entry.root_language == "Proto-Indo-European"


def test_load_iecor_cognates_keeps_multiple_entries_for_the_same_headword():
    result = load_iecor_cognates(FIXTURE)

    assert len(result["ὄνυξ"]) == 2
    assert {entry.gloss for entry in result["ὄνυξ"]} == {"fingernail, hoof", "nail, claw, hoof"}


def test_load_iecor_cognates_returns_empty_for_lemma_with_no_entry():
    result = load_iecor_cognates(FIXTURE)

    assert "λέγω" not in result
