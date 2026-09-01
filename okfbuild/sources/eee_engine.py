"""Wraps the already-installed eee_project package.

Backend registration (ancient-greek + unimorph chains) is the caller's
responsibility — this module only wraps the already-registered
get_slot_templates()/inflect_slot() calls, never a backend directly.
"""

from dataclasses import dataclass
from enum import Enum, auto

import eee_project as eee

from okfbuild.sources import llm_gap_filler


class FormSourceType(Enum):
    """Raw strings for this would risk a silent typo (e.g. "llm-inferred"
    vs "llm_inferred") passing static analysis and failing at runtime --
    an Enum makes the two valid values the only representable ones."""

    RULE_BASED = auto()
    LLM_INFERRED = auto()


@dataclass(frozen=True)
class SlotForms:
    """One slot template's result, with enough provenance for the
    concept builder to cite it correctly. Named SlotForms, not
    "AttestedForms" -- an earlier draft used that name, but it becomes
    actively misleading once source_type can be LLM_INFERRED, which by
    definition is not attested."""

    forms: set[str]
    source_type: FormSourceType
    method: str | None = None  # populated only when source_type == FormSourceType.LLM_INFERRED
    llm_backend_version: str | None = None  # ditto -- from GapFillResult, for reproducibility


def collect_slot_forms(
    lemma: str,
    pos: str,
    language: str,
    backend: str | None = None,
    gap_filler: "llm_gap_filler.GapFillerConfig | None" = None,
    cache: "llm_gap_filler.GapFillCache | None" = None,
) -> dict[str, SlotForms]:
    """As the former inflect_all_attested() (eee.get_slot_templates() +
    per-template eee.inflect_slot()), but: (1) the return type is
    dict[str, SlotForms] so callers can distinguish rule-based from
    LLM-inferred results; (2) when gap_filler is not None and a
    template's inflect_slot() call returns a CLEAN EMPTY set() -- never
    when inflect_slot() raises, that exception propagates unchanged --
    calls llm_gap_filler.fill_gap(lemma, template.features, pos,
    language, gap_filler, cache) -- only for templates where
    template.features is not None (ag-paradigm slots have no features
    dict and are structurally unfillable by the LLM regardless of
    gap_filler being configured). A template whose rule-based query
    succeeds is never sent to the gap-filler, regardless of gap_filler
    being configured -- LLM calls only ever happen for a clean, genuine
    gap. `cache` should be constructed once per pipeline.run() invocation
    (not once per lemma) and threaded through every call unchanged, so
    its run-local memoization actually spans the whole run.

    `backend` selects a named backend variant (eee.get_slot_templates's/
    eee.inflect_slot's own `backend=` parameter) instead of "the default
    backend" for `language` -- unchanged from before this section, and
    not passed to fill_gap() (the LLM gap-filler doesn't distinguish
    periods that way)."""
    if gap_filler is not None and cache is None:
        # fill_gap() requires a real GapFillCache (its first line calls
        # cache.make_key(...)) -- catch a caller that supplied gap_filler
        # but left cache at its default here, at the boundary, rather than
        # several frames deep inside fill_gap() as an AttributeError.
        raise ValueError("collect_slot_forms(): cache is required when gap_filler is set")

    templates = eee.get_slot_templates(language, pos, "en", backend=backend)
    if not templates:
        return {}

    result: dict[str, SlotForms] = {}
    for template in templates:
        forms = eee.inflect_slot(lemma, template, pos, language=language, backend=backend)
        if forms:
            result[template.label] = SlotForms(forms=forms, source_type=FormSourceType.RULE_BASED)
            continue

        if gap_filler is not None and template.features is not None:
            gap_result = llm_gap_filler.fill_gap(
                lemma, template.features, pos, language, gap_filler, cache
            )
            if gap_result.forms:
                result[template.label] = SlotForms(
                    forms=gap_result.forms,
                    source_type=FormSourceType.LLM_INFERRED,
                    method=gap_result.method,
                    llm_backend_version=gap_result.llm_backend_version,
                )
    return result
