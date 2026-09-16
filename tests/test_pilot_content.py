import re
from unittest.mock import Mock

from okfbuild.concepts import cultural_context, grammatical_rule
from okfbuild.pilot_content import CULTURAL_TOPICS, GRAMMAR_RULES


def _spec(rule_id: str):
    return next(s for s in GRAMMAR_RULES if s.rule_id == rule_id)


def _build(rule_id: str):
    spec = _spec(rule_id)
    return grammatical_rule.build(
        spec.rule_id, spec.body, spec.sources, spec.period_from, spec.period_to,
        level=spec.level, tags=spec.tags, dialect=spec.dialect,
    )


def _assert_footnotes_resolve(concept):
    footnote_ids = set(re.findall(r"\[\^([^\]]+)\]", concept.body))
    assert footnote_ids
    assert footnote_ids <= {s.id for s in concept.sources}


def test_second_declension_rule():
    concept = _build("second-declension-masc-neut")

    assert concept.extra_frontmatter["dialect"] == ["attic"]
    assert concept.extra_frontmatter["periods_spanned"] == {"from": "attic", "to": "attic"}
    assert "ἄνθρωπος" in concept.body
    assert "κλῆρος" in concept.body
    _assert_footnotes_resolve(concept)


def test_third_singular_present_indicative_rule():
    concept = _build("third-singular-present-indicative")

    assert "φιλεῖ" in concept.body
    assert "ἐστί" in concept.body
    _assert_footnotes_resolve(concept)


def test_movable_nu_and_enclitics_rule():
    concept = _build("movable-nu-and-enclitics")

    assert "ἐστίν" in concept.body
    assert "ἐφελκυστικόν" in concept.body
    _assert_footnotes_resolve(concept)


def test_present_imperative_active_rule():
    concept = _build("present-imperative-active")

    assert "ἴσθι" in concept.body
    assert "πάρισθι" in concept.body
    assert "μή" in concept.body
    _assert_footnotes_resolve(concept)


def test_verb_accentuation_final_trochee_rule():
    concept = _build("verb-accentuation-final-trochee")

    assert "ἐκβαίνω" in concept.body
    assert "ἔκβαινε" in concept.body
    assert "λῦε" in concept.body
    _assert_footnotes_resolve(concept)


def test_adjective_declension_and_suppletion_rule():
    concept = _build("adjective-declension-and-suppletion")

    assert "δίκαιος" in concept.body
    assert "μέγας" in concept.body
    assert "πολύς" in concept.body
    assert "supplet" in concept.body.lower() or "суппле" in concept.body.lower() or "different stems" in concept.body.lower()
    _assert_footnotes_resolve(concept)


def test_word_order_and_agreement_rule():
    concept = _build("word-order-and-agreement")

    assert "τὸν κλῆρον" in concept.body
    assert "ὁ ἄνθρωπος" in concept.body
    _assert_footnotes_resolve(concept)


def test_preverb_word_formation_rule():
    concept = _build("preverb-word-formation")

    assert "ἐκβαίνει" in concept.body
    assert "βαίνει" in concept.body
    _assert_footnotes_resolve(concept)


def test_future_tha_periphrasis_rule():
    concept = _build("future-tha-periphrasis")

    assert concept.extra_frontmatter["periods_spanned"] == {"from": "koine", "to": "modern"}
    assert concept.extra_frontmatter["dialect"] == []
    assert "θα λύσω" in concept.body
    assert "λύσω" in concept.body
    _assert_footnotes_resolve(concept)


def test_perfect_pluperfect_periphrasis_rule():
    concept = _build("perfect-pluperfect-periphrasis")

    assert "λέλυκα" in concept.body
    assert "έχω λύσει" in concept.body or "έχω λυμένο" in concept.body
    _assert_footnotes_resolve(concept)


def test_optative_replacement_rule():
    concept = _build("optative-replacement")

    assert "εἴθε" in concept.body
    assert "μακάρι" in concept.body
    _assert_footnotes_resolve(concept)


def test_mediopassive_merger_rule():
    concept = _build("mediopassive-merger")

    assert "λύομαι" in concept.body
    assert "λύνομαι" in concept.body
    _assert_footnotes_resolve(concept)


def test_augment_loss_rule():
    concept = _build("augment-loss")

    assert "ἔλυον" in concept.body
    assert "έλυνα" in concept.body
    _assert_footnotes_resolve(concept)


def test_reduplicated_participles_as_adjectives_rule():
    concept = _build("reduplicated-participles-as-adjectives")

    assert "πεπεισμένος" in concept.body
    assert "убеждённый" in concept.body or "convinced" in concept.body.lower()
    _assert_footnotes_resolve(concept)


def test_future_continuous_new_tense_rule():
    concept = _build("future-continuous-new-tense")

    assert "εξακολουθητικός" in concept.body
    assert "στιγμιαίος" in concept.body
    _assert_footnotes_resolve(concept)


def _culture_spec(topic_id: str):
    return next(s for s in CULTURAL_TOPICS if s.topic_id == topic_id)


def _build_culture(topic_id: str):
    spec = _culture_spec(topic_id)
    sources = Mock(wikipedia=Mock())
    sources.wikipedia.summary.return_value = None  # unit tests don't hit the network
    return cultural_context.build(
        spec.topic_id, spec.lesson_prose, spec.wiki_title, sources,
        level=spec.level, tags=spec.tags,
        related_words=spec.related_words, related_lessons=spec.related_lessons,
        extra_sources=spec.extra_sources, periods_spanned=spec.periods_spanned,
        dialect=spec.dialect,
    )


def test_peloponnesian_war_setting_topic():
    concept = _build_culture("peloponnesian-war-setting")

    assert concept.extra_frontmatter["dialect"] == ["attic"]
    assert "Pericles" in concept.body or "Перикл" in concept.body
    assert "Sparta" in concept.body or "Спарт" in concept.body
    _assert_footnotes_resolve(concept)


def test_greek_dialect_history_topic():
    concept = _build_culture("greek-dialect-history")

    assert concept.extra_frontmatter["dialect"] == []
    assert concept.extra_frontmatter["periods_spanned"] == {"from": "homeric", "to": "koine"}
    assert "κοινή" in concept.body or "koine" in concept.body.lower()
    _assert_footnotes_resolve(concept)


def test_bronze_age_chronology_topic():
    concept = _build_culture("bronze-age-to-peloponnesian-war-chronology")

    assert concept.extra_frontmatter["dialect"] == []
    assert "776" in concept.body  # first Olympic Games
    assert "431" in concept.body  # war outbreak
    _assert_footnotes_resolve(concept)


def test_athenian_farmer_class_system_topic():
    concept = _build_culture("athenian-farmer-class-system")

    assert "Thucydides" in concept.body or "Фукидид" in concept.body
    thucydides_cited = any(s.id == "thucydides-2-14" for s in concept.sources)
    assert thucydides_cited
    assert "zeugitai" in concept.body.lower() or "ζευγίτ" in concept.body
    _assert_footnotes_resolve(concept)


def test_dikaiopolis_name_and_acharnians_topic():
    concept = _build_culture("dikaiopolis-name-and-acharnians")

    assert "δίκαιος" in concept.body
    assert "πόλις" in concept.body
    assert "426" in concept.body
    _assert_footnotes_resolve(concept)


def test_slavery_in_athens_topic():
    concept = _build_culture("slavery-in-ancient-athens")

    pseudo_xenophon_cited = any(s.id == "pseudo-xenophon-ath-pol-1-10" for s in concept.sources)
    assert pseudo_xenophon_cited
    assert "Ξανθίας" in concept.body
    assert "Aristotle" in concept.body or "Аристотель" in concept.body
    _assert_footnotes_resolve(concept)
