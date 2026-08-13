"""Shared pytest fixtures for okfbuild's test suite."""

from unittest.mock import Mock

import pytest

from okfbuild.sources import SourceBundle


def _eee_engine_stub(attested_lemmas: set[str]):
    """Lemma-aware stub for SourceBundle.eee_engine: lemmas in
    `attested_lemmas` get a fixed homeric form back (via
    inflect_all_attested's language="grc", backend="homeric" branch, per
    the real per-period backend scoping documented in
    okfbuild/concepts/lexical_entry.py); every other lemma/backend/language
    combination returns empty, so a test can control exactly which
    candidate lemmas end up with attested data."""
    engine = Mock()

    def _inflect(lemma, pos, language, backend=None):
        if lemma in attested_lemmas and language == "grc" and backend == "homeric":
            return {"Nom.Sing": {lemma}}
        return {}

    engine.inflect_all_attested.side_effect = _inflect
    return engine


@pytest.fixture
def make_source_bundle():
    """Factory fixture: make_source_bundle(attested_lemmas={...}) returns a
    SourceBundle whose eee_engine reports attested homeric forms only for
    the given lemmas; every other source client is stubbed to return
    nothing. A lemma not named in attested_lemmas gets no data from any
    source — the "candidate with no data anywhere" case."""

    def _make(attested_lemmas: set[str] = frozenset()) -> SourceBundle:
        return SourceBundle(
            eee_engine=_eee_engine_stub(set(attested_lemmas)),
            morpheus=Mock(analyze=Mock(return_value=[])),
            byzantine_forms={},
            wiktextract=Mock(lookup=Mock(return_value=None)),
            lsj=Mock(),
            wikipedia=Mock(),
        )

    return _make
