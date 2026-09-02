"""Wraps the already-installed eee_project package.

Backend registration (ancient-greek + unimorph chains) is the caller's
responsibility — this module only wraps the already-registered
get_slot_templates()/inflect_slot() calls, never a backend directly.
"""

import logging
from dataclasses import dataclass
from enum import Enum, auto

import eee_project as eee
from modern_greek_inflexion_eee.exceptions import (
    NotInGreekException,
    NotLegalAdjectiveException,
    NotLegalPronounException,
    NotLegalVerbException,
)

from okfbuild import course_context
from okfbuild.sources import llm_gap_filler

logger = logging.getLogger(__name__)

# modern_greek_backend_eee (via modern_greek_inflexion_eee) has no graceful
# "not a valid word" return value for a lemma that simply isn't Modern
# Greek -- it raises instead of returning the clean empty result every
# other "no form here" case produces. The architecturally correct fix
# belongs in modern_greek_backend_eee itself (catch-and-return-empty,
# matching every other backend's "no rule-based form" contract); this is
# a caller-side workaround pending that.
#
# All four are unambiguous, purpose-built signals -- safe to catch by
# name. Pronouns are a first-class case here (see collect_slot_forms()'s
# own PronType handling below): every ancient-only pronoun hits
# NotLegalPronounException on every real run. Deliberately still NOT a
# broad `except Exception`: an unrelated real bug in a different
# exception class (e.g. the library's own short-word IndexError on ὅς)
# still propagates loudly instead of being silently swallowed here too.
_LEMMA_NOT_A_MODERN_GREEK_WORD_EXCEPTIONS = (
    NotInGreekException,
    NotLegalAdjectiveException,
    NotLegalPronounException,
    NotLegalVerbException,
)


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
    such claim is made or checked anywhere in this pipeline.

    For pos == "pronoun" specifically: get_slot_templates() returns one
    POS-level template set covering every PronType family mixed together
    (Prs/Dem/Rel/Int/Ind/Rcp all in one list -- see the comment above
    _POS_TSV in ancient_greek_backend_eee's backend.py), so an empty
    inflect_slot() result can mean either a genuine gap or simply the
    wrong family for this lemma (e.g. the personal pronoun ἐγώ has no
    demonstrative form -- asking is a category error, not a gap). To
    tell these apart, every failed pronoun template is deferred until
    every template has been tried rule-based; a failed one only then
    reaches fill_gap() if its own features["PronType"] matches a
    PronType some OTHER template already confirmed rule-based for this
    lemma. If rule-based inflection produced zero successes at all for
    this lemma (its family can't be determined), every unresolved
    pronoun slot is skipped rather than guessed at -- logged once as a
    warning, never sent to the LLM.

    A lemma that plainly isn't a word in `language` at all (not "has a
    gap", but "the underlying inflexion library refuses to recognize it
    as this language/pos" -- see _LEMMA_NOT_A_MODERN_GREEK_WORD_EXCEPTIONS)
    is detected on the first template that triggers it and short-circuits
    the rest of this call: no further rule-based attempts (the underlying
    paradigm construction is lemma-level, not slot-level, so it would
    fail identically on every other template too) and no gap-filling
    (this isn't a gap -- the word doesn't exist here at all)."""
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
    rule_based_failures = []
    confirmed_pron_types: set[str] = set()
    for template in templates:
        try:
            forms = eee.inflect_slot(lemma, template, pos, language=language, backend=backend)
        except _LEMMA_NOT_A_MODERN_GREEK_WORD_EXCEPTIONS as exc:
            logger.info(
                "gap-filler: lemma=%r pos=%r language=%r is not a valid word for this "
                "backend (%s: %s) -- skipping the rest of this call rather than treating "
                "every remaining slot as a separate rule-based failure or LLM gap",
                lemma,
                pos,
                language,
                type(exc).__name__,
                exc,
            )
            return result
        if forms:
            result[template.label] = SlotForms(
                forms=forms, source_type=FormSourceType.RULE_BASED, features=template.features
            )
            if pos == "pronoun" and template.features is not None:
                pron_type = template.features.get("PronType")
                if pron_type is not None:
                    confirmed_pron_types.add(pron_type)
            continue
        rule_based_failures.append(template)

    if gap_filler is None:
        return result

    if pos == "pronoun" and rule_based_failures and not confirmed_pron_types:
        logger.warning(
            "gap-filler: lemma=%r pos='pronoun' has no rule-based form in any PronType "
            "family -- cannot tell which of %d unresolved slot(s) actually apply to it, "
            "skipping LLM gap-fill entirely rather than querying every family",
            lemma,
            len(rule_based_failures),
        )

    for template in rule_based_failures:
        if template.features is None:
            continue

        if pos == "pronoun":
            pron_type = template.features.get("PronType")
            if pron_type is not None and pron_type not in confirmed_pron_types:
                # Cross-family cell (see this function's docstring): an empty
                # rule-based result here means "wrong PronType family for
                # this lemma", not a genuine gap -- never worth an LLM call.
                continue

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
