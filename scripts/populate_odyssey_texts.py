"""One-off (re-runnable) script that assembles texts/odyssey/*.md from
hand-extracted translator sections. See docs in
~/work/greek/EEE/plans/superpowers/specs/2026-09-07-odyssey-translations-corpus-design.md
for why this content lives here rather than being live-queried.

Each *_SECTION constant below is copied byte-for-byte from
created_with_eee's abandoned `translations` branch via `git show` -- never
retyped by hand. Re-run this script whenever a section needs updating;
okf.write()'s idempotency means re-running with unchanged content is a
harmless no-op.
"""

from pathlib import Path

from okfbuild.concepts.literary_translation import build
from okfbuild.okf import Source, write

_REPO_ROOT = Path(__file__).parent.parent
_TEXTS_DIR = _REPO_ROOT / "texts" / "odyssey"

# Copied verbatim via:
#   git -C ~/work/greek/git/codeberg.org/EEE-project/created_with_eee \
#     show translations:odyssey/2026_06_01/translations_en.md
# -- the "## Pope" section only (up to, not including, "## Lattimore").
_POPE_SECTION = """\
## Pope

<!-- Pope A. The Odyssey of Homer. London, 1725–1726 · https://en.wikisource.org/wiki/Odyssey_(Pope) -->
<!-- **Pope, 1725–26** · [wikisource.org ↗](https://en.wikisource.org/wiki/Odyssey_(Pope)) · eng., heroic couplets · elegant 18th-c. rhetorical style · poetic adaptation; long considered the standard English version -->

### Odyss. I.1–5

The man, for wisdom's various arts renown'd,
Long exercis'd in woes, O Muse! resound;
Who, when his arms had wrought the destin'd fall
Of sacred Troy, and raz'd her heav'n-built wall,
Wand'ring from clime to clime, observant stray'd,
Their manners noted, and their states survey'd,
On stormy seas unnumber'd toils he bore,
Safe with his friends to gain his natal shore.

### Odyss. I.6–10

Vain toils! their impious folly dar'd to prey
On herds devoted to the god of day;
The god vindictive doom'd them then to die,
For sacrilegious crimes — nor could his care
Preserve from death a race of men so bold.
Begin from hence, and all the truth unfold.

### Odyss. I.11–15

Now all the rest who 'scap'd the cruel fate
In safety reach'd their long-desir'd retreat.
Him, yet alone from Ithaca detain'd,
Calypso long in her soft arms contain'd;
Who, in her grottoes, fond of him remain'd,
Desiring, fain would make the hero stay.

### Odyss. I.16–21

But when the years, by great Jove's sister's will,
Had fill'd their number on the rolling year,
When Ithaca at last was destin'd nigh,
New toils await him, and new dangers nigh.
The gods relent, and all except the god
Of ocean, who relentless still pursu'd
With hatred fierce divine Ulysses' way,
Till safe he landed on his native shore.

"""

# Copied verbatim via:
#   git -C ~/work/greek/git/codeberg.org/EEE-project/created_with_eee \
#     show translations:odyssey/2026_06_15/translations_en.md
# -- the "## Murray" section only (up to, not including, "## Lattimore").
_MURRAY_SECTION = """\
## Murray

<!-- Murray A. T. The Odyssey. London, Heinemann, 1919 · https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0136 -->
<!-- **Murray, 1919** · [perseus.tufts.edu ↗](https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0136) · eng., prose · Loeb Classical Library · close to literal; parallel Greek text on Perseus -->

### Odyss. IX.19–24

I am Odysseus, son of Laertes, who am known among men
for all manner of wiles, and my fame reaches unto heaven.
And I dwell in clear-seen Ithaca, wherein is a mountain Neriton,
with trembling leaves, conspicuous from afar;
and round it lie many islands hard by one another,
Dulichium and Same and wooded Zacynthus.

### Odyss. IX.25–28

Ithaca itself lies low, furthest up the sea toward the darkness,
but those others lie apart toward the dawn and the sun —
a rugged isle, but a good nurse of young men;
and for myself I can see nothing sweeter than a man's own country.

### Odyss. IX.29–33

Verily Calypso, the beautiful goddess, kept me with her in her hollow caves,
yearning for me to be her husband;
and likewise, too, Circe of Aeaea, the crafty,
kept me in her halls, yearning for me to be her husband.
But never did they persuade the heart in my breast.

### Odyss. IX.34–38

So true it is that nothing is sweeter than a man's own land and his parents,
even though one dwell in a rich house in a foreign land,
far from his parents.
But come, let me tell you of my much-troubled homeward voyage,
which Zeus appointed for me as I came from Troy.

"""


def populate_translations_en() -> None:
    body = _POPE_SECTION.rstrip("\n") + "\n\n---\n\n" + _MURRAY_SECTION.rstrip("\n") + "\n"
    sources = [
        Source(id="tr-pope", resource="https://en.wikisource.org/wiki/Odyssey_(Pope)",
               title="The Odyssey of Homer", author="Alexander Pope"),
        Source(id="tr-murray1919", resource="https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0136",
               title="The Odyssey", author="A. T. Murray"),
        Source(id="grc-murray1919", resource="https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0136",
               title="Perseus Digital Library Greek text (Murray ed.)", author="ed. A. T. Murray"),
    ]
    concept = build(
        work="Odyssey", passage="I.1-21, IX.19-38", language="en",
        translators=["Pope", "Murray"], body=body, sources=sources,
    )
    write(concept, _TEXTS_DIR / "translations_en.md")


if __name__ == "__main__":
    populate_translations_en()
