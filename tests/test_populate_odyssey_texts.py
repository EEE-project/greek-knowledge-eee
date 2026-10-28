"""Tests for scripts/populate_odyssey_texts.py -- the previously-untested,
re-runnable script that assembles texts/odyssey/*.md from hand-extracted
translator sections (see that module's own docstring)."""

import re
from pathlib import Path

import pytest
import yaml

import eee_project as eee
from scripts import populate_odyssey_texts as script

_GENERATED_FILES = [
    "translations_en.md",
    "translations_ru.md",
    "translations_el.md",
]


def _split(path: Path) -> tuple[dict, str]:
    _, yaml_text, body = path.read_text().split("---\n", 2)
    return yaml.safe_load(yaml_text), body


def _without_generated_at(frontmatter: dict) -> dict:
    fm = dict(frontmatter)
    fm["generated"] = {k: v for k, v in fm["generated"].items() if k != "at"}
    return fm


# --- Full corpus regeneration matches what's committed ---


def test_populate_all_matches_committed_content(tmp_path, monkeypatch):
    """Regenerating the whole corpus into a scratch directory must produce
    content identical to what's committed under texts/odyssey/ -- other
    than the `generated.at` timestamp, which is expected to differ.

    _TEXTS_DIR is read from the module's globals at call time inside each
    populate_*() function, so patching the module attribute (rather than
    passing a directory argument) is enough to redirect every write()
    without any production-code change.
    """
    real_texts_dir = script._TEXTS_DIR
    monkeypatch.setattr(script, "_TEXTS_DIR", tmp_path)

    script.populate_translations_en()
    script.populate_translations_ru()
    script.populate_translations_el()

    for filename in _GENERATED_FILES:
        generated_fm, generated_body = _split(tmp_path / filename)
        committed_fm, committed_body = _split(real_texts_dir / filename)
        assert _without_generated_at(generated_fm) == _without_generated_at(committed_fm), filename
        assert generated_body == committed_body, filename


# --- _strip_header() ---


def test_strip_header_strips_header_comments_and_blank_lines():
    """The exact bug class Task 4 found by hand: a second `## Header`
    section merged under a prior one must have its header line, comment
    line(s), and surrounding blank lines fully stripped, leaving only the
    `### `-prefixed stanza content -- this is the regression test that
    would have caught the original bug."""
    section = (
        "## Header\n"
        "\n"
        "<!-- plain citation line -->\n"
        "<!-- **bold description** -->\n"
        "\n"
        "### Stanza 1\n"
        "\n"
        "line one\n"
        "line two\n"
    )

    result = script._strip_header(section)

    assert result == "### Stanza 1\n\nline one\nline two"


# --- Fix 1 regression: merged Πολυλάς description covers both editions ---


def test_polylas_description_covers_both_editions():
    """_POLYLAS_I's description is the ONE surviving citation line for the
    merged Πολυλάς section (_strip_header drops _POLYLAS_IX's own header) --
    it must name both the 1875 (I.1-21) and 1877 (IX.19-180) editions, since
    35 of the merged section's 39 stanzas are actually from the 1877 edition."""
    body = script._POLYLAS_I.rstrip("\n") + "\n\n" + script._strip_header(script._POLYLAS_IX) + "\n"

    stanzas, descriptions = eee.parse_stanza_translations(body)

    assert len(stanzas["Πολυλάς"]) == 39  # 4 (I.1-21) + 35 (IX.19-180)
    assert "1875" in descriptions["Πολυλάς"]
    assert "1877" in descriptions["Πολυλάς"]


def test_polylas_description_names_the_ranges_the_section_holds():
    """A lesson shows the description beside the translation: its I and IX ranges
    must be the ranges of the stanzas the merged section really holds."""
    body = script._POLYLAS_I.rstrip("\n") + "\n\n" + script._strip_header(script._POLYLAS_IX) + "\n"

    stanzas, descriptions = eee.parse_stanza_translations(body, ref_prefix="### Odyss. ")

    for book in ("I", "IX"):
        spans = [tuple(map(int, m.groups())) for ref in stanzas["Πολυλάς"] if (m := re.fullmatch(rf"{book}\.(\d+)–(\d+)", ref))]
        assert f"{book}.{min(s for s, _ in spans)}-{max(e for _, e in spans)}" in descriptions["Πολυλάς"]


# --- Regression: every EN/RU translator must cover both books, not just the one it started with ---


def test_pope_and_murray_each_cover_both_books():
    """Pope originally only had Book I (from the abandoned translations
    branch); Murray originally only had Book IX. A consuming notebook that
    offers both as dropdown options on both lessons needs both translators
    to actually have both books, not silently show '-' for the missing
    half -- this is the exact gap a downstream consumer (created_with_eee's
    host-resilience Task 3) found the hard way."""
    en_body = (
        script._POPE_I.rstrip("\n") + "\n\n" + script._strip_header(script._POPE_IX)
        + "\n\n---\n\n"
        + script._MURRAY_IX.rstrip("\n") + "\n\n" + script._strip_header(script._MURRAY_I)
        + "\n"
    )
    stanzas, _ = eee.parse_stanza_translations(en_body, ref_prefix="### Odyss. ")

    # Pope groups IX.39-180 into 13 larger "(equivalent passage)" chunks
    # (a loose poetic translation doesn't map 1:1 to the Greek line numbers).
    pope_expected_refs = {
        'I.11–15', 'I.16–21', 'I.1–5', 'I.6–10', 'IX.105–115 (equivalent passage)',
        'IX.116–129 (equivalent passage)', 'IX.130–145 (equivalent passage)',
        'IX.146–160 (equivalent passage)', 'IX.161–169 (equivalent passage)',
        'IX.170–180 (equivalent passage)', 'IX.19–24', 'IX.25–28', 'IX.29–33',
        'IX.34–38', 'IX.39–46 (equivalent passage)', 'IX.47–55 (equivalent passage)',
        'IX.56–66 (equivalent passage)', 'IX.67–75 (equivalent passage)',
        'IX.76–81 (equivalent passage)', 'IX.82–90 (equivalent passage)',
        'IX.91–104 (equivalent passage)',
    }
    # Murray is line-precise even in the extension, so it gets many more,
    # smaller stanzas instead.
    murray_expected_refs = {
        'I.11–15', 'I.16–21', 'I.1–5', 'I.6–10', 'IX.105–111', 'IX.112–115',
        'IX.116–121', 'IX.122–124', 'IX.125–129', 'IX.130–133', 'IX.134–139',
        'IX.140–141', 'IX.142–145', 'IX.146–151', 'IX.152–155', 'IX.156–160',
        'IX.161–165', 'IX.166–169', 'IX.170–176', 'IX.177–180', 'IX.19–24',
        'IX.25–28', 'IX.29–33', 'IX.34–38', 'IX.39–42', 'IX.43–46', 'IX.47–50',
        'IX.51–55', 'IX.56–61', 'IX.62–66', 'IX.67–71', 'IX.72–75', 'IX.76–78',
        'IX.79–81', 'IX.82–86', 'IX.87–90', 'IX.91–93', 'IX.94–97', 'IX.98–104',
    }
    assert len(stanzas["Pope"]) == 21
    assert set(stanzas["Pope"]) == pope_expected_refs
    assert len(stanzas["Murray"]) == 39
    assert set(stanzas["Murray"]) == murray_expected_refs


def test_murray_ix_39_42_is_a_single_line():
    """IX.39-42 used to be transcribed across 2 physical lines splitting
    mid-sentence ("...to the Cicones," / "to Ismarus. There I sacked...")
    -- a leftover from IX.19-38's one-line-per-verse style that was never
    carried through when IX.43 onward switched to one dense line per stanza
    (the style every other Murray stanza from IX.43 on already uses).
    parse_stanza_translations joins physical lines with a bare "\\n", and a
    consuming notebook's display renders each resulting line as its own
    block -- so the stray line break rendered as a visible gap splitting
    the sentence in two. Fixed 2026-09-29 by joining onto one line, matching
    every neighboring stanza; see this repo's CHANGELOG for the report."""
    stanzas, _ = eee.parse_stanza_translations(script._MURRAY_IX, ref_prefix="### Odyss. ")
    assert "\n" not in stanzas["Murray"]["IX.39–42"]


def test_interlinear_en_and_el_each_cover_both_books():
    """interlinear_en/interlinear_el are folded into translations_{en,el}.md
    as ordinary ## sections (not separate files) -- parse_stanza_translations
    handles them like any other translator; I.1-21 was the gap originally
    (only IX.19-38 existed, authored fresh 2026-09-14 to close it), the
    same class this test file already guards for Pope/Murray/подстрочник."""
    # Fine-grained per-lesson stanza split, matching interlinear_ru (and
    # every lesson's own greek.md) exactly -- re-split 2026-09-28 from the
    # coarser 13-chunk grouping interlinear_en/el originally shared with
    # Pope (a genuine "equivalent passage" translator, where that coarser
    # grouping is correct; interlinear is a word-for-word crib, so a coarser
    # match there means unrelated lines bleeding in from a neighboring
    # stanza -- see eee-project's find_stanza_translation docstring).
    expected_refs = {
        'I.1–5', 'I.6–10', 'I.11–15', 'I.16–21',
        'IX.19–24', 'IX.25–28', 'IX.29–33', 'IX.34–38',
        'IX.39–42', 'IX.43–46', 'IX.47–50', 'IX.51–55', 'IX.56–61',
        'IX.62–66', 'IX.67–71', 'IX.72–75', 'IX.76–78', 'IX.79–81',
        'IX.82–86', 'IX.87–90', 'IX.91–93', 'IX.94–97', 'IX.98–104',
        'IX.105–111', 'IX.112–115', 'IX.116–121', 'IX.122–124', 'IX.125–129',
        'IX.130–133', 'IX.134–139', 'IX.140–141', 'IX.142–145', 'IX.146–151',
        'IX.152–155', 'IX.156–160', 'IX.161–165', 'IX.166–169',
        'IX.170–176', 'IX.177–180',
    }

    interlinear_en = script._INTERLINEAR_EN_I.rstrip("\n") + "\n\n" + script._strip_header(script._INTERLINEAR_EN_IX)
    en_stanzas, _ = eee.parse_stanza_translations(interlinear_en, ref_prefix="### Odyss. ")
    assert set(en_stanzas["interlinear_en"]) == expected_refs

    interlinear_el = script._INTERLINEAR_EL_I.rstrip("\n") + "\n\n" + script._strip_header(script._INTERLINEAR_EL_IX)
    el_stanzas, _ = eee.parse_stanza_translations(interlinear_el, ref_prefix="### Odyss. ")
    assert set(el_stanzas["interlinear_el"]) == expected_refs


def test_interlinear_grc_comment_strips_to_plain_gloss():
    """The Greek source line an interlinear translator echoes as
    <!-- grc: ... --> must actually strip clean via GreekUtils.
    strip_comment_lines(), leaving only the gloss -- the whole reason the
    marker moved from bold (**...**) to a comment: any translator's text
    can carry one without a dedicated parser."""
    interlinear_en = script._INTERLINEAR_EN_I.rstrip("\n") + "\n\n" + script._strip_header(script._INTERLINEAR_EN_IX)
    en_stanzas, _ = eee.parse_stanza_translations(interlinear_en, ref_prefix="### Odyss. ")

    raw = en_stanzas["interlinear_en"]["I.1–5"]
    assert "<!-- grc:" in raw  # sanity: the raw parse still has the comment

    cleaned = eee.strip_comment_lines(raw)
    assert "<!-- grc:" not in cleaned
    assert "man to-me tell" in cleaned


def test_interlinear_ru_present_and_covers_both_books():
    """подстрочник (RU's own literal interlinear rendering, renamed to the
    'interlinear_ru' heading 2026-09-26 to match interlinear_en/el's
    convention -- still labeled "подстрочник" in the translators= metadata)
    was silently dropped entirely when the KB corpus was first populated --
    it's the dropdown's *default* value in every consuming notebook, so its
    absence is a regression (shows '-' by default), not just a missing
    option."""
    body = (
        script._INTERLINEAR_RU_I.rstrip("\n") + "\n\n" + script._strip_header(script._INTERLINEAR_RU_IX)
        + "\n"
    )
    stanzas, descriptions = eee.parse_stanza_translations(body, ref_prefix="### Odyss. ")

    assert len(stanzas["interlinear_ru"]) == 39  # 4 (I.1-21) + 35 (IX.19-180)
    assert descriptions.get("interlinear_ru", "") == ""


# --- Regression: the first two passages hold each translator's own text ---
# Each anchor is a line (Murray: a whole stanza) of the translator's primary text: Project Gutenberg #30613 (Polylas),
# en.wikisource (Pope), Perseus (Murray), ru.wikisource (Zhukovsky) and az.lib.ru (Veresaev). Earlier these stanzas held
# invented or reworded lines under the translators' names, and the regeneration test could not see it.

_OWN_TEXT_ANCHORS = [
    ('translations_el.md', 'Πολυλάς', 'I.1–5', "Τον άνδρα, μούσα, λέγε μου, πολύτροπον, 'που εις μέρη"),
    ('translations_en.md', 'Pope', 'I.6–10', "(Ah, men unbless'd!) to touch that natal shore."),
    ('translations_en.md', 'Murray', 'IX.19–24', 'I am Odysseus, son of Laertes, who am known among men for all manner of wiles, and my fame reaches unto heaven. But I dwell in clear-seen Ithaca, wherein is a mountain, Neriton, covered with waving forests, conspicuous from afar; and round it lie many isles hard by one another, Dulichium, and Same, and wooded Zacynthus.'),
    ('translations_ru.md', 'Жуковский', 'IX.34–38', 'Сладостней нет ничего нам отчизны и сродников наших,'),
    ('translations_ru.md', 'Вересаев', 'IX.19–24', 'Я - Одиссей Лаэртид. Измышленьями хитрыми славен'),
    ('translations_ru.md', 'Жуковский', 'IX.170–176', 'Дикий ли, нравом свирепый, не знающий веры и правды,'),
    ('translations_ru.md', 'Жуковский', 'IX.116–121', 'Шум; никогда не заглядывал к ним звероловец, за дичью'),
    ('translations_ru.md', 'Вересаев', 'IX.166–169', 'Дым, голоса их самих, овечье и козье блеянье.'),
    # Σπανούδης: the print edition, as transcribed by the maintainer; the three Latin-v words are the corrected ones
    ('translations_el.md', 'Σπανούδης', 'I.1–5', 'Μούσα, τον πολλοπάητον άντραν να τραγουδήσεις,'),
    ('translations_el.md', 'Σπανούδης', 'IX.19–24', "Εγιώ 'μαι του Λαέρτη γιος τζαι φτάνν' η πονηριά μου"),
    ('translations_el.md', 'Σπανούδης', 'IX.62–66', "τους φίλους που εππέσασιν νεκρούς ν' αθθυμηθούμεν."),
    ('translations_el.md', 'Σπανούδης', 'IX.72–75', 'Να μεν πνιούμεν τα πανιά χαμαί κάτω τραβούμεν'),
    ('translations_el.md', 'Σπανούδης', 'IX.76–78', 'πίσω στα σπίθκια μας γεροί τζι όλα θα ήταν θάμμαν.'),
    ('translations_el.md', 'Σπανούδης', 'IX.177–180', 'Στους πάγκους τους εκάτσασιν τζαι τα σιοινιά κρατούσιν,'),
]


@pytest.mark.parametrize(("file", "translator", "ref", "line"), _OWN_TEXT_ANCHORS)
def test_first_passages_hold_each_translators_own_text(file, translator, ref, line):
    _, body = _split(script._TEXTS_DIR / file)

    stanzas, _ = eee.parse_stanza_translations(body, ref_prefix="### Odyss. ")

    assert line in stanzas[translator][ref]


# --- Σπανούδης: fragments of a Cypriot-dialect translation that is in copyright ---
# The section holds fragments only (the translator's permission covers fragments), assigned by sense to the lessons'
# stanzas. The edition has no online copy to compare against, so these tests pin the shape: the stanza split, the
# verse ranges, clean text, and that a gloss sits right after the verse it explains.

_SPANOUDIS_FRAGMENTS = {"Α'": (1, 30), "Ι'": (19, 166)}  # verses of the edition's own numbering the section may hold
_SPANOUDIS_WORK_VERSES = 11076
_SPANOUDIS_DRIFTS = {
    "footnote_mark": ("Μούσα, τον πολλοπάητον άντραν", "Μούσα, τον πολλοπάητον[^a1] άντραν"),
    "verse_number": ("Μούσα, τον πολλοπάητον άντραν", "1. Μούσα, τον πολλοπάητον άντραν"),
    "book_marker": ("τούτος καμπόσους τόπους,", "τούτος καμπόσους τόπους, *(5)*"),
    "latin_v": ("χαμαί κάτω τραβούμεν", "χαμαί κάτω τραβούμεv"),
    "cyrillic_letter": ("Εγιώ 'μαι του Λαέρτη", "Εгιώ 'μαι του Λαέρτη"),
    "extra_verse": ("πάντα πρασινισμένος.\n", "πάντα πρασινισμένος.\nμια στίχος που δεν υπάρχει\n"),
    "gap": ("στ. 25–28 -->", "στ. 26–28 -->"),
    "divided_couplet": ("<!-- Ραψωδία Ι' στ. 29–30 -->", "<!-- Ραψωδία Ι' στ. 29–29 -->"),
    "gloss_on_wrong_verse": ("<!-- gloss: πολλοπάητον — ", "<!-- gloss: αλλοπάητον — "),
    "gloss_without_meaning": ("<!-- gloss: άβλαβος — άνευ βλάβης -->", "<!-- gloss: άβλαβος -->"),
    "no_range_comment": ("<!-- Ραψωδία Α' στ. 1–8 -->\n", ""),
}


def _spanoudis_section(text: str) -> str:
    """The `## Σπανούδης` section of a translations_el.md body, up to its closing `---`."""
    return re.search(r"(?ms)^## Σπανούδης\n.*?(?=^---$)", text).group(0)


def _spanoudis_problems(section: str) -> list:
    """What the Σπανούδης section must satisfy; [] when it does."""
    problems = []
    spans = {rhapsody: [] for rhapsody in _SPANOUDIS_FRAGMENTS}
    verse_total = 0
    for block in re.split(r"(?m)^### Odyss\. ", section)[1:]:
        ref, _, text = block.partition("\n")
        match = re.search(r"(?m)^<!-- Ραψωδία (Α'|Ι') στ\. (\d+)–(\d+) -->$", text)
        if not match:
            problems.append(f"{ref}: no verse-range comment")
            continue
        rhapsody, first, last = match.group(1), int(match.group(2)), int(match.group(3))
        spans[rhapsody].append((first, last))
        lines = [line for line in text.splitlines() if line.strip()]
        verses = eee.strip_comment_lines("\n".join(lines)).splitlines()
        verse_total += len(verses)
        if len(verses) != last - first + 1:
            problems.append(f"{ref}: {len(verses)} verse lines for στ. {first}–{last}")
        if first % 2 == 0 or last % 2 == 1:  # a rhymed couplet is an odd verse and the even verse after it
            problems.append(f"{ref}: στ. {first}–{last} divides a couplet")
        for verse in verses:
            if re.match(r"\d+\.", verse) or "*(" in verse or "[^" in verse or "####" in verse:
                problems.append(f"{ref}: edition markup left in {verse!r}")
            if re.search(r"[A-Za-zЀ-ӿ]", verse):
                problems.append(f"{ref}: Latin or Cyrillic letter in {verse!r}")
        for before, line in zip(lines, lines[1:]):
            if not line.startswith("<!-- gloss:"):
                continue
            match = re.fullmatch(r"<!-- gloss: (.+) -->", line)
            for part in match.group(1).split(" · ") if match else []:
                word, _, meaning = part.partition(" — ")
                if not meaning.strip() or word not in before:
                    problems.append(f"{ref}: gloss {part!r} lacks a meaning, or its word is not in the verse above")
            if not match or before.startswith("<!--"):
                problems.append(f"{ref}: malformed gloss line {line!r}")
    for rhapsody, (start, end) in _SPANOUDIS_FRAGMENTS.items():
        found = spans[rhapsody]
        if not found or found[0][0] != start or found[-1][1] != end:
            problems.append(f"{rhapsody}: blocks do not run from στ. {start} to στ. {end}")
        for (_, previous_last), (next_first, _) in zip(found, found[1:]):
            if next_first != previous_last + 1:
                problems.append(f"{rhapsody}: στ. {previous_last} is followed by στ. {next_first}")
    if verse_total > 0.02 * _SPANOUDIS_WORK_VERSES:  # fragments only: the permission does not cover the work
        problems.append(f"{verse_total} verses is more than fragments of an {_SPANOUDIS_WORK_VERSES}-verse work")
    return problems


def _spanoudis_el_file():
    frontmatter, body = _split(script._TEXTS_DIR / "translations_el.md")
    return frontmatter, body


def test_spanoudis_follows_the_lessons_stanza_split():
    """Every lesson stanza (the split interlinear_el already matches, from each lesson's greek.md) is an exact key:
    lessons 2026_06_01 and 2026_06_15 look a stanza up with a plain d.get(ref), with no containing-range fallback."""
    _, body = _spanoudis_el_file()

    stanzas, _ = eee.parse_stanza_translations(body, ref_prefix="### Odyss. ")

    assert list(stanzas["Σπανούδης"]) == list(stanzas["interlinear_el"])
    assert len(stanzas["Σπανούδης"]) == 39  # 4 (I.1-21) + 35 (IX.19-180)


def test_spanoudis_section_meets_its_shape_rules():
    _, body = _spanoudis_el_file()

    assert _spanoudis_problems(_spanoudis_section(body)) == []
    assert _spanoudis_problems(script._SPANOUDIS) == []


@pytest.mark.parametrize("kind", sorted(_SPANOUDIS_DRIFTS))
def test_spanoudis_guard_rejects_drifted_copies(kind):
    old, new = _SPANOUDIS_DRIFTS[kind]
    section = script._SPANOUDIS
    assert section.count(old) == 1, f"{kind}: the drift anchor must occur once"

    assert _spanoudis_problems(section.replace(old, new)) != []


def test_spanoudis_gloss_strips_away_and_is_kept_in_the_raw_text():
    """The edition's margin glossary is data, not verse: strip_comment_lines (what the lessons apply) removes it."""
    _, body = _spanoudis_el_file()
    stanzas, _ = eee.parse_stanza_translations(body, ref_prefix="### Odyss. ")

    raw = stanzas["Σπανούδης"]["I.1–5"]
    assert "<!-- gloss: πολλοπάητον — παμπόνηρος, πανέξυπνος -->" in raw
    assert "gloss" not in eee.strip_comment_lines(raw)
    assert "<!--" not in eee.strip_comment_lines(raw)


def test_spanoudis_description_and_provenance_state_what_was_reproduced():
    """A lesson shows the description beside the text; the provenance comment is where a reader learns that the
    translation is in copyright, that these are fragments, who vouches for the permission, and how they were cut."""
    frontmatter, body = _spanoudis_el_file()
    stanzas, descriptions = eee.parse_stanza_translations(body, ref_prefix="### Odyss. ")

    assert "κυπριακή διάλεκτος" in descriptions["Σπανούδης"]
    assert "Α' στ. 1-30" in descriptions["Σπανούδης"] and "Ι' στ. 19-166" in descriptions["Σπανούδης"]
    provenance = _spanoudis_section(body).splitlines()[2]
    assert provenance.startswith("<!-- Άκης Σπανούδης, Ομήρου Οδύσσεια")
    for phrase in ("In copyright", "the maintainer states that the translator permitted the use of fragments in the maintainer's demo",
                   "the rest of the translation is NOT reproduced", "a couplet is never divided"):
        assert phrase in provenance
    assert frontmatter["translators"] == ["Πολυλάς", "Σπανούδης", "interlinear_el", "Καζαντζάκης/Κακριδής (reference only)"]
    assert "tr-spanoudis2021" in {source["id"] for source in frontmatter["sources"]}
