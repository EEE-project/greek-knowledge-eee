"""Wires a real SourceBundle from one repo checkout -- the same wiring
README.md's "Usage" section documents by hand, factored into one
importable function so examples/ and okfbuild/cli.py don't each
reimplement it.

Deliberately simpler than tests/conftest.py's real_source_bundle
fixture: that fixture shares one LSJ dump scan between `lsj` and
`lsj_period_map` and warms a TLG-abbreviation cache, both test-session
optimizations that don't belong in a general-purpose helper. This
module always constructs plain CachedLSJIndex/CachedWiktextractIndex
instances -- correct, just not scan-sharing.
"""

import dataclasses
from pathlib import Path

import eee_project as eee
from ancient_greek_backend_eee import AncientGreekBackend
from modern_greek_backend_eee import ModernGreekBackend

from okfbuild.sources import SourceBundle, eee_engine, wikipedia_client
from okfbuild.sources.byzantine_lexicon import load_byzantine_forms
from okfbuild.sources.iecor_client import load_iecor_cognates
from okfbuild.sources.lsj_index import CachedLSJIndex
from okfbuild.sources.lsj_periods import LSJPeriodMap
from okfbuild.sources.morpheus_client import MorpheusClient
from okfbuild.sources.wiktextract_index import CachedWiktextractIndex


def default_source_bundle(repo_root: Path) -> SourceBundle:
    """Registers the EEE backends (idempotent -- see eee.register_backend's
    own docstring, safe to call from a process that's already registered
    them) and returns a SourceBundle wired from `repo_root`'s own data/
    directory. The Byzantine lexicon lives in a sibling greek-inflexion-eee
    checkout (repo_root.parent / "greek-inflexion-eee" / ...) -- gracefully
    empty ({}) when that checkout isn't present, never a blocking
    dependency, matching how lsj/wiktextract already behave without their
    real dumps."""
    eee.register_backend("grc", AncientGreekBackend.for_period("epic"), backend="homeric")
    eee.register_backend("grc", AncientGreekBackend.for_period("attic"), backend="attic")
    eee.register_backend("el", ModernGreekBackend())

    byzantine_path = (
        repo_root.parent / "greek-inflexion-eee" / "src" / "greek_inflexion_eee" / "data" / "byzantine_verbs_lexicon.yaml"
    )
    byzantine_forms = load_byzantine_forms(byzantine_path) if byzantine_path.is_file() else {}

    return SourceBundle(
        eee_engine=eee_engine,
        morpheus=MorpheusClient(cache_dir=repo_root / "data" / "morpheus-cache"),
        byzantine_forms=byzantine_forms,
        wiktextract=CachedWiktextractIndex(cache_dir=repo_root / "data" / "wiktextract-cache", jsonl_path=None, lang_code="el"),
        lsj=CachedLSJIndex(cache_dir=repo_root / "data" / "lsj-cache", tei_xml_dir=None),
        wikipedia=wikipedia_client,
        iecor=load_iecor_cognates(repo_root / "data" / "iecor" / "ancient_greek_cognates.tsv"),
    )


def full_source_bundle(repo_root: Path) -> SourceBundle:
    """default_source_bundle() plus a real LSJPeriodMap, so LSJ citations
    get period/dialect tags (e.g. "**[7th c. BC, Boeot.]**") instead of
    dialect-only ones. This is what okfbuild.cli's `regenerate` subcommand
    uses -- the one real write path that touches this repo's tracked
    words/grammar/culture content -- so a regeneration never silently
    degrades citation quality the way an incomplete wiring would.

    Skips tests/conftest.py's real_source_bundle fixture's scan-sharing
    optimization (which avoids scanning the ~270MB LSJ dump twice, once
    for `lsj` and once for `lsj_period_map`): LSJPeriodMap.build() does
    its own full scan here if its own on-disk cache is stale. Acceptable
    for a regeneration a human runs deliberately and infrequently, not
    worth duplicating that fixture's more complex sharing logic for."""
    sources = default_source_bundle(repo_root)

    lsj_tei_xml_dir = repo_root / "data" / "lsj"
    diorisis_catalog_path = repo_root / "data" / "diorisis" / "catalog.tsv"
    lsj_dump_present = (lsj_tei_xml_dir / "grc.lsj.perseus-eng1.xml").is_file()
    lsj_period_map = (
        LSJPeriodMap.build(
            tei_xml_dir=lsj_tei_xml_dir,
            diorisis_catalog_path=diorisis_catalog_path,
            cache_path=repo_root / "data" / "lsj-tlg-map-cache.json",
        )
        if lsj_dump_present and diorisis_catalog_path.is_file()
        else None
    )
    return dataclasses.replace(sources, lsj_period_map=lsj_period_map)
