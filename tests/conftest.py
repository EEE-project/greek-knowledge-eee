"""Shared pytest fixtures for okfbuild's test suite."""

import dataclasses
import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from okfbuild.sources import SourceBundle
from okfbuild.sources.byzantine_lexicon import load_byzantine_forms
from okfbuild.sources.eee_engine import FormSourceType, SlotForms
from okfbuild.sources.iecor_client import load_iecor_cognates
from okfbuild.sources.llm_gap_filler import GapFillerConfig, LLMModelConfig
from okfbuild.sources.lsj_index import CachedLSJIndex, _load_entries
from okfbuild.sources.lsj_periods import LSJPeriodMap, tlg_map_cache_is_fresh
from okfbuild.sources.morpheus_client import MorpheusClient
from okfbuild.sources.wiktextract_index import CachedWiktextractIndex
from okfbuild.sources import wikipedia_client

pytest_plugins = ["pytester"]

PAID_LLM_CONFIRM_VAR = "GREEK_KNOWLEDGE_RUN_PAID_LLM_TESTS"


def pytest_addoption(parser):
    parser.addoption(
        "--run-paid-llm-tests",
        action="store_true",
        default=False,
        help="run tests marked paid_llm_api (issues real, billed LLM API calls)",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-paid-llm-tests"):
        return
    skip_paid = pytest.mark.skip(reason="need --run-paid-llm-tests to run paid_llm_api tests")
    for item in items:
        if "paid_llm_api" in item.keywords:
            item.add_marker(skip_paid)


def require_paid_llm_gate(key_env_var: str) -> None:
    """The actual paid-LLM-API enforcement boundary. Call this from inside
    any fixture that is about to construct a real LLM client or issue a
    real, billed call -- BEFORE that construction happens -- regardless of
    how the calling test was invoked (marker selection, --run-paid-llm-tests,
    or anything else). Skips (pytest.skip -- never raises/errors) unless
    BOTH, independently:
      - key_env_var is set in the environment to a non-empty,
        non-whitespace-only value (layer 2).
      - GREEK_KNOWLEDGE_RUN_PAID_LLM_TESTS is set to exactly "1" -- not
        merely truthy; "0"/"false"/anything else does NOT satisfy this
        (layer 3).
    Distinguishable skip messages for each failure case -- see
    tests/test_paid_llm_gating.py. This is the real security boundary,
    not the marker/CLI-flag layer above -- a fixture that calls this first
    genuinely cannot construct anything real unless both checks pass, no
    matter how the test got collected/selected in the first place."""
    value = os.environ.get(key_env_var, "").strip()
    if not value:
        pytest.skip(f"paid LLM tests require {key_env_var} to be set (real, billed API key)")
    confirm = os.environ.get(PAID_LLM_CONFIRM_VAR, "")
    if confirm != "1":
        pytest.skip(
            f"paid LLM tests require {PAID_LLM_CONFIRM_VAR}=1 (explicit opt-in to real, billed API calls)"
        )


def _eee_engine_stub(attested_lemmas: set[str]):
    """Lemma-aware stub for SourceBundle.eee_engine: lemmas in
    `attested_lemmas` get a fixed homeric form back (via
    collect_slot_forms's language="grc", backend="homeric" branch, per
    the real per-period backend scoping documented in
    okfbuild/concepts/lexical_entry.py); every other lemma/backend/language
    combination returns empty, so a test can control exactly which
    candidate lemmas end up with attested data. Returns dict[str,
    SlotForms] (source_type=RULE_BASED), matching collect_slot_forms()'s
    real return shape post section-02/03."""
    engine = Mock()

    def _collect(lemma, pos, language, backend=None, gap_filler=None, cache=None, source_course=None):
        if lemma in attested_lemmas and language == "grc" and backend == "homeric":
            return {"Nom.Sing": SlotForms(forms={lemma}, source_type=FormSourceType.RULE_BASED)}
        return {}

    engine.collect_slot_forms.side_effect = _collect
    return engine


@pytest.fixture
def make_source_bundle():
    """Factory fixture: make_source_bundle(attested_lemmas={...}) returns a
    SourceBundle whose eee_engine reports attested homeric forms only for
    the given lemmas; every other source client is stubbed to return
    nothing. A lemma not named in attested_lemmas gets no data from any
    source — the "candidate with no data anywhere" case. `llm_gap_filler`
    is opaque here (never inspected by anything this stub does) — a test
    that needs it set only cares that pipeline.run() sees a non-None
    value on sources.llm_gap_filler, to engage its gap-fill-cache
    construction/persistence logic."""

    def _make(attested_lemmas: set[str] = frozenset(), llm_gap_filler=None) -> SourceBundle:
        return SourceBundle(
            eee_engine=_eee_engine_stub(set(attested_lemmas)),
            morpheus=Mock(analyze=Mock(return_value=[])),
            byzantine_forms={},
            wiktextract=Mock(lookup=Mock(return_value=None)),
            lsj=Mock(lookup=Mock(return_value=None)),
            wikipedia=Mock(),
            llm_gap_filler=llm_gap_filler,
        )

    return _make


# --- section-07 pilot: real (non-fixture) fixtures -------------------------
#
# Everything below wires REAL source clients against REAL sibling-repo data
# for the pilot acceptance run (tests/test_pilot_acceptance.py), as opposed
# to make_source_bundle's synthetic stubs above. See section-07-pilot.md's
# "Preparing the real inputs" for the source of every path/decision here.


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """This checkout's own root. out_dir for the pilot run IS this repo —
    the pipeline writes real words/grammar/culture files here, and running
    the acceptance test is how those files get generated; a human reviews
    the resulting git diff before committing."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def created_with_eee_root(repo_root: Path) -> Path:
    """Locate the sibling created_with_eee checkout (lesson content lives
    there, not in this repo). Resolution order: a CREATED_WITH_EEE_PATH env
    var, else the conventional sibling-checkout layout (both repos under
    the same EEE-project/ parent directory)."""
    env_path = os.environ.get("CREATED_WITH_EEE_PATH")
    candidate = Path(env_path) if env_path else repo_root.parent / "created_with_eee"
    if not candidate.is_dir():
        pytest.skip(f"created_with_eee checkout not found at {candidate} (set CREATED_WITH_EEE_PATH)")
    return candidate


@pytest.fixture(scope="session")
def real_source_bundle(repo_root: Path) -> SourceBundle:
    """Wires the REAL (non-fixture, non-mocked) section-03 clients.

    Backend registration is this fixture's own responsibility (eee_engine.py's
    module docstring: "Backend registration... is the caller's
    responsibility") — registers named "homeric"/"attic" AncientGreekBackend
    variants (see docs/api-patterns.md's for_period() example) plus a plain
    ModernGreekBackend for "el", matching lexical_entry.build()'s expected
    backend names exactly.

    lsj is a CachedLSJIndex, mirroring wiktextract below: headwords already
    resolved on a prior run come from data/lsj-cache/ (small, git-tracked)
    with no need for the raw TEI-XML dump at all; a genuinely new headword
    falls back to the real 27-file Perseus dump if present locally (a
    one-time, gitignored download, see data/lsj/README.md). A cache miss
    with no dump available returns None rather than skipping — LSJ is
    enrichment, not a hard requirement, same as wiktextract below.

    wiktextract is a CachedWiktextractIndex: lemmas already resolved on a
    prior run come from data/wiktextract-cache/ (small, git-tracked) with no
    need for the raw dump at all; a genuinely new lemma falls back to the
    real kaikki.org el-extract.jsonl dump if present locally (a one-time,
    gitignored download, see data/wiktextract/README.md), filtered to
    lang_code="el" — see wiktextract_index.py's lang_code parameter, added
    by this section after discovering the real dump has both an "el" and a
    "grc" section for shared headwords like νόστος, and the unfiltered
    loader silently kept whichever sorted last (grc), which would have
    mislabeled Ancient-Greek glosses as the Modern-period citation. A cache
    miss with no dump available returns None rather than skipping — the
    modern-period section can still be satisfied by eee_engine's own
    Modern Greek inflection alone; wiktextract is enrichment, not a hard
    requirement, for νόστος specifically."""
    # Checked first, before any backend registration or directory creation
    # below — a missing lexicon should skip cleanly with no side effects.
    byzantine_yaml = (
        repo_root.parent / "greek-inflexion-eee" / "src" / "greek_inflexion_eee" / "data" / "byzantine_verbs_lexicon.yaml"
    )
    if not byzantine_yaml.is_file():
        pytest.skip(f"greek-inflexion-eee byzantine lexicon not found at {byzantine_yaml}")
    byzantine_forms = load_byzantine_forms(byzantine_yaml)

    from ancient_greek_backend_eee import AncientGreekBackend
    from modern_greek_backend_eee import ModernGreekBackend
    import eee_project as eee
    from okfbuild.sources import eee_engine as eee_engine_wrapper

    eee.register_backend("grc", AncientGreekBackend.for_period("epic"), backend="homeric")
    eee.register_backend("grc", AncientGreekBackend.for_period("attic"), backend="attic")
    eee.register_backend("el", ModernGreekBackend())

    morpheus = MorpheusClient(cache_dir=repo_root / "data" / "morpheus-cache")

    wiktextract_jsonl = repo_root / "data" / "wiktextract" / "el-extract.jsonl"
    wiktextract = CachedWiktextractIndex(
        cache_dir=repo_root / "data" / "wiktextract-cache",
        jsonl_path=wiktextract_jsonl if wiktextract_jsonl.is_file() else None,
        lang_code="el",
    )

    # data/lsj/ always exists (it has its own README.md even before the real
    # dump is downloaded) -- checking for one of the 27 expected files, not
    # just directory existence, matches wiktextract's is_file() check above.
    lsj_tei_xml_dir = repo_root / "data" / "lsj"
    lsj_dump_present = (lsj_tei_xml_dir / "grc.lsj.perseus-eng1.xml").is_file()
    diorisis_catalog_path = repo_root / "data" / "diorisis" / "catalog.tsv"
    lsj_cache_dir = repo_root / "data" / "lsj-cache"
    tlg_map_cache_path = repo_root / "data" / "lsj-tlg-map-cache.json"

    # Unlike lsj/wiktextract above, this extract is small and git-tracked
    # (like diorisis_catalog_path), so it's always present -- no
    # conditional-availability dance needed.
    iecor = load_iecor_cognates(repo_root / "data" / "iecor" / "ancient_greek_cognates.tsv")

    # `lsj` (CachedLSJIndex, lazy -- scans only on an actual cache miss)
    # and `lsj_period_map` (LSJPeriodMap, eager -- scans at construction
    # unless its own TLG-map cache is warm) would otherwise each
    # independently scan the full 27-file dump on a cold cache -- two
    # full scans instead of one. Shared here specifically when the
    # TLG-map cache is stale (the one condition under which
    # LSJPeriodMap.build() is about to scan regardless): do ONE
    # _load_entries() pass with its own tlg_abbreviation_collector
    # parameter, hand CachedLSJIndex the resulting index directly (its
    # own lazy-scan contract is otherwise untouched -- this only ever
    # preloads what a real, in-flight scan already produced, never
    # forces an eager scan that wouldn't have happened anyway) and hand
    # LSJPeriodMap.build() the resulting collector instead of letting it
    # rescan independently. When the cache is already fresh (the common
    # case after the first real run in an environment), neither side
    # scans at all -- behavior is then identical to before this sharing
    # was added.
    preloaded_lsj_entries = None
    precomputed_tlg_map = None
    if lsj_dump_present and not tlg_map_cache_is_fresh(lsj_tei_xml_dir, tlg_map_cache_path):
        precomputed_tlg_map = {}
        preloaded_lsj_entries = _load_entries(lsj_tei_xml_dir, tlg_abbreviation_collector=precomputed_tlg_map)

    lsj = CachedLSJIndex(
        cache_dir=lsj_cache_dir,
        tei_xml_dir=lsj_tei_xml_dir if lsj_dump_present else None,
        preloaded_index=preloaded_lsj_entries,
    )
    # Same conditional-availability shape as `lsj` immediately above, not
    # cost-gated the way real_source_bundle_with_gap_filler's separate
    # opt-in fixture is (that one exists specifically to keep real, billed
    # LLM calls out of the default pilot run -- LSJPeriodMap.build() is a
    # local dump scan with its own disk cache, no such concern applies).
    # Wired directly here, not behind a wrapper fixture: pilot_build_report
    # (the fixture that actually regenerates this repo's real words/*.md
    # content) constructs its pipeline.run() call from this exact
    # SourceBundle -- a separate wrapper fixture nothing else consumes
    # would leave real content generation never actually seeing period/
    # dialect tags, silently defeating the whole feature's real-world
    # purpose. Gracefully None when the dump (or the diorisis catalog,
    # though that one's git-tracked so always present) isn't available --
    # LSJPeriodMap is enrichment, not a hard requirement, same as lsj/
    # wiktextract elsewhere in this fixture.
    lsj_period_map = (
        LSJPeriodMap.build(
            tei_xml_dir=lsj_tei_xml_dir,
            diorisis_catalog_path=diorisis_catalog_path,
            cache_path=tlg_map_cache_path,
            precomputed_tlg_abbreviation_map=precomputed_tlg_map,
        )
        if lsj_dump_present and diorisis_catalog_path.is_file()
        else None
    )

    return SourceBundle(
        eee_engine=eee_engine_wrapper,
        morpheus=morpheus,
        byzantine_forms=byzantine_forms,
        wiktextract=wiktextract,
        lsj=lsj,
        wikipedia=wikipedia_client,
        lsj_period_map=lsj_period_map,
        iecor=iecor,
    )


@pytest.fixture(scope="session")
def pilot_output_dir(tmp_path_factory):
    """A scratch directory for pilot_build_report to write into -- NOT
    repo_root. The test suite must never change this repo's own tracked
    words/grammar/culture content as a side effect of running (that used
    to be pilot_build_report's job, until running a bare `uv run pytest`
    was found to silently rewrite real content, including regressing LSJ
    period/dialect tags when sources.lsj_period_map happened not to be
    available in a given local run -- a change nobody asked for or
    reviewed). Deliberately regenerating real content is now
    `okfbuild.cli`'s `regenerate` subcommand's job -- see its docstring
    -- gated behind an explicit --write flag, never a test."""
    return tmp_path_factory.mktemp("pilot-output")


@pytest.fixture(scope="session")
def pilot_build_report(pilot_output_dir, real_source_bundle, created_with_eee_root):
    """The single real pipeline.run() call every test in
    test_pilot_acceptance.py reads its result from — session-scoped so the
    expensive, network-touching real run happens once per test session.
    course_paths / grammar_rules / cultural_topics are the curated pilot
    inputs from section-07-pilot.md's "Preparing the real inputs". Writes
    to pilot_output_dir (a scratch directory), not this repo's own
    words/grammar/culture -- see that fixture's docstring for why."""
    from okfbuild import pipeline
    from okfbuild.pilot_content import CULTURAL_TOPICS, GRAMMAR_RULES, enrich_nostos_with_beekes

    course_paths = [
        created_with_eee_root / "ancient_greek" / "odyssey",
        created_with_eee_root / "modern_greek" / "b1greeklanguageandculture" / "kavafis_ithaki",
    ]

    report = pipeline.run(
        course_paths,
        out_dir=pilot_output_dir,
        sources=real_source_bundle,
        grammar_rules=GRAMMAR_RULES,
        cultural_topics=CULTURAL_TOPICS,
    )
    # Adds the Etymology section pipeline.run()'s own auto-extraction loop
    # has no way to supply (see enrich_nostos_with_beekes's own docstring).
    # Runs after the main report so a failure here doesn't hide whether the
    # bulk run itself succeeded.
    enrich_nostos_with_beekes(pilot_output_dir, real_source_bundle)
    return report


# --- section-04 gap-filler pilot: real, gated OpenRouter-backed fixtures ---
#
# Do NOT modify real_source_bundle/pilot_build_report/test_pilot_acceptance.py
# above -- these two fixtures build on top of real_source_bundle without
# touching it (see real_source_bundle_with_gap_filler's own docstring).

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_OPENROUTER_API_KEY_ENV = "GREEK_KNOWLEDGE_OPENROUTER_API_KEY"


def _build_real_gap_filler_config(max_requests_per_run: int = 500) -> GapFillerConfig:
    """The real_gap_filler_config fixture's own construction logic, factored
    out as a plain, directly-callable function -- lets a unit test verify
    the two-model config shape without going through the session-scoped
    fixture (and its require_paid_llm_gate() call, already exhaustively
    tested on its own in tests/test_paid_llm_gating.py). max_requests_per_run
    defaults to 500 (the real fixture's own value, "a safety cap against a
    runaway/misconfigured run, not cost minimization") but is overridable --
    test_real_gated_pilot_run_stops_and_resumes_cleanly passes a small value
    to cheaply exercise the stop/resume mechanism for real, rather than the
    default (which a full two-course run cannot complete under regardless --
    confirmed at ~92,700 real requests needed, see that test's own docstring)."""
    return GapFillerConfig(
        models=(
            LLMModelConfig(
                name="gpt-4o-mini",
                model="openai/gpt-4o-mini",
                api_key_env=_OPENROUTER_API_KEY_ENV,
                base_url=_OPENROUTER_BASE_URL,
            ),
            LLMModelConfig(
                name="claude-3.5-haiku",
                model="anthropic/claude-3.5-haiku",
                api_key_env=_OPENROUTER_API_KEY_ENV,
                base_url=_OPENROUTER_BASE_URL,
            ),
        ),
        max_requests_per_run=max_requests_per_run,
    )


@pytest.fixture(scope="session")
def real_gap_filler_config() -> GapFillerConfig:
    """Real, two-model GapFillerConfig via OpenRouter (one API key, two
    genuinely different model families for a meaningful independent second
    opinion). Gated by require_paid_llm_gate() -- called first, before
    anything else in this fixture body -- so this fixture is itself the
    fixture-level double-gate section-03 describes as the actual
    enforcement boundary; it does not re-implement that gate's checks,
    only depends on it."""
    require_paid_llm_gate(_OPENROUTER_API_KEY_ENV)
    return _build_real_gap_filler_config()


@pytest.fixture(scope="session")
def real_source_bundle_with_gap_filler(real_source_bundle, real_gap_filler_config) -> SourceBundle:
    """Identical to real_source_bundle in every field except llm_gap_filler
    -- built via dataclasses.replace() (a NEW instance), never in-place
    mutation. SourceBundle is a plain, mutable @dataclass, so
    `real_source_bundle.llm_gap_filler = ...` would compile but silently
    corrupt the shared, session-scoped real_source_bundle fixture for
    every other test in the session, including pilot_build_report/
    test_pilot_acceptance.py."""
    return dataclasses.replace(real_source_bundle, llm_gap_filler=real_gap_filler_config)
