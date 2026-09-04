"""Assembles a Lexical Entry ConceptFile from section-03's source clients.

Note on body/footnote shape: this module's `body` strings contain ONLY
inline `[^id]` references, never `[^id]: ...` definition lines — okf.py's
render() (section-02) auto-generates the footnote-definition block from
ConceptFile.sources, filtered by ids actually referenced in body. Adding
definition lines here would duplicate what render() already emits.

Note on homeric/attic period-scoping: eee_engine.collect_slot_forms()
is called with `backend=period` for both ancient periods, so each gets
its own, genuinely period-scoped query rather than one shared query
reused for both. This requires the caller to have registered distinct
named backend variants for "grc" — e.g.
eee.register_backend("grc", AncientGreekBackend.for_period("epic"), backend="homeric")
eee.register_backend("grc", AncientGreekBackend.for_period("attic"), backend="attic")
(the registered backend *name* is an arbitrary label chosen at
registration time — it doesn't have to match for_period()'s own argument
spelling; "homeric" above is this module's period vocabulary, "epic" is
the backend's). If no backend is registered under a given period's name,
that period's eee_engine contribution is simply empty (see
eee_engine.collect_slot_forms's own docstring) — not an error, so a
caller that only wants one period doesn't need to register the others.

Note on LLM-inferred forms: collect_slot_forms() can return a mix of
RULE_BASED and LLM_INFERRED SlotForms under different labels (never both
for the same label). LLM-inferred forms are cited distinctly (one Source
per distinct model/method, not per slot) and marked with `†` in body text
— never the linguistic `*`, which has established, different meanings
(reconstructed/unattested/ungrammatical) that an LLM guess doesn't
necessarily fit. Rule-based forms are unaffected either way; this module's
output is byte-identical to before when sources.llm_gap_filler is None.
"""

from collections.abc import Callable
from dataclasses import dataclass

from okfbuild.concepts import GENERATED_BY
from okfbuild.okf import ConceptFile, Source
from okfbuild.sources import SourceBundle
from okfbuild.sources.eee_engine import FormSourceType, SlotForms
from okfbuild.sources.llm_gap_filler import GapFillCache
from okfbuild.sources.lsj_index import LSJCitation, LSJText
from okfbuild.sources.lsj_periods import LSJPeriodMap

_ANCIENT_PERIODS = ("homeric", "attic")


@dataclass(frozen=True)
class GapFillRecord:
    """One LLM_INFERRED form, with enough context to become one JSON
    handoff entry (see gap_filler_pilot.run_gap_filler_pilot()). Captured
    directly from the structured SlotForms result as the run executes --
    never derived by parsing rendered markdown body text back apart."""

    lemma: str
    form: str
    slot_label: str
    features: dict[str, str]
    pos: str
    language: str
    period: str | None
    method: str
    llm_backend_version: str


_EEE_ENGINE_SOURCE = {
    "resource": "https://codeberg.org/EEE-project/eee-project",
    "title": "EEE morphology engine",
    "author": "EEE project",
}
_MORPHEUS_SOURCE = {
    "resource": "https://services.perseids.org/bsp/morphologyservice/analysis/word",
    "title": "Perseids Morpheus",
    "author": "Perseids Project",
}
_BYZANTINE_SOURCE = {
    "resource": "greek-inflexion-eee/byzantine_verbs_lexicon.yaml",
    "title": "Byzantine Verbs Lexicon",
    "author": "Sophocles (1887), curated",
}
_WIKTEXTRACT_SOURCE = {
    "resource": "https://kaikki.org/elwiktionary/", "title": "Wiktextract (kaikki.org)", "author": "kaikki.org"
}
_BEEKES_SOURCE = {
    "resource": "Beekes (2010), Etymological Dictionary of Greek",
    "title": "Etymological Dictionary of Greek",
    "author": "Robert Beekes",
}
_LSJ_SOURCE = {
    "resource": "https://github.com/PerseusDL/lexica/tree/master/CTS_XML_TEI/perseus/pdllex/grc/lsj",
    "title": "Liddell-Scott-Jones Greek-English Lexicon",
    "author": "Perseus Digital Library",
}
_LLM_GAP_FILLER_SOURCE = {
    "resource": "llm-backend-eee gap-filler",
    "title": "LLM-inferred (unverified)",
}
_LLM_MARKER_LEGEND = "† LLM-inferred (unverified) form; not independently attested or rule-derived."


def _lsj_citation_tag(citation: LSJCitation, period_map: "LSJPeriodMap | None") -> "str | None":
    """The inline `**[Period, Dialect]**` tag for one citation, or None
    when neither is known (never fabricated). Order is always
    [period, dialect] when both are present; multiple dialects join with
    " / "."""
    period = period_map.period_for_citation(citation) if period_map is not None else None
    parts = []
    if period is not None:
        parts.append(period.label)
    if citation.dialects:
        parts.append(" / ".join(citation.dialects))
    return f"**[{', '.join(parts)}]**" if parts else None


def render_lsj_entry(segments: "list[LSJText | LSJCitation]", period_map: "LSJPeriodMap | None" = None) -> str:
    """Turn a headword's LSJ segment list (produced by
    okfbuild.sources.lsj_index's segment-producing extraction) into the
    markdown string for the "## Ancient Greek meaning" section body
    (before the trailing `[^lsj]` footnote reference, which the caller
    still appends exactly as today). Each LSJCitation gets a leading
    inline tag combining its resolved period and/or dialect(s) when
    either is known -- see _lsj_citation_tag() -- with one space before
    its own text; a citation with neither known renders with no tag at
    all, exactly as it would have before this section's changes.
    LSJText segments render as plain, untagged text; consecutive
    segments concatenate directly (no separator inserted), since each
    segment's own text already carries whatever whitespace/punctuation
    belongs at its boundary -- this is a straight re-linearization of
    what extraction split apart, not a reformatting pass.

    `period_map=None` (the default) is a legitimate, common case, not a
    caller error -- an LSJPeriodMap is expensive to build (a full dump
    scan when its own cache is stale), and every citation still renders
    correctly with dialect-only tags (or no tag) when period data isn't
    available."""
    parts = []
    for segment in segments:
        if isinstance(segment, LSJText):
            parts.append(segment.text)
        else:
            tag = _lsj_citation_tag(segment, period_map)
            parts.append(f"{tag} {segment.text}" if tag else segment.text)
    return "".join(parts)


def build(
    lemma: str,
    pos: str,
    periods: list[str],
    sources: SourceBundle,
    level: list[str],
    tags: list[str],
    beekes_citation: str | None = None,
    source_course: str | None = None,
    cache: "GapFillCache | None" = None,
    on_llm_inferred: "Callable[[GapFillRecord], None] | None" = None,
) -> ConceptFile:
    """Assemble a Lexical Entry for `lemma`, querying each source relevant
    to the requested `periods`: eee_engine + morpheus_client for
    homeric/attic (each ancient period queries eee_engine with its own
    `backend=period` — see module docstring), byzantine_lexicon for
    byzantine, eee_engine + wiktextract_index for modern. Each attested
    form becomes a cited footnote. A requested period with no data in any
    relevant source produces no section — `periods` in the returned
    ConceptFile may be a subset of the requested `periods`.

    If `periods` includes homeric and/or attic and `sources.lsj` has an
    entry for `lemma`, a single "Ancient Greek meaning" section is added
    after the per-period sections (once, not duplicated per period — LSJ
    entries aren't period-scoped the way inflected forms are). Independent
    of morphological attestation: a lemma with no eee_engine/Morpheus hits
    for either ancient period can still get this section on its own,
    matching how a Modern-period Wiktextract gloss doesn't require
    attested inflected forms either.

    `sources.llm_gap_filler` (if set) is forwarded to every
    collect_slot_forms() call, opaquely — this function never inspects a
    GapFillerConfig's internals. When it is None (the default), behavior
    and output are unchanged from before LLM gap-filling existed.

    `cache`, if given, is used as-is for every collect_slot_forms() call in
    this invocation instead of constructing a fresh GapFillCache
    internally — this is what lets a caller share one cache across many
    build() calls (see pipeline.run()). Omitting it (the default) falls
    back to today's per-build()-call, ephemeral cache whenever
    sources.llm_gap_filler is set; every caller that predates this
    parameter is unaffected.

    `beekes_citation`, if given, should embed its own page locator inline
    as normal scholarly prose would (e.g. "...(Beekes 2010, p. 1017)") —
    build() has no separate parameter for it, since different lemmas cite
    different pages of the same work.

    `on_llm_inferred`, if given, is called once per individual LLM-inferred
    form (a GapFillRecord each) as soon as each period's collect_slot_forms()
    result comes back — this is the ONLY point in the whole pipeline where
    the structured SlotForms data (features, method, llm_backend_version)
    is still available; it is discarded once rendered into this function's
    markdown `body`. Omitting it (the default) is a pure no-op — behavior
    and output are byte-identical to before this parameter existed."""
    concept_sources: list[Source] = []
    seen_source_ids: set[str] = set()
    body_sections: list[str] = []
    attested_periods: list[str] = []

    def cite(source_id: str, resource: str, title: str, author: str) -> None:
        if source_id not in seen_source_ids:
            concept_sources.append(Source(id=source_id, resource=resource, title=title, author=author))
            seen_source_ids.add(source_id)

    def emit_llm_inferred_records(forms: dict[str, SlotForms], language: str, period_arg: str | None) -> None:
        if on_llm_inferred is None:
            return
        for slot_label, slot_forms in forms.items():
            if slot_forms.source_type != FormSourceType.LLM_INFERRED:
                continue
            for form in slot_forms.forms:
                on_llm_inferred(
                    GapFillRecord(
                        lemma=lemma,
                        form=form,
                        slot_label=slot_label,
                        features=slot_forms.features or {},
                        pos=pos,
                        language=language,
                        period=period_arg,
                        method=slot_forms.method,
                        llm_backend_version=slot_forms.llm_backend_version,
                    )
                )

    # collect_slot_forms() requires a real GapFillCache whenever gap_filler
    # is set (raises ValueError otherwise). A caller-supplied `cache` is
    # used as-is -- this is what lets pipeline.run() share one GapFillCache
    # across every candidate it processes, not just across the homeric/
    # modern queries within one build() call. Falling back to a fresh,
    # build()-scoped instance keeps every caller that predates `cache`
    # (and any direct build() call that just wants an ephemeral cache)
    # working unchanged.
    if cache is not None:
        gap_fill_cache = cache
    elif sources.llm_gap_filler is not None:
        gap_fill_cache = GapFillCache()
    else:
        gap_fill_cache = None

    morpheus_readings = None
    modern_forms = None
    wiktextract_entry = None
    lsj_entry = None
    lsj_looked_up = False

    for period in periods:
        if period in _ANCIENT_PERIODS:
            ancient_forms = sources.eee_engine.collect_slot_forms(
                lemma, pos, "grc", backend=period, gap_filler=sources.llm_gap_filler, cache=gap_fill_cache,
                source_course=source_course,
            )
            emit_llm_inferred_records(ancient_forms, "grc", period)
            if morpheus_readings is None:
                morpheus_readings = sources.morpheus.analyze(lemma)
            # A separate flag, not `if lsj_entry is None:` -- lookup()'s
            # legitimate "no entry" return value is also None, so that
            # sentinel would re-query on every ancient period whenever
            # nothing was found (the common case today: every LSJIndex
            # constructed anywhere in this codebase is still the empty
            # placeholder, see data/lsj/README.md).
            if not lsj_looked_up:
                lsj_entry = sources.lsj.lookup(lemma)
                lsj_looked_up = True
            section = _ancient_period_section(period, ancient_forms, morpheus_readings, cite)
        elif period == "byzantine":
            forms = sources.byzantine_forms.get(lemma)
            section = _byzantine_period_section(forms, cite) if forms else None
        elif period == "modern":
            if modern_forms is None:
                modern_forms = sources.eee_engine.collect_slot_forms(
                    lemma, pos, "el", gap_filler=sources.llm_gap_filler, cache=gap_fill_cache,
                    source_course=source_course,
                )
                emit_llm_inferred_records(modern_forms, "el", None)
            if wiktextract_entry is None:
                wiktextract_entry = sources.wiktextract.lookup(lemma)
            section = _modern_period_section(modern_forms, wiktextract_entry, cite)
        else:
            raise ValueError(f"unknown period: {period!r}")

        if section is not None:
            attested_periods.append(period)
            body_sections.append(f"## {period.capitalize()}\n\n{section}")

    if any(source_id.startswith("llm-gap-filler-") for source_id in seen_source_ids):
        body_sections.append(_LLM_MARKER_LEGEND)

    if lsj_entry:
        source_id = "lsj"
        cite(source_id, **_LSJ_SOURCE)
        rendered_lsj_entry = render_lsj_entry(lsj_entry, sources.lsj_period_map)
        body_sections.append(f"## Ancient Greek meaning\n\n{rendered_lsj_entry}[^{source_id}]")
        # attested_periods must reflect this too, not just body_sections --
        # pipeline.py's real candidate-acceptance gate discards any concept
        # whose extra_frontmatter["periods"] comes back empty ("no attested
        # data in any source"). Without this, a lemma with an LSJ entry but
        # no eee_engine/Morpheus/wiktextract/byzantine hit anywhere would
        # have its whole concept silently dropped, LSJ content included.
        for ancient_period in _ANCIENT_PERIODS:
            if ancient_period in periods and ancient_period not in attested_periods:
                attested_periods.append(ancient_period)

    if beekes_citation:
        source_id = "beekes-edg"
        cite(source_id, **_BEEKES_SOURCE)
        body_sections.append(f"## Etymology\n\n{beekes_citation}[^{source_id}]")

    return ConceptFile(
        type="Lexical Entry",
        title=lemma,
        description=f"Lexical entry for {lemma}.",
        tags=tags,
        level=level,
        sources=concept_sources,
        generated_by=GENERATED_BY,
        body="\n\n".join(body_sections),
        extra_frontmatter={"lemma": lemma, "periods": attested_periods},
    )


def _format_forms(forms: dict[str, set[str]]) -> str:
    parts = [f"{label}: {', '.join(sorted(forms[label]))}" for label in sorted(forms)]
    return "; ".join(parts)


def _partition_slot_forms(forms: dict[str, SlotForms]) -> tuple[dict[str, set[str]], dict[str, SlotForms]]:
    """Splits a collect_slot_forms() result by provenance. `rule_based`
    matches _format_forms's existing input shape unchanged ({label: forms}),
    so the rule-based rendering path is untouched by this split. `llm_inferred`
    keeps the full SlotForms (its method/llm_backend_version are needed for
    citation)."""
    rule_based = {label: sf.forms for label, sf in forms.items() if sf.source_type == FormSourceType.RULE_BASED}
    llm_inferred = {label: sf for label, sf in forms.items() if sf.source_type == FormSourceType.LLM_INFERRED}
    return rule_based, llm_inferred


def _llm_inferred_lines(llm_inferred: dict[str, SlotForms], cite) -> list[str]:
    """One line per distinct method among llm_inferred's values, each
    citing exactly one Source -- deduplicated across the WHOLE build()
    call (not just this period) via cite()'s existing seen_source_ids
    mechanism, keyed on a method-derived (not period-derived) source_id --
    and marked with `†`, never `*` (see module docstring)."""
    forms_by_method: dict[str, dict[str, set[str]]] = {}
    version_by_method: dict[str, str | None] = {}
    for label, slot_forms in llm_inferred.items():
        forms_by_method.setdefault(slot_forms.method, {})[label] = slot_forms.forms
        version_by_method[slot_forms.method] = slot_forms.llm_backend_version

    lines = []
    for method in sorted(forms_by_method):
        source_id = "llm-gap-filler-" + method.replace(":", "-")
        cite(
            source_id,
            **_LLM_GAP_FILLER_SOURCE,
            author=f"{method} (llm-backend-eee v{version_by_method[method]})",
        )
        lines.append(f"LLM-inferred forms: {_format_forms(forms_by_method[method])}†[^{source_id}]")
    return lines


def _ancient_period_section(period, ancient_forms, morpheus_readings, cite) -> str | None:
    rule_based, llm_inferred = _partition_slot_forms(ancient_forms)
    lines = []
    if rule_based:
        source_id = f"eee-{period}"
        cite(source_id, **_EEE_ENGINE_SOURCE)
        lines.append(f"Attested forms: {_format_forms(rule_based)}[^{source_id}]")
    lines.extend(_llm_inferred_lines(llm_inferred, cite))
    if morpheus_readings:
        source_id = f"morpheus-{period}"
        cite(source_id, **_MORPHEUS_SOURCE)
        readings = sorted({r["lemma"] for r in morpheus_readings if r.get("lemma")})
        if readings:
            lines.append(f"Independently confirmed by Morpheus analysis ({', '.join(readings)})[^{source_id}]")
    return "\n\n".join(lines) if lines else None


def _byzantine_period_section(forms: dict[str, str | list[str]], cite) -> str:
    source_id = "byzantine-lexicon"
    cite(source_id, **_BYZANTINE_SOURCE)
    cells = "; ".join(f"{tag}: {_join_form(form)}" for tag, form in sorted(forms.items()))
    return f"Attested Byzantine forms: {cells}[^{source_id}]"


def _join_form(form: str | list[str]) -> str:
    return form if isinstance(form, str) else ", ".join(form)


def _modern_period_section(modern_forms, wiktextract_entry, cite) -> str | None:
    rule_based, llm_inferred = _partition_slot_forms(modern_forms)
    lines = []
    if rule_based:
        source_id = "eee-modern"
        cite(source_id, **_EEE_ENGINE_SOURCE)
        lines.append(f"Attested forms: {_format_forms(rule_based)}[^{source_id}]")
    lines.extend(_llm_inferred_lines(llm_inferred, cite))
    if wiktextract_entry:
        source_id = "wiktextract-modern"
        cite(source_id, **_WIKTEXTRACT_SOURCE)
        glosses = [", ".join(sense["glosses"]) for sense in wiktextract_entry.get("senses") or [] if sense.get("glosses")]
        if len(glosses) > 1:
            lines.extend(f"**Sense {i}:** {gloss}[^{source_id}]" for i, gloss in enumerate(glosses, start=1))
        elif glosses:
            lines.append(f"{glosses[0]}[^{source_id}]")
    return "\n\n".join(lines) if lines else None
