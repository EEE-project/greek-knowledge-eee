"""Cross-checks section-04's LLM-inferred-forms handoff file against the
real Perseids Morpheus service, via okfbuild.sources.morpheus_client's
MorpheusClient.

Interface choice: MorpheusClient (okfbuild/sources/morpheus_client.py),
not the sibling-repo tools/morpheus/query_morpheus.py CLI. MorpheusClient
is already a dependency (used for lemma-level "Independently confirmed by
Morpheus analysis" citations in okfbuild/concepts/lexical_entry.py),
already cached, already rate-limited (_REQUEST_DELAY), and its analyze()
already returns exactly the structured grammatical detail this section
needs (lemma/pofs/case/number/gender/person/tense/mood/voice/stemtype/
decl/dial) -- confirmed sufficient for every feature axis this pilot's
Ancient Greek slot templates use. query_morpheus.py lives under
greek-inflexion-eee's own tools/ directory, not its installable package
-- importing it directly would mean depending on another repo's internal
layout rather than its public API (the same reasoning morpheus_client.py's
own module docstring already gives for not importing it there either).

Informational only: flags disagreement, blocks nothing, never modifies
words/*.md.
"""

import json
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from okfbuild.sources.llm_gap_filler import normalize_form
from okfbuild.sources.morpheus_client import MorpheusClient

_HANDOFF_FORMAT_VERSION = 1

# --- UD-FEATS <-> Morpheus vocabulary mapping --------------------------------
#
# Scoped to exactly the seven feature axes this pilot's Ancient Greek slot
# templates use (Case, Number, Gender, Person, Tense, Voice, VerbForm+Mood)
# -- not a general UD<->Perseus translator. Values are the REAL, full,
# spelled-out lowercase English words real Morpheus responses use (e.g.
# "genitive", "masculine", "participle") -- NOT the abbreviated shape this
# repo's own pre-existing MorpheusClient test fixtures happen to use
# (those predate this module, are out of scope to fix, and using their
# shape here would make this module's own tests look correct while being
# silently wrong against every real response).

_CASE = {"Nom": "nominative", "Acc": "accusative", "Gen": "genitive", "Dat": "dative", "Voc": "vocative"}
_NUMBER = {"Sing": "singular", "Plur": "plural", "Dual": "dual"}
_GENDER = {"Masc": "masculine", "Fem": "feminine", "Neut": "neuter"}
_PERSON = {"1": "1st", "2": "2nd", "3": "3rd"}
_TENSE = {"Pres": "present", "Imp": "imperfect", "Aor": "aorist", "Perf": "perfect", "Pqp": "pluperfect", "Fut": "future"}
# VerbForm=="Fin" carries no independent check of its own -- Mood (checked
# separately, only present in `features` for finite forms) carries it.
# VerbForm in ("Inf", "Part") stands in for what would otherwise be a Mood
# check, since Morpheus has no separate "verbform" field -- infinitive and
# participle are themselves *mood* values in Morpheus's own vocabulary.
_FINITE_MOOD = {"Ind": "indicative", "Sub": "subjunctive", "Opt": "optative", "Imp": "imperative"}
_NONFINITE_VERBFORM = {"Inf": "infinitive", "Part": "participle"}

# Voice is the one axis with genuine value-level ambiguity: Morpheus commonly
# reports "mediopassive" for stems where Greek doesn't morphologically
# distinguish middle from passive -- a mediopassive reading neither confirms
# nor contradicts a specifically-requested Mid or Pass, so it's modeled as
# match-sets, not a flat 1:1 dict.
_VOICE_MATCH = {
    "Act": {"active"},
    "Mid": {"middle"},
    "Pass": {"passive"},
    "Mid,Pass": {"mediopassive", "middle", "passive"},
}
_VOICE_COMPATIBLE_NOT_CONFIRMING = {
    "Act": set(),
    "Mid": {"mediopassive"},
    "Pass": {"mediopassive"},
    "Mid,Pass": set(),
}


class CrosscheckCategory(Enum):
    CONFIRMED = auto()  # "Confirmed, matching slot"
    DIFFERENT_ANALYSIS = auto()  # "Found, but different analysis"
    UNDERSPECIFIED = auto()  # "Found, compatible but insufficiently specified to confirm the full slot"
    UNCONFIRMED = auto()  # displayed as: "not confirmed by queried Morpheus source" (never a bare "unconfirmed")
    QUERY_FAILED = auto()  # the Morpheus query itself errored


_CATEGORY_LABELS: dict[CrosscheckCategory, str] = {
    CrosscheckCategory.CONFIRMED: "Confirmed, matching slot",
    CrosscheckCategory.DIFFERENT_ANALYSIS: "Found, but different analysis",
    CrosscheckCategory.UNDERSPECIFIED: "Found, compatible but insufficiently specified to confirm the full slot",
    CrosscheckCategory.UNCONFIRMED: "not confirmed by queried Morpheus source",
    CrosscheckCategory.QUERY_FAILED: "Morpheus query failed",
}


@dataclass(frozen=True)
class CrosscheckResult:
    lemma: str
    form: str
    slot_label: str
    features: dict[str, str]
    pos: str
    language: str
    period: str | None
    method: str
    category: CrosscheckCategory
    detail: str = ""  # e.g. which reading(s) matched, or the query-failure message


@dataclass(frozen=True)
class CrosscheckReport:
    results: list[CrosscheckResult]
    skipped_non_grc: list[dict]  # raw handoff entries never sent to Morpheus


def _feature_key_outcome(key: str, value: str, reading: dict) -> str:
    """Returns "MATCH", "COMPATIBLE", or "CONTRADICT" for one requested
    feature key/value against one Morpheus reading."""
    if key == "VerbForm":
        if value == "Fin":
            return "MATCH"  # structural marker only -- Mood (below) carries the real check
        return "MATCH" if reading.get("mood") == _NONFINITE_VERBFORM[value] else "CONTRADICT"
    if key == "Mood":
        return "MATCH" if reading.get("mood") == _FINITE_MOOD[value] else "CONTRADICT"
    if key == "Voice":
        reading_voice = reading.get("voice")
        if reading_voice in _VOICE_MATCH[value]:
            return "MATCH"
        if reading_voice in _VOICE_COMPATIBLE_NOT_CONFIRMING[value]:
            return "COMPATIBLE"
        return "CONTRADICT"
    field_name, vocab = {
        "Case": ("case", _CASE),
        "Number": ("number", _NUMBER),
        "Gender": ("gender", _GENDER),
        "Person": ("person", _PERSON),
        "Tense": ("tense", _TENSE),
    }[key]
    return "MATCH" if reading.get(field_name) == vocab[value] else "CONTRADICT"


def _classify_one_reading(features: dict[str, str], reading: dict) -> str:
    """Aggregates every requested feature key's outcome against ONE
    reading: all MATCH -> "MATCH"; all MATCH-or-COMPATIBLE with at least
    one COMPATIBLE -> "COMPATIBLE"; any CONTRADICT -> "CONTRADICT"."""
    outcomes = [_feature_key_outcome(key, value, reading) for key, value in features.items()]
    if all(outcome == "MATCH" for outcome in outcomes):
        return "MATCH"
    if all(outcome in ("MATCH", "COMPATIBLE") for outcome in outcomes):
        return "COMPATIBLE"
    return "CONTRADICT"


def _describe_reading(reading: dict) -> str:
    parts = [f"{key}={value}" for key, value in reading.items() if value not in (None, "", [])]
    return ", ".join(parts)


def _classify_readings(lemma: str, features: dict[str, str], readings: "list[dict] | None") -> tuple:
    """Pure classification logic -- no I/O. `readings=None` means the query
    failed (-> QUERY_FAILED); `readings=[]` means it succeeded with nothing
    found (-> UNCONFIRMED). A reading only counts at all if its own
    "lemma" field matches the requested lemma -- Morpheus analyzes a
    *form* and can report readings under an unrelated homograph lemma
    that must never be mistaken for confirmation of THIS request."""
    if readings is None:
        return CrosscheckCategory.QUERY_FAILED, _CATEGORY_LABELS[CrosscheckCategory.QUERY_FAILED]

    lemma_readings = [reading for reading in readings if reading.get("lemma") == lemma]
    if not lemma_readings:
        return CrosscheckCategory.UNCONFIRMED, _CATEGORY_LABELS[CrosscheckCategory.UNCONFIRMED]

    outcomes = [(_classify_one_reading(features, reading), reading) for reading in lemma_readings]

    matches = [reading for outcome, reading in outcomes if outcome == "MATCH"]
    if matches:
        return CrosscheckCategory.CONFIRMED, f"matched reading: {_describe_reading(matches[0])}"

    compatible = [reading for outcome, reading in outcomes if outcome == "COMPATIBLE"]
    if compatible:
        return CrosscheckCategory.UNDERSPECIFIED, f"compatible (ambiguous) reading: {_describe_reading(compatible[0])}"

    return CrosscheckCategory.DIFFERENT_ANALYSIS, f"{len(lemma_readings)} reading(s) under this lemma, none matched"


def _query_morpheus_or_none(morpheus: MorpheusClient, form: str) -> "list[dict] | None":
    """Wraps morpheus.analyze(form, raise_on_error=True); returns None
    (not raises) on failure, so callers get a plain three-state signal
    (list of readings / empty list / None)."""
    try:
        return morpheus.analyze(form, raise_on_error=True)
    except Exception:
        return None


def _dedup_key(entry: dict) -> tuple:
    return (
        entry["lemma"],
        normalize_form(entry["form"]),
        tuple(sorted(entry["features"].items())),  # dict isn't hashable; same pattern GapFillCache.make_key() uses
        entry["pos"],
        entry["language"],
    )


def crosscheck_handoff_file(handoff_path: Path, report_path: Path, morpheus: MorpheusClient) -> CrosscheckReport:
    """Reads handoff_path (validating format_version == 1, raising a clear
    error otherwise -- mirrors GapFillCache.load()'s established
    fail-loudly convention from section-02, applied lightly here since
    there is only one schema version so far), splits entries by
    language == "grc" (Morpheus's morpheusgrc engine is Ancient/Koine-only
    -- non-grc entries are never queried, never classified, and are
    reported in their own distinct section instead of being silently
    dropped or folded into UNCONFIRMED), deduplicates the grc entries via
    _dedup_key(), queries `morpheus` at most once per unique key (but every
    original entry -- even ones sharing a dedup key, e.g. the same form
    generated for both "homeric" and "attic" -- still gets its own line in
    the returned report), classifies each, writes a human-readable
    Markdown report to report_path, and returns the same data as a
    CrosscheckReport. `morpheus` is caller-supplied (not constructed here)
    so tests can pass a Mock() -- this function performs no MorpheusClient
    construction and reads no real cache_dir itself. An empty `entries`
    list produces a well-formed, empty report -- not an error."""
    try:
        data = json.loads(handoff_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"crosscheck_handoff_file(): corrupt handoff file at {handoff_path}: {exc}") from exc
    format_version = data.get("format_version")
    if format_version != _HANDOFF_FORMAT_VERSION:
        raise ValueError(
            f"crosscheck_handoff_file(): unsupported handoff format_version {format_version!r} "
            f"at {handoff_path} (expected {_HANDOFF_FORMAT_VERSION})"
        )
    run_timestamp = data.get("run_timestamp", "")
    entries = data.get("entries", [])

    grc_entries = [entry for entry in entries if entry["language"] == "grc"]
    skipped_non_grc = [entry for entry in entries if entry["language"] != "grc"]

    classification_by_key: dict[tuple, tuple] = {}
    for entry in grc_entries:
        key = _dedup_key(entry)
        if key not in classification_by_key:
            readings = _query_morpheus_or_none(morpheus, entry["form"])
            classification_by_key[key] = _classify_readings(entry["lemma"], entry["features"], readings)

    results = [
        CrosscheckResult(
            lemma=entry["lemma"],
            form=entry["form"],
            slot_label=entry["slot_label"],
            features=entry["features"],
            pos=entry["pos"],
            language=entry["language"],
            period=entry.get("period"),
            method=entry["method"],
            category=classification_by_key[_dedup_key(entry)][0],
            detail=classification_by_key[_dedup_key(entry)][1],
        )
        for entry in grc_entries
    ]

    report = CrosscheckReport(results=results, skipped_non_grc=skipped_non_grc)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(report, run_timestamp), encoding="utf-8")
    return report


def render_report(report: CrosscheckReport, run_timestamp: str) -> str:
    """Pure Markdown-rendering helper, separately testable from the
    querying/classification above -- grouped by category, each result
    line showing lemma/form/slot_label/pos/language/period/method/detail;
    the non-grc section listed separately, not folded into any category."""
    lines = ["# Morpheus Cross-Check Report", "", f"Run timestamp: {run_timestamp}", ""]

    by_category: dict[CrosscheckCategory, list[CrosscheckResult]] = {}
    for result in report.results:
        by_category.setdefault(result.category, []).append(result)

    for category in CrosscheckCategory:
        results = by_category.get(category, [])
        lines.append(f"## {_CATEGORY_LABELS[category]} ({len(results)})")
        lines.append("")
        if not results:
            lines.append("_None._")
        else:
            for result in results:
                period_part = f", {result.period}" if result.period else ""
                lines.append(
                    f"- **{result.lemma}** / {result.form} ({result.slot_label}, {result.pos}, "
                    f"{result.language}{period_part}) — method: {result.method}"
                    + (f" — {result.detail}" if result.detail else "")
                )
        lines.append("")

    lines.append(
        f"## Not checked — non-Ancient-Greek entries; Morpheus is Ancient/Koine-only ({len(report.skipped_non_grc)})"
    )
    lines.append("")
    if not report.skipped_non_grc:
        lines.append("_None._")
    else:
        for entry in report.skipped_non_grc:
            lines.append(f"- **{entry.get('lemma')}** / {entry.get('form')} ({entry.get('language')})")
    lines.append("")

    return "\n".join(lines)
