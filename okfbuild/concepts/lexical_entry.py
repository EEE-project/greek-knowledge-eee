"""Assembles a Lexical Entry ConceptFile from section-03's source clients.

Note on body/footnote shape: this module's `body` strings contain ONLY
inline `[^id]` references, never `[^id]: ...` definition lines — okf.py's
render() (section-02) auto-generates the footnote-definition block from
ConceptFile.sources, filtered by ids actually referenced in body. Adding
definition lines here would duplicate what render() already emits.

Note on homeric/attic period-scoping: eee_engine.inflect_all_attested()
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
eee_engine.inflect_all_attested's own docstring) — not an error, so a
caller that only wants one period doesn't need to register the others.
"""

from okfbuild.concepts import GENERATED_BY
from okfbuild.okf import ConceptFile, Source
from okfbuild.sources import SourceBundle

_ANCIENT_PERIODS = ("homeric", "attic")

_EEE_ENGINE_SOURCE = dict(
    resource="https://codeberg.org/EEE-project/eee-project",
    title="EEE morphology engine",
    author="EEE project",
)
_MORPHEUS_SOURCE = dict(
    resource="https://services.perseids.org/bsp/morphologyservice/analysis/word",
    title="Perseids Morpheus",
    author="Perseids Project",
)
_BYZANTINE_SOURCE = dict(
    resource="greek-inflexion-eee/byzantine_verbs_lexicon.yaml",
    title="Byzantine Verbs Lexicon",
    author="Sophocles (1887), curated",
)
_WIKTEXTRACT_SOURCE = dict(
    resource="https://kaikki.org/elwiktionary/", title="Wiktextract (kaikki.org)", author="kaikki.org"
)
_BEEKES_SOURCE = dict(
    resource="Beekes (2010), Etymological Dictionary of Greek",
    title="Etymological Dictionary of Greek",
    author="Robert Beekes",
)


def build(
    lemma: str,
    pos: str,
    periods: list[str],
    sources: SourceBundle,
    level: list[str],
    tags: list[str],
    beekes_citation: str | None = None,
) -> ConceptFile:
    """Assemble a Lexical Entry for `lemma`, querying each source relevant
    to the requested `periods`: eee_engine + morpheus_client for
    homeric/attic (each ancient period queries eee_engine with its own
    `backend=period` — see module docstring), byzantine_lexicon for
    byzantine, eee_engine + wiktextract_index for modern. Each attested
    form becomes a cited footnote. A requested period with no data in any
    relevant source produces no section — `periods` in the returned
    ConceptFile may be a subset of the requested `periods`.

    `beekes_citation`, if given, should embed its own page locator inline
    as normal scholarly prose would (e.g. "...(Beekes 2010, p. 1017)") —
    build() has no separate parameter for it, since different lemmas cite
    different pages of the same work."""
    concept_sources: list[Source] = []
    seen_source_ids: set[str] = set()
    body_sections: list[str] = []
    attested_periods: list[str] = []

    def cite(source_id: str, resource: str, title: str, author: str) -> None:
        if source_id not in seen_source_ids:
            concept_sources.append(Source(id=source_id, resource=resource, title=title, author=author))
            seen_source_ids.add(source_id)

    morpheus_readings = None
    modern_forms = None
    wiktextract_entry = None

    for period in periods:
        if period in _ANCIENT_PERIODS:
            ancient_forms = sources.eee_engine.inflect_all_attested(lemma, pos, "grc", backend=period)
            if morpheus_readings is None:
                morpheus_readings = sources.morpheus.analyze(lemma)
            section = _ancient_period_section(period, ancient_forms, morpheus_readings, cite)
        elif period == "byzantine":
            forms = sources.byzantine_forms.get(lemma)
            section = _byzantine_period_section(forms, cite) if forms else None
        elif period == "modern":
            if modern_forms is None:
                modern_forms = sources.eee_engine.inflect_all_attested(lemma, pos, "el")
            if wiktextract_entry is None:
                wiktextract_entry = sources.wiktextract.lookup(lemma)
            section = _modern_period_section(modern_forms, wiktextract_entry, cite)
        else:
            raise ValueError(f"unknown period: {period!r}")

        if section is not None:
            attested_periods.append(period)
            body_sections.append(f"## {period.capitalize()}\n\n{section}")

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


def _ancient_period_section(period, ancient_forms, morpheus_readings, cite) -> str | None:
    lines = []
    if ancient_forms:
        source_id = f"eee-{period}"
        cite(source_id, **_EEE_ENGINE_SOURCE)
        lines.append(f"Attested forms: {_format_forms(ancient_forms)}[^{source_id}]")
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
    lines = []
    if modern_forms:
        source_id = "eee-modern"
        cite(source_id, **_EEE_ENGINE_SOURCE)
        lines.append(f"Attested forms: {_format_forms(modern_forms)}[^{source_id}]")
    if wiktextract_entry:
        source_id = "wiktextract-modern"
        cite(source_id, **_WIKTEXTRACT_SOURCE)
        glosses = [", ".join(sense["glosses"]) for sense in wiktextract_entry.get("senses") or [] if sense.get("glosses")]
        if len(glosses) > 1:
            lines.extend(f"**Sense {i}:** {gloss}[^{source_id}]" for i, gloss in enumerate(glosses, start=1))
        elif glosses:
            lines.append(f"{glosses[0]}[^{source_id}]")
    return "\n\n".join(lines) if lines else None
