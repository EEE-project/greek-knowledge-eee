"""Tests for okfbuild.lookup.lookup_word()."""

from unittest.mock import Mock

from okfbuild.lookup import lookup_word
from okfbuild.sources import SourceBundle
from okfbuild.sources.iecor_client import IECorEntry


def _eee_engine_stub(grc_forms_by_backend=None, el_forms=None):
    engine = Mock()

    def _collect(lemma, pos, language, backend=None, gap_filler=None, cache=None, source_course=None):
        if language == "el":
            return el_forms or {}
        return (grc_forms_by_backend or {}).get(backend, {})

    engine.collect_slot_forms.side_effect = _collect
    return engine


def test_lookup_word_omits_sources_with_no_hit():
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(),
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(lookup=Mock(return_value=None)),
        wikipedia=Mock(),
    )

    assert lookup_word("ἄγνωστος", sources) == {}


def test_lookup_word_includes_every_source_with_a_hit():
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(grc_forms_by_backend={"homeric": {"Nom.Sing": Mock()}}),
        morpheus=Mock(analyze=Mock(return_value=[{"lemma": "νόστος"}])),
        byzantine_forms={"νόστος": {"XAI.3P": "νενόστηκε"}},
        wiktextract=Mock(lookup=Mock(return_value={"senses": [{"glosses": ["return"]}]})),
        lsj=Mock(lookup=Mock(return_value=["some segment"])),
        wikipedia=Mock(),
        iecor={"νόστος": [IECorEntry(gloss="return", root_form="*nes-", root_language="PIE", justification="x")]},
    )

    results = lookup_word("νόστος", sources)

    assert set(results.keys()) == {
        "eee_engine (homeric)", "morpheus", "lsj", "wiktextract", "byzantine_lexicon", "iecor",
    }


def test_lookup_word_omits_wikipedia_always():
    """Wikipedia is keyed by topic/person for Cultural Context entries,
    not by lexeme -- lookup_word never queries it."""
    wikipedia = Mock()
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(),
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(lookup=Mock(return_value=None)),
        wikipedia=wikipedia,
    )

    lookup_word("νόστος", sources)

    assert wikipedia.mock_calls == []
