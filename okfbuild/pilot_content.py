"""Curated inputs for the section-07 pilot run.

Unlike Lexical Entry candidates (auto-extracted from course vocabulary
TSVs by pipeline._collect_lexical_candidates), a Grammatical Rule or
Cultural Context entry has no TSV to derive from — the plan requires a
human to curate the excerpt/prose/example forms directly (see
plans/sections/section-07-pilot.md, "Preparing the real inputs"). This
module holds that curated content so tests/conftest.py's pilot_build_report
fixture stays focused on fixture wiring, and so the same specs are usable
from a future standalone re-run script, not only from pytest.
"""

from pathlib import Path

from okfbuild import okf
from okfbuild.concepts import lexical_entry
from okfbuild.okf import Source
from okfbuild.pipeline import CulturalTopicSpec, GrammarRuleSpec
from okfbuild.sources import SourceBundle

# Matches pipeline.py's own _ALL_PERIODS — duplicated rather than imported
# since that name is private to pipeline.py (this module only rebuilds one
# specific lemma's entry, not a general-purpose pipeline helper).
_ALL_PERIODS = ["homeric", "attic", "byzantine", "modern"]

_SOPHOCLES_SOURCE = Source(
    id="sophocles-1887",
    resource="analisys/sophocles-byzantine-morphology.md",
    title="Greek Lexicon of the Roman and Byzantine Periods (1887)",
    author="E. A. Sophocles",
)

_OSAN_BODY = """\
## The -οσαν aorist/imperfect 3rd plural

In post-classical (Byzantine-period) Greek, the classical 3rd-plural \
imperfect/2nd-aorist active ending **-ον** is often replaced by an \
analogical ending **-οσαν** — grammarians call it "Boeotic, Chalcidean, \
or Asiatic."[^sophocles-1887] The innovation resolves a real syncretism: \
classically, a 2nd-aorist verb's 3rd-plural form is identical to its \
1st-singular (ἦλθον = "I came" *or* "they came"; εἶδον = "I saw" *or* \
"they saw"). The Byzantine -οσαν ending gives the 3rd plural a form of \
its own.

Both of the verbs cited below are common Homeric verbs of coming/going \
and seeing, already attested (in their classical 3rd-singular aorist \
forms, ἦλθε/ἴδεν) in the same Odyssey passage this knowledge base draws \
its Lexical Entry examples from.

ὁράω is replaced by ἴδοσαν in Byzantine Greek[^sophocles-1887]

ὁράω is replaced by εἴδοσαν in Byzantine Greek[^sophocles-1887]

ἔρχομαι is replaced by ἤλθοσαν in Byzantine Greek[^sophocles-1887]"""

GRAMMAR_RULES: list[GrammarRuleSpec] = [
    GrammarRuleSpec(
        rule_id="aorist-3pl-osan",
        body=_OSAN_BODY,
        sources=[_SOPHOCLES_SOURCE],
        period_from="attic",
        period_to="byzantine",
        level=["advanced"],
        tags=["morphology", "verb", "byzantine", "aorist"],
    )
]

_CAVAFY_LESSON_PROSE = [
    (
        "## Who was Cavafy\n\n"
        "Constantine P. Cavafy was born in **Alexandria in 1863** and died there in "
        "**1933**. He left about **154 poems**, in which he often turns to history "
        "and mythology to speak about modern man. «Ithaka» is perhaps his most "
        "famous poem worldwide."
    ),
    (
        "«Ithaka» speaks to Homer's Odyssey: Odysseus's journey home — a "
        "[νόστος](../words/νόστος.md) — becomes, in Cavafy, an image of every "
        "person's journey through life."
    ),
    (
        "## Who they were\n\n"
        "**The Laestrygonians** — man-eating giants who destroyed the ships of "
        "strangers and killed their crews; a symbol of great dangers and "
        "destruction.\n\n"
        "**The Cyclopes** — giants with a single eye on the forehead, possessing "
        "enormous strength and living in isolation; a symbol of violence, brute "
        "force, and the absence of civilization.\n\n"
        "**Poseidon** — the god of the sea, Odysseus's enemy (since Odysseus "
        "blinded his son Polyphemus); a symbol of the forces we cannot control — "
        "nature, fate, circumstance.\n\n"
        "For Cavafy, these figures are not just mythological characters — they "
        "carry a deeper, symbolic meaning."
    ),
    (
        "## Metaphorical meaning\n\n"
        "These figures can symbolize: our fears, anxiety, insecurity, "
        "difficulties, problems, people who disappoint us, obstacles we create "
        "for ourselves. The poem's language — the verbs of coming and arriving "
        "discussed in [the -οσαν aorist grammatical rule](../grammar/aorist-3pl-osan.md) "
        "among them — is the same vocabulary of travel and homecoming that runs "
        "through the Odyssey itself."
    ),
]

CULTURAL_TOPICS: list[CulturalTopicSpec] = [
    CulturalTopicSpec(
        topic_id="cavafy",
        lesson_prose=_CAVAFY_LESSON_PROSE,
        wiki_title="Constantine P. Cavafy",
        level=["B1"],
        tags=["poetry", "cavafy", "ithaka", "modern-greek-literature"],
        related_words=["νόστος"],
        related_lessons=["kavafis_ithaki/1", "kavafis_ithaki/2"],
    )
]

# Per section-07-pilot.md's post-section-01 amendment: νόστος is this
# pilot's headline word and should exercise the beekes_citation mechanism
# section-04 added. lexical_entry.build() has no separate parameter for a
# page locator — the citation embeds its own, as scholarly prose would.
# Own paraphrase of the etymology (not a verbatim quote from Beekes'
# copyrighted text), cross-checked against Wiktionary's own citation of the
# same page before writing this summary.
NOSTOS_BEEKES_CITATION = (
    "νόστος is an o-grade derivative of the PIE root *nes- (\"to return home\") "
    "plus the suffix -τος, from the same root as the verb νέομαι (\"to go/come "
    "back\") (Beekes 2010, p. 1024)"
)


def enrich_nostos_with_beekes(repo_root: Path, sources: SourceBundle) -> bool:
    """Rebuild words/νόστος.md with an Etymology section and write it back
    via okf.write() (verification-preserving, same as every other write in
    this pipeline). pipeline.py's own auto-extraction loop has no plumbing
    for a per-lemma curated citation (grep-confirmed: GrammarRuleSpec/
    CulturalTopicSpec both carry curated content, but lexical_entry
    candidates only ever come from _collect_lexical_candidates's TSV scan)
    — adding that plumbing to already-reviewed section-05 code for one
    word's one optional field isn't proportionate, so this rebuilds the
    same entry directly instead, the same way the Grammar Rule and
    Cultural Context entries are already built outside the generic loop.
    pos/level/tags match the real vocab_I_1-21.tsv row for νόστος exactly
    (pos=noun; the Odyssey vocab TSV schema has no level/tags columns).
    Returns okf.write()'s own bool (True if the file changed)."""
    concept = lexical_entry.build(
        "νόστος",
        "noun",
        _ALL_PERIODS,
        sources,
        level=[],
        tags=[],
        beekes_citation=NOSTOS_BEEKES_CITATION,
    )
    return okf.write(concept, repo_root / "words" / "νόστος.md")
