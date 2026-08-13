from pathlib import Path

from okfbuild.sources.byzantine_lexicon import load_byzantine_forms

FIXTURE = Path(__file__).parent.parent / "fixtures" / "sources" / "byzantine_verbs_sample.yaml"


def test_load_byzantine_forms_returns_lemma_keyed_dict_with_single_and_list_forms():
    result = load_byzantine_forms(FIXTURE)

    assert result["δίδωμι"]["XAI.3P"] == "δέδωκαν"
    assert result["λέγω"]["AAI.3P"] == ["εἴποσαν", "εἴπασι"]
    assert result["λέγω"]["AAO.3P"] == ["εἴποισαν", "εἴπαισαν"]
