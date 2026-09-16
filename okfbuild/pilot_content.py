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
_THUCYDIDES_2_14 = Source(
    id="thucydides-2-14",
    resource="Thucydides, History of the Peloponnesian War, II.14",
    title="History of the Peloponnesian War",
    author="Thucydides",
)
_PSEUDO_XENOPHON_ATH_POL = Source(
    id="pseudo-xenophon-ath-pol-1-10",
    resource="Pseudo-Xenophon, Constitution of the Athenians, I.10",
    title="Constitution of the Athenians",
    author="Pseudo-Xenophon",
)
_EBOOKS_EDU_GR_ITHAKA = Source(
    id="ebooks-edu-gr-ithaka",
    resource="https://ebooks.edu.gr/ebooks/v/html/8547/2700/Keimena-Neoellinikis-Logotechnias_A-Lykeiou_html-empl/indexG3_2.html",
    title="Κείμενα Νεοελληνικής Λογοτεχνίας Α΄ Λυκείου (official Greek Ministry of Education literature textbook)",
    author="Greek Institute of Educational Policy (ΙΕΠ)",
)

_OSAN_BODY = """\
## The -οσαν aorist/imperfect 3rd plural

The classical 3rd-plural imperfect/2nd-aorist active ending **-ον** has \
an analogical variant, **-οσαν** — grammarians traditionally call it \
"Boeotic, Chalcidean, or Asiatic."[^sophocles-1887] It is attested from \
the Hellenistic period onward, not as an exclusively Byzantine \
innovation, though it became the norm only in Byzantine and later \
Greek. The new ending also resolves a real syncretism: classically, a \
2nd-aorist verb's 3rd-plural form is identical to its 1st-singular \
(ἦλθον = "I came" *or* "they came"; εἶδον = "I saw" *or* "they saw") — \
which may have helped -οσαν spread, giving the 3rd plural a distinct \
form of its own.

Both of the verbs cited below are common Homeric verbs of coming/going \
and seeing, already attested (in their classical 3rd-singular aorist \
forms, ἦλθε/ἴδεν) in the same Odyssey passage this knowledge base draws \
its Lexical Entry examples from. Both belong to a suppletive aorist \
stem, not a replacement of the present-tense lemma itself.

ὁράω's later 3rd-plural aorist ἴδοσαν occurs alongside classical \
ἴδον[^sophocles-1887]

ὁράω's later 3rd-plural aorist εἴδοσαν occurs alongside classical \
εἶδον[^sophocles-1887]

ἔρχομαι's later 3rd-plural aorist ἤλθοσαν occurs alongside classical \
ἦλθον[^sophocles-1887]"""

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
the 3rd-plural ending **-ουσι(ν)**.[^athenaze-ch1]

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

κοινή has one synthetic future (**λύσω**). [The θα-periphrasis \
rule](future-tha-periphrasis.md) already covers how Modern \
Greek's θα-periphrasis reintroduces an aspect distinction κοινή's \
future itself lacked — but Modern Greek names and \
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
        "and mythology to speak about modern man. «Ithaka» -- first published in "
        "the journal *Γράμματα* (Grammata), October-November 1911, when Cavafy was "
        "48 -- is perhaps his most famous poem worldwide.[^ebooks-edu-gr-ithaka]"
    ),
    (
        "«Ithaka» speaks to Homer's Odyssey: Odysseus's journey home is a "
        "[νόστος](../words/νόστος.md) in the epic's own terms, though the "
        "word itself doesn't appear in Cavafy's poem — Cavafy transforms "
        "that homecoming into an image of every person's journey through "
        "life."
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
        "for ourselves. The poem's own vocabulary of travel and arrival — "
        "βγεις, φτάσεις, ταξίδι, δρόμος — covers the same thematic ground as "
        "the Odyssey itself, journey and homecoming, even though Cavafy "
        "writes in Modern Greek, not Homer's own language."
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
        extra_sources=[_EBOOKS_EDU_GR_ITHAKA],
    )
]

CULTURAL_TOPICS.append(
    CulturalTopicSpec(
        topic_id="peloponnesian-war-setting",
        lesson_prose=[
            (
                "## The historical setting of Athenaze's narrative\n\n"
                "Athenaze's fictional story of Dikaiopolis and his family is set "
                "against a precise historical backdrop: from autumn 433 to spring "
                "431 BC, at the height of Athenian democracy under "
                "**Pericles**. Athens dominates the sea and holds a large empire, "
                "but its power provokes fear and envy in Sparta and its "
                "Peloponnesian League allies — above all Corinth. By spring 431, "
                "Athens and the Peloponnesian League are already at war — a war "
                "that will end, twenty-seven years later, in Athens's defeat."
                "[^athenaze-ch1]"
            ),
            (
                "The story's main plot resolves by Chapters 18-20; the second "
                "book's opening draws the family into the Athens-Corinth "
                "conflict that actually triggered the Peloponnesian War, and "
                "Chapters 21-23 (set at the war's outbreak) are based directly "
                "on Thucydides's own history of the conflict.[^athenaze-ch1]"
            ),
        ],
        wiki_title=None,
        level=["beginner"],
        tags=["history", "peloponnesian-war", "athens", "pericles"],
        related_words=[],
        related_lessons=["ancient_greek/palaestra/athenaze-vol1/chapter-1", "ancient_greek/palaestra/athenaze-vol1/chapter-2"],
        extra_sources=[_ATHENAZE_CH1],
        periods_spanned={"from": "attic", "to": "attic"},
        dialect=["attic"],
    )
)

CULTURAL_TOPICS.append(
    CulturalTopicSpec(
        topic_id="greek-dialect-history",
        lesson_prose=[
            (
                "## From Indo-European to Koine\n\n"
                "Greek, like Latin and Sanskrit, belongs to the Indo-European "
                "language family. Prehistoric Greek arrived in the Balkan "
                "peninsula in waves — Achaean speakers in the early 2nd "
                "millennium BC (whose fusion with the pre-existing Minoan "
                "civilization on Crete produced the Mycenaean civilization "
                "Homer would later celebrate in the *Iliad*), and Dorian "
                "speakers around 1100 BC.[^athenaze-ch1]"
            ),
            (
                "Contact with earlier local languages and later historical "
                "events split what was originally a fairly uniform prehistoric "
                "Greek into several dialects — Ionic, Attic, Aeolic, Doric, "
                "among others. These literary dialects are often quite "
                "artificial, removed from actual everyday speech: Homer's own "
                "poems, for instance, are written in a mixed language, "
                "fundamentally Ionic but heavily laced with Aeolic elements."
                "[^athenaze-ch1]"
            ),
            (
                "The Attic dialect of Periclean-era Athens (5th c. BC) earned "
                "its later prestige — studied today simply as \"Ancient "
                "Greek\" — from the literary achievements of its great prose "
                "writers: Plato, Thucydides, Xenophon. After Alexander the "
                "Great's conquests (he died 323 BC), a common Greek — **ἡ "
                "κοινὴ διάλεκτος**, koine — spread across the Mediterranean as "
                "a language of trade and culture: based on Attic, but shorn "
                "of its most narrowly local features. Byzantine and Modern "
                "Greek both developed, in essence, out of this koine — though "
                "a purist literary movement, Atticism, kept returning to the "
                "cleaner 5th-century Attic for centuries afterward."
                "[^athenaze-ch1]"
            ),
        ],
        wiki_title=None,
        level=["beginner"],
        tags=["history", "linguistics", "dialect", "koine"],
        related_words=[],
        related_lessons=["ancient_greek/palaestra/athenaze-vol1/chapter-1"],
        extra_sources=[_ATHENAZE_CH1],
        periods_spanned={"from": "homeric", "to": "koine"},
    )
)

CULTURAL_TOPICS.append(
    CulturalTopicSpec(
        topic_id="bronze-age-to-peloponnesian-war-chronology",
        lesson_prose=[
            (
                "## A chronology of early Greek history\n\n"
                "**Bronze Age:** Minos, king of Crete; Theseus, king of "
                "Athens. Around 1220 BC, Agamemnon of Mycenae takes Troy. A "
                "so-called \"Dark Age\" follows, including the Ionian "
                "migration to Asia Minor around 1050 BC.[^athenaze-ch1-ext]"
            ),
            (
                "**Greek renaissance:** city-states (Sparta, Corinth, etc.) "
                "form around 850 BC. The first Olympic Games are held in 776 "
                "BC. Trade and colonial expansion follow, c. 750-500 BC. "
                "Homer composes the *Iliad* and *Odyssey* around 725 BC "
                "(Ionia); Hesiod composes *Works and Days* around 700 BC "
                "(Boeotia). Cypselus tyrannizes Corinth c. 657-625 BC; Solon "
                "reforms Athens soon after.[^athenaze-ch1-ext]"
            ),
            (
                "**Persian invasions:** in 546 BC Croesus, king of Lydia, and "
                "the Greeks of Asia Minor are defeated by Cyrus of Persia. In "
                "507 BC Cleisthenes lays the foundations of Athenian "
                "democracy. Darius's expedition against Athens and the Battle "
                "of Marathon follow in 490 BC; Xerxes invades Greece in 480 "
                "BC (Thermopylae and Salamis, both 480 BC; Plataea, 479 BC)."
                "[^athenaze-ch1-ext]"
            ),
            (
                "**The Athenian empire:** the Delian League, founded 478 BC, "
                "grows into the Athenian empire. Aeschylus's *Persians* is "
                "staged in 472 BC. Pericles dominates Athens 461-429 BC — "
                "radical democracy and imperial expansion, and, from 446 BC, "
                "a Thirty Years' Peace with Sparta. Herodotus writes his "
                "*Histories* in this period.[^athenaze-ch1-ext]"
            ),
            (
                "**The Peloponnesian War:** war between Athens and the "
                "Peloponnesian League breaks out in 431 BC. Plague strikes "
                "Athens and Pericles dies, 430-429 BC. Aristophanes stages "
                "*Acharnians* in 425 BC. A fragile peace holds in 421 BC; the "
                "Sicilian expedition (415 BC) fails disastrously by 413 BC, "
                "reigniting the war outright, which ends with Athens's "
                "surrender in 404 BC. Thucydides writes his *History of the "
                "Peloponnesian War* covering these events.[^athenaze-ch1-ext]"
            ),
        ],
        wiki_title=None,
        level=["beginner"],
        tags=["history", "chronology", "timeline"],
        related_words=[],
        related_lessons=["ancient_greek/palaestra/athenaze-vol1/chapter-1"],
        extra_sources=[_ATHENAZE_CH1_EXT],
        periods_spanned={"from": "homeric", "to": "attic"},
    )
)

CULTURAL_TOPICS.append(
    CulturalTopicSpec(
        topic_id="athenian-farmer-class-system",
        lesson_prose=[
            (
                "## Farmers, the backbone of Athenian democracy\n\n"
                "Dikaiopolis lives in the Attic deme of Cholleidai, about "
                "twenty kilometers southeast of Athens. Though Athens and "
                "its port, Piraeus, formed a substantial urban center by "
                "ancient standards, most Athenians actually lived and worked "
                "in the countryside. Thucydides records that when Spartan "
                "invasion forced rural residents into the city in 431 BC, "
                "\"this removal was a hard thing for them to bear, most of "
                "them having always been used to a country life.\"[^thucydides-2-14]"
            ),
            (
                "Farm plots like Dikaiopolis's were typically small — four "
                "to eight hectares on average. What a farmer grew depended "
                "on terrain: the plain around Athens suited vegetables and "
                "wheat, but Attica is mostly hilly, and its thin soils "
                "favored vines, olives, and grazing sheep and goats instead "
                "(dairy cattle were rarely kept). Self-sufficiency was the "
                "goal, though few achieved it fully — two-thirds of the "
                "wheat Athenians ate was imported — and any surplus, oil or "
                "wine especially, went to market in Athens.[^athenaze-ch1-ext]"
            ),
            (
                "Athenian citizens were divided into four property classes. "
                "The *pentacosiomedimnoi* — landholders whose estates "
                "produced at least 500 medimnoi of grain a year (a medimnos "
                "≈ 52 liters) — were the wealthiest, effectively "
                "today's millionaires. The *hippeis* (\"horsemen\") could "
                "afford to keep a horse and formed the cavalry. The largest "
                "class, farmers like Dikaiopolis who owned a yoke of oxen "
                "(*zeugos*), were called *zeugitai* and served as heavy "
                "infantry (hoplites). The *thetes* — landless or "
                "land-poor hired laborers — formed the fourth class."
                "[^athenaze-ch1-ext]"
            ),
            (
                "Sources present farmers as the pillar of Athenian democracy "
                "— strong, hardworking, thrifty, plain, yet sensible people, "
                "often contrasted in Aristophanes's comedies against "
                "ambitious politicians, impoverished aristocrats, and "
                "grasping merchants.[^athenaze-ch1]"
            ),
        ],
        wiki_title=None,
        level=["beginner"],
        tags=["history", "athens", "agriculture", "social-class"],
        related_words=[],
        related_lessons=["ancient_greek/palaestra/athenaze-vol1/chapter-1"],
        extra_sources=[_THUCYDIDES_2_14, _ATHENAZE_CH1_EXT, _ATHENAZE_CH1],
        periods_spanned={"from": "attic", "to": "attic"},
        dialect=["attic"],
    )
)

CULTURAL_TOPICS.append(
    CulturalTopicSpec(
        topic_id="dikaiopolis-name-and-acharnians",
        lesson_prose=[
            (
                "## Dikaiopolis's name, and Aristophanes's Acharnians\n\n"
                "The protagonist's name, **Δικαιόπολις**, is built from "
                "**δίκαιος** \"just\" and **πόλις** \"city, state\" — "
                "roughly \"just citizen\" or \"one who lives in a just "
                "city.\"[^athenaze-ch1]"
            ),
            (
                "Dikaiopolis is also the protagonist of Aristophanes's "
                "comedy *Acharnians*, first staged in 425 BC — the play "
                "Athenaze's own course draws its final readings from, where "
                "Dikaiopolis appears as a peacemaker.[^athenaze-ch1]"
            ),
        ],
        wiki_title=None,
        level=["beginner"],
        tags=["history", "aristophanes", "athens", "etymology"],
        related_words=[],
        related_lessons=["ancient_greek/palaestra/athenaze-vol1/chapter-1"],
        extra_sources=[_ATHENAZE_CH1],
        periods_spanned={"from": "attic", "to": "attic"},
        dialect=["attic"],
    )
)

CULTURAL_TOPICS.append(
    CulturalTopicSpec(
        topic_id="slavery-in-ancient-athens",
        lesson_prose=[
            (
                "## Slavery in ancient Athens\n\n"
                "The adult male population of Athens in 431 BC has been "
                "estimated at roughly 50,000 citizens, 25,000 metics "
                "(free resident foreigners with no political rights, who "
                "could not own land in Attica or marry Athenian citizens, "
                "but had court protection, served in the military, took "
                "part in religious festivals, and were prominent in trade "
                "and manufacture), and about 100,000 slaves.[^athenaze-ch2-ext]"
            ),
            (
                "Slaves had no legal rights and were the property of the "
                "state or of private individuals. Aristotle, in the "
                "*Politics*, describes a slave as \"animate property\" "
                "(**κτῆμα ἔμψυχον**) and a tool of his master. Most were "
                "born into slavery or enslaved through war or piracy — a "
                "415 BC document records the sale of fourteen slaves: five "
                "from Thrace, two from Syria, three from Caria, two from "
                "Illyria, one from Scythia, one from Colchis. Enslaving "
                "fellow Greeks was considered immoral and was very rare."
                "[^athenaze-ch2-ext]"
            ),
            (
                "The ancient economy, with little machinery, depended "
                "heavily on slave labor. Some slaves worked for the state, "
                "e.g. in the silver mines; some worked in workshops (the "
                "largest known, a shield factory, employed 120 slaves); "
                "individual citizens often owned one or more slaves "
                "according to their means. As Aristotle observes, for a "
                "poor farmer \"an ox takes the place of a "
                "slave.\"[^athenaze-ch2-ext]"
            ),
            (
                "Not all slaves were treated inhumanely. A 5th-century "
                "writer (Pseudo-Xenophon) remarks with some irritation: "
                "\"In Athens, slaves and metics live with the greatest "
                "license; one is not permitted to strike them, nor will a "
                "slave step aside for you in the street — the reason being "
                "that if the law allowed a free man to strike a slave, a "
                "metic, or a freedman, he would often strike a citizen by "
                "mistake, since in dress the common people of Athens are no "
                "different from slaves and metics.\"[^pseudo-xenophon-ath-pol-1-10] "
                "Slaves and citizens sometimes worked side by side for "
                "equal pay on public building projects, per surviving "
                "inscriptions; some slaves saved enough to buy their "
                "freedom, though this was less common in Athens than in "
                "Rome. Rural slave-farmers typically lived and ate "
                "alongside their masters, and Aristophanes's comic slaves "
                "are lively, bold characters, not figures of tyrannical "
                "control.[^athenaze-ch2-ext]"
            ),
            (
                "The slave in Athenaze's own story, **Ξανθίας** (Xanthias), "
                "takes his name from **ξανθός** \"fair-haired, blond\" — a "
                "typical name for a slave of Thracian or northern origin."
                "[^athenaze-ch2]"
            ),
        ],
        wiki_title=None,
        level=["beginner"],
        tags=["history", "athens", "slavery", "social-class"],
        related_words=[],
        related_lessons=["ancient_greek/palaestra/athenaze-vol1/chapter-2"],
        extra_sources=[_ATHENAZE_CH2_EXT, _PSEUDO_XENOPHON_ATH_POL, _ATHENAZE_CH2],
        periods_spanned={"from": "attic", "to": "attic"},
        dialect=["attic"],
    )
)

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
