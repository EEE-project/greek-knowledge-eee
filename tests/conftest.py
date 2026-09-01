"""Shared pytest fixtures for okfbuild's test suite."""

import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from okfbuild.sources import SourceBundle
from okfbuild.sources.byzantine_lexicon import load_byzantine_forms
from okfbuild.sources.eee_engine import FormSourceType, SlotForms
from okfbuild.sources.lsj_index import LSJIndex
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
            lsj=Mock(),
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

    lsj is deliberately an empty LSJIndex({}), not a real downloaded Perseus
    dump: none of the three concept builders needed for this pilot's
    required deliverables (lexical_entry / grammatical_rule /
    cultural_context) ever read sources.lsj — confirmed by reading all three
    modules directly, not assumed. Downloading and parsing the 27 real LSJ
    TEI-XML files would add real time/disk cost for zero effect on this
    pilot's actual output.

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

    return SourceBundle(
        eee_engine=eee_engine_wrapper,
        morpheus=morpheus,
        byzantine_forms=byzantine_forms,
        wiktextract=wiktextract,
        lsj=LSJIndex({}),
        wikipedia=wikipedia_client,
    )


@pytest.fixture(scope="session")
def pilot_build_report(repo_root, real_source_bundle, created_with_eee_root):
    """The single real pipeline.run() call every test in
    test_pilot_acceptance.py reads its result from — session-scoped so the
    expensive, network-touching real run happens once per test session.
    course_paths / grammar_rules / cultural_topics are the curated pilot
    inputs from section-07-pilot.md's "Preparing the real inputs"."""
    from okfbuild import pipeline
    from okfbuild.pilot_content import CULTURAL_TOPICS, GRAMMAR_RULES, enrich_nostos_with_beekes

    course_paths = [
        created_with_eee_root / "ancient_greek" / "odyssey",
        created_with_eee_root / "modern_greek" / "b1greeklanguageandculture" / "kavafis_ithaki",
    ]

    report = pipeline.run(
        course_paths,
        out_dir=repo_root,
        sources=real_source_bundle,
        grammar_rules=GRAMMAR_RULES,
        cultural_topics=CULTURAL_TOPICS,
    )
    # Adds the Etymology section pipeline.run()'s own auto-extraction loop
    # has no way to supply (see enrich_nostos_with_beekes's own docstring).
    # Runs after the main report so a failure here doesn't hide whether the
    # bulk run itself succeeded.
    enrich_nostos_with_beekes(repo_root, real_source_bundle)
    return report
