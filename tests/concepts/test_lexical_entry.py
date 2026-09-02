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
from okfbuild.sources.llm_gap_filler import (
    GapFillCache,
    GapFillerConfig,
    LLMModelConfig,
)
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


def _no_lsj_entry() -> Mock:
    """A fresh Mock per call (not a shared instance) -- a test that asserts
    on lsj.lookup's call history (e.g. assert_called_once_with) needs its
    own Mock, not one whose history already includes every other test's
    calls."""
    return Mock(lookup=Mock(return_value=None))


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
        lsj=_no_lsj_entry(),
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
        lsj=_no_lsj_entry(),
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
        lsj=_no_lsj_entry(),
        wikipedia=Mock(),
    )

    concept = build("νόστος", "noun", ["homeric", "byzantine"], sources, level=["B1"], tags=["test"])

    assert concept.extra_frontmatter["periods"] == ["homeric"]
    assert concept.body.count("## ") == 1


def test_build_includes_lsj_meaning_section_when_entry_found(morpheus_client):
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(grc_forms_by_backend={"homeric": _rule_based({"Nom.Sing": {"νόστος"}})}),
        morpheus=morpheus_client,
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(lookup=Mock(return_value="return, homecoming; a coming back.")),
        wikipedia=Mock(),
    )

    concept = build("νόστος", "noun", ["homeric"], sources, level=["B1"], tags=["test"])

    assert "## Ancient Greek meaning" in concept.body
    assert "return, homecoming; a coming back." in concept.body
    assert "[^lsj]" in concept.body
    assert "lsj" in {s.id for s in concept.sources}


def test_build_skips_lsj_section_when_no_entry(morpheus_client):
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(grc_forms_by_backend={"homeric": _rule_based({"Nom.Sing": {"νόστος"}})}),
        morpheus=morpheus_client,
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=_no_lsj_entry(),
        wikipedia=Mock(),
    )

    concept = build("νόστος", "noun", ["homeric"], sources, level=["B1"], tags=["test"])

    assert "## Ancient Greek meaning" not in concept.body
    assert "lsj" not in {s.id for s in concept.sources}


def test_build_lsj_meaning_not_duplicated_across_both_ancient_periods(morpheus_client, wiktextract_index):
    """LSJ entries aren't period-scoped -- requesting both homeric and attic
    must still look the lemma up once and render one section, not two."""
    lsj = Mock(lookup=Mock(return_value="return, homecoming."))
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(
            grc_forms_by_backend={
                "homeric": _rule_based({"Nom.Sing": {"νόστος"}}),
                "attic": _rule_based({"Nom.Sing": {"νόστος"}}),
            }
        ),
        morpheus=morpheus_client,
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=lsj,
        wikipedia=Mock(),
    )

    concept = build("νόστος", "noun", ["homeric", "attic"], sources, level=["B1"], tags=["test"])

    assert concept.body.count("## Ancient Greek meaning") == 1
    assert concept.body.count("return, homecoming.") == 1
    lsj.lookup.assert_called_once_with("νόστος")


def test_build_lsj_lookup_called_once_even_when_no_entry_found(morpheus_client, wiktextract_index):
    """Regression test: an earlier version memoized via `if lsj_entry is
    None:`, which collides with lookup()'s legitimate "no entry" return
    value of None -- that sentinel re-queries on every ancient period
    whenever nothing is found, the common case today since every LSJIndex
    constructed anywhere in this codebase is still the empty placeholder
    (data/lsj/README.md)."""
    lsj = _no_lsj_entry()
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(
            grc_forms_by_backend={
                "homeric": _rule_based({"Nom.Sing": {"νόστος"}}),
                "attic": _rule_based({"Nom.Sing": {"νόστος"}}),
            }
        ),
        morpheus=morpheus_client,
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=lsj,
        wikipedia=Mock(),
    )

    build("νόστος", "noun", ["homeric", "attic"], sources, level=["B1"], tags=["test"])

    lsj.lookup.assert_called_once_with("νόστος")


def test_build_lsj_meaning_independent_of_attested_forms(morpheus_client):
    """LSJ is an independent dictionary source, not derived from
    morphological analysis -- a lemma with zero eee_engine/Morpheus hits
    for the ancient period must still get its LSJ meaning shown, matching
    how a Modern-period Wiktextract gloss doesn't require attested forms
    either. `periods` must still list "homeric" despite no "## Homeric"
    heading (no rule-based/LLM/Morpheus content, so _ancient_period_section
    itself returns None) -- pipeline.py's real candidate-acceptance gate
    discards any concept whose `periods` comes back empty, so an LSJ-only
    lemma must not look unattested just because its content landed in the
    separate "Ancient Greek meaning" section instead of a period heading."""
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(grc_forms_by_backend={}),
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=Mock(lookup=Mock(return_value="return, homecoming.")),
        wikipedia=Mock(),
    )

    concept = build("νόστος", "noun", ["homeric"], sources, level=["B1"], tags=["test"])

    assert "## Ancient Greek meaning" in concept.body
    assert "## Homeric" not in concept.body
    assert "homeric" in concept.extra_frontmatter["periods"]


def test_build_includes_beekes_etymology_section_when_supplied(morpheus_client):
    sources = SourceBundle(
        eee_engine=_eee_engine_stub(grc_forms_by_backend={"homeric": _rule_based({"Nom.Sing": {"νόστος"}})}),
        morpheus=morpheus_client,
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=_no_lsj_entry(),
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
        lsj=_no_lsj_entry(),
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
        lsj=_no_lsj_entry(),
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
        lsj=_no_lsj_entry(),
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
        lsj=_no_lsj_entry(),
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
        lsj=_no_lsj_entry(),
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
        lsj=_no_lsj_entry(),
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
        lsj=_no_lsj_entry(),
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
        lsj=_no_lsj_entry(),
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
        lsj=_no_lsj_entry(),
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
        lsj=_no_lsj_entry(),
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
        lsj=_no_lsj_entry(),
        wikipedia=Mock(),
    )
    rule_based_only_concept = build("νόστος", "noun", ["homeric"], rule_based_only_sources, level=["B1"], tags=["test"])

    assert "†" not in rule_based_only_concept.body
    assert not any(s.id.startswith("llm-gap-filler-") for s in rule_based_only_concept.sources)


def test_build_reuses_caller_supplied_cache_instance_across_multiple_calls():
    engine = _eee_engine_stub(grc_forms_by_backend={"homeric": _rule_based({"Nom.Sing": {"νόστος"}})})
    gap_filler = GapFillerConfig(models=(LLMModelConfig(name="a", model="gpt-4o-mini", api_key_env="TEST_LLM_KEY"),))
    sources = SourceBundle(
        eee_engine=engine,
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=_no_lsj_entry(),
        wikipedia=Mock(),
        llm_gap_filler=gap_filler,
    )
    shared_cache = GapFillCache()

    build("νόστος", "noun", ["homeric"], sources, level=["B1"], tags=["test"], cache=shared_cache)
    build("φίλος", "noun", ["homeric"], sources, level=["B1"], tags=["test"], cache=shared_cache)

    assert engine.collect_slot_forms.call_count == 2
    for call in engine.collect_slot_forms.call_args_list:
        assert call.kwargs.get("cache") is shared_cache


def test_build_fallback_cache_is_a_real_gapfillcache_instance_not_merely_non_none():
    """Distinct from test_build_passes_non_none_cache_whenever_gap_filler_is_configured:
    that test only checks `is not None`; this confirms the fallback cache
    build() constructs internally (cache= omitted) is genuinely a
    GapFillCache, not some other truthy non-None stand-in."""
    engine = _eee_engine_stub(grc_forms_by_backend={"homeric": _rule_based({"Nom.Sing": {"νόστος"}})})
    gap_filler = GapFillerConfig(models=(LLMModelConfig(name="a", model="gpt-4o-mini", api_key_env="TEST_LLM_KEY"),))
    sources = SourceBundle(
        eee_engine=engine,
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=_no_lsj_entry(),
        wikipedia=Mock(),
        llm_gap_filler=gap_filler,
    )

    build("νόστος", "noun", ["homeric"], sources, level=["B1"], tags=["test"])  # cache omitted

    passed_cache = engine.collect_slot_forms.call_args.kwargs.get("cache")
    assert isinstance(passed_cache, GapFillCache)


def test_build_on_llm_inferred_fires_once_per_form_for_llm_inferred_slots_only():
    """Mix of RULE_BASED and LLM_INFERRED in the same period -- the
    callback must fire only for the LLM_INFERRED slot, once per distinct
    form in that slot's forms set, and never for the RULE_BASED one."""
    engine = _eee_engine_stub(
        grc_forms_by_backend={
            "homeric": {
                **_rule_based({"Nom.Sing": {"νόστος"}}),
                "Gen.Sing": SlotForms(
                    forms={"νόστου", "νόστοιο"},
                    source_type=FormSourceType.LLM_INFERRED,
                    method="llm:gpt-4o-mini",
                    llm_backend_version="0.2.1",
                    features={"Case": "Gen", "Number": "Sing"},
                ),
            }
        }
    )
    sources = SourceBundle(
        eee_engine=engine,
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=_no_lsj_entry(),
        wikipedia=Mock(),
    )
    records = []

    build("νόστος", "noun", ["homeric"], sources, level=["B1"], tags=["test"], on_llm_inferred=records.append)

    assert len(records) == 2  # one per form in the LLM-inferred slot's forms set
    assert {r.form for r in records} == {"νόστου", "νόστοιο"}
    assert not any(r.slot_label == "Nom.Sing" for r in records)  # the RULE_BASED slot never produces a record
    for record in records:
        assert record.lemma == "νόστος"
        assert record.slot_label == "Gen.Sing"
        assert record.features == {"Case": "Gen", "Number": "Sing"}
        assert record.pos == "noun"
        assert record.language == "grc"
        assert record.period == "homeric"
        assert record.method == "llm:gpt-4o-mini"
        assert record.llm_backend_version == "0.2.1"


def test_build_on_llm_inferred_period_is_none_for_modern():
    engine = _eee_engine_stub(el_forms=_llm_inferred({"Nom.Sing": {"form"}}, method="llm:gpt-4o-mini"))
    sources = SourceBundle(
        eee_engine=engine,
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=_no_lsj_entry(),
        wikipedia=Mock(),
    )
    records = []

    build("word", "noun", ["modern"], sources, level=["B1"], tags=["test"], on_llm_inferred=records.append)

    assert len(records) == 1
    assert records[0].language == "el"
    assert records[0].period is None
    # _llm_inferred() (this file's helper) never sets SlotForms.features,
    # so it defaults to None -- confirms the `slot_forms.features or {}`
    # fallback in emit_llm_inferred_records() actually maps that to {},
    # not just that it doesn't crash.
    assert records[0].features == {}


def test_build_omitting_on_llm_inferred_is_a_no_op():
    """Every LLM-inferred-output test elsewhere in this file already omits
    on_llm_inferred -- this confirms explicitly that build() doesn't
    require it, with no behavior change to the returned ConceptFile."""
    engine = _eee_engine_stub(
        grc_forms_by_backend={"homeric": _llm_inferred({"Gen.Sing": {"νόστου"}}, method="llm:gpt-4o-mini")}
    )
    sources = SourceBundle(
        eee_engine=engine,
        morpheus=Mock(analyze=Mock(return_value=[])),
        byzantine_forms={},
        wiktextract=Mock(lookup=Mock(return_value=None)),
        lsj=_no_lsj_entry(),
        wikipedia=Mock(),
    )

    concept = build("νόστος", "noun", ["homeric"], sources, level=["B1"], tags=["test"])  # on_llm_inferred omitted

    assert "νόστου†" in concept.body
