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

_ATHENAZE_CH1 = Source(
    id="athenaze-ch1",
    resource="lectures/Palaestra/ancient_greek.2026.summer/athenaze-vol1-chpt1-corrected-v2.md",
    title="Athenaze: Introduzione al greco antico, Vol. I, Ch. 1",
    author="M. Balme, G. Lawall, L. Miraglia, T. F. Bórri",
)
_ATHENAZE_CH1_EXT = Source(
    id="athenaze-ch1-ext",
    resource="lectures/Palaestra/ancient_greek.2026.summer/1. Athenaze. Vol. 1. Chpt. 1.md",
    title="Athenaze: Introduzione al greco antico, Vol. I, Ch. 1 (extended transcription)",
    author="M. Balme, G. Lawall, L. Miraglia, T. F. Bórri",
)
_ATHENAZE_CH2 = Source(
    id="athenaze-ch2",
    resource="lectures/Palaestra/ancient_greek.2026.summer/athenaze-vol1-chpt2.md",
    title="Athenaze: Introduzione al greco antico, Vol. I, Ch. 2",
    author="M. Balme, G. Lawall, L. Miraglia, T. F. Bórri",
)
_ATHENAZE_CH2_EXT = Source(
    id="athenaze-ch2-ext",
    resource="lectures/Palaestra/ancient_greek.2026.summer/1. Athenaze. Vol. 1. Chpt. 2.md",
    title="Athenaze: Introduzione al greco antico, Vol. I, Ch. 2 (extended transcription)",
    author="M. Balme, G. Lawall, L. Miraglia, T. F. Bórri",
)
_CONSPECTUS_I = Source(
    id="conspectus-i",
    resource="lectures/ancient_greek/CONSPECTVS GRAMMATICVS I_graecus.pdf",
    title="CONSPECTVS GRAMMATICVS I",
    author="Palaestra (Sodalitas Litterarum)",
)
_CONSPECTUS_II = Source(
    id="conspectus-ii",
    resource="lectures/Palaestra/ancient_greek.2026.summer/CONSPECTVS GRAMMATICVS II_graecus.pdf",
    title="CONSPECTVS GRAMMATICVS II",
    author="Palaestra (Sodalitas Litterarum)",
)
_CONSPECTUS_III = Source(
    id="conspectus-iii",
    resource="lectures/ancient_greek/CONSPECTVS GRAMMATICVS III_graecus.pdf",
    title="CONSPECTVS GRAMMATICVS III",
    author="Palaestra (Sodalitas Litterarum)",
)
_ATTICIST_KOINE = Source(
    id="atticist-koine-tenses",
    resource="https://t.me/atticist",
    title="Verb tenses in Hellenistic Koine and Modern Greek",
    author="ΑΤΤΙΚΙΣΤΑ (t.me/atticist)",
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

GRAMMAR_RULES.append(
    GrammarRuleSpec(
        rule_id="second-declension-masc-neut",
        body="""\
## The 2nd declension (ὁ ἄνθρωπος / τὸ δένδρον-type nouns)

Greek's 2nd declension covers masculine nouns in **-ος** and neuter nouns \
in **-ον**, sharing one set of endings across five cases: nominative \
**-ος/-ον**, genitive **-ου/-ου**, dative **-ῳ/-ῳ**, accusative \
**-ον/-ον**, vocative **-ε/-ον**.[^conspectus-i] Because the neuter's \
nominative, vocative, and accusative endings are all identical, subject \
and direct object can only be told apart by context or word order — \
τὸ δένδρον is "the tree" in any of those three roles.[^athenaze-ch2]

Where the accent falls is lexical, not predictable purely from the \
ending: **προπαροξύτονα** like ἄνθρωπος keep the accent as far from the \
end as the general accent rules allow, while **ὀξύτονα** like γεωργός \
keep it on the final syllable throughout every case and number.[^conspectus-i]

Athenaze's own first examples keep to the nominative and accusative \
singular — **ὁ κλῆρος** (subject) and **τὸν κλῆρον** (direct object) — \
with gender marked by the article rather than guessable from the noun's \
own ending alone.[^athenaze-ch1]

A handful of vocative peculiarities are worth noting early: θεός has no \
singular vocative in classical authors at all (the New Testament's \
ὦ θεέ is a later development); ἀδελφός more often takes ὦ ἄδελφε than \
the "regular" ὦ ἀδελφέ; and the vocative is sometimes replaced by the \
nominative outright, ὦ φίλος alongside ὦ φίλε.[^conspectus-i]""",
        sources=[_CONSPECTUS_I, _ATHENAZE_CH1, _ATHENAZE_CH2],
        period_from="attic",
        period_to="attic",
        level=["beginner"],
        tags=["morphology", "noun", "declension", "2nd-declension"],
        dialect=["attic"],
    )
)

GRAMMAR_RULES.append(
    GrammarRuleSpec(
        rule_id="third-singular-present-indicative",
        body="""\
## Third person singular, present indicative

The present indicative's third-person-singular ending is **-ει**, added \
directly to an unchanging stem: **λύ-ει** "he/she looses," from the stem \
**λυ-**.[^conspectus-i] A verb whose stem ends in a vowel (**verba \
contracta**, contract verbs) fuses that vowel with the ending instead of \
leaving it bare: a stem in **-ε** fuses **ε+ει → ει**, so **φιλέ-ει** \
becomes **φιλεῖ** "he/she loves" — the same rule Athenaze's own reading \
illustrates directly: **οἰκεῖ**, **γεωργεῖ**, and **πονεῖ** all share \
this contracted **-εῖ** ending.[^athenaze-ch1] εἰμί "to be" is irregular \
and athematic: its 3rd-singular present is **ἐστί(ν)**, from the bare \
stem **ἐσ-** plus **-τί(ν)**.[^conspectus-i]

εἰμί's own paradigm preserves its prehistory: **εἰμί** itself goes back \
to *ἐσ-μί, **εἶ** "(you) are" to *ἐσ-σί, and the plural **εἰσί(ν)** \
"(they) are" to *σ-ενσί.[^conspectus-i]""",
        sources=[_CONSPECTUS_I, _ATHENAZE_CH1],
        period_from="attic",
        period_to="attic",
        level=["beginner"],
        tags=["morphology", "verb", "present", "conjugation"],
        dialect=["attic"],
    )
)

GRAMMAR_RULES.append(
    GrammarRuleSpec(
        rule_id="movable-nu-and-enclitics",
        body="""\
## Movable ν and enclitics

**ἐστίν** replaces **ἐστί** in two situations: before a pause (marked in \
writing by any punctuation) and before a word beginning with a vowel. \
This appended **-ν** is called the movable ν (**ν ἐφελκυστικόν**) and \
shows up under the same conditions on other words too — most commonly \
the 3rd-plural ending **-ουσι(ν)**.[^athenaze-ch1] Athenaze's own text \
supplies all three conditions directly: **Αὐτουργὸς γάρ ἐστιν.** keeps \
-ν before a full stop, **Ὁ κλῆρος μικρός ἐστιν, καί...** keeps it \
before a following vowel, while **Χαλεπὸς δέ ἐστιν ὁ βίος.** drops it \
before a consonant.[^athenaze-ch1]

**ἐστί(ν)** is also an **enclitic**: it carries no accent of its own \
and leans on the preceding word for its accentuation, which is why it \
appears unaccented in ordinary running text — true of every disyllabic \
present form of εἰμί except **εἶ** "(you) are," which keeps its own \
accent.[^conspectus-i][^athenaze-ch2]""",
        sources=[_ATHENAZE_CH1, _CONSPECTUS_I, _ATHENAZE_CH2],
        period_from="attic",
        period_to="attic",
        level=["beginner"],
        tags=["morphology", "verb", "accentuation", "enclitic"],
        dialect=["attic"],
    )
)

GRAMMAR_RULES.append(
    GrammarRuleSpec(
        rule_id="present-imperative-active",
        body="""\
## Present imperative active

The present active imperative follows the same three-way split as the \
indicative. Pure verbs add **-ε** (2sg): **λῦ-ε** "loose!," \
**σπεῦδ-ε** "hurry!," **λάμβαν-ε** "take!" — all three drawn straight \
from Athenaze's own Chapter 2 reading.[^athenaze-ch2] Contract verbs in \
**-έω** fuse exactly as in the indicative: **φίλε-ε → φίλει** "love!," \
**πόνε-ε → πόνει** "work!," **ἀκολούθε-ε → ἀκολούθει** \
"follow!".[^athenaze-ch2][^conspectus-ii] εἰμί's imperative is \
suppletive rather than built on ἐσ-: **ἴσθι** "be! (sg.)," **ἔστε** \
"be! (pl.)," **ἔστω** "let him/her/it be," **ἔστων** "let them \
be".[^conspectus-ii]

Compound verbs built on εἰμί keep the same suppletive imperative but \
move the accent onto the prefix instead: **πάρειμι** "to be present" \
gives **πάρισθι** "be present!," **πάρεστε**, **παρέστω**, **παρέστων**. \
Besides πάρειμι, the commonest such compounds are ἄπειμι "to be \
absent," ἔνειμι "to be contained in," ἔπειμι "to be in charge of," \
μέτειμι "to have a share in," and σύνειμι "to be together with" — none \
of which Athenaze's own Chapter 2 vocabulary lists.[^conspectus-ii]

Negative commands use **μή**, not οὐ: **Μὴ λάμβανε τὸ ἄροτρον** "don't \
take the plow!," **Μὴ ἀργὸς ἴσθι** "don't be lazy!," **Μὴ καθεῦδε** \
"don't sleep!".[^athenaze-ch2]""",
        sources=[_ATHENAZE_CH2, _CONSPECTUS_II],
        period_from="attic",
        period_to="attic",
        level=["beginner"],
        tags=["morphology", "verb", "imperative", "mood"],
        dialect=["attic"],
    )
)

GRAMMAR_RULES.append(
    GrammarRuleSpec(
        rule_id="verb-accentuation-final-trochee",
        body="""\
## Verb accentuation: regressive accent and the law of the final trochee

Greek verb accent is **regressive**: it recedes as far toward the start \
of the word as the length of the final syllable allows. The indicative \
**ἐκβαίνω**, **ἐκβαίνεις**, **ἐκβαίνει** keeps its acute accent on the \
penult because the final syllable is long, but the imperative \
**ἔκβαινε** moves the same accent one syllable further back — to the \
antepenult — because its final **-ε** is short. The same pattern \
governs **λάμβανε**, **ἔλαυνε**, **κάθευδε**.[^athenaze-ch2]

A further rule fixes the accent's *shape*, not just its position: when \
the accent falls on the penult, that syllable is long, and the final \
syllable is short, the accent must be **circumflex**, never acute — the \
"law of the final trochee." This is why **λῦε** (from λύω) and \
**σπεῦδε** carry a circumflex rather than an acute on their first \
syllable.[^athenaze-ch2]""",
        sources=[_ATHENAZE_CH2, _ATHENAZE_CH2_EXT],
        period_from="attic",
        period_to="attic",
        level=["beginner"],
        tags=["morphology", "verb", "accentuation"],
        dialect=["attic"],
    )
)

GRAMMAR_RULES.append(
    GrammarRuleSpec(
        rule_id="adjective-declension-and-suppletion",
        body="""\
## Adjective declension: 3-termination, 2-termination, and μέγας/πολύς

1st/2nd-declension adjectives come in two shapes. **Three-termination** \
adjectives give masculine and neuter the same -ος/-ον endings as 2nd- \
declension nouns and a separate 1st-declension feminine: **δίκαιος, \
δικαία, δίκαιον** "just" (feminine in **-α**, after a vowel or ρ) and \
**καλός, καλή, καλόν** "beautiful" (feminine in **-η** \
elsewhere).[^conspectus-iii] **Two-termination** adjectives share a \
single **-ος** form across masculine and feminine, with only the \
neuter taking its own **-ον**: **ἄδικος, ἄδικον** "unjust".[^conspectus-iii]

**μέγας** "big" (μέγας, μεγάλη, μέγα) and **πολύς** "much/many" (πολύς, \
πολλή, πολύ) are irregular by **suppletion** — they build their forms \
from two different stems rather than one. The feminine (μεγάλη/πολλή) \
and every masculine/neuter case except the nominative and accusative \
singular (μεγάλου, μεγάλῳ... / πολλοῦ, πολλῷ...) use the longer stem \
μεγαλο-/πολλο-, following the ordinary 1st/2nd-declension pattern; only \
the masculine and neuter nominative/accusative singular (**μέγας, \
μέγα** / **πολύς, πολύ**) keep the short stem μεγα-/πολυ-, inflecting \
instead like a 3rd-declension noun.[^conspectus-iii] Athenaze's own \
Chapter 1 vocabulary already flags this irregularity without explaining \
it — listing μέγας with its accusative μέγαν, and πολύς with its \
accusative πολύν — right alongside its ordinary 2nd-declension \
adjectives like καλός.[^athenaze-ch1]

Articles and adjectives agree with the noun they modify in gender, \
number, and case: **ὁ καλὸς ἀγρός** (masculine singular nominative), \
**τὸν μικρὸν οἶκον** (masculine singular accusative) — the same rule \
that governs the predicate adjective after "to be," as in **Ὁ κλῆρός \
ἐστι μικρός**.[^athenaze-ch1]""",
        sources=[_CONSPECTUS_III, _ATHENAZE_CH1],
        period_from="attic",
        period_to="attic",
        level=["beginner"],
        tags=["morphology", "adjective", "declension", "suppletion"],
        dialect=["attic"],
    )
)

GRAMMAR_RULES.append(
    GrammarRuleSpec(
        rule_id="word-order-and-agreement",
        body="""\
## Case-determined meaning and the stylistic role of word order

Unlike many modern languages, Greek's core sentence meaning comes from \
case endings, not word order: **ὁ κλῆρός ἐστι μικρός** and **μικρός \
ἐστιν ὁ κλῆρος** mean exactly the same thing ("the plot is small"). \
Likewise **ὁ ἄνθρωπος γεωργεῖ τὸν κλῆρον** and **τὸν κλῆρον γεωργεῖ ὁ \
ἄνθρωπος** both mean "the man farms the plot" — the endings **-ος** \
(subject) and **-ον** (direct object) fix each word's role regardless \
of where it sits in the sentence.[^athenaze-ch1]

Word order still does real work, though — a stylistic and logical one. \
The word a speaker wants to emphasize is usually moved to the front of \
the sentence: putting the direct object first, as in **τὸν κλῆρον \
γεωργεῖ ὁ ἄνθρωπος**, throws emphasis onto *the plot* specifically — \
"it's the *plot* (and not something else) that the man \
farms".[^athenaze-ch1]""",
        sources=[_ATHENAZE_CH1],
        period_from="attic",
        period_to="attic",
        level=["beginner"],
        tags=["syntax", "word-order", "case"],
        dialect=["attic"],
    )
)

GRAMMAR_RULES.append(
    GrammarRuleSpec(
        rule_id="preverb-word-formation",
        body="""\
## Word formation: prepositions as preverbs

The four prepositions introduced by Chapter 2 — **εἰς** "into" (motion \
toward), **ἐκ** "out of" (motion away), **ἐν** "in" (location), and \
**πρός** "toward" (motion toward) — are often prefixed directly onto a \
verb, where they're called **preverbs**. A preverb keeps its ordinary \
meaning in the compound: **βαίνει** "goes, walks" becomes **ἐκβαίνει** \
"goes out, exits".[^athenaze-ch2-ext]

Because this pattern is so productive, later chapters' vocabulary lists \
stop separately glossing a compound verb whenever its meaning follows \
predictably from preverb + simple verb — a learner is expected to work \
it out, the same way one can already work out **προσφέρει**, \
**ἐκφέρει**, **προσελαύνει**, **προσβαίνει**, and **ἐκκαλεῖ** from \
**φέρει**, **ἐλαύνει**, **βαίνει**, and **καλεῖ**.[^athenaze-ch2-ext]""",
        sources=[_ATHENAZE_CH2_EXT],
        period_from="attic",
        period_to="attic",
        level=["beginner"],
        tags=["word-formation", "preposition", "preverb"],
        dialect=["attic"],
    )
)

GRAMMAR_RULES.append(
    GrammarRuleSpec(
        rule_id="future-tha-periphrasis",
        body="""\
## Future tense: from κοινή's synthetic future to Modern Greek's θα

Hellenistic κοινή built its future synthetically, by adding **-σω** \
directly to the verb stem: **λύσω, λύσεις, λύσει...** "I will loose, \
you will loose...".[^atticist-koine-tenses] Modern Greek replaces this \
with a periphrasis: the particle **θα** plus a conjugated verb form — \
**θα λύσω, λύσεις, λύσει...**.[^atticist-koine-tenses] **θα** itself \
descends through a chain of contractions from the phrase **θέλω ἵνα** \
"I want that," via **θέλω να**, **θε να**, to **θα**.[^atticist-koine-tenses]

The form that follows θα carries a real aspectual distinction κοινή's \
one-tense future lacked: **θα λύνω** ("I will be loosing," an ongoing \
or habitual future) against **θα λύσω** ("I will loose," a single \
bounded event) — using the present stem for the first and the aorist \
stem for the second.[^atticist-koine-tenses]""",
        sources=[_ATTICIST_KOINE],
        period_from="koine",
        period_to="modern",
        level=["beginner"],
        tags=["morphology", "verb", "future", "tha", "modern-greek"],
    )
)

GRAMMAR_RULES.append(
    GrammarRuleSpec(
        rule_id="perfect-pluperfect-periphrasis",
        body="""\
## Perfect and pluperfect: from synthetic forms to έχω-periphrasis

κοινή's active perfect and pluperfect are synthetic, built with \
reduplication and their own personal endings: perfect **λέλυκα, \
λέλυκας, λέλυκε(ν)...** "I have loosed...," pluperfect **ἐλελύκειν, \
ἐλελύκεις, ἐλελύκει...** "I had loosed...".[^atticist-koine-tenses] \
Modern Greek replaces both with periphrasis instead: the active perfect \
becomes **έχω λύσει** (or **έχω λυμένο**) — "I have loosed" — built \
from **έχω** "I have" plus the invariant aorist infinitive λύσει (or, \
alternatively, the accusative of the perfect medio-passive participle \
λυμένος, -η, -ο). The pluperfect follows the same pattern with **είχα** \
"I had" in place of **έχω**: **είχα λύσει** / **είχα \
λυμένο**.[^atticist-koine-tenses] The medio-passive perfect/pluperfect \
mirror this exactly, substituting **είμαι**/**ήμουν** ("I am"/"I was") \
for **έχω**/**είχα** where the participle option is used, since the \
medio-passive participle needs the nominative rather than the \
accusative: **έχω λυθεί** or **είμαι λυμένος**.[^atticist-koine-tenses]""",
        sources=[_ATTICIST_KOINE],
        period_from="koine",
        period_to="modern",
        level=["beginner"],
        tags=["morphology", "verb", "perfect", "pluperfect", "modern-greek"],
    )
)

GRAMMAR_RULES.append(
    GrammarRuleSpec(
        rule_id="optative-replacement",
        body="""\
## The optative's decline and its Modern Greek replacements

By the time the New Testament was written, the optative mood \
(**Εὐκτική**) was already falling out of use in κοινή, its functions \
increasingly absorbed by the subjunctive.[^atticist-koine-tenses] \
Modern Greek has no synthetic optative at all — the wish-meaning it \
once carried is now expressed periphrastically, and in fact quite \
widely, across several equivalent constructions: the inherited particle \
**εἴθε** plus **να** (from ἵνα), the phrase **μακάρι** (from ancient \
**μάκαρ** "blessed, happy") plus **να**, **ας ήταν να**, **αχ (και) \
να**, plain **ας**, or the verb **εύχομαι** "I wish" followed by a verb \
in the indicative or subjunctive — all expressing roughly "oh, if \
only...", "would that...".[^atticist-koine-tenses]""",
        sources=[_ATTICIST_KOINE],
        period_from="koine",
        period_to="modern",
        level=["beginner"],
        tags=["morphology", "verb", "mood", "optative", "modern-greek"],
    )
)

GRAMMAR_RULES.append(
    GrammarRuleSpec(
        rule_id="mediopassive-merger",
        body="""\
## Voice: κοινή's middle vs. Modern Greek's single mediopassive

κοινή keeps the middle and passive voices formally distinct outside the \
future and aorist (where they've already diverged, e.g. future passive \
**λυθήσομαι** vs. future middle **λύσομαι**) — but in the present, \
imperfect, perfect, and pluperfect, middle and passive already share \
one identical paradigm, e.g. present **λύομαι, λύῃ, λύεται...**, doing \
double duty for both voices even at this stage.[^atticist-koine-tenses] \
Modern Greek completes this merger: it uses one single mediopassive \
paradigm throughout — **λύνομαι, λύνεσαι, λύνεται...** — and which \
sense (middle or passive) a given verb carries is determined lexically \
and by context, not by any surviving formal distinction.[^atticist-koine-tenses]""",
        sources=[_ATTICIST_KOINE],
        period_from="koine",
        period_to="modern",
        level=["beginner"],
        tags=["morphology", "verb", "voice", "mediopassive", "modern-greek"],
    )
)

GRAMMAR_RULES.append(
    GrammarRuleSpec(
        rule_id="augment-loss",
        body="""\
## Unstressed augment loss in Modern Greek

κοινή's past tenses (imperfect, aorist, pluperfect) mark past time with \
a prefixed **augment**, normally **ἐ-**, added whenever the stem's own \
first vowel wouldn't otherwise be accented: κοινή imperfect **ἔλυον**, \
aorist **ἔλυσα**.[^atticist-koine-tenses] Modern Greek keeps this \
augment only when it would carry the word's stress; an unstressed \
augment is simply dropped. So κοινή's **ἔλυον** ("I was loosing") \
survives into Modern Greek as **έλυνα**, its augment retained because \
the stress still falls there, while a form whose stress moves \
elsewhere in the paradigm drops the augment \
entirely.[^atticist-koine-tenses]""",
        sources=[_ATTICIST_KOINE],
        period_from="koine",
        period_to="modern",
        level=["beginner"],
        tags=["morphology", "verb", "augment", "accentuation", "modern-greek"],
    )
)

GRAMMAR_RULES.append(
    GrammarRuleSpec(
        rule_id="reduplicated-participles-as-adjectives",
        body="""\
## Reduplicated perfect participles surviving as ordinary adjectives

κοινή's perfect medio-passive participle (**λελυμένος, -η, -ον**) \
carries the perfect's characteristic reduplication — repeating the \
stem's first consonant with **ε**, e.g. **λε-λυ-μένος**. Modern Greek \
lost the reduplication in its ordinary perfect periphrasis (using bare \
**λυμένος** instead), but a substantial set of individual \
reduplicated participles survive whole, fossilized as ordinary \
adjectives with independent, often non-literal meanings: \
**πεπεισμένος** "convinced," **πεπαιδευμένος** "educated," \
**πεφωτισμένος** "enlightened," **πεπρωμένος** "destined, fated," and \
**κεχαριτωμένος** "full of grace" among roughly forty such \
survivals.[^atticist-koine-tenses]""",
        sources=[_ATTICIST_KOINE],
        period_from="koine",
        period_to="modern",
        level=["beginner"],
        tags=["morphology", "participle", "perfect", "word-formation", "modern-greek"],
    )
)

GRAMMAR_RULES.append(
    GrammarRuleSpec(
        rule_id="future-continuous-new-tense",
        body="""\
## Future continuous: a tense with no κοινή ancestor

κοινή has one synthetic future (**λύσω**). Task 19's rule already \
covers how Modern Greek's θα-periphrasis reintroduces an aspect \
distinction κοινή's future itself lacked — but Modern Greek names and \
uses this distinction as two fully separate tenses in its own right, \
not just an incidental side effect of the periphrasis: **future \
continuous** (**μέλλοντας εξακολουθητικός**, θα + present stem: **θα \
λύνω**) against **future simple/instantaneous** (**μέλλοντας \
στιγμιαίος**, θα + aorist stem: **θα λύσω**). Grammars name and drill \
these as two distinct tenses specifically so learners keep the \
ongoing-vs-single-event contrast straight — a contrast with no \
dedicated tense-name at all in κοινή's own one-future \
system.[^atticist-koine-tenses] The same continuous/simple split \
recurs in the future's mediopassive and perfect forms.[^atticist-koine-tenses]""",
        sources=[_ATTICIST_KOINE],
        period_from="koine",
        period_to="modern",
        level=["beginner"],
        tags=["morphology", "verb", "future", "aspect", "modern-greek"],
    )
)

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
