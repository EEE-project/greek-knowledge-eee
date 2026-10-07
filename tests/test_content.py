"""Content spot-checks for hand-authored grammar/culture entries, read
directly from the committed files. okfbuild/check.py (see tests/test_check.py)
verifies every file's *structure* (frontmatter shape, footnote resolution);
this module verifies specific *content* -- the real facts and regression
guards that used to live in tests/test_pilot_content.py, back when these
entries were built from Python specs instead of hand-authored directly.
Replaces that module (deleted when the build pipeline for these two
concept types was retired -- see CHANGELOG).
"""

import hashlib
import re

import pytest

from okfbuild import okf
from okfbuild.query import find_concepts


def _verse_lines(body: str) -> list[str]:
    return [line for line in body.split("\n") if line.strip() and not line.startswith(("#", "<!--"))]


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


def test_cavafy_topic_lists_the_ithaka_readings_and_the_musical_piece(repo_root):
    concept = _read_culture(repo_root, "cavafy")

    urls = {s.id: s.resource for s in concept.sources if s.id.startswith(("ithaka-reading-", "ithaka-music-"))}
    assert len([i for i in urls if i.startswith("ithaka-reading-")]) == 7
    assert urls["ithaka-music-deep-pressed"] == "https://www.youtube.com/watch?v=4nHqjy65n6I"
    # every listed recording is cited in the prose, and the sections say what they hold
    assert all(f"[^{i}]" in concept.body for i in urls)
    assert "Seven readings are on YouTube" in concept.body
    assert "## Ithaka in music" in concept.body


def test_kavafis_text_index_counts_the_recordings_of_the_cavafy_page(repo_root):
    text = (repo_root / "texts" / "kavafis_ithaki" / "index.md").read_text(encoding="utf-8")

    # regression guard: the index said "Two recorded readings" after culture/cavafy.md listed seven (see CHANGELOG).
    assert "Seven recorded readings" in text
    assert "Two recorded readings" not in text


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


def test_ithaka_text_is_the_complete_36_line_poem(repo_root):
    concept = okf.read(repo_root / "texts" / "kavafis_ithaki" / "text.md")

    assert concept.type == "Literary Text"
    assert concept.extra_frontmatter["passage"] == "1-36"
    lines = _verse_lines(concept.body)
    assert len(lines) == 36
    # regression guards: the course text had «Σαν» in στ. 1, and the span was once misstated as "of 40".
    assert lines[0].startswith("Σα βγεις")
    assert lines[32].startswith("Άλλα δεν έχει")


def test_odyssey_text_carries_exactly_the_greek_lines_echoed_beside_the_glosses(repo_root):
    concept = okf.read(repo_root / "texts" / "odyssey" / "text.md")
    en = (repo_root / "texts" / "odyssey" / "translations_en.md").read_text(encoding="utf-8")
    echoed = re.findall(r"(?m)^<!-- grc: (.*) -->$", en.split("\n## interlinear_en\n", 1)[1])

    assert concept.type == "Literary Text"
    assert concept.extra_frontmatter["language"] == "grc"
    assert _verse_lines(concept.body) == echoed
    assert len(echoed) == 183  # I.1-21 (21) + IX.19-180 (162)


def test_imperative_rule_pairs_affirmative_and_negative_clitic_placement(repo_root):
    concept = _read_grammar(repo_root, "imperative-mood-and-clitics")

    assert any(s.id == "ellinika-a" for s in concept.sources)
    assert "Περίμενέ με." in concept.body
    assert "Μη με περιμένεις." in concept.body
    assert "να μη διαβάσεις" in concept.body


def test_koine_to_modern_rules_state_the_corrected_facts(repo_root):
    augment = _read_grammar(repo_root, "augment-loss").body
    assert "wouldn't otherwise be accented" not in augment
    assert "**ἐλύομεν**" in augment  # Koine's augment sits on every indicative form, stressed or not

    assert "formally distinct only in the future and aorist" in _read_grammar(repo_root, "mediopassive-merger").body

    participles = _read_grammar(repo_root, "reduplicated-participles-as-adjectives").body
    assert "roughly forty" not in participles
    assert "**φ → π**" in participles  # πεφωτισμένος and κεχαριτωμένος de-aspirate, so "repeat the first consonant" is wrong


def test_a2_b1_rules_no_longer_state_what_review_found_wrong(repo_root):
    wrong = {
        "aorist-past-tense": ["When a stem has fewer than three syllables", "μίλησαν(ε)", "wholly different, suppletive stem"],
        "combining-imperfect-aorist": ["λεωφορέιο"],
        "genitive-possession": ["all neuters change to"],
        "imperfect-formation": ["suppletive imperfect"],
        "location-prepositions": ["never used without a following preposition", "Movement *toward* a destination instead takes"],
        "masculine-feminine-noun-plurals": ["one true exception", "and all feminine nouns"],
        "modern-neuter-noun-plurals": ["with stress staying on the same syllable as the singular"],
        "na-dependent-verb-forms": ["only two kinds of verb form", "negates just the dependent action"],
        "negation-questions-and-min": ["raised semicolon"],
        "noun-declension-genitive-singular": ["masculine **-ος**, masculine **-ας**"],
        "prefix-word-formation": ["**εξάρτητος** dependent"],  # not a Modern Greek word; ανεξάρτητος has no such base
        "prepei-tense-shift": ["descends from Ancient Greek's lost infinitive"],
    }
    for rule_id, phrases in wrong.items():
        body = _read_grammar(repo_root, rule_id).body
        for phrase in phrases:
            assert phrase not in body, f"{rule_id} still says {phrase!r}"


def test_a2_b1_rules_carry_the_corrected_forms(repo_root):
    assert "μιλήσανε" in _read_grammar(repo_root, "aorist-past-tense").body
    assert "εδώ κοντά" in _read_grammar(repo_root, "location-prepositions").body
    assert "**Νίκο!**" in _read_grammar(repo_root, "vocative-case").body
    assert "**το μάθημα → τα μαθήματα**" in _read_grammar(repo_root, "modern-neuter-noun-plurals").body


def test_the_noun_verb_ending_rule_stays_deleted(repo_root):
    # It read the spelling cue on Ελληνικά Β΄ p. 19 (ο/ω, η/ει in nouns and verbs) as a rule that a noun's ending predicts its verb's conjugation.
    assert not (repo_root / "grammar" / "noun-verb-ending-correlation.md").exists()


def test_every_modern_grammar_rule_is_verified_for_its_current_text(repo_root):
    # The modern-grammar selection must return only rules someone checked against sources. A rule that is new, or
    # was edited after its review, fails here: check it, then `greek-knowledge verify <file> --by ... --against ...`.
    rules = find_concepts(repo_root, type="Grammatical Rule", period="modern")

    assert rules
    unverified = [path.name for path, concept in rules if okf.current_verification(concept) is None]
    assert unverified == []


def test_koine_to_modern_comparisons_are_advanced_not_beginner(repo_root):
    # They compare two periods of the language rather than teach Modern Greek, so a `--period modern --level beginner`
    # selection must not hand them to a learner.
    comparisons = [
        concept
        for _, concept in find_concepts(repo_root, type="Grammatical Rule", period="modern")
        if concept.extra_frontmatter["periods_spanned"]["from"] != "modern"
    ]

    assert len(comparisons) == 8
    assert all(concept.level == ["advanced"] for concept in comparisons)


_ITHAKA_EN_REFS = ["Ιθάκη, στ. 1–3", "Ιθάκη, στ. 4–12", "Ιθάκη, στ. 13–23", "Ιθάκη, στ. 24–30", "Ιθάκη, στ. 31–33", "Ιθάκη, στ. 34–36"]
_ITHAKA_EN_SECTIONS = [
    "interlinear_en",
    "literal",
    "Valassopoulo",
    "Keeley/Sherrard (reference only, not reproduced)",
    "Barnstone (reference only, not reproduced)",
    "Mendelsohn (reference only, not reproduced)",
]
_VALASSOPOULO_WORDS = 263
_VALASSOPOULO_SHA256 = "7d27649472fb9554d0d67cabfd1c774644d8657ecaed609d020c4eaecaa42f82"  # of the 36 text lines joined by "\n"


def _ithaka_en_sections(body: str) -> dict:
    """{`##` section name: its text} in file order, for the body of texts/kavafis_ithaki/translations_en.md."""
    chunks = (chunk.partition("\n") for chunk in re.split(r"(?m)^## ", body)[1:])
    return {name.strip(): rest for name, _, rest in chunks}


def _ithaka_en_verse_pairs(section: str) -> list:
    """[(ref, [(echoed Greek line, text line), ...], non-blank line count)] for each `###` block of a translation section."""
    blocks = []
    for block in re.split(r"(?m)^### ", section)[1:]:
        ref, _, rest = block.partition("\n")
        pairs = re.findall(r"(?m)^<!-- el: (.*) -->\n(.*)$", rest)
        blocks.append((ref.strip(), pairs, len([line for line in rest.splitlines() if line.strip()])))
    return blocks


def _ithaka_en_problems(body: str, greek: list) -> list:
    """What texts/kavafis_ithaki/translations_en.md must satisfy; [] when it does."""
    problems = []
    sections = _ithaka_en_sections(body)
    if list(sections) != _ITHAKA_EN_SECTIONS:
        problems.append(f"sections are {list(sections)}")
    for name in ("interlinear_en", "literal", "Valassopoulo"):
        blocks = _ithaka_en_verse_pairs(sections.get(name, ""))
        if [ref for ref, _, _ in blocks] != _ITHAKA_EN_REFS:
            problems.append(f"{name}: blocks are {[ref for ref, _, _ in blocks]}")
        for ref, pairs, non_blank in blocks:
            first, last = (int(n) for n in re.findall(r"\d+", ref))
            # one echo line and one text line per verse and nothing else: a text line split in two adds a physical line
            if len(pairs) != last - first + 1 or non_blank != 2 * len(pairs):
                problems.append(f"{name} {ref}: {len(pairs)} pairs in {non_blank} non-blank lines")
        pairs = [pair for _, block_pairs, _ in blocks for pair in block_pairs]
        if [g for g, _ in pairs] != greek:
            problems.append(f"{name}: echoed Greek lines differ from text.md")
        if not all(text.strip() for _, text in pairs):
            problems.append(f"{name}: empty text line")
        if name == "Valassopoulo":
            text = "\n".join(line for _, line in pairs)
            words = re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())
            if len(words) != _VALASSOPOULO_WORDS or hashlib.sha256(text.encode("utf-8")).hexdigest() != _VALASSOPOULO_SHA256:
                problems.append("Valassopoulo: the text differs from the pinned 1924 text")
    for name, section in sections.items():
        if name.endswith("(reference only, not reproduced)"):
            lines = [line for line in section.splitlines() if line.strip()]
            if any(not (line.startswith("<!--") and line.endswith("-->")) and not (line.startswith("*(") and line.endswith(")*")) for line in lines):
                problems.append(f"{name}: carries more than its citation comment and note")
    return problems


def _ithaka_en_variant(body: str, kind: str) -> str:
    """A deliberately drifted copy of the real file body, built without retyping any poem text."""
    if kind == "pasted_reference_lines":
        return body.replace("(reference only, not reproduced)\n", "(reference only, not reproduced)\n\na pasted line of verse\n", 1)
    if kind == "extra_keeley_section":
        return body.rstrip("\n") + "\n\n## Keeley/Sherrard\n\n### Ιθάκη, στ. 1–3\n\n<!-- el: x -->\ny\n"
    if kind == "missing_echo":
        head, sep, tail = body.partition("\n## literal\n")
        return head + sep + tail.replace("<!-- el:", "<!-- gr:", 1)
    head, sep, rest = body.partition("\n## Valassopoulo\n")
    section, keeley_sep, tail = rest.partition("\n## Keeley/Sherrard")
    lines = section.split("\n")
    first = next(n for n, line in enumerate(lines) if line.strip() and not line.startswith(("<!--", "###")))
    words = lines[first].split()
    lines[first] = {
        "split_line": " ".join(words[:3]) + "\n" + " ".join(words[3:]),
        "dropped_word": " ".join(words[1:]),
        "swapped_words": " ".join([words[1], words[0], *words[2:]]),
    }[kind]
    return head + sep + "\n".join(lines) + keeley_sep + tail


def test_ithaka_en_translations_are_line_for_line_with_the_greek(repo_root):
    greek = _verse_lines(okf.read(repo_root / "texts" / "kavafis_ithaki" / "text.md").body)
    body = okf.read(repo_root / "texts" / "kavafis_ithaki" / "translations_en.md").body

    assert _ithaka_en_problems(body, greek) == []


@pytest.mark.parametrize(
    "kind", ["split_line", "dropped_word", "swapped_words", "pasted_reference_lines", "extra_keeley_section", "missing_echo"]
)
def test_ithaka_en_guard_rejects_drifted_copies(repo_root, kind):
    greek = _verse_lines(okf.read(repo_root / "texts" / "kavafis_ithaki" / "text.md").body)
    body = okf.read(repo_root / "texts" / "kavafis_ithaki" / "translations_en.md").body

    assert _ithaka_en_problems(body, greek) == []
    assert _ithaka_en_problems(_ithaka_en_variant(body, kind), greek) != []


def test_ithaka_en_front_matter_lists_valassopoulo_as_reproduced(repo_root):
    concept = okf.read(repo_root / "texts" / "kavafis_ithaki" / "translations_en.md")
    valassopoulo = _ithaka_en_verse_pairs(_ithaka_en_sections(concept.body)["Valassopoulo"])

    assert concept.extra_frontmatter["translators"][:3] == ["interlinear_en", "literal", "Valassopoulo"]
    assert {"tr-valassopoulo1924", "tr-valassopoulo1924-wdtprs"} <= {s.id for s in concept.sources}
    # regression guards: Valassopoulo's own opening and closing words
    assert valassopoulo[0][1][0][1].startswith("When you start on the way to Ithaca")
    assert valassopoulo[-1][1][-1][1].endswith("these Ithacas mean.")


def test_ithaka_en_makes_no_unverifiable_provenance_or_jurisdiction_claims(repo_root):
    folder = repo_root / "texts" / "kavafis_ithaki"
    for name in ("translations_en.md", "index.md"):
        # the KB's evidence for Valassopoulo is "public domain in the US as a pre-1929 publication": no claim beyond it
        assert not re.search(r"public domain(?! in the US)", (folder / name).read_text(encoding="utf-8")), name
    literal = _ithaka_en_sections(okf.read(folder / "translations_en.md").body)["literal"]

    assert "written for this course from the Greek text" in literal
    assert not re.search(r"not (copied|taken|adapted)|word-for-word", literal)
