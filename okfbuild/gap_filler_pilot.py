"""Real, gated pilot: runs pipeline.run() against real course data with a
real, OpenRouter-backed GapFillerConfig, writing output to an isolated
directory plus a versioned JSON "handoff" file listing every LLM-inferred
form collected during the run (for section-05's Morpheus cross-check).

Factored out of any pytest test body (both external plan reviews flagged
this) so the actual orchestration logic is directly callable and
independently unit-testable, not locked inside a fixture chain -- this
keeps a future non-pytest entry point (a real CLI, eventually) possible
without duplicating orchestration logic. tests/test_gap_filler_pilot.py's
one real, doubly-gated end-to-end test is a thin wrapper around this
function, not a reimplementation of it.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from okfbuild import pipeline
from okfbuild.concepts.lexical_entry import GapFillRecord
from okfbuild.pipeline import BuildReport
from okfbuild.sources import SourceBundle

_HANDOFF_FORMAT_VERSION = 1


def run_gap_filler_pilot(
    sources: SourceBundle,
    course_paths: list[Path],
    out_dir: Path,
    handoff_path: Path,
) -> BuildReport:
    """Runs pipeline.run() against course_paths, writing concept files
    under out_dir (NEVER the tracked repository tree -- this may be an
    exploratory, imperfect LLM-gap-filled run a human hasn't reviewed yet)
    and sharing one run-scoped, interruption-safe GapFillCache under
    out_dir too (gap_fill_cache_dir=out_dir, so the cache lives at
    out_dir/.gap_fill_runs/<run-id>/cache.json -- see pipeline.run()'s own
    docstring). Collects every individual LLM-inferred form produced
    during the run directly from the structured SlotForms data via
    on_llm_inferred (never parsed back out of rendered markdown -- see
    lexical_entry.build()'s on_llm_inferred docstring), and writes those
    records to handoff_path in this module's JSON schema (see
    _encode_record()). `handoff_path` is the caller's own responsibility
    to make collision-resistant (e.g. embedding a run ID or timestamp) --
    this function writes wherever it's told, unconditionally overwriting
    any existing file at that exact path.

    Handoff entries are NOT a strict subset of "forms that ended up in a
    written concept file": on_llm_inferred fires eagerly, per period,
    inside lexical_entry.build() -- if a LATER step in that same build()
    call raises (e.g. Morpheus/wiktextract lookup, rendering), the whole
    concept file is skipped (pipeline.run()'s per-candidate isolation
    catches it and records it in BuildReport.errors), but any record
    already emitted for an earlier period in that same call is already in
    this handoff. A consumer should not assume every handoff entry's
    lemma has a corresponding written words/*.md file."""
    records: list[GapFillRecord] = []

    report = pipeline.run(
        course_paths,
        out_dir,
        sources,
        gap_fill_cache_dir=out_dir,
        on_llm_inferred=records.append,
    )

    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(
        json.dumps(
            {
                "format_version": _HANDOFF_FORMAT_VERSION,
                "run_timestamp": datetime.now(UTC).isoformat(),
                "entries": [_encode_record(record) for record in records],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return report


def _encode_record(record: GapFillRecord) -> dict:
    """`method` names the model(s) REQUESTED for this fill, not necessarily
    the model that actually served it -- a routing/fallback provider (e.g.
    OpenRouter) can silently substitute a different model, and
    llm-backend-eee v0.2.1 has no mechanism to surface which one actually
    responded (see GapFillResult.method's own comment in llm_gap_filler.py).
    A consumer of this handoff (e.g. section-05's Morpheus cross-check)
    should treat `method` as "what was asked for," not "what generated
    this form"."""
    return {
        "lemma": record.lemma,
        "form": record.form,
        "slot_label": record.slot_label,
        "features": record.features,
        "pos": record.pos,
        "language": record.language,
        "period": record.period,
        "method": record.method,
        "llm_backend_version": record.llm_backend_version,
    }
