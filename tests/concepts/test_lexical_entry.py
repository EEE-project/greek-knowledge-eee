import shutil
import urllib.parse
from pathlib import Path
from unittest.mock import Mock

import pytest

from okfbuild.concepts.lexical_entry import build
from okfbuild.okf import Source
from okfbuild.sources import SourceBundle
from okfbuild.sources.byzantine_lexicon import load_byzantine_forms
from okfbuild.sources.eee_engine import FormSourceType, SlotForms
from okfbuild.sources.llm_gap_filler import GapFillerConfig, LLMModelConfig
from okfbuild.sources.morpheus_client import MorpheusClient
from okfbuild.sources.wiktextract_index import WiktextractIndex

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "concepts"
BYZANTINE_FIXTURE = Path(__file__).parent.parent / "fixtures" / "sources" / "byzantine_verbs_sample.yaml"


def _rule_based(forms_by_label: dict) -> dict:
    return {label: SlotForms(forms=forms, source_type=FormSourceType.RULE_BASED) for label, forms in forms_by_label.items()}


def _llm_inferred(forms_by_label: dict, method: str, llm_backend_version: str = "0.2.1") -> dict:
    return {
        label: SlotForms(
            forms=forms, source_type=FormSourceType.LLM_INFERRED, method=method, llm_backend_version=llm_backend_version
        )
        for label, forms in forms_by_label.items()
    }


def _eee_engine_stub(grc_forms_by_backend=None, el_forms=None):
    """Stub matching collect_slot_forms()'s real per-period backend
    scoping: for language="grc", the result depends on which `backend`
    name is passed (keyed in grc_forms_by_backend), not just the lemma —
    mirroring how a real caller would register distinct
    AncientGreekBackend.for_period(...) instances under period-named
    backend labels (e.g. backend="homeric" vs backend="attic"). Values are
    dict[str, SlotForms] (built via _rule_based()/_llm_inferred() above),
    matching collect_slot_forms()'s real return shape."""
    engine = Mock()

    def _collect(lemma, pos, language, backend=None, gap_filler=None, cache=None, source_course=None):
        if language == "el":
            return el_forms or {}
        return (grc_forms_by_backend or {}).get(backend, {})

    engine.collect_slot_forms.side_effect = _collect
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
        eee_engine=_eee_engine_stub(grc_forms_by_backend={"homeric": _rule_based({"Nom.Sing": {"νόστος"}})}),
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
            grc_forms_by_backend={"homeric": _rule_based({"Nom.Sing": {"νόστος"}})},
            el_forms=_rule_based({"Nom.Sing": {"νόστος"}}),
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
        eee_engine=_eee_engine_stub(grc_forms_by_backend={"homeric": _rule_based({"Nom.Sing": {"νόστος"}})}),
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
        eee_engine=_eee_engine_stub(grc_forms_by_backend={"homeric": _rule_based({"Nom.Sing": {"νόστος"}})}),
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
        eee_engine=_eee_engine_stub(grc_forms_by_backend={"homeric": _rule_based({"Nom.Sing": {"νόστος"}})}),
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


# --- LLM gap-filler citation model -------------------------------------------


def test_build_passes_non_none_cache_whenever_gap_filler_is_configured():
    """Regression test for a real bug found in review: collect_slot_forms()
    raises ValueError whenever gap_filler is set but cache is None (section-02's
    own defensive guard) -- build() must never call it with gap_filler set and
    cache omitted/None, or the very first real use of sources.llm_gap_filler
    would crash inside collect_slot_forms(). Uses the real _eee_engine_stub
    (a Mock()) so this checks the actual kwargs build() passes, not just that
    the call happens to succeed against a permissive stub."""
    engine = _eee_engine_stub(grc_forms_by_backend={"homeric": _rule_based({"Nom.Sing": {"νόστος"}})})
    gap_filler = GapFillerConfig(
        models=(LLMModelConfig(name="a", model="gpt-4o-mini", api_key_env="TEST_LLM_KEY"),)
    )
    sources = SourceBundle(
        eee_engine=engine,
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(),
        wikipedia=Mock(),
        llm_gap_filler=gap_filler,
    )

    build("νόστος", "noun", ["homeric"], sources, level=["B1"], tags=["test"])

    engine.collect_slot_forms.assert_called_once()
    call_kwargs = engine.collect_slot_forms.call_args.kwargs
    assert call_kwargs.get("gap_filler") is gap_filler
    assert call_kwargs.get("cache") is not None


def test_build_forwards_source_course_to_both_ancient_and_modern_call_sites():
    engine = _eee_engine_stub(
        grc_forms_by_backend={"homeric": _rule_based({"Nom.Sing": {"νόστος"}})},
        el_forms=_rule_based({"Nom.Sing": {"νόστος"}}),
    )
    sources = SourceBundle(
        eee_engine=engine,
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(),
        wikipedia=Mock(),
    )

    build("νόστος", "noun", ["homeric", "modern"], sources, level=["B1"], tags=["test"], source_course="odyssey")

    assert engine.collect_slot_forms.call_count == 2
    for call in engine.collect_slot_forms.call_args_list:
        assert call.kwargs.get("source_course") == "odyssey"


def test_build_omitting_source_course_defaults_to_none():
    engine = _eee_engine_stub(grc_forms_by_backend={"homeric": _rule_based({"Nom.Sing": {"νόστος"}})})
    sources = SourceBundle(
        eee_engine=engine,
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(),
        wikipedia=Mock(),
    )

    build("νόστος", "noun", ["homeric"], sources, level=["B1"], tags=["test"])

    assert engine.collect_slot_forms.call_args.kwargs.get("source_course") is None


def test_build_output_unchanged_when_no_gap_filler_configured(morpheus_client, wiktextract_index):
    """Regression/snapshot test, not just 'no exception raised': with no
    llm_gap_filler on SourceBundle (today's default), build()'s output
    must be byte-identical to before this change. Touches homeric +
    modern + beekes in one call to exercise every RULE_BASED-only code
    path at once. Expected values below were captured from an actual run
    of this exact call against this section's own implementation."""
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(
            grc_forms_by_backend={"homeric": _rule_based({"Nom.Sing": {"νόστος"}})},
            el_forms=_rule_based({"Nom.Sing": {"νόστος"}}),
        ),
        morpheus=morpheus_client,
        byzantine_forms={},
        wiktextract=wiktextract_index,
        lsj=Mock(),
        wikipedia=Mock(),
    )

    concept = build(
        "νόστος",
        "noun",
        ["homeric", "modern"],
        sources,
        level=["B1"],
        tags=["test"],
        beekes_citation="From PIE *nes- 'return safely, come home'.",
    )

    # Full-content comparison, captured from an actual run of this exact
    # call (not hand-typed) — the point is to catch ANY change to the
    # RULE_BASED-only rendering path, not just the presence/absence of a
    # marker.
    assert concept.body == (
        "## Homeric\n\n"
        "Attested forms: Nom.Sing: νόστος[^eee-homeric]\n\n"
        "Independently confirmed by Morpheus analysis (νόστος)[^morpheus-homeric]\n\n"
        "## Modern\n\n"
        "Attested forms: Nom.Sing: νόστος[^eee-modern]\n\n"
        "homecoming, return (literary)[^wiktextract-modern]\n\n"
        "## Etymology\n\n"
        "From PIE *nes- 'return safely, come home'.[^beekes-edg]"
    )
    assert concept.sources == [
        Source(
            id="eee-homeric",
            resource="https://codeberg.org/EEE-project/eee-project",
            title="EEE morphology engine",
            author="EEE project",
        ),
        Source(
            id="morpheus-homeric",
            resource="https://services.perseids.org/bsp/morphologyservice/analysis/word",
            title="Perseids Morpheus",
            author="Perseids Project",
        ),
        Source(
            id="eee-modern",
            resource="https://codeberg.org/EEE-project/eee-project",
            title="EEE morphology engine",
            author="EEE project",
        ),
        Source(
            id="wiktextract-modern",
            resource="https://kaikki.org/elwiktionary/",
            title="Wiktextract (kaikki.org)",
            author="kaikki.org",
        ),
        Source(
            id="beekes-edg",
            resource="Beekes (2010), Etymological Dictionary of Greek",
            title="Etymological Dictionary of Greek",
            author="Robert Beekes",
        ),
    ]
    assert concept.extra_frontmatter == {"lemma": "νόστος", "periods": ["homeric", "modern"]}


def test_build_llm_inferred_slot_gets_distinct_source_and_dagger_marker():
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(
            grc_forms_by_backend={"homeric": _llm_inferred({"Gen.Sing": {"νόστου"}}, method="llm:gpt-4o-mini")}
        ),
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(),
        wikipedia=Mock(),
    )

    concept = build("νόστος", "noun", ["homeric"], sources, level=["B1"], tags=["test"])

    llm_source_ids = {s.id for s in concept.sources if s.id.startswith("llm-gap-filler-")}
    assert len(llm_source_ids) == 1
    (llm_source_id,) = llm_source_ids
    assert f"[^{llm_source_id}]" in concept.body
    assert "νόστου†" in concept.body
    assert not any(s.id in {"eee-homeric"} for s in concept.sources)  # no rule-based data for this period
    assert concept.body.count("LLM-inferred (unverified) form") == 1  # legend present, exactly once


def test_build_two_llm_inferred_labels_same_period_same_method_dedupe_to_one_source():
    """Two DIFFERENT labels within the SAME period, both LLM-inferred by
    the same method, must produce exactly one LLM-gap-filler Source —
    the other half of the plan's dedup requirement (the sibling test
    below covers the cross-period half)."""
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(
            grc_forms_by_backend={
                "homeric": _llm_inferred(
                    {"Gen.Sing": {"νόστου"}, "Dat.Sing": {"νόστῳ"}}, method="llm:gpt-4o-mini"
                )
            }
        ),
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(),
        wikipedia=Mock(),
    )

    concept = build("νόστος", "noun", ["homeric"], sources, level=["B1"], tags=["test"])

    llm_source_ids = [s.id for s in concept.sources if s.id.startswith("llm-gap-filler-")]
    assert len(llm_source_ids) == 1
    (llm_source_id,) = llm_source_ids
    assert concept.body.count(f"[^{llm_source_id}]") == 1  # one combined line, one reference
    assert "νόστου" in concept.body
    assert "νόστῳ" in concept.body


def test_build_two_llm_inferred_slots_same_method_dedupe_to_one_source():
    """Same method reused across two different periods (homeric + attic)
    within one build() call must still collapse to exactly one
    LLM-gap-filler Source — cite()'s dedup is keyed on a method-derived
    source_id, not a period-derived one."""
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(
            grc_forms_by_backend={
                "homeric": _llm_inferred({"Gen.Sing": {"νόστου"}}, method="llm:gpt-4o-mini"),
                "attic": _llm_inferred({"Gen.Sing": {"νόστου"}}, method="llm:gpt-4o-mini"),
            }
        ),
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(),
        wikipedia=Mock(),
    )

    concept = build("νόστος", "noun", ["homeric", "attic"], sources, level=["B1"], tags=["test"])

    llm_source_ids = [s.id for s in concept.sources if s.id.startswith("llm-gap-filler-")]
    assert len(llm_source_ids) == 1
    (llm_source_id,) = llm_source_ids
    assert concept.body.count(f"[^{llm_source_id}]") == 2  # both periods reference the same source
    assert concept.body.count("LLM-inferred (unverified) form") == 1  # legend once, not once per period


def test_build_llm_marker_and_source_never_leak_into_rule_based_or_disabled_output():
    mixed_sources = SourceBundle(
        eee_engine=_eee_engine_stub(
            grc_forms_by_backend={
                "homeric": {
                    **_rule_based({"Nom.Sing": {"νόστος"}}),
                    **_llm_inferred({"Gen.Sing": {"νόστου"}}, method="llm:gpt-4o-mini"),
                }
            }
        ),
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(),
        wikipedia=Mock(),
    )

    mixed_concept = build("νόστος", "noun", ["homeric"], mixed_sources, level=["B1"], tags=["test"])

    # The rule-based line itself must never carry the marker.
    rule_based_line = next(line for line in mixed_concept.body.splitlines() if line.startswith("Attested forms:"))
    assert "†" not in rule_based_line

    # A separate, later build() call using only RULE_BASED data must show
    # neither the marker nor the LLM Source — confirms no leakage across
    # build() invocations via any shared/module-level state.
    rule_based_only_sources = SourceBundle(
        eee_engine=_eee_engine_stub(grc_forms_by_backend={"homeric": _rule_based({"Nom.Sing": {"νόστος"}})}),
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(),
        wikipedia=Mock(),
    )
    rule_based_only_concept = build("νόστος", "noun", ["homeric"], rule_based_only_sources, level=["B1"], tags=["test"])

    assert "†" not in rule_based_only_concept.body
    assert not any(s.id.startswith("llm-gap-filler-") for s in rule_based_only_concept.sources)
