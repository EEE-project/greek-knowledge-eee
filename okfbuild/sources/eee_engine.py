"""Wraps the already-installed eee_project package.

Backend registration (ancient-greek + unimorph chains) is the caller's
responsibility — this module only wraps the already-registered
get_slot_templates()/inflect_slot() calls, never a backend directly.
"""

from dataclasses import dataclass
from enum import Enum, auto

import eee_project as eee

from okfbuild import course_context
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
    features: dict[str, str] | None = None  # the template's own features dict, for RULE_BASED and LLM_INFERRED alike


def collect_slot_forms(
    lemma: str,
    pos: str,
    language: str,
    backend: str | None = None,
    gap_filler: "llm_gap_filler.GapFillerConfig | None" = None,
    cache: "llm_gap_filler.GapFillCache | None" = None,
    source_course: str | None = None,
) -> dict[str, SlotForms]:
    """As the former inflect_all_attested() (eee.get_slot_templates() +
    per-template eee.inflect_slot()), but: (1) the return type is
    dict[str, SlotForms] so callers can distinguish rule-based from
    LLM-inferred results; (2) when gap_filler is not None and a
    template's inflect_slot() call returns a CLEAN EMPTY set() -- never
    when inflect_slot() raises, that exception propagates unchanged --
    calls llm_gap_filler.fill_gap(lemma, template.features, pos,
    language, gap_filler, cache, context=...) -- only for templates
    where template.features is not None (ag-paradigm slots have no
    features dict and are structurally unfillable by the LLM regardless
    of gap_filler being configured). A template whose rule-based query
    succeeds is never sent to the gap-filler, regardless of gap_filler
    being configured -- LLM calls only ever happen for a clean, genuine
    gap. `cache` should be constructed once per pipeline.run() invocation
    (not once per lemma) and threaded through every call unchanged, so
    its run-local memoization actually spans the whole run.

    `backend` selects a named backend variant (eee.get_slot_templates's/
    eee.inflect_slot's own `backend=` parameter) instead of "the default
    backend" for `language` -- unchanged from before this section.
    `backend` (as a period, e.g. "homeric"/"attic") and `source_course`
    (looked up in course_context.COURSE_CONTEXT for author/work/dialect,
    when it names a known course) are not passed to fill_gap() directly
    -- both are folded into a single `context` string alongside the
    slot's own template.label, so the LLM gap-filler is told which slot
    and (when known) which period/dialect/author/work it's filling. This
    is course-level metadata ("sourced from the Odyssey course"), not an
    attestation claim ("Homer's own text uses this exact form") -- no
    such claim is made or checked anywhere in this pipeline."""
    if gap_filler is not None and cache is None:
        # fill_gap() requires a real GapFillCache (its first line calls
        # cache.make_key(...)) -- catch a caller that supplied gap_filler
        # but left cache at its default here, at the boundary, rather than
        # several frames deep inside fill_gap() as an AttributeError.
        raise ValueError("collect_slot_forms(): cache is required when gap_filler is set")

    templates = eee.get_slot_templates(language, pos, "en", backend=backend)
    if not templates:
        return {}

    course = course_context.COURSE_CONTEXT.get(source_course) if source_course else None

    result: dict[str, SlotForms] = {}
    for template in templates:
        forms = eee.inflect_slot(lemma, template, pos, language=language, backend=backend)
        if forms:
            result[template.label] = SlotForms(
                forms=forms, source_type=FormSourceType.RULE_BASED, features=template.features
            )
            continue

        if gap_filler is not None and template.features is not None:
            parts = [template.label]
            if backend:
                parts.append(f"period={backend}")
            if course is not None:
                if course.author:
                    parts.append(f"author={course.author}")
                if course.work:
                    parts.append(f"work={course.work}")
                if course.dialect:
                    parts.append(f"dialect={course.dialect}")
            context = ", ".join(parts)

            gap_result = llm_gap_filler.fill_gap(
                lemma, template.features, pos, language, gap_filler, cache, context=context
            )
            if gap_result.forms:
                result[template.label] = SlotForms(
                    forms=gap_result.forms,
                    source_type=FormSourceType.LLM_INFERRED,
                    method=gap_result.method,
                    llm_backend_version=gap_result.llm_backend_version,
                    features=template.features,
                )
    return result
