"""Source clients: EEE engine, Morpheus, Byzantine lexicon, Wiktextract, LSJ, Wikipedia."""

from dataclasses import dataclass
from types import ModuleType

from okfbuild.sources.llm_gap_filler import GapFillerConfig
from okfbuild.sources.lsj_index import CachedLSJIndex, LSJIndex
from okfbuild.sources.morpheus_client import MorpheusClient
from okfbuild.sources.wiktextract_index import CachedWiktextractIndex, WiktextractIndex


@dataclass
class SourceBundle:
    """Bundles one instance/handle of each source client, for concept
    builders (okfbuild/concepts/*.py) to consume. eee_engine and wikipedia
    are the respective modules themselves (accessed as
    sources.eee_engine.collect_slot_forms(...) /
    sources.wikipedia.summary(...)), not bare functions, since concept
    builders call them via dotted attribute access."""

    eee_engine: ModuleType
    morpheus: MorpheusClient
    byzantine_forms: dict[str, dict[str, "str | list[str]"]]
    wiktextract: "WiktextractIndex | CachedWiktextractIndex"
    lsj: "LSJIndex | CachedLSJIndex"
    wikipedia: ModuleType
    llm_gap_filler: "GapFillerConfig | None" = None
