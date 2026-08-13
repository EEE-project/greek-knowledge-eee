import shutil
import urllib.parse
from pathlib import Path
from unittest.mock import Mock

import pytest

from okfbuild.concepts.lexical_entry import build
from okfbuild.sources import SourceBundle
from okfbuild.sources.byzantine_lexicon import load_byzantine_forms
from okfbuild.sources.morpheus_client import MorpheusClient
from okfbuild.sources.wiktextract_index import WiktextractIndex

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "concepts"
BYZANTINE_FIXTURE = Path(__file__).parent.parent / "fixtures" / "sources" / "byzantine_verbs_sample.yaml"


def _eee_engine_stub(grc_forms_by_backend=None, el_forms=None):
    """Stub matching inflect_all_attested's real per-period backend
    scoping: for language="grc", the result depends on which `backend`
    name is passed (keyed in grc_forms_by_backend), not just the lemma —
    mirroring how a real caller would register distinct
    AncientGreekBackend.for_period(...) instances under period-named
    backend labels (e.g. backend="homeric" vs backend="attic")."""
    engine = Mock()

    def _inflect(lemma, pos, language, backend=None):
        if language == "el":
            return el_forms or {}
        return (grc_forms_by_backend or {}).get(backend, {})

    engine.inflect_all_attested.side_effect = _inflect
    return engine


@pytest.fixture
def morpheus_client(tmp_path):
    cache_dir = tmp_path / "morpheus_cache"
    cache_dir.mkdir()
    cache_name = urllib.parse.quote("νόστος", safe="") + ".json"
    shutil.copy(FIXTURES_DIR / "morpheus_nostos.json", cache_dir / cache_name)
    return MorpheusClient(cache_dir)


@pytest.fixture
def wiktextract_index():
    return WiktextractIndex.load(FIXTURES_DIR / "wiktextract_nostos.jsonl")


def test_build_single_attested_period_produces_one_section(morpheus_client):
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(grc_forms_by_backend={"homeric": {"Nom.Sing": {"νόστος"}}}),
        morpheus=morpheus_client,
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(),
        wikipedia=Mock(),
    )

    concept = build("νόστος", "noun", ["homeric"], sources, level=["B1"], tags=["test"])

    assert concept.type == "Lexical Entry"
    assert concept.extra_frontmatter["periods"] == ["homeric"]
    assert concept.body.count("## ") == 1
    assert "[^eee-homeric]" in concept.body
    assert "[^morpheus-homeric]" in concept.body
    footnote_ids = {s.id for s in concept.sources}
    assert "eee-homeric" in footnote_ids
    assert "morpheus-homeric" in footnote_ids


def test_build_two_attested_periods_each_get_own_footnote(morpheus_client, wiktextract_index):
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(
            grc_forms_by_backend={"homeric": {"Nom.Sing": {"νόστος"}}},
            el_forms={"Nom.Sing": {"νόστος"}},
        ),
        morpheus=morpheus_client,
        byzantine_forms={},
        wiktextract=wiktextract_index,
        lsj=Mock(),
        wikipedia=Mock(),
    )

    concept = build("νόστος", "noun", ["homeric", "modern"], sources, level=["B1"], tags=["test"])

    assert concept.extra_frontmatter["periods"] == ["homeric", "modern"]
    assert concept.body.count("## ") == 2
    assert "[^eee-homeric]" in concept.body
    assert "[^wiktextract-modern]" in concept.body


def test_build_skips_period_with_no_attested_data(morpheus_client):
    byzantine_forms = load_byzantine_forms(BYZANTINE_FIXTURE)  # δίδωμι/λέγω only, no νόστος (it's a noun)

    sources = SourceBundle(
        eee_engine=_eee_engine_stub(grc_forms_by_backend={"homeric": {"Nom.Sing": {"νόστος"}}}),
        morpheus=morpheus_client,
        byzantine_forms=byzantine_forms,
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(),
        wikipedia=Mock(),
    )

    concept = build("νόστος", "noun", ["homeric", "byzantine"], sources, level=["B1"], tags=["test"])

    assert concept.extra_frontmatter["periods"] == ["homeric"]
    assert concept.body.count("## ") == 1


def test_build_includes_beekes_etymology_section_when_supplied(morpheus_client):
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(grc_forms_by_backend={"homeric": {"Nom.Sing": {"νόστος"}}}),
        morpheus=morpheus_client,
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(),
        wikipedia=Mock(),
    )

    concept = build(
        "νόστος",
        "noun",
        ["homeric"],
        sources,
        level=["B1"],
        tags=["test"],
        beekes_citation="From PIE *nes- 'return safely, come home'.",
    )

    assert "## Etymology" in concept.body
    assert "[^beekes-edg]" in concept.body
    assert any(s.id == "beekes-edg" for s in concept.sources)


def test_build_homeric_and_attic_query_independently_scoped_backends():
    """homeric and attic must each query eee_engine with their own
    backend=period, not share one cached result — a backend registered
    only under "homeric" (simulating AncientGreekBackend.for_period("epic")
    registered under that name) must NOT leak into the attic section."""
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(grc_forms_by_backend={"homeric": {"Nom.Sing": {"νόστος"}}}),
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(),
        wikipedia=Mock(),
    )

    concept = build("νόστος", "noun", ["homeric", "attic"], sources, level=["B1"], tags=["test"])

    assert concept.extra_frontmatter["periods"] == ["homeric"]
    assert concept.body.count("## ") == 1


def test_build_modern_period_labels_multiple_distinct_senses():
    """The per-period sense amendment: >1 sense in the wiktextract entry
    must render as labeled sub-items; a single sense stays plain prose
    (already covered by test_build_two_attested_periods_each_get_own_footnote,
    whose fixture has exactly one sense)."""
    multi_sense_entry = {
        "senses": [
            {"glosses": ["homecoming, return"]},
            {"glosses": ["a narrative of a hero's return journey"]},
        ]
    }
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(el_forms={}),
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=multi_sense_entry)),
        lsj=Mock(),
        wikipedia=Mock(),
    )

    concept = build("νόστος", "noun", ["modern"], sources, level=["B1"], tags=["test"])

    assert "**Sense 1:** homecoming, return" in concept.body
    assert "**Sense 2:** a narrative of a hero's return journey" in concept.body
