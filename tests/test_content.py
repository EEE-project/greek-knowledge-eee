"""Content spot-checks for hand-authored grammar/culture entries, read
directly from the committed files. okfbuild/check.py (see tests/test_check.py)
verifies every file's *structure* (frontmatter shape, footnote resolution);
this module verifies specific *content* -- the real facts and regression
guards that used to live in tests/test_pilot_content.py, back when these
entries were built from Python specs instead of hand-authored directly.
Replaces that module (deleted when the build pipeline for these two
concept types was retired -- see CHANGELOG).
"""

from okfbuild import okf


def _read_grammar(repo_root, rule_id: str):
    return okf.read(repo_root / "grammar" / f"{rule_id}.md")


def _read_culture(repo_root, topic_id: str):
    return okf.read(repo_root / "culture" / f"{topic_id}.md")


def test_second_declension_rule(repo_root):
    concept = _read_grammar(repo_root, "second-declension-masc-neut")

    assert concept.extra_frontmatter["dialect"] == ["attic"]
    assert concept.extra_frontmatter["periods_spanned"] == {"from": "attic", "to": "attic"}
    assert "ἄνθρωπος" in concept.body
    assert "κλῆρος" in concept.body


def test_third_singular_present_indicative_rule(repo_root):
    concept = _read_grammar(repo_root, "third-singular-present-indicative")

    assert "φιλεῖ" in concept.body
    assert "ἐστί" in concept.body


def test_movable_nu_and_enclitics_rule(repo_root):
    concept = _read_grammar(repo_root, "movable-nu-and-enclitics")

    assert "ἐστίν" in concept.body
    assert "ἐφελκυστικόν" in concept.body


def test_present_imperative_active_rule(repo_root):
    concept = _read_grammar(repo_root, "present-imperative-active")

    assert "ἴσθι" in concept.body
    assert "πάρισθι" in concept.body
    assert "μή" in concept.body


def test_verb_accentuation_final_trochee_rule(repo_root):
    concept = _read_grammar(repo_root, "verb-accentuation-final-trochee")

    assert "ἐκβαίνω" in concept.body
    assert "ἔκβαινε" in concept.body
    assert "λῦε" in concept.body


def test_adjective_declension_and_suppletion_rule(repo_root):
    concept = _read_grammar(repo_root, "adjective-declension-and-suppletion")

    assert "δίκαιος" in concept.body
    assert "μέγας" in concept.body
    assert "πολύς" in concept.body
    assert "supplet" in concept.body.lower()


def test_word_order_and_agreement_rule(repo_root):
    concept = _read_grammar(repo_root, "word-order-and-agreement")

    assert "τὸν κλῆρον" in concept.body
    assert "ὁ ἄνθρωπος" in concept.body


def test_preverb_word_formation_rule(repo_root):
    concept = _read_grammar(repo_root, "preverb-word-formation")

    assert "ἐκβαίνει" in concept.body
    assert "βαίνει" in concept.body


def test_future_tha_periphrasis_rule(repo_root):
    concept = _read_grammar(repo_root, "future-tha-periphrasis")

    assert concept.extra_frontmatter["periods_spanned"] == {"from": "koine", "to": "modern"}
    assert concept.extra_frontmatter["dialect"] == []
    assert "θα λύσω" in concept.body


def test_perfect_pluperfect_periphrasis_rule(repo_root):
    concept = _read_grammar(repo_root, "perfect-pluperfect-periphrasis")

    assert "λέλυκα" in concept.body
    assert "έχω λύσει" in concept.body or "έχω λυμένο" in concept.body


def test_optative_replacement_rule(repo_root):
    concept = _read_grammar(repo_root, "optative-replacement")

    assert "είθε" in concept.body
    assert "μακάρι" in concept.body
    assert "εύχεσαι" in concept.body
    cavafy_cited = any(s.id == "cavafy-ithaka-text" for s in concept.sources)
    assert cavafy_cited


def test_infinitive_loss_rule(repo_root):
    concept = _read_grammar(repo_root, "infinitive-loss")

    assert concept.extra_frontmatter["periods_spanned"] == {"from": "koine", "to": "modern"}
    assert "να" in concept.body
    osu_cited = any(s.id == "osu-loss-of-infinitive" for s in concept.sources)
    assert osu_cited
    # regression guard: the poem's own να-clauses cited here turned out to be
    # jussive/wish constructions, not infinitive-replacement examples -- see
    # analisys/infinitive-loss.md and CHANGELOG. Must not come back.
    cavafy_cited = any(s.id == "cavafy-ithaka-text" for s in concept.sources)
    assert not cavafy_cited


def test_mediopassive_merger_rule(repo_root):
    concept = _read_grammar(repo_root, "mediopassive-merger")

    assert "λύομαι" in concept.body
    assert "λύνομαι" in concept.body


def test_augment_loss_rule(repo_root):
    concept = _read_grammar(repo_root, "augment-loss")

    assert "ἔλυον" in concept.body
    assert "έλυνα" in concept.body


def test_reduplicated_participles_as_adjectives_rule(repo_root):
    concept = _read_grammar(repo_root, "reduplicated-participles-as-adjectives")

    assert "πεπεισμένος" in concept.body
    assert "convinced" in concept.body.lower()


def test_future_continuous_new_tense_rule(repo_root):
    concept = _read_grammar(repo_root, "future-continuous-new-tense")

    assert "εξακολουθητικός" in concept.body
    assert "στιγμιαίος" in concept.body


def test_peloponnesian_war_setting_topic(repo_root):
    concept = _read_culture(repo_root, "peloponnesian-war-setting")

    assert concept.extra_frontmatter["dialect"] == ["attic"]
    assert "Pericles" in concept.body


def test_greek_dialect_history_topic(repo_root):
    concept = _read_culture(repo_root, "greek-dialect-history")

    assert concept.extra_frontmatter["dialect"] == []
    assert concept.extra_frontmatter["periods_spanned"] == {"from": "homeric", "to": "koine"}
    assert "κοινή" in concept.body or "koine" in concept.body.lower()


def test_bronze_age_chronology_topic(repo_root):
    concept = _read_culture(repo_root, "bronze-age-to-peloponnesian-war-chronology")

    assert "776" in concept.body  # first Olympic Games
    assert "431" in concept.body  # war outbreak


def test_athenian_farmer_class_system_topic(repo_root):
    concept = _read_culture(repo_root, "athenian-farmer-class-system")

    assert "Thucydides" in concept.body
    thucydides_cited = any(s.id == "thucydides-2-14" for s in concept.sources)
    assert thucydides_cited
    assert "zeugitai" in concept.body.lower()


def test_dikaiopolis_name_and_acharnians_topic(repo_root):
    concept = _read_culture(repo_root, "dikaiopolis-name-and-acharnians")

    assert "δίκαιος" in concept.body
    assert "πόλις" in concept.body
    # regression guard: the play premiered 425 BC, not 426 -- see CHANGELOG.
    assert "425" in concept.body


def test_slavery_in_athens_topic(repo_root):
    concept = _read_culture(repo_root, "slavery-in-ancient-athens")

    pseudo_xenophon_cited = any(s.id == "pseudo-xenophon-ath-pol-1-10" for s in concept.sources)
    assert pseudo_xenophon_cited
    assert "Ξανθίας" in concept.body
    assert "Aristotle" in concept.body


def test_cavafy_topic_cites_official_textbook_and_the_poem_text(repo_root):
    concept = _read_culture(repo_root, "cavafy")

    ebooks_cited = any(s.id == "ebooks-edu-gr-ithaka" for s in concept.sources)
    assert ebooks_cited
    cavafy_text_cited = any(s.id == "cavafy-ithaka-text" for s in concept.sources)
    assert cavafy_text_cited
    assert "Γράμματα" in concept.body
    assert "κουβανείς" in concept.body
    # regression guard: the poem's own body never uses -οσαν forms, so this
    # entry must not link to the grammar rule about them (see CHANGELOG).
    assert "aorist-3pl-osan" not in concept.body


def test_article_rules_state_the_final_nu_rule_with_the_masculine_always_kept(repo_root):
    for rule_id in ("definite-articles-nom-acc", "indefinite-article-enas"):
        concept = _read_grammar(repo_root, rule_id)

        assert any(s.id == "wikipedia-teliko-ni" for s in concept.sources)
        assert "always written" in concept.body
        # regression guard: the masculine -ν is always written, not "very often" kept (see CHANGELOG).
        assert "very often" not in concept.body


def test_ellinika_a_citations_carry_the_verified_bibliographic_form(repo_root):
    authors = "Γιώργος Σιμόπουλος, Ειρήνη Παθιάκη, Ρίτα Κανελλοπούλου, Αγλαΐα Παυλοπούλου"
    citing = 0
    for path in sorted((repo_root / "grammar").glob("*.md")):
        concept = okf.read(path)
        if concept is None:
            continue
        for source in concept.sources:
            if source.id != "ellinika-a":
                continue
            citing += 1
            assert source.author == authors, path.name
            assert "Εκδόσεις Πατάκη, 2010" in source.title, path.name
            assert "(2015)" not in source.resource, path.name
    assert citing > 0


def test_imperative_rule_pairs_affirmative_and_negative_clitic_placement(repo_root):
    concept = _read_grammar(repo_root, "imperative-mood-and-clitics")

    assert any(s.id == "ellinika-a" for s in concept.sources)
    assert "Περίμενέ με." in concept.body
    assert "Μη με περιμένεις." in concept.body
    assert "να μη διαβάσεις" in concept.body
