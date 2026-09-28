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
_POPE_I = """\
## Pope

<!-- Pope A. The Odyssey of Homer. London, 1725–1726 · https://en.wikisource.org/wiki/Odyssey_(Pope) -->
<!-- **Pope, 1725–26** · [wikisource.org ↗](https://en.wikisource.org/wiki/Odyssey_(Pope)) (archived 22.09.2026: https://web.archive.org/web/20260922110929/https://en.wikisource.org/wiki/Odyssey_(Pope)) · eng., heroic couplets · elegant 18th-c. rhetorical style · poetic adaptation; long considered the standard English version -->

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

# NOT from the abandoned translations branch -- that branch never had a
# Pope rendering of Book IX (confirmed: `git show translations:odyssey/
# 2026_06_15/translations_en.md` has only Murray + Lattimore). Sourced
# fresh from Wikisource (https://en.wikisource.org/wiki/Odyssey_(Pope)/
# Book_IX, the same edition/page already cited above for Book I), fetched
# directly (not via WebFetch's summarizer, which paraphrases rather than
# quoting verbatim) and copied byte-for-byte except stripping the source's
# own <br/> line-break markup. Stanza boundaries are sense-unit splits
# (Pope's couplets don't line up 1:1 with the Greek either, an already-
# accepted property of this translator -- see the design doc's "why the
# flex-column display doesn't require line-alignment"). One reading not
# independently re-verified against a second source: "none no lovely to
# my sight" (stanza 2) -- almost certainly a Wikisource transcription slip
# for "none so lovely", but per this corpus's own copy-what-the-source-
# says convention, left exactly as the source has it rather than silently
# "corrected".
_POPE_IX = """\
## Pope

### Odyss. IX.19–24

"Know first the man (though now a wretch distress'd)
Who hopes thee, monarch, for his future guest.
Behold Ulysses! no ignoble name,
Earth sounds my wisdom and high heaven my fame.

"My native soil is Ithaca the fair,
Where high Neritus waves his woods in air;
Dulichium, Same and Zaccynthus crown'd
With shady mountains spread their isles around.

### Odyss. IX.25–28

(These to the north and night's dark regions run,
Those to Aurora and the rising sun).
Low lies our isle, yet bless'd in fruitful stores;
Strong are her sons, though rocky are her shores;
And none, ah none no lovely to my sight,
Of all the lands that heaven o'erspreads with light.

### Odyss. IX.29–33

In vain Calypso long constrained my stay,
With sweet, reluctant, amorous delay;
With all her charms as vainly Circe strove,
And added magic to secure my love.
In pomps or joys, the palace or the grot,
My country's image never was forgot;
My absent parents rose before my sight,
And distant lay contentment and delight.

### Odyss. IX.34–38

"Hear, then, the woes which mighty Jove ordain'd
To wait my passage from the Trojan land.

### Odyss. IX.39–46 (equivalent passage)

The winds from Ilion to the Cicons' shore,
Beneath cold Ismarus our vessels bore.
We boldly landed on the hostile place,
And sack'd the city, and destroy'd the race,
Their wives made captive, their possessions shared,
And every soldier found a like reward
I then advised to fly; not so the rest,
Who stay'd to revel, and prolong the feast:
The fatted sheep and sable bulls they slay,
And bowls flow round, and riot wastes the day.

### Odyss. IX.47–55 (equivalent passage)

Meantime the Cicons, to their holds retired,
Call on the Cicons, with new fury fired;
With early morn the gather'd country swarms,
And all the continent is bright with arms;
Thick as the budding leaves or rising flowers
O'erspread the land, when spring descends in showers:
All expert soldiers, skill'd on foot to dare,
Or from the bounding courser urge the war.
Now fortune changes (so the Fates ordain);
Our hour was come to taste our share of pain.
Close at the ships the bloody fight began,
Wounded they wound, and man expires on man.
Long as the morning sun increasing bright
O'er heaven's pure azure spreads the glowing light,
Promiscuous death the form of war confounds,
Each adverse battle gored with equal wounds;
But when his evening wheels o'erhung the main,
Then conquest crown'd the fierce Ciconian train.

### Odyss. IX.56–66 (equivalent passage)

Six brave companions from each ship we lost,
The rest escape in haste, and quit the coast,
With sails outspread we fly the unequal strife,
Sad for their loss, but joyful of our life.
Yet as we fled, our fellows' rites we paid,
And thrice we call'd on each unhappy shade,

### Odyss. IX.67–75 (equivalent passage)

Meanwhile the god, whose hand the thunder forms,
Drives clouds on clouds, and blackens heaven with storms:
Wide o'er the waste the rage of Boreas sweeps,
And night rush'd headlong on the shaded deeps.
Now here, now there, the giddy ships are borne,
And all the rattling shrouds in fragments torn.
We furl'd the sail, we plied the labouring oar,
Took down our masts, and row'd our ships to shore.
Two tedious days and two long nights we lay,
O'erwatch'd and batter'd in the naked bay.

### Odyss. IX.76–81 (equivalent passage)

But the third morning when Aurora brings,
We rear the masts, we spread the canvas wings;
Refresh'd and careless on the deck reclined,
We sit, and trust the pilot and the wind.
Then to my native country had I sail'd:
But, the cape doubled, adverse winds prevail'd.
Strong was the tide, which by the northern blast
Impell'd, our vessels on Cythera cast,

### Odyss. IX.82–90 (equivalent passage)

Nine days our fleet the uncertain tempest bore
Far in wide ocean, and from sight of shore:
The tenth we touch'd, by various errors toss'd,
The land of Lotus and the flowery coast.
We climb'd the beach, and springs of water found,
Then spread our hasty banquet on the ground.
Three men were sent, deputed from the crew
(A herald one) the dubious coast to view,
And learn what habitants possess'd the place.
They went, and found a hospitable race:
Not prone to ill, nor strange to foreign guest,
They eat, they drink, and nature gives the feast

### Odyss. IX.91–104 (equivalent passage)

The trees around them all their food produce:
Lotus the name: divine, nectareous juice!
(Thence call'd Lo'ophagi); which whose tastes,
Insatiate riots in the sweet repasts,
Nor other home, nor other care intends,
But quits his house, his country, and his friends.
The three we sent, from off the enchanting ground
We dragg'd reluctant, and by force we bound.
The rest in haste forsook the pleasing shore,
Or, the charm tasted, had return'd no more.
Now placed in order on their banks, they sweep
The sea's smooth face, and cleave the hoary deep:
With heavy hearts we labour through the tide,
To coasts unknown, and oceans yet untried.

### Odyss. IX.105–115 (equivalent passage)

The land of Cyclops first, a savage kind,
Nor tamed by manners, nor by laws confined:
Untaught to plant, to turn the glebe, and sow,
They all their products to free nature owe:
The soil, untill'd, a ready harvest yields,
With wheat and barley wave the golden fields;
Spontaneous wines from weighty clusters pour,
And Jove descends in each prolific shower,
By these no statues and no rights are known,
No council held, no monarch fills the throne;
But high on hills, or airy cliffs, they dwell,
Or deep in caves whose entrance leads to hell.
Each rules his race, his neighbour not his care,
Heedless of others, to his own severe.

### Odyss. IX.116–129 (equivalent passage)

Opposed to the Cyclopean coast, there lay
An isle, whose hill their subject fields survey;
Its name Lachaea, crown'd with many a grove,
Where savage goats through pathless thickets rove:
No needy mortals here, with hunger bold,
Or wretched hunters through the wintry cold
Pursue their flight; but leave them safe to bound
From hill to hill, o'er all the desert ground.
Nor knows the soil to feed the fleecy care,
Or feels the labours of the crooked share;
But uninhabited, untill'd, unsown,
It lies, and breeds the bleating goat alone.
For there no vessel with vermilion prore,
Or bark of traffic, glides from shore to shore;
The rugged race of savages, unskill'd
The seas to traverse, or the ships to build,
Gaze on the coast, nor cultivate the soil,
Unlearn'd in all the industrious art of toil,
Yet here all produces and all plants abound,
Sprung from the fruitful genius of the ground;
Fields waving high with heavy crops are seen,
And vines that flourish in eternal green,
Refreshing meads along the murmuring main,
And fountains streaming down the fruitful plain.

### Odyss. IX.130–145 (equivalent passage)

A port there is, inclosed on either side,
Where ships may rest, unanchor'd and untied;
Till the glad mariners incline to sail,
And the sea whitens with the rising gale,
High at the head, from out the cavern'd rock,
In living rills a gushing fountain broke:
Around it, and above, for ever green,
The busy alders form'd a shady scene;
Hither some favouring god, beyond our thought,
Through all surrounding shade our navy brought;
For gloomy night descended on the main,
Nor glimmer'd Phoebe in the ethereal plain:

### Odyss. IX.146–160 (equivalent passage)

But all unseen the clouded island lay,
And all unseen the surge and rolling sea,
Till safe we anchor'd in the shelter'd bay:
Our sails we gather'd, cast our cables o'er,
And slept secure along the sandy shore.
Soon as again the rosy morning shone,
Reveal'd the landscape and the scene unknown,
With wonder seized, we view the pleasing ground,
And walk delighted, and expatiate round.
Roused by the woodland nymphs at early dawn,
The mountain goats came bounding o'er the lawn:
In haste our fellows to the ships repair,
For arms and weapons of the sylvan war;
Straight in three squadrons all our crew we part,
And bend the bow, or wing the missile dart;
The bounteous gods afford a copious prey,
And nine fat goats each vessel bears away:
The royal bark had ten. Our ships complete
We thus supplied (for twelve were all the fleet).

### Odyss. IX.161–169 (equivalent passage)

Here, till the setting sun roll'd down the light,
We sat indulging in the genial rite:
Nor wines were wanting; those from ample jars
We drain'd, the prize of our Ciconian wars.
The land of Cyclops lay in prospect near:
The voice of goats and bleating flocks we hear,
And from their mountains rising smokes appear.

### Odyss. IX.170–180 (equivalent passage)

Now sunk the sun, and darkness cover'd o'er
The face of things: along the sea-beat shore
Satiate we slept: but, when the sacred dawn
Arising glitter'd o'er the dewy lawn,
I call'd my fellows, and these words address'd
'My dear associates, here indulge your rest;
While, with my single ship, adventurous, I
Go forth, the manners of you men to try;
Whether a race unjust, of barbarous might,
Rude and unconscious of a stranger's right;
Or such who harbour pity in their breast,
Revere the gods, and succour the distress'd,'

This said, I climb'd my vessel's lofty side;
My train obey'd me, and the ship untied.
In order seated on their banks, they sweep
Neptune's smooth face, and cleave the yielding deep.

"""

# Copied verbatim via:
#   git -C ~/work/greek/git/codeberg.org/EEE-project/created_with_eee \
#     show translations:odyssey/2026_06_15/translations_en.md
# -- the "## Murray" section only (up to, not including, "## Lattimore").
_MURRAY_IX = """\
## Murray

<!-- Murray A. T. The Odyssey. London, Heinemann, 1919 · https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0136 -->
<!-- **Murray, 1919** · [perseus.tufts.edu ↗](https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0136) (archived 22.09.2026: https://web.archive.org/web/20260922111108/https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0136) · eng., prose · Loeb Classical Library · close to literal; parallel Greek text on Perseus -->

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

### Odyss. IX.39–42

"From Ilios the wind bore me and brought me to the Cicones,
to Ismarus. There I sacked the city and slew the men; and from the city we took their wives and great store of treasure, and divided them among us, that so far as lay in me no man might go defrauded of an equal share.

### Odyss. IX.43–46

Then verily I gave command that we should flee with swift foot, but the others in their great folly did not hearken. But there much wine was drunk, and many sheep they slew by the shore, and sleek kine of shambling gait.

### Odyss. IX.47–50

Meanwhile the Cicones went and called to other Cicones who were their neighbors, at once more numerous and braver than they—men that dwelt inland and were skilled at fighting with their foes from chariots, and, if need were, on foot.

### Odyss. IX.51–55

So they came in the morning, as thick as leaves or flowers spring up in their season; and then it was that an evil fate from Zeus beset us luckless men, that we might suffer woes full many. They set their battle in array and fought by the swift ships, and each side hurled at the other with bronze-tipped spears.

### Odyss. IX.56–61

Now as long as it was morn and the sacred day was waxing, so long we held our ground and beat them off, though they were more than we. But when the sun turned to the time for the unyoking of oxen, then the Cicones prevailed and routed the Achaeans, and six of my well-greaved comrades perished from each ship; but the rest of us escaped death and fate.

### Odyss. IX.62–66

"Thence we sailed on, grieved at heart, glad to have escaped from death, though we had lost our dear comrades; nor did I let my curved ships pass on till we had called thrice on each of those hapless comrades of ours who died on the plain, cut down by the Cicones.

### Odyss. IX.67–71

But against our ships Zeus, the cloud-gatherer, roused the North Wind with a wondrous tempest, and hid with clouds the land and the sea alike, and night rushed down from heaven. Then the ships were driven headlong, and their sails were torn to shreds by the violence of the wind.

### Odyss. IX.72–75

So we lowered the sails and stowed them aboard, in fear of death, and rowed the ships hurriedly toward the land. There for two nights and two days continuously we lay, eating our hearts for weariness and sorrow.

### Odyss. IX.76–78

But when now fair-tressed Dawn brought to its birth the third day, we set up the masts and hoisted the white sails, and took our seats, and the wind and the helmsmen steered the ships.

### Odyss. IX.79–81

And now all unscathed should I have reached my native land, but the wave and the current and the North Wind beat me back as I was rounding Malea, and drove me from my course past Cythera.

### Odyss. IX.82–86

"Thence for nine days' space I was borne by direful winds over the teeming deep; but on the tenth we set foot on the land of the Lotus-eaters, who eat a flowery food. There we went on shore and drew water, and straightway my comrades took their meal by the swift ships.

### Odyss. IX.87–90

But when we had tasted food and drink, I sent forth some of my comrades to go and learn who the men were, who here ate bread upon the earth; two men I chose, sending with them a third as a herald.

### Odyss. IX.91–93

So they went straightway and mingled with the Lotus-eaters, and the Lotus-eaters did not plan death for my comrades, but gave them of the lotus to taste.

### Odyss. IX.94–97

And whosoever of them ate of the honey-sweet fruit of the lotus, had no longer any wish to bring back word or to return, but there they were fain to abide among the Lotus-eaters, feeding on the lotus, and forgetful of their homeward way.

### Odyss. IX.98–104

These men, therefore, I brought back perforce to the ships, weeping, and dragged them beneath the benches and bound them fast in the hollow ships; and I bade the rest of my trusty comrades to embark with speed on the swift ships, lest perchance anyone should eat of the lotus and forget his homeward way. So they went on board straightway and sat down upon the benches, and sitting well in order smote the grey sea with their oars.

### Odyss. IX.105–111

"Thence we sailed on, grieved at heart, and we came to the land of the Cyclopes, an overweening and lawless folk, who, trusting in the immortal gods, plant nothing with their hands nor plough; but all these things spring up for them without sowing or ploughing, wheat, and barley, and vines, which bear the rich clusters of wine, and the rain of Zeus gives them increase.

### Odyss. IX.112–115

Neither assemblies for council have they, nor appointed laws, but they dwell on the peaks of lofty mountains in hollow caves, and each one is lawgiver to his children and his wives, and they reck nothing one of another.

### Odyss. IX.116–121

"Now there is a level isle that stretches aslant outside the harbor, neither close to the shore of the land of the Cyclopes, nor yet far off, a wooded isle. Therein live wild goats innumerable, for the tread of men scares them not away, nor are hunters wont to come thither, men who endure toils in the woodland as they course over the peaks of the mountains.

### Odyss. IX.122–124

Neither with flocks is it held, nor with ploughed lands, but unsown and untilled all the days it knows naught of men, but feeds the bleating goats.

### Odyss. IX.125–129

For the Cyclopes have at hand no ships with vermilion cheeks, nor are there ship-wrights in their land who might build them well-benched ships, which should perform all their wants, passing to the cities of other folk, as men often cross the sea in ships to visit one another—

### Odyss. IX.130–133

craftsmen, who would have made of this isle also a fair settlement. For the isle is nowise poor, but would bear all things in season. In it are meadows by the shores of the grey sea, well-watered meadows and soft, where vines would never fail,

### Odyss. IX.134–139

and in it level ploughland, whence they might reap from season to season harvests exceeding deep, so rich is the soil beneath; and in it, too, is a harbor giving safe anchorage, where there is no need of moorings, either to throw out anchor-stones or to make fast stern cables, but one may beach one's ship and wait until the sailors' minds bid them put out, and the breezes blow fair.

### Odyss. IX.140–141

Now at the head of the harbor a spring of bright water flows forth from beneath a cave, and round about it poplars grow.

### Odyss. IX.142–145

Thither we sailed in, and some god guided us through the murky night; for there was no light to see, but a mist lay deep about the ships and the moon showed no light from heaven, but was shut in by clouds.

### Odyss. IX.146–151

Then no man's eyes beheld that island, nor did we see the long waves rolling on the beach, until we ran our well-benched ships on shore. And when we had beached the ships we lowered all the sails and ourselves went forth on the shore of the sea, and there we fell asleep and waited for the bright Dawn.

### Odyss. IX.152–155

"As soon as early Dawn appeared, the rosy-fingered, we roamed throughout the isle marvelling at it; and the nymphs, the daughters of Zeus who bears the aegis, roused the mountain goats, that my comrades might have whereof to make their meal.

### Odyss. IX.156–160

Straightway we took from the ships our curved bows and long javelins, and arrayed in three bands we fell to smiting; and the god soon gave us game to satisfy our hearts. The ships that followed me were twelve, and to each nine goats fell by lot, but for me alone they chose out ten.

### Odyss. IX.161–165

"So then all day long till set of sun we sat feasting on abundant flesh and sweet wine. For not yet was the red wine spent from out our ships, but some was still left; for abundant store had we drawn in jars for each crew when we took the sacred citadel of the Cicones.

### Odyss. IX.166–169

And we looked across to the land of the Cyclopes, who dwelt close at hand, and marked the smoke, and the voice of men, and of the sheep, and of the goats. But when the sun set and darkness came on, then we lay down to rest on the shore of the sea.

### Odyss. IX.170–176

And as soon as early Dawn appeared, the rosy-fingered, I called my men together and spoke among them all: "‘Remain here now, all the rest of you, my trusty comrades, but I with my own ship and my own company will go and make trial of yonder men, to learn who they are, whether they are cruel, and wild, and unjust, or whether they love strangers and fear the gods in their thoughts.’

### Odyss. IX.177–180

"So saying, I went on board the ship and bade my comrades themselves to embark, and to loose the stern cables. So they went on board straightway and sat down upon the benches, and sitting well in order smote the grey sea with their oars.

"""

# NOT from the abandoned translations branch -- that branch never had a
# Murray rendering of Book I (confirmed: `git show translations:odyssey/
# 2026_06_01/translations_en.md` has only Pope + Lattimore). Sourced fresh
# from the Internet Archive's OCR of the actual 1919 Heinemann/Harvard
# volume (archive.org/stream/odysseymurray01homeuoft/
# odysseymurray01homeuoft_djvu.txt), the same edition already cited above
# for Book IX -- used in place of Perseus's own page directly, since
# Perseus loads the English translation via client-side JS the fetch
# tooling available here can't execute. Two clear OCR artifacts corrected
# ("Tet: me" -> "Tell me", "own felk" -> "own folk"); wording otherwise
# unchanged from the source. Line breaks, however, are NOT the source's
# own (its page-width wrapping includes mid-word hyphens like "com-\\nrades",
# "Ca-\\nlypso" -- printing artifacts, not part of the prose translation
# itself) -- re-flowed at clause boundaries instead, matching the visual
# rhythm _MURRAY_IX above already established (short line breaks are this
# corpus's own presentational convention for Murray's prose, not something
# Murray's original publication imposes either way -- a prose translation
# has no metrically-required line length the way Pope's verse does).
# First found as a real, visible bug: Book I's stanzas originally shipped
# as one dense unbroken line each, next to Book IX's already-short-lined
# stanzas -- inconsistent under the same "## Murray" header.
_MURRAY_I = """\
## Murray

### Odyss. I.1–5

Tell me, O Muse, of the man of many devices,
who wandered full many ways after he had sacked
the sacred citadel of Troy. Many were the men
whose cities he saw and whose mind he learned, aye,
and many the woes he suffered in his heart upon the sea,
seeking to win his own life and the return of his comrades.

### Odyss. I.6–10

Yet even so he saved not his comrades, though he desired it sore,
for through their own blind folly they perished—fools, who devoured
the kine of Helios Hyperion; but he took from them the day of their returning.
Of these things, goddess, daughter of Zeus, beginning where thou wilt, tell thou even unto us.

### Odyss. I.11–15

Now all the rest, as many as had escaped sheer destruction,
were at home, safe from both war and sea, but Odysseus alone,
filled with longing for his return and for his wife,
did the queenly nymph Calypso, that bright goddess,
keep back in her hollow caves, yearning that he should be her husband.

### Odyss. I.16–21

But when, as the seasons revolved, the year came
in which the gods had ordained that he should return home to Ithaca,
not even there was he free from toils, even among his own folk.
And all the gods pitied him save Poseidon;
but he continued to rage unceasingly against godlike Odysseus
until at length he reached his own land.

"""


# Cited identically by all four populate_*() functions below -- the same
# Greek source-text edition underlies every language's translations/
# interlinear file.
_GRC_MURRAY1919_SOURCE = Source(
    id="grc-murray1919", resource="https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0136",
    title="Perseus Digital Library Greek text (Murray ed.)", author="ed. A. T. Murray",
)


def _strip_header(section: str) -> str:
    lines = section.splitlines()
    out = []
    skipping_header = True
    for line in lines:
        if skipping_header and (
            line.startswith("## ") or line.startswith("<!--") or not line.strip()
        ):
            continue
        skipping_header = False
        out.append(line)
    return "\n".join(out).strip("\n")


# New 2026-09-14, sourced from Project Gutenberg ebook #48895 (public
# domain, d. 1634). Not extended past IX.38 (unlike Pope/Murray/
# interlinear_en) -- added alongside the IX.39-180 extension but scoped
# to match its own original addition, not retroactively extended.
_CHAPMAN = """\
## Chapman

<!-- Chapman G. Homer's Odysses. London, 1614-1615 · https://www.gutenberg.org/ebooks/48895 -->
<!-- **Chapman, 1614/15** · [gutenberg.org ↗](https://www.gutenberg.org/ebooks/48895) · eng., "fourteener" couplets (iambic heptameter) · Elizabethan/Jacobean idiom · first complete English Odyssey; public domain (d. 1634). Chapman's own line divisions don't correspond 1:1 to the Greek line numbers below -- headings mark the equivalent passage, not an exact line match; footnote markers from the Gutenberg edition are omitted. -->

### Odyss. I.1–5 (equivalent passage)

The man, O Muse, inform, that many a way
Wound with his wisdom to his wished stay;
That wander'd wondrous far, when he the town
Of sacred Troy had sack'd and shiver'd down;
The cities of a world of nations,
With all their manners, minds, and fashions,
He saw and knew; at sea felt many woes,
Much care sustain'd, to save from overthrows
Himself and friends in their retreat for home;

### Odyss. I.6–10 (equivalent passage)

But so their fates he could not overcome,
Though much he thirsted it. O men unwise,
They perish'd by their own impieties!
That in their hunger's rapine would not shun
The oxen of the lofty-going Sun,
Who therefore from their eyes the day bereft
Of safe return. These acts, in some part left,
Tell us, as others, deified Seed of Jove.

### Odyss. I.11–15 (equivalent passage)

Now all the rest that austere death outstrove
At Troy's long siege at home safe anchor'd are,
Free from the malice both of sea and war;
Only Ulysses is denied access
To wife and home. The grace of Goddesses,
The rev'rend nymph Calypso, did detain
Him in her caves, past all the race of men
Enflam'd to make him her lov'd lord and spouse.

### Odyss. I.16–21 (equivalent passage)

And when the Gods had destin'd that his house,
Which Ithaca on her rough bosom bears,
(The point of time wrought out by ambient years)
Should be his haven, Contention still extends
Her envy to him, ev'n amongst his friends.
All Gods took pity on him; only he,
That girds earth in the cincture of the sea,
Divine Ulysses ever did envy,
And made the fix'd port of his birth to fly.

### Odyss. IX.19–24 (equivalent passage)

I am Ulysses Laertiades,
The fear of all the world for policies,
For which my facts as high as heav'n resound.
I dwell in Ithaca, earth's most renown'd,
All over-shadow'd with the shake-leaf hill,
Tree-fam'd Neritus; whose near confines fill
Islands a number, well-inhabited,
That under my observance taste their bread;
Dulichius, Samos, and the full-of-food
Zacynthus, likewise grac'd with store of wood.

### Odyss. IX.25–28 (equivalent passage)

But Ithaca, though in the seas it lie,
Yet lies she so aloft she casts her eye
Quite over all the neighbour continent;
Far northward situate, and, being lent
But little favour of the morn and sun,
With barren rocks and cliffs is over-run;
And yet of hardy youths a nurse of name;
Nor could I see a soil, where'er I came,
More sweet and wishful. Yet, from hence was I

### Odyss. IX.29–33 (equivalent passage)

Withheld with horror by the Deity,
Divine Calypso, in her cavy house,
Enflam'd to make me her sole lord and spouse.
Circe Ææa too, that knowing dame,
Whose veins the like affections did enflame,
Detain'd me likewise. But to neither's love
Could I be tempted; which doth well approve,

### Odyss. IX.34–38 (equivalent passage)

Nothing so sweet is as our country's earth,
And joy of those from whom we claim our birth.
Though roofs far richer we far off possess,
Yet, from our native, all our more is less.
To which as I contended, I will tell
The much-distress-conferring facts that fell
By Jove's divine prevention, since I set
From ruin'd Troy my first foot in retreat.
"""

_FITZGERALD_REF = """\
## Fitzgerald (reference only, not reproduced)

<!-- R. Fitzgerald, The Odyssey (Farrar, Straus and Giroux, 1961) -- widely-used classroom edition, still in print. Fitzgerald d. 1985, presumptively still under copyright, so NOT reproduced here. No clean current publisher product page was found; background: https://en.wikipedia.org/wiki/Robert_Fitzgerald -->

*(Not reproduced here -- presumptively still under copyright; see the citation above.)*
"""

_FAGLES_REF = """\
## Fagles (reference only, not reproduced)

<!-- R. Fagles, The Odyssey, introduction and notes by Bernard Knox (Penguin Classics, 1996). Fagles d. 2008, presumptively still under copyright, so NOT reproduced here. Publisher page: https://www.penguinrandomhouse.com/books/299801/the-odyssey-by-homer-translated-by-robert-fagles-introduction-and-notes-by-bernard-knox/ -->

*(Not reproduced here -- presumptively still under copyright; see the citation above.)*
"""

_WILSON_REF = """\
## Wilson (reference only, not reproduced)

<!-- E. Wilson, The Odyssey (W. W. Norton, 2017) -- first published translation of the Odyssey into English by a woman. Presumptively still under copyright (translator living), so NOT reproduced here. Publisher page: https://wwnorton.com/books/9780393356250 -->

*(Not reproduced here -- presumptively still under copyright; see the citation above.)*
"""

_KAZANTZAKIS_REF = """\
## Καζαντζάκης/Κακριδής (reference only, not reproduced)

<!-- Ν. Καζαντζάκης – Ι. Θ. Κακριδής, Ὁμήρου Ὀδύσσεια (πρώτη έκδοση: τυπ. Μ. Ρόδη, 1965· επανέκδοση: Ίδρυμα Μανόλη Τριανταφυλλίδη, 2015). Ο Καζαντζάκης πέθανε το 1957, ο Κακριδής το 1992 -- η μετάφραση παραμένει υπό πνευματικά δικαιώματα, ΔΕΝ αναπαράγεται εδώ. Επίσημη βιβλιογραφική αναφορά: https://www.kazantzaki.gr/gr/metafraseis/logotexnika-222 -->

*(Not reproduced here -- in copyright; see the citation above.)*
"""

def populate_translations_en() -> None:
    pope = _POPE_I.rstrip("\n") + "\n\n" + _strip_header(_POPE_IX)
    murray = _MURRAY_IX.rstrip("\n") + "\n\n" + _strip_header(_MURRAY_I)
    chapman = _CHAPMAN.rstrip("\n")
    interlinear = _INTERLINEAR_EN_I.rstrip("\n") + "\n\n" + _strip_header(_INTERLINEAR_EN_IX)
    fitzgerald_ref = _FITZGERALD_REF.rstrip("\n")
    fagles_ref = _FAGLES_REF.rstrip("\n")
    wilson_ref = _WILSON_REF.rstrip("\n")
    body = (
        pope + "\n\n---\n\n" + murray + "\n\n---\n\n" + chapman + "\n\n---\n\n"
        + interlinear + "\n\n---\n\n" + fitzgerald_ref + "\n\n"
        + fagles_ref + "\n\n" + wilson_ref + "\n"
    )
    sources = [
        Source(id="tr-pope", resource="https://en.wikisource.org/wiki/Odyssey_(Pope)",
               title="The Odyssey of Homer", author="Alexander Pope"),
        Source(id="tr-murray1919", resource="https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0136",
               title="The Odyssey", author="A. T. Murray"),
        _GRC_MURRAY1919_SOURCE,
        Source(id="tr-chapman1615", resource="https://www.gutenberg.org/ebooks/48895",
               title="The Odysseys of Homer", author="George Chapman"),
    ]
    concept = build(
        work="Odyssey", passage="I.1-21, IX.19-180", language="en",
        translators=["Pope", "Murray", "Chapman", "interlinear_en",
                     "Fitzgerald (reference only)", "Fagles (reference only)",
                     "Wilson (reference only)"],
        body=body, sources=sources,
        description=(
            "en translations of Odyssey I.1-21, IX.19-180: Pope, Murray, "
            "Chapman (1615, public domain) and interlinear_en, plus "
            "citation-only references to the translations of R. Fitzgerald "
            "(1961), R. Fagles (1996) and E. Wilson (2017), which are in "
            "copyright -- not reproduced here."
        ),
    )
    write(concept, _TEXTS_DIR / "translations_en.md")


# Copied verbatim via:
#   git -C ~/work/greek/git/codeberg.org/EEE-project/created_with_eee \
#     show translations:odyssey/2026_06_01/translations_ru.md
# -- the "## Жуковский" section only (up to, not including, "## Вересаев").
_ZHUKOVSKY_I = """\
## Жуковский

<!-- Жуковский В. А. Одиссея. СПб., 1849 · https://ru.wikisource.org/wiki/Одиссея_(Гомер;_Жуковский) -->
<!-- **Жуковский, 1849** · [wikisource.org ↗](https://ru.wikisource.org/wiki/Одиссея_(Гомер;_Жуковский)) (архивная копия от 22.09.2026: https://web.archive.org/web/20260922110724/https://ru.wikisource.org/wiki/%D0%9E%D0%B4%D0%B8%D1%81%D1%81%D0%B5%D1%8F_(%D0%93%D0%BE%D0%BC%D0%B5%D1%80;_%D0%96%D1%83%D0%BA%D0%BE%D0%B2%D1%81%D0%BA%D0%B8%D0%B9)) · рус., белый стих (пятистопный ямб) · романтический возвышенный стиль · первый классический стихотворный перевод на русский -->

### Odyss. I.1–5

Муза, скажи мне о том многоопытном муже, который,
Странствуя долго со дня, как святой Илион им разрушен,
Многих людей города посетил и обычаи видел,
Много и сердцем скорбел на морях, о спасенье заботясь
Жизни своей и возврате в отчизну сопутников; тщетны…

### Odyss. I.6–10

Были, однако, заботы, не спас он сопутников: сами
Гибель они на себя навлекли святотатством, безумцы,
Съевши быков Гелиоса, над нами ходящего бога, —
День возврата у них он похитил. Скажи же об этом
Что-нибудь нам, о Зевесова дочь, благосклонная Муза.

### Odyss. I.11–15

Все уж другие, погибели верной избегшие, были
Дома, избегнув и брани и моря; его лишь, разлукой
С милой женой и отчизной крушимого, в гроте глубоком
Светлая нимфа Калипсо, богиня богинь, произвольной
Силой держала, напрасно желая, чтоб был ей супругом.

### Odyss. I.16–21

Но когда наконец обращеньем времен приведен был
Год, в который ему возвратиться назначили боги
В дом свой, в Итаку (но где и в объятиях верных друзей он
Всё не избег от тревог), преисполнились жалостью боги
Все; Посейдон лишь единый упорствовал гнать Одиссея,
Богоподобного мужа, пока не достиг он отчизны.

"""

# Copied verbatim via:
#   git -C ~/work/greek/git/codeberg.org/EEE-project/created_with_eee \
#     show translations:odyssey/2026_06_15/translations_ru.md
# -- the "## Жуковский" section only (up to, not including, "## Вересаев").
_ZHUKOVSKY_IX = """\
## Жуковский

<!-- Жуковский В. А. Одиссея. СПб., 1849 · https://ru.wikisource.org/wiki/Одиссея_(Гомер;_Жуковский) -->
<!-- **Жуковский, 1849** · [wikisource.org ↗](https://ru.wikisource.org/wiki/Одиссея_(Гомер;_Жуковский)) (архивная копия от 22.09.2026: https://web.archive.org/web/20260922110724/https://ru.wikisource.org/wiki/%D0%9E%D0%B4%D0%B8%D1%81%D1%81%D0%B5%D1%8F_(%D0%93%D0%BE%D0%BC%D0%B5%D1%80;_%D0%96%D1%83%D0%BA%D0%BE%D0%B2%D1%81%D0%BA%D0%B8%D0%B9)) · рус., белый стих (пятистопный ямб) · романтический возвышенный стиль · первый классический стихотворный перевод на русский -->

### Odyss. IX.19–24

Я Одиссей, сын Лаэртов, везде изобретеньем многих
Хитростей славных и громкой молвой до небес вознесенный.
В солнечносветлой Итаке живу я; там Нерион, всюду
Видимый с моря, подъемлет вершину лесистую; много
Там и других островов, недалеких один от другого:
Зам, и Дулихий, и лесом богатый Закинф;

### Odyss. IX.25–28

и на самом
Западе плоско лежит окруженная морем Итака
(Прочие ж ближе к пределу, где Эос и Гелиос всходят);
Лоно ее каменисто, но юношей бодрых питает;
Я же не ведаю края прекраснее милой Итаки.

### Odyss. IX.29–33

Тщетно Калипсо, богиня богинь, в заключении долгом
Силой держала меня, убеждая, чтоб был ей супругом;
Тщетно меня чародейка, владычица Эи, Цирцея
В доме держала своем, убеждая, чтоб был ей супругом, —
Хитрая лесть их в груди у меня не опутала сердца

### Odyss. IX.34–38

Нет ничего нам дороже отчизны и ближних родных нам;
пусть и в чужбине далёкой богатый имеешь ты кров свой
меж чужаков вдалеке от родителей — всё же тоскуешь.
Но расскажу о пути злополучном, что Зевс мне назначил,
с той поры, как из Трои пустился я в путь.

### Odyss. IX.39–42

Ветер от стен Илиона привел нас ко граду киконов,
Исмару: град мы разрушили, жителей всех истребили.
Жен сохранивши и всяких сокровищ награбивши много,
Стали добычу делить мы, чтоб каждый мог взять свой участок.

### Odyss. IX.43–46

Я ж настоял, чтоб немедля стопою поспешною в бегство
Все обратились: но добрый совет мой отвергли безумцы;
Полные хмеля, они пировали на бреге песчаном,
Мелкого много скота и быков криворогих зарезав.

### Odyss. IX.47–50

Тою порою киконы, из града бежавшие, многих
Собрали живших соседственно с ними в стране той киконов,
Сильных числом, приобыкших сражаться с коней и не мене
Смелых, когда им и пешим в сраженье вступать надлежало.

### Odyss. IX.51–55

Вдруг их явилось так много, как листьев древесных иль ранних
Вешних цветов; и тогда же нам сделалось явно, что злую
Участь и бедствия многие нам приготовил Кронион.
Сдвинувшись, начали бой мы вблизи кораблей быстроходных,
Острые копья, обитые медью, бросая друг в друга.

### Odyss. IX.56–61

Покуда
Длилося утро, пока продолжал подыматься священный
День, мы держались и их отбивали, сильнейших; когда же
Гелиос к позднему часу волов отпряженья склонился,
В бег обратили киконы осиленных ими ахеян.
С каждого я корабля по шести броненосцев отважных
Тут потерял; от судьбы и от смерти ушли остальные.

### Odyss. IX.62–66

Далее поплыли мы в сокрушенье великом о милых
Мертвых, но радуясь в сердце, что сами спаслися от смерти.
Я ж не отвел кораблей легкоходных от брега, покуда
Три раза не был по имени назван из наших несчастных
Спутников каждый, погибший в бою и оставленный в поле.

### Odyss. IX.67–71

Вдруг собирающий тучи Зевес буреносца Борея,
Страшно ревущего, выслал на нас; облака обложили
Море и землю, и темная с грозного неба сошла ночь.
Мчались суда, погружаяся в волны носами; ветрила
Трижды, четырежды были разорваны силою бури.

### Odyss. IX.72–75

Мы, избегая беды, в корабли их, свернув, уложили;
Сами же начали веслами к ближнему берегу править;
Там провели мы в бездействии скучном два дня и две ночи,
В силах своих изнуренные, с тяжкой печалию сердца.

### Odyss. IX.76–78

Третий нам день привела светлозарнокудрявая Эос;
Мачты устроив и снова подняв паруса, на суда мы
Сели; они понеслись, повинуясь кормилу и ветру.

### Odyss. IX.79–81

Мы невредимо бы в милую землю отцов возвратились,
Если б волнение моря и сила Борея не сбили
Нас, обходящих Малею, с пути, отдалив от Киферы.

### Odyss. IX.82–86

Девять носила нас дней раздраженная буря по темным
Рыбообильным водам; на десятый к земле лотофагов,
Пищей цветочной себя насыщающих, ветер примчал нас.
Вышед на твердую землю и свежей водою запасшись,
Наскоро легкий обед мы у быстрых судов учредили.

### Odyss. IX.87–90

Свой удовольствовав голод питьем и едою, избрал я
Двух расторопнейших самых товарищей наших (был третий
С ними глашатай) и сведать послал их, к каким мы достигли
Людям, вкушающим хлеб на земле, изобильной дарами.

### Odyss. IX.91–93

Мирных они лотофагов нашли там; и посланным нашим
Зла лотофаги не сделали; их с дружелюбною лаской
Встретив, им лотоса дали отведать они;

### Odyss. IX.94–97

но лишь только
Сладко-медвяного лотоса каждый отведал, мгновенно
Все позабыл и, утратив желанье назад возвратиться,
Вдруг захотел в стороне лотофагов остаться, чтоб вкусный
Лотос сбирать, навсегда от своей отказавшись отчизны.

### Odyss. IX.98–104

Силой их, плачущих, к нашим судам притащив, повелел я
Крепко их там привязать к корабельным скамьям; остальным же
Верным товарищам дал приказанье, нимало не медля,
Всем на проворные сесть корабли, чтоб из них никоторый,
Лотосом сладким прельстясь, от возврата домой не отрекся.
Все на суда собралися и, севши на лавках у весел,
Разом могучими веслами вспенили темные воды.

### Odyss. IX.105–111

Далее поплыли мы, сокрушенные сердцем, и в землю
Прибыли сильных, свирепых, не знающих правды циклопов.
Там беззаботно они, под защитой бессмертных имея
Всё, ни руками не сеют, ни плугом не пашут; земля там
Тучная щедро сама без паханья и сева дает им
Рожь, и пшено, и ячмень, и роскошных кистей винограда
Полные лозы, и сам их Кронион дождем оплождает.

### Odyss. IX.112–115

Нет между ними ни сходбищ народных, ни общих советов;
В темных пещерах они иль на горных вершинах высоких
Вольно живут; над женой и детьми безотчетно там каждый
Властвует, зная себя одного, о других не заботясь.

### Odyss. IX.116–121

Есть островок там пустынный и дикий; лежит он на темном
Лоне морском, ни далеко, ни близко от брега циклопов,
Лесом покрытый; в великом там множестве дикие козы
Водятся; их никогда не тревожил шагов человека
Шум; никогда не заглядывал к ним зверолов, за дичью
С тяжким трудом по горам крутобоким с псами бродящий;

### Odyss. IX.122–124

Там не пасутся стада и земли не касаются плуги;
Там ни в какие дни года не сеют, не пашут; людей там
Нет; без боязни там ходят одни тонконогие козы,

### Odyss. IX.125–129

Ибо циклопы еще кораблей красногрудых не знают;
Нет между ними искусников, опытных в хитром строенье
Крепких судов, из которых бы каждый, моря обтекая,
Разных народов страны посещал, как бывает, что ходят
По морю люди, с другими людьми дружелюбно знакомясь.

### Odyss. IX.130–133

Дикий тот остров могли обратить бы в цветущий циклопы;
Он не бесплоден; там все бы роскошно рождалося к сроку;
Сходят широкой отлогостью к морю луга там густые,
Влажные, мягкие; много б везде разрослось винограда

### Odyss. IX.134–139

Плугу легко покоряся, поля бы покрылись высокой
Рожью, и жатва была бы на тучной земле изобильна.
Есть там надежная пристань, в которой не нужно ни тяжкий
Якорь бросать, ни канатом привязывать шаткое судно;
Может оно простоять безопасно там, сколько захочет
Плаватель сам иль пока не подымется ветер попутный.

### Odyss. IX.140–141

В самой вершине залива прозрачно ввергается в море
Ключ, из пещеры бегущий под сению тополей черных.

### Odyss. IX.142–145

В эту мы пристань вошли с кораблями; в ночной темноте нам
Путь указал благодетельный демон: был остров невидим;
Влажный туман окружал корабли; не светила Селена
С неба высокого; тучи его покрывали густые

### Odyss. IX.146–151

Острова было нельзя различить нам глазами во мраке;
Видеть и длинных, широко на берег отлогий бегущих
Волн не могли мы, пока корабли не коснулися брега.
Но лишь коснулися брега они, паруса мы свернули;
Сами же, вышед на брег, поражаемый шумно волнами,
Сну предались в ожиданье восхода на небо денницы.

### Odyss. IX.152–155

Вышла из мрака младая с перстами пурпурными Эос;
Весь обошли с удивленьем великим мы остров пустынный;
Нимфы же, дочери Зевса-эгидодержавца, пригнали
Коз с обвеваемых ветрами гор, для богатой нам пищи

### Odyss. IX.156–160

Гибкие луки, охотничьи легкие копья немедля
Взяли с своих кораблей мы и, на три толпы разделяся,
Начали битву; и бог благосклонный великой добычей
Нас наградил: все двенадцать моих кораблей запасли мы,
Девять на каждый досталось по жеребью коз; для себя же
Выбрал я десять.

### Odyss. IX.161–165

И целый мы день до вечернего мрака
Ели прекрасное мясо и сладким вином утешались,
Ибо еще на моих кораблях золотого довольно
Было вина: мы наполнили много скудельных сосудов
Сладким напитком, разрушивши город священный киконов.

### Odyss. IX.166–169

С острова ж в области близкой циклопов нам ясно был виден
Дым; голоса их, блеянье их коз и баранов могли мы
Слышать. Тем временем солнце померкло, и тьма наступила.
Все мы заснули под говором волн, ударяющих в берег.

### Odyss. IX.170–176

Вышла из мрака младая с перстами пурпурными Эос;
Верных товарищей я на совет пригласил и сказал им:
«Все вы, товарищи верные, здесь без меня оставайтесь;
Я же, с моим кораблем и моими людьми удаляся,
Сведать о том попытаюсь, какой там народ обитает.
Дикий ли, нравом свирепый, не знающий правды,
Или приветливый, богобоязненный, гостеприимный?»

### Odyss. IX.177–180

Так я сказал и, вступив на корабль, повелел, чтоб за мною
Люди мои на него все взошли и канат отвязали;
Люди взошли на корабль и, севши на лавках у весел,
Разом могучими веслами вспенили темные воды.

"""

# Copied verbatim via:
#   git -C ~/work/greek/git/codeberg.org/EEE-project/created_with_eee \
#     show translations:odyssey/2026_06_01/translations_ru.md
# -- the "## Вересаев" section only (to end of file).
_VERESAEV_I = """\
## Вересаев

<!-- Вересаев В. В. Одиссея. М., 1953 · http://az.lib.ru/g/gomer/text_0070.shtml -->
<!-- **Вересаев, 1953** · [az.lib.ru ↗](http://az.lib.ru/g/gomer/text_0070.shtml) (архивная копия от 22.09.2026: https://web.archive.org/web/20260922110540/http://az.lib.ru/g/gomer/text_0070.shtml) · рус., проза · ясный современный язык · ориентирован на смысловую точность · стандартный учебный перевод -->

### Odyss. I.1–5

Муза, скажи мне о том многоопытном муже, который
Долго скитался с тех пор, как разрушил священную Трою,
Многих людей города посетил и обычаи видел,
Много духом страдал на морях, о спасеньи заботясь
Жизни своей и возврате в отчизну товарищей верных.

### Odyss. I.6–10

Все же при этом не спас он товарищей, как ни старался.
Собственным сами себя святотатством они погубили:
Съели, безумцы, коров Гелиоса Гиперионида.
Дня возвращенья домой навсегда их за это лишил он.
Муза! Об этом и нам расскажи, начав с чего хочешь.

### Odyss. I.11–15

Все остальные в то время, избегнув погибели близкой,
Были уж дома, равно и войны избежавши и моря.
Только его, по жене и отчизне болевшего сердцем,
Нимфа-царица Калипсо, богиня в богинях, держала
В гроте глубоком, желая, чтоб сделался ей он супругом.

### Odyss. I.16–21

Но протекали года, и уж год наступил, когда было
Сыну Лаэрта богами назначено в дом свой вернуться.
Также, однако, и там, на Итаке, не мог избежать он
Многих трудов, хоть и был меж друзей. Сострадания полны
Были все боги к нему. Лишь один Посейдон непрерывно
Гнал Одиссея, покамест своей он земли не достигнул.
"""

# Copied verbatim via:
#   git -C ~/work/greek/git/codeberg.org/EEE-project/created_with_eee \
#     show translations:odyssey/2026_06_15/translations_ru.md
# -- the "## Вересаев" section only (to end of file).
_VERESAEV_IX = """\
## Вересаев

<!-- Вересаев В. В. Одиссея. М., 1953 · http://az.lib.ru/g/gomer/text_0070.shtml -->
<!-- **Вересаев, 1953** · [az.lib.ru ↗](http://az.lib.ru/g/gomer/text_0070.shtml) (архивная копия от 22.09.2026: https://web.archive.org/web/20260922110540/http://az.lib.ru/g/gomer/text_0070.shtml) · рус., проза · ясный современный язык · ориентирован на смысловую точность · стандартный учебный перевод -->

### Odyss. IX.19–24

Я — Одиссей, сын Лаэрта. Среди всех людей
прославлен я хитроумием, и слава о нём до небес достигает.
Живу в ясно видимой Итаке. На ней гора Неритон
с шумящими листьями, приметная. Вокруг острова
многие лежат, близко одни к другим:
Дулихий, и Сама, и покрытый лесами Закинф.

### Odyss. IX.25–28

Сама Итака низко лежит, всех дальше в море,
к западу; те острова — вдали, к востоку и к солнцу.
Суровая, но добрая кормилица юношей.
Краше своей земли ничего не знаю.

### Odyss. IX.29–33

Правда, там меня удерживала Калипсо, дивная между богинями,
в глубоких пещерах, желая, чтобы я стал её мужем;
точно так же в своих чертогах меня удерживала Кирка Айайская,
коварная, желая, чтобы я стал её мужем.
Но никогда они не могли убедить сердца в моей груди.

### Odyss. IX.34–38

Так ничто не бывает слаще родины и своих родителей,
даже если и живёт кто-нибудь вдали в богатом доме
на чужбине, вдали от родителей.
Ну а теперь расскажу тебе о многострадальном возвращении своём,
которое назначил мне Зевс на пути от Трои.

### Odyss. IX.39–42

Ветер от стен илионских к Исмару пригнал нас, к киконам.
Город я этот разрушил, самих же их гибели предал.
В городе много забравши и женщин и разных сокровищ,
Начали мы их делить, чтоб никто не ушел обделенным.

### Odyss. IX.43–46

Стал тут советовать я как можно скорее отсюда
Всем убежать, но меня не послушались глупые люди.
Было тут выпито много вина и зарезано было
Много у моря быков криворогих и жирных баранов.

### Odyss. IX.47–50

Те между тем из киконов, кто спасся, призвали киконов,
Живших в соседстве, - и больших числом и доблестью лучших,
Внутрь материк населявших, умевших прекрасно сражаться
И с лошадей, а случится нужда, так и пешими биться.

### Odyss. IX.51–55

Столько с зарею явилося их, как цветов или листьев
В пору весны. И тогда перед нами, злосчастными, злая
Зевсова встала судьба, чтобы много мы бед испытали.
Близ кораблей наших быстрых жестокая битва вскипела.
Стали мы яро друг в друга метать медноострые копья.

### Odyss. IX.56–61

С самого утра все время, как день разрастался священный,
Мы, защищаясь, упорно стояли, хоть было их больше.
Но лишь склонилося солнце к поре, как волов распрягают,
Верх получили киконы, вполне одолевши ахейцев.
С каждого судна по шесть сотоварищей наших погибло.
Всем остальным удалось убежать от судьбы и от смерти.

### Odyss. IX.62–66

Дальше оттуда мы двинулись в путь с опечаленным сердцем,
Сами избегнув конца, но товарищей милых лишившись.
В море, однако, не вывел двухвостых судов я, покуда
Трижды каждого мы не позвали из наших несчастных
Спутников, павших на поле в бою под руками киконов.

### Odyss. IX.67–71

Тучи сбирающий Зевс на суда наши северный ветер
С вихрем неслыханным ринул и скрыл под густейшим туманом
Сушу и море. И ночь ниспустилася с неба на землю.
Мчались суда, зарываясь носами в кипящие волны.
Вихрем на три, на четыре куска паруса разорвало.

### Odyss. IX.72–75

Мы, испугавшись беды, в корабли их, свернув, уложили,
Сами же веслами стали к ближайшему берегу править.
На берегу мы подряд пролежали два дня и две ночи,
И пожирали все время нам дух и печаль и усталость.

### Odyss. IX.76–78

Третий день привела за собой пышнокосая Эос.
Мачты поставив и снова подняв паруса, на суда мы
Сели. Они понеслись, повинуяся ветру и кормчим.

### Odyss. IX.79–81

Тут невредимым бы я воротился в родимую землю,
Но и волна, и теченье, и северный ветер — в то время,
Как огибал я Малею — отбили меня от Киферы.

### Odyss. IX.82–86

Девять носили нас дней по обильному рыбою морю
Смертью грозящие ветры. В десятый же день мы приплыли
В край лотофагов, живущих одной лишь цветочною пищей.
Выйдя на твердую землю и свежей водою запасшись,
Близ кораблей быстроходных товарищи сели обедать.

### Odyss. IX.87–90

После того как едой и питьем мы вполне насладились,
Спутникам верным своим приказал я пойти и разведать,
Что за племя мужей хлебоядных живет в этом крае.
Выбрал двух я мужей и глашатая третьим прибавил.

### Odyss. IX.91–93

В путь они тотчас пустились и скоро пришли к лотофагам.
Гибели те лотофаги товарищам нашим нисколько
Не замышляли, но дали им лотоса только отведать.

### Odyss. IX.94–97

Кто от плода его, меду по сладости равного, вкусит,
Тот уж не хочет ни вести подать о себе, ни вернуться,
Но, средь мужей лотофагов оставшись навеки, желает
Лотос вкушать, перестав о своем возвращеньи и думать.

### Odyss. IX.98–104

Силою их к кораблям привел я, рыдавших, обратно
И в кораблях наших полых, связав, положил под скамьями.
После того остальным приказал я товарищам верным
В быстрые наши суда поскорее войти, чтоб, вкусивши
Лотоса, кто и другой не забыл о возврате в отчизну.
Все они быстро взошли на суда, и к уключинам сели
Следом один за другим, и ударили веслами море.

### Odyss. IX.105–111

Дальше оттуда мы двинулись в путь с опечаленным сердцем.
Прибыли вскоре в страну мы не знающих правды циклопов,
Гордых и злых. На бессмертных надеясь богов, ни растений
Не насаждают руками циклопы, ни пашни не пашут.
Без пахоты и без сева обильно у них всё родится —
Белый ячмень и пшеница. Дают виноградные лозы
Множество гроздий, и множат вино в них дожди Громовержца.

### Odyss. IX.112–115

Ни совещаний, ни общих собраний у них не бывает.
Между горами они обитают, в глубоких пещерах
Горных высоких вершин. Над женой и детьми у них каждый
Суд свой творит полновластно, до прочих же нет ему дела.

### Odyss. IX.116–121

Плоский есть там ещё островок, в стороне от залива,
Не далеко и не близко лежащий от края циклопов,
Лесом покрытый. В великом там множестве водятся козы
Дикие. Их никогда не пугают шаги человека;
Нет охотников там, которые бродят лесами,
Много лишений терпя, по горным вершинам высоким.

### Odyss. IX.122–124

Стад никто не пасёт, и поля никто там не пашет.
Ни пахоты никакой, ни сева земля там не знает,
Также не знает людей; лишь блеющих коз она кормит.

### Odyss. IX.125–129

Ибо циклопы не знают ещё кораблей краснобоких,
Плотников нет корабельных у них, искусных в постройке
Прочновесельных судов, своё совершающих дело,
Разных людей города посещая, как это обычно
Делают люди, общаясь друг с другом чрез бездны морские.

### Odyss. IX.130–133

Эти и дикий тот остров смогли бы им сделать цветущим,
Ибо не плох он и вовремя все там могло бы рождаться;
Много лугов там лежит вдоль берега моря седого,
Влажных и мягких: могли бы расти виноградные лозы

### Odyss. IX.134–139

Гладки для пашен поля; богатейшую жатву с посевов
Вовремя можно сбирать, ибо много под почвою жира.
Гавань удобная там, никаких в ней не нужно причалов —
Якорных камней бросать иль привязывать судно канатом.
К суше пристав с кораблем, мореплаватель там остается,
Сколько захочет, пока не подуют попутные ветры.

### Odyss. IX.140–141

В самом конце этой бухты бежит из пещеры источник
С светлоструистой водой, обросший вокруг тополями.

### Odyss. IX.142–145

В этот залив мы вошли. Благодетельный бог нам какой-то
Путь указал через мрачную ночь: был остров невидим.
Влажный туман окружал корабли. Нам луна не светила
С неба высокого. Тучи густые ее закрывали.

### Odyss. IX.146–151

Острова было нельзя различить нам глазами во мраке.
Также не видели мы и высоких, на берег бегущих
Волн до поры, как суда наши прочные врезались в сушу.
К суше пристав, на судах паруса мы немедля спустили,
Сами же вышли на берег прибоем шумящего моря
И, в ожидании Эос божественной, спать улеглися.

### Odyss. IX.152–155

Рано рожденная вышла из тьмы розоперстая Эос.
Вставши, по острову стали бродить мы, немало дивяся.
Нимфы, дочери Зевса эгидодержавного, горных
Подняли коз, чтобы было товарищам чем пообедать

### Odyss. IX.156–160

Гнутые луки тогда, длинноострые легкие копья
Из кораблей мы достали и, на три толпы разделившись,
Стали метать. И богатую бог даровал нам добычу.
Было двенадцать со мной кораблей, и досталось по девять
Коз на корабль: для себя ж одного отобрал я десяток.

### Odyss. IX.161–165

Так мы весь день напролет до зашествия солнца сидели,
Ели обильно мы мясо и сладким вином утешались:
Ибо еще на судах моих быстрых вино не иссякло
Красное. Много его в амфорах на каждый корабль наш
Мы погрузили, священный разрушивши город киконов.

### Odyss. IX.166–169

Видели близко мы землю циклопов. С нее доходили
Дым, голоса их самих, овечье и козье бленье.
Солнце меж тем закатилось, и сумрак спустился на землю.
Спать мы все улеглись у прибоем шумящего моря.

### Odyss. IX.170–176

Рано рожденная встала из тьмы розоперстая Эос.
Всех я тогда на собранье созвал и вот что сказал им:
— Здесь все другие останьтесь, товарищи, мне дорогие!
Я ж на моем корабле и с дружиной моей корабельной
К этим отправлюсь мужам и исследую, кто эти мужи, —
Дикие ль, гордые духом и знать не хотящие правды
Или радушные к гостю и с богобоязненным сердцем.

### Odyss. IX.177–180

Так сказав и взойдя на корабль, приказал и другим я,
Севши самим на корабль, развязать судовые причалы.
Тотчас они на корабль поднялись, и к уключинам сели
Следом один за другим, и ударили веслами море.

"""


# Renamed 'подстрочник' -> 'interlinear_ru' and extended to IX.19-180
# with per-line <!-- grc: --> echoes (2026-09-26), matching the
# established interlinear_en/interlinear_el convention. Extracted
# verbatim from the already-committed texts/odyssey/translations_ru.md.
_INTERLINEAR_RU_I = """\
## interlinear_ru

### Odyss. I.1–5

<!-- grc: Ἄνδρα μοι ἔννεπε, μοῦσα, πολύτροπον, ὃς μάλα πολλὰ -->
О муже мне расскажи, муза, о многостранном, который весьма много

<!-- grc: πλάγχθη, ἐπεὶ Τροίης ἱερὸν πτολίεθρον ἔπερσεν· -->
скитался, когда Трои святую твердыню разрушил.

<!-- grc: πολλῶν δ' ἀνθρώπων ἴδεν ἄστεα καὶ νόον ἔγνω, -->
Многих людей он видел города и ум узнал,

<!-- grc: πολλὰ δ' ὅ γ' ἐν πόντῳ πάθεν ἄλγεα ὃν κατὰ θυμόν, -->
много также он и на море претерпел страданий в своем духе,

<!-- grc: ἀρνύμενος ἥν τε ψυχὴν καὶ νόστον ἑταίρων. -->
борясь и за свою душу, и за возвращение товарищей.


### Odyss. I.6–10

<!-- grc: ἀλλ' οὐδ' ὣς ἑτάρους ἐρρύσατο, ἱέμενός περ· -->
но и своих товарищей он не спас, хотя и стремился,

<!-- grc: αὐτῶν γὰρ σφετέρῃσιν ἀτασθαλίῃσιν ὄλοντο, -->
от их ведь собственных нечестий они погибли,

<!-- grc: νήπιοι, οἳ κατὰ βοῦς Ὑπερίονος Ἠελίοιο -->
неразумные, которые быков Гипериона Гелиоса

<!-- grc: ἤσθιον· αὐτὰρ ὁ τοῖσιν ἀφείλετο νόστιμον ἦμαρ. -->
пожрали, и был у них отнят возвратный день.

<!-- grc: τῶν ἁμόθεν γε, θεά, θύγατερ Διός, εἰπὲ καὶ ἡμῖν. -->
Вот об этом откуда-нибудь, богиня, дочь Зевса, расскажи и нам.


### Odyss. I.11–15

<!-- grc: Ἔνθ' ἄλλοι μὲν πάντες, ὅσοι φύγον αἰπὺν ὄλεθρον, -->
Когда другие все, которые избежали стремительной гибели,

<!-- grc: οἴκοι ἔσαν, πόλεμόν τε πεφευγότες ἠδὲ θάλασσαν· -->
дома были, войны избежав и моря,

<!-- grc: τὸν δ' οἶον νόστου κεχρημένον ἠδὲ γυναικὸς -->
его одного, возвращения лишенного и жены,

<!-- grc: νύμφη πότνι' ἔρυκε Καλυψὼ δῖα θεάων -->
нимфа владычица держала Калипсо, славная среди богинь,

<!-- grc: ἐν σπέσσι γλαφυροῖσι, λιλαιομένη πόσιν εἶναι. -->
в пещерах глубоких, страстно желая, чтобы мужем он был.


### Odyss. I.16–21

<!-- grc: ἀλλ' ὅτε δὴ ἔτος ἦλθε περιπλομένων ἐνιαυτῶν, -->
но когда уже год пришел, по обращении времен,

<!-- grc: τῷ οἱ ἐπεκλώσαντο θεοὶ οἰκόνδε νέεσθαι -->
в который ему назначили боги домой вернуться

<!-- grc: εἰς Ἰθάκην, οὐδ' ἔνθα πεφυγμένος ἦεν ἀέθλων -->
на Итаку, и даже там он не избег испытаний,

<!-- grc: καὶ μετὰ οἷσι φίλοισι. θεοὶ δ' ἐλέαιρον ἅπαντες -->
и со своими друзьями. А боги все смилостивились,

<!-- grc: νόσφι Ποσειδάωνος· ὁ δ' ἀσπερχὲς μενέαινεν -->
кроме Посейдона: он беспрерывно гневался

<!-- grc: ἀντιθέῳ Ὀδυσῆι πάρος ἥν γαῖαν ἱκέσθαι. -->
на богоравного Одиссея, пока он не прибыл на свою землю.

"""

# IX.19-180 half of the same interlinear_ru section.
_INTERLINEAR_RU_IX = """\
## interlinear_ru

### Odyss. IX.19–24

<!-- grc: εἶμ' Ὀδυσεὺς Λαερτιάδης, ὃς πᾶσι δόλοισιν -->
Я - Одиссей Лаэртид, который всем хитростями

<!-- grc: ἀνθρώποισι μέλω, καί μευ κλέος οὐρανὸν ἵκει. -->
людям интересен (всех людей умы занимает), и моя слава до неба идет.

<!-- grc: ναιετάω δ' Ἰθάκην εὐδείελον· ἐν δ' ὄρος αὐτῇ -->
а живу я на Итаке хорошо различимой, а на ней гора

<!-- grc: Νήριτον εἰνοσίφυλλον, ἀριπρεπές· ἀμφὶ δὲ νῆσοι -->
Нерит, листвы колебатель, прекраснозаметный, а кругом острова

<!-- grc: πολλαὶ ναιετάουσι μάλα σχεδὸν ἀλλήλῃσι, -->
многие обретаются, очень близко друг к другу,

<!-- grc: Δουλίχιόν τε Σάμη τε καὶ ὑλήεσσα Ζάκυνθος. -->
Дулихий и Сама, и лесистый Закинф.


### Odyss. IX.25–28

<!-- grc: αὐτὴ δὲ χθαμαλὴ πανυπερτάτη εἰν ἁλὶ κεῖται -->
и она сама, невысокая, самая крайняя в море лежит

<!-- grc: πρὸς ζόφον, αἱ δέ τ' ἄνευθε πρὸς ἠῶ τ' ἠέλιόν τε, -->
к западу, а они вдалеке к заре и солнцу,

<!-- grc: τρηχεῖ', ἀλλ' ἀγαθὴ κουροτρόφος· οὔ τοι ἐγώ γε -->
скалистая, но добрая и юных питающая: нет, я точно не

<!-- grc: ἧς γαίης δύναμαι γλυκερώτερον ἄλλο ἰδέσθαι. -->
этой земли могу что-то другое слаще увидеть.


### Odyss. IX.29–33

<!-- grc: ἦ μέν μ' αὐτόθ' ἔρυκε Καλυψώ, δῖα θεάων, -->
поистине меня там удерживала Калипсо, божественная из богинь,

<!-- grc: ἐν σπέσσι γλαφυροῖσι, λιλαιομένη πόσιν εἶναι· -->
в пещерах выдолбленных, страстно желая, чтоб был я супругом,

<!-- grc: ὣς δ' αὔτως Κίρκη κατερήτυεν ἐν μεγάροισιν -->
так же точно Кирка удерживала в залах,

<!-- grc: Αἰαίη δολόεσσα, λιλαιομένη πόσιν εἶναι· -->
Ээянка коварная, страстно желая, чтоб был я супругом,

<!-- grc: ἀλλ' ἐμὸν οὔ ποτε θυμὸν ἐνὶ στήθεσσιν ἔπειθον. -->
но мой никогда дух в груди не убеждали.


### Odyss. IX.34–38

<!-- grc: ὣς οὐδὲν γλύκιον ἧς πατρίδος οὐδὲ τοκήων -->
потому что ничто не слаще собственной родины и родителей

<!-- grc: γίγνεται, εἴ περ καί τις ἀπόπροθι πίονα οἶκον -->
бывает, если даже и кто-то вдалеке богатый дом

<!-- grc: γαίῃ ἐν ἀλλοδαπῇ ναίει ἀπάνευθε τοκήων. -->
в земле чужой населяет, вдали от родителей.

<!-- grc: εἰ δ' ἄγε τοι καὶ νόστον ἐμὸν πολυκηδέ' ἐνίσπω, -->
или ладно, давай тебе и возвращение мое многоскорбное расскажу,

<!-- grc: ὅν μοι Ζεὺς ἐφέηκεν ἀπὸ Τροίηθεν ἰόντι. -->
которое мне Зевс послал, когда я уходил из Трои.


### Odyss. IX.39–42

<!-- grc: Ἰλιόθεν με φέρων ἄνεμος Κικόνεσσι πέλασσεν, -->
Из Илиона меня неся ветер к киконам притащил,

<!-- grc: Ἰσμάρῳ. ἔνθα δ᾽ ἐγὼ πόλιν ἔπραθον, ὤλεσα δ᾽ αὐτούς: -->
к Исмару; а там я город разрушил и погубил их (жителей).

<!-- grc: ἐκ πόλιος δ᾽ ἀλόχους καὶ κτήματα πολλὰ λαβόντες -->
А из города наложниц и добра много забрав,

<!-- grc: δασσάμεθ᾽, ὡς μή τίς μοι ἀτεμβόμενος κίοι ἴσης. -->
мы поделили между собой, чтобы никто у меня (на меня) обиженным не ходил равной (долей).


### Odyss. IX.43–46

<!-- grc: ἔνθ᾽ ἦ τοι μὲν ἐγὼ διερῷ ποδὶ φευγέμεν ἡμέας -->
Тут, говорю тебе, я-то, чтобы живой = быстрой ногой бежали мы,

<!-- grc: ἠνώγεα, τοὶ δὲ μέγα νήπιοι οὐκ ἐπίθοντο. -->
велел/убеждал, а они, очень неразумные, не послушались.

<!-- grc: ἔνθα δὲ πολλὸν μὲν μέθυ πίνετο, πολλὰ δὲ μῆλα -->
И тогда много хмельного было пито, и много мелкого скота

<!-- grc: ἔσφαζον παρὰ θῖνα καὶ εἰλίποδας ἕλικας βοῦς: -->
они резали у берега и волочащих ноги гнуто(рогих) быков/коров.


### Odyss. IX.47–50

<!-- grc: τόφρα δ᾽ ἄρ᾽ οἰχόμενοι Κίκονες Κικόνεσσι γεγώνευν, -->
Тут-то как раз уходящие киконы киконам сделались слышны,

<!-- grc: οἵ σφιν γείτονες ἦσαν, ἅμα πλέονες καὶ ἀρείους, -->
которые им соседями были, также их было больше и они были крепче/храбрее,

<!-- grc: ἤπειρον ναίοντες, ἐπιστάμενοι μὲν ἀφ᾽ ἵππων -->
материк населяющие, сведущие в том, как с коней

<!-- grc: ἀνδράσι μάρνασθαι καὶ ὅθι χρὴ πεζὸν ἐόντα. -->
с мужами сражаться и где нужно пешим будучи.


### Odyss. IX.51–55

<!-- grc: ἦλθον ἔπειθ᾽ ὅσα φύλλα καὶ ἄνθεα γίγνεται ὥρῃ, -->
Пришли они затем, сколько листьев и цветов вырастает в сезон,

<!-- grc: ἠέριοι: τότε δή ῥα κακὴ Διὸς αἶσα παρέστη -->
ранним утром; тогда-то вот злой Зевса рок стал рядом

<!-- grc: ἡμῖν αἰνομόροισιν, ἵν᾽ ἄλγεα πολλὰ πάθοιμεν. -->
с нами злосчастными, что страданий много нам претерпеть.

<!-- grc: στησάμενοι δ᾽ ἐμάχοντο μάχην παρὰ νηυσὶ θοῇσι, -->
став, они бились в битве при кораблях быстрых,

<!-- grc: βάλλον δ᾽ ἀλλήλους χαλκήρεσιν ἐγχείῃσιν. -->
и бросали друг в друга бронзоконечными копьями.


### Odyss. IX.56–61

<!-- grc: ὄφρα μὲν ἠὼς ἦν καὶ ἀέξετο ἱερὸν ἦμαρ, -->
Пока утро было и нарастал священный день,

<!-- grc: τόφρα δ᾽ ἀλεξόμενοι μένομεν πλέονάς περ ἐόντας. -->
столько защищаясь мы оставались, хотя тех было больше;

<!-- grc: ἦμος δ᾽ ἠέλιος μετενίσσετο βουλυτόνδε, -->
в это время солнце передвинулось в сторону распряжки волов/быков,

<!-- grc: καὶ τότε δὴ Κίκονες κλῖναν δαμάσαντες Ἀχαιούς. -->
и вот тогда киконы заставили склониться одолев ахеййцев.

<!-- grc: ἓξ δ᾽ ἀφ᾽ ἑκάστης νηὸς ἐυκνήμιδες ἑταῖροι -->
Шесть с каждого корабля красивопоножных товарищей

<!-- grc: ὤλονθ᾽: οἱ δ᾽ ἄλλοι φύγομεν θάνατόν τε μόρον τε. -->
погибло, а мы, остальные, избежали смерти и судьбы.


### Odyss. IX.62–66

<!-- grc: ἔνθεν δὲ προτέρω πλέομεν ἀκαχήμενοι ἦτορ, -->
и оттуда мы дальше поплыли, весьма опечаленные в сердце,

<!-- grc: ἄσμενοι ἐκ θανάτοιο, φίλους ὀλέσαντες ἑταίρους. -->
радостно избегшие смерти, потеряв милых товарищей.

<!-- grc: οὐδ᾽ ἄρα μοι προτέρω νῆες κίον ἀμφιέλισσαι, -->
и, значит, корабли обоюдозагнутые у меня дальше не двинулись,

<!-- grc: πρίν τινα τῶν δειλῶν ἑτάρων τρὶς ἕκαστον ἀῦσαι, -->
прежде чем мы не позвали трижды каждого из несчастных товарищей,

<!-- grc: οἳ θάνον ἐν πεδίῳ Κικόνων ὕπο δῃωθέντες. -->
которые умерли на поле, растерзанные киконами.


### Odyss. IX.67–71

<!-- grc: νηυσὶ δ᾽ ἐπῶρσ᾽ ἄνεμον Βορέην νεφεληγερέτα Ζεὺς -->
и кораблям поднял ветер Борей тучегонитель Зевс

<!-- grc: λαίλαπι θεσπεσίῃ, σὺν δὲ νεφέεσσι κάλυψε -->
бурей сверхъестественной, а с облаками скрыл

<!-- grc: γαῖαν ὁμοῦ καὶ πόντον: ὀρώρει δ᾽ οὐρανόθεν νύξ. -->
землю вместе и море: и устремилась с неба ночь.

<!-- grc: αἱ μὲν ἔπειτ᾽ ἐφέροντ᾽ ἐπικάρσιαι, ἱστία δέ σφιν -->
и после этого они неслись поперек, а паруса у них

<!-- grc: τριχθά τε καὶ τετραχθὰ διέσχισεν ἲς ἀνέμοιο. -->
натрое и начетверо разорвала сила ветра.


### Odyss. IX.72–75

<!-- grc: καὶ τὰ μὲν ἐς νῆας κάθεμεν, δείσαντες ὄλεθρον, -->
и их (паруса) в корабли мы сложили, испугавшись гибели,

<!-- grc: αὐτὰς δ᾽ ἐσσυμένως προερέσσαμεν ἤπειρόνδε. -->
и сами (корабли) стремительно веслами направили к материку.

<!-- grc: ἔνθα δύω νύκτας δύο τ᾽ ἤματα συνεχὲς αἰεὶ -->
там две ночи и два дня непрерывно все время

<!-- grc: κείμεθ᾽, ὁμοῦ καμάτῳ τε καὶ ἄλγεσι θυμὸν ἔδοντες. -->
мы лежали, съедая дух вместе усталостью и скорбями.


### Odyss. IX.76–78

<!-- grc: ἀλλ᾽ ὅτε δὴ τρίτον ἦμαρ ἐυπλόκαμος τέλεσ᾽ Ἠώς, -->
но когда уже третий день прекраснокудрая завершила Эос,

<!-- grc: ἱστοὺς στησάμενοι ἀνά θ᾽ ἱστία λεύκ᾽ ἐρύσαντες -->
поставив мачты и натянув наверх белые паруса,

<!-- grc: ἥμεθα, τὰς δ᾽ ἄνεμός τε κυβερνῆταί τ᾽ ἴθυνον. -->
мы сидели, а их ветер и кормчие направляли.


### Odyss. IX.79–81

<!-- grc: καί νύ κεν ἀσκηθὴς ἱκόμην ἐς πατρίδα γαῖαν: -->
и вот-вот я бы и вернулся невредимым в отчую землю,

<!-- grc: ἀλλά με κῦμα ῥόος τε περιγνάμπτοντα Μάλειαν -->
но волна и течение меня, огибающего Малею,

<!-- grc: καὶ Βορέης ἀπέωσε, παρέπλαγξεν δὲ Κυθήρων. -->
и Борей оттолкнул, и отбросил от Киферы.


### Odyss. IX.82–86

<!-- grc: ἔνθεν δ᾽ ἐννῆμαρ φερόμην ὀλοοῖς ἀνέμοισιν -->
А оттуда девятидневье несся я на гибельных ветрах

<!-- grc: πόντον ἐπ᾽ ἰχθυόεντα: ἀτὰρ δεκάτῃ ἐπέβημεν -->
по морю рыбному; но на десятый добрались мы

<!-- grc: γαίης Λωτοφάγων, οἵ τ᾽ ἄνθινον εἶδαρ ἔδουσιν. -->
до земли лотофагов, которые цветочную еду едят.

<!-- grc: ἔνθα δ᾽ ἐπ᾽ ἠπείρου βῆμεν καὶ ἀφυσσάμεθ᾽ ὕδωρ, -->
А там на сушу сошли мы и начерпали воды,

<!-- grc: αἶψα δὲ δεῖπνον ἕλοντο θοῇς παρὰ νηυσὶν ἑταῖροι. -->
а тотчас за обед взялись быстрых у кораблей товарищи.


### Odyss. IX.87–90

<!-- grc: αὐτὰρ ἐπεὶ σίτοιό τ᾽ ἐπασσάμεθ᾽ ἠδὲ ποτῆτος, -->
И вот когда пищи поели и питья (попили),

<!-- grc: δὴ τοτ᾽ ἐγὼν ἑτάρους προΐειν πεύθεσθαι ἰόντας, -->
вот тогда-то я товарищей отправил разузнать пойти,

<!-- grc: οἵ τινες ἀνέρες εἶεν ἐπὶ χθονὶ σῖτον ἔδοντες -->
что за какие-то люди на земле хлеб/пищу едящие,

<!-- grc: ἄνδρε δύω κρίνας, τρίτατον κήρυχ᾽ ἅμ᾽ ὀπάσσας. -->
двух человек выделив, третьего глашатаем вместе с ними отправив.


### Odyss. IX.91–93

<!-- grc: οἱ δ᾽ αἶψ᾽ οἰχόμενοι μίγεν ἀνδράσι Λωτοφάγοισιν: -->
А они тут же уйдя повстречались с мужами лотофагами;

<!-- grc: οὐδ᾽ ἄρα Λωτοφάγοι μήδονθ᾽ ἑτάροισιν ὄλεθρον -->
И вот лотофаги не замышляли товарищам погибели

<!-- grc: ἡμετέροις, ἀλλά σφι δόσαν λωτοῖο πάσασθαι. -->
нашим, но им дали лотоса поесть.


### Odyss. IX.94–97

<!-- grc: τῶν δ᾽ ὅς τις λωτοῖο φάγοι μελιηδέα καρπόν, -->
Из них тот, кто лотоса съел медосладкого плода,

<!-- grc: οὐκέτ᾽ ἀπαγγεῖλαι πάλιν ἤθελεν οὐδὲ νέεσθαι, -->
ни сообщить весть не пожелал, ни возвращаться,

<!-- grc: ἀλλ᾽ αὐτοῦ βούλοντο μετ᾽ ἀνδράσι Λωτοφάγοισι -->
но там предпочли с мужами лотофагами

<!-- grc: λωτὸν ἐρεπτόμενοι μενέμεν νόστου τε λαθέσθαι. -->
лотосом кормясь остаться и о возвращении позабыть.


### Odyss. IX.98–104

<!-- grc: τοὺς μὲν ἐγὼν ἐπὶ νῆας ἄγον κλαίοντας ἀνάγκῃ, -->
Я их на корабли отвел, плачущих от принуждения,

<!-- grc: νηυσὶ δ᾽ ἐνὶ γλαφυρῇσιν ὑπὸ ζυγὰ δῆσα ἐρύσσας. -->
а на кораблях гладко выструганных под скамьи привязал, притащив;

<!-- grc: αὐτὰρ τοὺς ἄλλους κελόμην ἐρίηρας ἑταίρους -->
и вот другим приказал верным товарищам

<!-- grc: σπερχομένους νηῶν ἐπιβαινέμεν ὠκειάων, -->
торопливо на корабли взойти скорые,

<!-- grc: μή πώς τις λωτοῖο φαγὼν νόστοιο λάθηται. -->
чтобы никто лотоса поев о возвращении не забыл.

<!-- grc: οἱ δ᾽ αἶψ᾽ εἴσβαινον καὶ ἐπὶ κληῖσι καθῖζον, -->
А они тотчас взошли и на скамьи сели,

<!-- grc: ἑξῆς δ᾽ ἑζόμενοι πολιὴν ἅλα τύπτον ἐρετμοῖς. -->
а друг за другом сидя седое море ударили веслами.


### Odyss. IX.105–111

<!-- grc: ἔνθεν δὲ προτέρω πλέομεν ἀκαχήμενοι ἦτορ: -->
А оттуда дальше мы поплыли опечаленные сердцем.

<!-- grc: Κυκλώπων δ᾽ ἐς γαῖαν ὑπερφιάλων ἀθεμίστων -->
И в киклопов землю надменных беззаконных

<!-- grc: ἱκόμεθ᾽, οἵ ῥα θεοῖσι πεποιθότες ἀθανάτοισιν -->
прибыли, которые богам подчиняясь бессмертным

<!-- grc: οὔτε φυτεύουσιν χερσὶν φυτὸν οὔτ᾽ ἀρόωσιν, -->
не выращивают руками растения и не пашут,

<!-- grc: ἀλλὰ τά γ᾽ ἄσπαρτα καὶ ἀνήροτα πάντα φύονται, -->
но несеяным и непаханым всё растёт:

<!-- grc: πυροὶ καὶ κριθαὶ ἠδ᾽ ἄμπελοι, αἵ τε φέρουσιν -->
и пшеница, и ячмень, и лозы, которые несут

<!-- grc: οἶνον ἐριστάφυλον, καί σφιν Διὸς ὄμβρος ἀέξει. -->
вино из хороших виноградин, и их Зевсов дождь преумножает.


### Odyss. IX.112–115

<!-- grc: τοῖσιν δ᾽ οὔτ᾽ ἀγοραὶ βουληφόροι οὔτε θέμιστες, -->
И у них нет ни собраний советоносных, ни уложений,

<!-- grc: ἀλλ᾽ οἵ γ᾽ ὑψηλῶν ὀρέων ναίουσι κάρηνα -->
но они высоких гор населяют вершины

<!-- grc: ἐν σπέσσι γλαφυροῖσι, θεμιστεύει δὲ ἕκαστος -->
[живут] в пещерах блестящих/гладких, управляет же каждый

<!-- grc: παίδων ἠδ᾽ ἀλόχων, οὐδ᾽ ἀλλήλων ἀλέγουσιν. -->
детьми и супругами, и друг до друга им нет дела.


### Odyss. IX.116–121

<!-- grc: νῆσος ἔπειτα λάχεια παρὲκ λιμένος τετάνυσται, -->
Остров затем плодородный/плоский перед гаванью распростерся

<!-- grc: γαίης Κυκλώπων οὔτε σχεδὸν οὔτ᾽ ἀποτηλοῦ, -->
от земли киклопов не близко и не далеко

<!-- grc: ὑλήεσσ᾽: ἐν δ᾽ αἶγες ἀπειρέσιαι γεγάασιν -->
лесистый; а там козы бесчисленные народились

<!-- grc: ἄγριαι: οὐ μὲν γὰρ πάτος ἀνθρώπων ἀπερύκει, -->
дикие; ведь их поступь людей не отпугивает,

<!-- grc: οὐδέ μιν εἰσοιχνεῦσι κυνηγέται, οἵ τε καθ᾽ ὕλην -->
и к ним не приходят охотники, которые по лесу

<!-- grc: ἄλγεα πάσχουσιν κορυφὰς ὀρέων ἐφέποντες. -->
страдания претерпевают, верхушки гор исхаживая.


### Odyss. IX.122–124

<!-- grc: οὔτ᾽ ἄρα ποίμνῃσιν καταΐσχεται οὔτ᾽ ἀρότοισιν, -->
Ни пастбищами не покрыта, ни пашнями,

<!-- grc: ἀλλ᾽ ἥ γ᾽ ἄσπαρτος καὶ ἀνήροτος ἤματα πάντα -->
но несеяная и непаханая во дни все

<!-- grc: ἀνδρῶν χηρεύει, βόσκει δέ τε μηκάδας αἶγας. -->
людей лишена, а кормит мекающих коз.


### Odyss. IX.125–129

<!-- grc: οὐ γὰρ Κυκλώπεσσι νέες πάρα μιλτοπάρῃοι, -->
Ведь нет у киклопов ни кораблей краснощеких,

<!-- grc: οὐδ᾽ ἄνδρες νηῶν ἔνι τέκτονες, οἵ κε κάμοιεν -->
ни людей-корабельных плотников, которые могли бы трудиться

<!-- grc: νῆας ἐυσσέλμους, αἵ κεν τελέοιεν ἕκαστα -->
над кораблями прекраснопалубными, которые могли бы совершать каждое своё,

<!-- grc: ἄστε᾽ ἐπ᾽ ἀνθρώπων ἱκνεύμεναι, οἷά τε πολλὰ -->
к городам людей прибывая, как зачастую

<!-- grc: ἄνδρες ἐπ᾽ ἀλλήλους νηυσὶν περόωσι θάλασσαν: -->
люди друг к другу на кораблях бороздят море.


### Odyss. IX.130–133

<!-- grc: οἵ κέ σφιν καὶ νῆσον ἐυκτιμένην ἐκάμοντο. -->
они бы им и остров благоустроенным сделали.

<!-- grc: οὐ μὲν γάρ τι κακή γε, φέροι δέ κεν ὥρια πάντα: -->
ведь он совсем не плохой, а приносил бы всё по сезону:

<!-- grc: ἐν μὲν γὰρ λειμῶνες ἁλὸς πολιοῖο παρ᾽ ὄχθας -->
потому что там луга у берегов моря седого

<!-- grc: ὑδρηλοὶ μαλακοί: μάλα κ᾽ ἄφθιτοι ἄμπελοι εἶεν. -->
орошаемые и мягкие: очень бы неувядающие были виноградники.


### Odyss. IX.134–139

<!-- grc: ἐν δ᾽ ἄροσις λείη: μάλα κεν βαθὺ λήιον αἰεὶ -->
там и гладкая пашня: очень обильный посев всегда

<!-- grc: εἰς ὥρας ἀμῷεν, ἐπεὶ μάλα πῖαρ ὑπ᾽ οὖδας. -->
из сезона в сезон собирали, поскольку очень жирная внизу почва.

<!-- grc: ἐν δὲ λιμὴν ἐύορμος, ἵν᾽ οὐ χρεὼ πείσματός ἐστιν, -->
там и гавань удобная для стоянки, где нет нужды в швартове,

<!-- grc: οὔτ᾽ εὐνὰς βαλέειν οὔτε πρυμνήσι᾽ ἀνάψαι, -->
ни якоря кидать, ни кормовые канаты крепить,

<!-- grc: ἀλλ᾽ ἐπικέλσαντας μεῖναι χρόνον εἰς ὅ κε ναυτέων -->
но приставшим к берегу [есть нужда] оставаться время, в которое их

<!-- grc: θυμὸς ἐποτρύνῃ καὶ ἐπιπνεύσωσιν ἀῆται. -->
дух подтолкнет и подуют ветры.


### Odyss. IX.140–141

<!-- grc: αὐτὰρ ἐπὶ κρατὸς λιμένος ῥέει ἀγλαὸν ὕδωρ, -->
но на краю гавани течет блестящая вода,

<!-- grc: κρήνη ὑπὸ σπείους: περὶ δ᾽ αἴγειροι πεφύασιν. -->
источник из-под пещеры, а вокруг выросли тополя.


### Odyss. IX.142–145

<!-- grc: ἔνθα κατεπλέομεν, καί τις θεὸς ἡγεμόνευεν -->
туда мы подплывали, и некий бог вел

<!-- grc: νύκτα δι᾽ ὀρφναίην, οὐδὲ προυφαίνετ᾽ ἰδέσθαι: -->
через темную ночь, и не показывался, чтобы быть увиденным:

<!-- grc: ἀὴρ γὰρ περὶ νηυσὶ βαθεῖ᾽ ἦν, οὐδὲ σελήνη -->
потому что туман вокруг кораблей был глубокий, и луна

<!-- grc: οὐρανόθεν προύφαινε, κατείχετο δὲ νεφέεσσιν. -->
с неба не светила, а была покрыта облаками.


### Odyss. IX.146–151

<!-- grc: ἔνθ᾽ οὔ τις τὴν νῆσον ἐσέδρακεν ὀφθαλμοῖσιν, -->
там никто остров не увидел глазами,

<!-- grc: οὔτ᾽ οὖν κύματα μακρὰ κυλινδόμενα προτὶ χέρσον -->
но и волны длинные, катящиеся к суше,

<!-- grc: εἰσίδομεν, πρὶν νῆας ἐυσσέλμους ἐπικέλσαι. -->
не увидели, прежде чем корабли крепкопалубные не причалили.

<!-- grc: κελσάσῃσι δὲ νηυσὶ καθείλομεν ἱστία πάντα, -->
а причалившим кораблям мы спустили все паруса,

<!-- grc: ἐκ δὲ καὶ αὐτοὶ βῆμεν ἐπὶ ῥηγμῖνι θαλάσσης: -->
и сами вышли на прибрежную полосу моря;

<!-- grc: ἔνθα δ᾽ ἀποβρίξαντες ἐμείναμεν Ἠῶ δῖαν. -->
и там, уснув, дождались божественную Эос.


### Odyss. IX.152–155

<!-- grc: ἦμος δ᾽ ἠριγένεια φάνη ῥοδοδάκτυλος Ἠώς, -->
а когда показалась ранорожденная розоперстая Эос,

<!-- grc: νῆσον θαυμάζοντες ἐδινεόμεσθα κατ᾽ αὐτήν. -->
дивясь на остров, мы кружили по нему.

<!-- grc: ὦρσαν δὲ νύμφαι, κοῦραι Διὸς αἰγιόχοιο, -->
и подняли нимфы, дочери Зевса эгидодержавного,

<!-- grc: αἶγας ὀρεσκῴους, ἵνα δειπνήσειαν ἑταῖροι. -->
коз горных, чтобы отобедали спутники.


### Odyss. IX.156–160

<!-- grc: αὐτίκα καμπύλα τόξα καὶ αἰγανέας δολιχαύλους -->
тотчас изогнутые луки и копья длиннодревковые

<!-- grc: εἱλόμεθ᾽ ἐκ νηῶν, διὰ δὲ τρίχα κοσμηθέντες -->
мы себе взяли с кораблей, и, распределившись на три части,

<!-- grc: βάλλομεν: αἶψα δ᾽ ἔδωκε θεὸς μενοεικέα θήρην. -->
стали метать: и тут же дал бог достаточную добычу.

<!-- grc: νῆες μέν μοι ἕποντο δυώδεκα, ἐς δὲ ἑκάστην -->
за мной следовали 12 кораблей, и на каждый

<!-- grc: ἐννέα λάγχανον αἶγες: ἐμοὶ δὲ δέκ᾽ ἔξελον οἴῳ. -->
распределились по 9 коз; а мне одному я выделил 10.


### Odyss. IX.161–165

<!-- grc: ὣς τότε μὲν πρόπαν ἦμαρ ἐς ἠέλιον καταδύντα -->
так тогда весь день до заката солнца

<!-- grc: ἥμεθα δαινύμενοι κρέα τ᾽ ἄσπετα καὶ μέθυ ἡδύ: -->
мы сидели, вкушая несметное мясо и сладкое вино;

<!-- grc: οὐ γάρ πω νηῶν ἐξέφθιτο οἶνος ἐρυθρός, -->
ведь еще не иссякло с кораблей красное вино,

<!-- grc: ἀλλ᾽ ἐνέην: πολλὸν γὰρ ἐν ἀμφιφορεῦσιν ἕκαστοι -->
но было в наличии: ведь все мы много в амфорах

<!-- grc: ἠφύσαμεν Κικόνων. ἱερὸν πτολίεθρον ἑλόντες. -->
начерпали, взяв священную твердыню киконов.


### Odyss. IX.166–169

<!-- grc: Κυκλώπων δ᾽ ἐς γαῖαν ἐλεύσσομεν ἐγγὺς ἐόντων, -->
и в землю циклопов всматривались, рядом находившихся,

<!-- grc: καπνόν τ᾽ αὐτῶν τε φθογγὴν ὀίων τε καὶ αἰγῶν. -->
в их дым и голос овец и коз.

<!-- grc: ἦμος δ᾽ ἠέλιος κατέδυ καὶ ἐπὶ κνέφας ἦλθε, -->
когда же солнце село и в сумрак пришло,

<!-- grc: δὴ τότε κοιμήθημεν ἐπὶ ῥηγμῖνι θαλάσσης. -->
именно тогда мы уснули у прибоя моря.


### Odyss. IX.170–176

<!-- grc: ἦμος δ᾽ ἠριγένεια φάνη ῥοδοδάκτυλος Ἠώς, -->
а когда показалась ранорожденная розоперстая Эос,

<!-- grc: καὶ τότ᾽ ἐγὼν ἀγορὴν θέμενος μετὰ πᾶσιν ἔειπον: -->
и тогда я, учредив собрание, среди всех сказал:

<!-- grc: ‘ἄλλοι μὲν νῦν μίμνετ᾽, ἐμοὶ ἐρίηρες ἑταῖροι: -->
"прочие сейчас оставайтесь, мои верные товарищи;

<!-- grc: αὐτὰρ ἐγὼ σὺν νηί τ᾽ ἐμῇ καὶ ἐμοῖς ἑτάροισιν -->
а я с кораблем моим и моими товарищами

<!-- grc: ἐλθὼν τῶνδ᾽ ἀνδρῶν πειρήσομαι, οἵ τινές εἰσιν, -->
придя, этих мужей испытаю, каковы они,

<!-- grc: ἤ ῥ᾽ οἵ γ᾽ ὑβρισταί τε καὶ ἄγριοι οὐδὲ δίκαιοι, -->
наглецы ли они и дикие и несправедливые,

<!-- grc: ἦε φιλόξεινοι, καί σφιν νόος ἐστὶ θεουδής. -->
или гостеприимные, и у них ум богобоязненный."


### Odyss. IX.177–180

<!-- grc: ’ ὣς εἰπὼν ἀνὰ νηὸς ἔβην, ἐκέλευσα δ᾽ ἑταίρους -->
так сказав, на корабль я взошел, и приказал, чтобы товарищи

<!-- grc: αὐτούς τ᾽ ἀμβαίνειν ἀνά τε πρυμνήσια λῦσαι. -->
сами взошли и кормовые канаты отвязали;

<!-- grc: οἱ δ᾽ αἶψ᾽ εἴσβαινον καὶ ἐπὶ κληῖσι καθῖζον, -->
а они сразу стали входить и на скамьи для гребцов садиться,

<!-- grc: ἑξῆς δ᾽ ἑζόμενοι πολιὴν ἅλα τύπτον ἐρετμοῖς. -->
и по порядку садясь, седое море стали бить веслами.
"""

# Citation-only reference; translation itself is in copyright and not
# reproduced (see the embedded <!-- --> comment for full attribution).
_STARIKOVSKY_REF = """\
## Стариковский (reference only, not reproduced)

<!-- Г. Стариковский, Одиссея (пер. с др.-греч., тактовик вместо гексаметра; изд-во «Носорог» совместно с Jaromír Hladík press, ноябрь 2025). Переводчик жив, перевод под охраной авторского права, НЕ воспроизводится здесь. Страница издательства: https://nosorog.media/tproduct/418921535-224857850372-odisseya -->

*(Not reproduced here -- in copyright; see the citation above.)*
"""



def populate_translations_ru() -> None:
    interlinear_ru = _INTERLINEAR_RU_I.rstrip("\n") + "\n\n" + _strip_header(_INTERLINEAR_RU_IX)
    starikovsky_ref = _STARIKOVSKY_REF.rstrip("\n")
    zhukovsky = _ZHUKOVSKY_I.rstrip("\n") + "\n\n" + _strip_header(_ZHUKOVSKY_IX)
    veresaev = _VERESAEV_I.rstrip("\n") + "\n\n" + _strip_header(_VERESAEV_IX)
    body = (
        interlinear_ru + "\n\n---\n\n" + starikovsky_ref + "\n\n---\n\n"
        + zhukovsky + "\n\n---\n\n" + veresaev + "\n"
    )
    sources = [
        Source(id="tr-zhukovsky1849", resource="https://ru.wikisource.org/wiki/Одиссея_(Гомер;_Жуковский)",
               title="Одиссея", author="В. А. Жуковский"),
        Source(id="tr-veresaev1953", resource="http://az.lib.ru/g/gomer/text_0070.shtml",
               title="Одиссея", author="В. В. Вересаев"),
        _GRC_MURRAY1919_SOURCE,
    ]
    concept = build(
        work="Odyssey", passage="I.1-21, IX.19-180", language="ru",
        translators=["подстрочник", "Жуковский", "Вересаев", "Стариковский (reference only)"],
        body=body, sources=sources,
        description=(
            "ru translations of Odyssey I.1-21, IX.19-180: подстрочник, "
            "Жуковский, Вересаев, plus a citation-only reference to "
            "G. Starikovsky's 2025 translation (taktovnik, not hexameter), "
            "which is in copyright -- not reproduced here."
        ),
    )
    write(concept, _TEXTS_DIR / "translations_ru.md")


# Copied verbatim via:
#   git -C ~/work/greek/git/codeberg.org/EEE-project/created_with_eee \
#     show translations:odyssey/2026_06_01/translations_el.md
# -- the "## Πολυλάς" section only (up to, not including, "## Καζαντζάκης–Κακριδής").
_POLYLAS_I = """\
## Πολυλάς

<!-- Πολυλάς Ι. Ὀδύσσεια. Ἀθήνα, 1875 · https://www.openbook.gr/omirou-odysseia-metafrasi/ -->
<!-- **Πολυλάς, 1875/1877** · I.1-21 [openbook.gr ↗](https://www.openbook.gr/omirou-odysseia-metafrasi/) · IX.19-38 [gutenberg.org ↗](https://www.gutenberg.org/files/30614/30614-0.txt) (archived 22.09.2026: https://web.archive.org/web/20260922111612/https://www.gutenberg.org/files/30614/30614-0.txt) · ν.ε., Καθαρεύουσα · κανονική νεοελληνική μετάφραση του 19ου αι. · κλασικό λογοτεχνικό ύφος -->

### Odyss. I.1–5

Πες μου, θεά, τ' ἀνδρὸς τὸν πολύτροπον, ὅπου πλανήθη τόσο
ἀφότου τῆς Τροίας τὸ ἱερὸ κάστρο χάλασε·
πολλῶν ἀνθρώπων τὰ ἄστη εἶδε κι ἔγνωσε τὸν νοῦ τους,
πολλὰ κι ἔπαθε στὴ θάλασσα ἀλγέα μέσα στὴν ψυχή του,
παλεύοντας γιὰ τὴ ζωή του καὶ γιὰ τὸ νόστο τῶν ἑταίρων.

### Odyss. I.6–10

Μὰ μήτε ὡς τόσο τοὺς ἑταίρους του ἔσωσε, ποὺ τόσο φιλοτιμήθη·
γιατὶ χάθηκαν ἀπὸ τὴ δική τους τὴν ἀτασθαλία,
νήπιοι, ποὺ τοῦ Ἡλίου Ὑπερίωνα τοὺς βόες ἔφαγαν·
κι αὐτὸς τοὺς ἀφαίρεσε τὴν ἡμέρα τοῦ γυρισμοῦ.
Ἀπ' ὁπουδήποτε, θεά, κόρη τοῦ Δία, πές μας κι ἐμᾶς.

### Odyss. I.11–15

Ἐκεῖ οἱ ἄλλοι ὅλοι, ὅσοι γλύτωσαν τὸν αἰπὺν ὄλεθρο,
ἦταν στὸ σπίτι, τὸν πόλεμο καὶ τὴ θάλασσα γλυτώσαντες·
αὐτὸν μόνον, ποὺ λαχταροῦσε νόστο καὶ γυναίκα,
νύμφη ἡ πότνια τὸν κρατοῦσε, ἡ Καλυψώ, θεία στὶς θεές,
στὶς κοίλες σπηλιές, ποθώντας νὰ τὴν πάρει γιὰ ἄντρα της.

### Odyss. I.16–21

Μὰ ὅταν πέρασαν τὰ χρόνια κι ἦρθε ἐκεῖνο τὸ ἔτος,
ποὺ οἱ θεοὶ τοῦ ἔκλωσαν νὰ γυρίσει στὸ σπίτι του,
στὴν Ἰθάκη, μήτε ἐκεῖ γλύτωσε τοὺς ἄθλους
μέσα στοὺς δικούς του. Οἱ θεοὶ τὸν λυπήθηκαν ὅλοι,
ἐκτὸς ἀπὸ τὸν Ποσειδῶνα· αὐτὸς ἀδιάκοπα ὀργιζόταν
στὸν ἰσόθεο Ὀδυσσέα, ὣς νὰ φτάσει στὴ γῆ του.

"""

# Sourced 2026-09-08 from Project Gutenberg ebook #30614 (Ομήρου Οδύσσεια,
# Τόμος Β΄, Athens: G. D. Fexis, 1877; transcr. Sophia Canoni),
# https://www.gutenberg.org/files/30614/30614-0.txt -- cross-verified
# word-for-word against users.sch.gr's independent transcription of the
# same passage. Source-edition line-reference numbers stripped (not part
# of the translated text).
_POLYLAS_IX = """\
## Πολυλάς

<!-- Polylas I. Ομήρου Οδύσσεια, Τόμος Β΄ (Ραψωδίες Η–Μ). Athens: Georgios D. Fexis, 1877 (Project Gutenberg ebook #30614, transcr. Sophia Canoni) · https://www.gutenberg.org/files/30614/30614-0.txt -->
<!-- **Πολυλάς, 1877** · [gutenberg.org ↗](https://www.gutenberg.org/files/30614/30614-0.txt) · ν.ε., Καθαρεύουσα · line-for-line verse rendering · cross-verified against an independent second transcription (users.sch.gr), word-for-word match -->

### Odyss. IX.19–24

εγώ 'μαι ο δολομήχανος Λαερτιάδης Οδυσσέας,
και από την γη 'ς τους ουρανούς η δόξα μου έχει φθάσει.
και κατοικώ την ηλιακήν Ιθάκη, 'π' όρος έχει
μεγάλο κινησίφυλλο, το Νήριτο, και γύρω
νησιά πολλά, και σύνεγγυς το 'να με τ' άλλο, υπάρχουν,
Δουλίχιο, Σάμη, Ζάκυνθος η πολυδενδρωμένη•

### Odyss. IX.25–28

κείνη 'ς το πέλαο χαμηλή βαθειά την δύσι βλέπει,
και όλαις η άλλαις χωριστά προς της αυγής τα μέρη•
πετρώδης, αλλ' ανδρών καλή βυζάστρα• κ' εγώ άλλο
πράγμα δεν δύναμαι να ιδώ γλυκότερο απ' την γην μου.

### Odyss. IX.29–33

και ιδές, μ' εκράτ' η Καλυψώ, σεπτή θεά, μεγάλη,
'ς τα κοίλα σπήλαια, και άνδρας της επόθει να της ήμαι•
όμοια και η Κίρκη εκράτει με, η δολερή Αιαία,
'ς τα μέγαρά της, και άνδρας της επόθει να της ήμαι•
αλλά ποτέ δεν έπεισαν 'ς τα στήθη την ψυχή μου.

### Odyss. IX.34–38

αχ! τίποτε γλυκότερο δεν έχει απ' την πατρίδα
και απ' τους γονείς ο άνθρωπος, και σπίτι ευτυχισμένο
εις ξένην γην αν κατοικεί μακράν απ' τους γονείς του.
τώρ' άκουσε το θλιβερό ταξείδι, 'που εις εμένα,
ως απ' την Τροίαν έγερνα, διώρισεν ο Δίας.

### Odyss. IX.39–42

Απ' το Ίλιο μ' έφερ' άνεμος 'ς την άκραν των Κικόνων,
την Ίσμαρο• κ' εξέκαμα την πόλι και τους άνδραις•
Και όσαις γυναίκαις πήραμε και πλούτη από την πόλι,
ίσια τα μοιρασθήκαμε να μη κλαυθή κανένας.

### Odyss. IX.43–46

και τότ' εγώ να φύγουμεν εκείθ' ευθύς με βία
παρακινούσα, αλλ' οι μωροί ν' ακούσουν δεν ήθελαν.
και αυτού πίνονταν άδολο κρασί πολύ, κ' εσφάζαν
εις τ' ακρογιάλι αρνιά πολλά και στριφοπόδα βώδια.

### Odyss. IX.47–50

πήγαν ωστόσο οι Κίκονες τους Κίκοναις να κράξουν,
γείτοναις, 'που πλειότεροι και ανδρειότεροι απ' εκείνους
εκατοικούσαν 'ς την στερηά, και απ' τ' άλογα εγνωρίζαν
να πολεμούν, ή και πεζοί, αν το 'θελεν η ανάγκη.

### Odyss. IX.51–55

τόσ' ήλθαν, όσ' η άνοιξι φύλλα φυτρόνει και άνθη,
πρωί• τότ' ήλθε του Διός μοίρα κακή κοντά μας
των δύστυχων, όπ' έμελλε πολλά να φέρη πάθη.
την μάχη στήσαν και άρχισαν προς τα γοργά καράβια,
και απ' τα δυο μέρη ερρίχνονταν τα χάλκινα κοντάρια.

### Odyss. IX.56–61

και όσ' ήτο αυγή και τ' άγιο φως αύξαινε της ημέρας,
προς τους πολλούς τον πόλεμον κρατούσαμεν οι ολίγοι•
αλλ' άμ' ο ήλιος έγερνεν, όταν τα βώδια λυώνται,
τους Αχαιούς εσύντριψαν οι Κίκονες κ' εσπρώξαν.
έξι ανδρειωμένοι σύντροφοι μέσ' από κάθε πλοίο
χάθηκαν και απ' τον θάνατον σωθήκαμεν οι άλλοι.

### Odyss. IX.62–66

θλιμμένοι εμπρός επλέαμεν, μακράν από τον χάρο
πρόθυμ', αλλά των ποθητών συντρόφων στερημένοι.
αλλά δεν μου ξεκίνησαν τα ισόμετρα καράβια,
πριν τρεις φωνάξουμε φοραίς τους άμοιρους συντρόφους,
όσους 'ς τον κάμπον έστρωσαν τ' ακόντια των Κικόνων.

### Odyss. IX.67–71

και ο Δίας μας εσήκωσεν ο νεφελοσυνάκτης
ζάλην φρικτήν απ' τον Βορηά, κ' ετύλιξε 'ς τα νέφη
πόντον και γην, κ' εχύθηκεν απ' τον αιθέρα νύκτα•
κ' έτρεχαν επικέφαλα, και τα πανιά τους όλα
έσχισεν, ετετάρτιασεν η δύναμι του ανέμου,

### Odyss. IX.72–75

κάτω τα εσύραμεν ευθύς, μη μας καταποντίσουν,
και λάμνοντας εφέραμεν εις την στερηά τα πλοία.
ασάλευτοι αυτού μείναμε δυο 'μέραις και δυο νύκταις,
και την καρδιά μας έτρωγεν η μέριμνα και ο κόπος.

### Odyss. IX.76–78

η τρίτη ως έλαμψεν αυγή, τα κάτασπρα πανία
εις τα κατάρτια απλώσαμε, καθίσαμε και ωδήγαν
τα πλοία μας ο άνεμος ομού και οι κυβερνήταις.

### Odyss. IX.79–81

και άβλαπτος τότε θα' φθανα 'ς την ποθητήν πατρίδα,
αλλ' ως τον Μαληά γύριζα, το κύμα και το ρεύμα
και ο Βορηάς πολύ μακράν μ' έδιωξαν των Κυθήρων.

### Odyss. IX.82–86

κατόπιν άνεμοι κακοί μ' έδερναν εννηά 'μέραις,
'ς την ιχθυοφόρα θάλασσαν ήλθαμε την δεκάτη
των Λωτοφάγων εις την γη, 'πώχουν τροφή τους άνθη.
'ς την γην εβγήκαμε, νερό επήραμε από βρύσι,
και οι σύντροφοι εγευμάτισαν προς τα γοργά καράβια.

### Odyss. IX.87–90

και το φαγί και το πιοτό άμα ευφρανθήκαμ' όλοι,
τότε συντρόφους έστειλα, να υπάγουν και να μάθουν
ποιοι σιτοφάγοι άνθρωποι 'ς την γην εκείνην ήσαν,
δύο διαλεκτούς, και κήρυκα μ' αυτούς έσμιξα τρίτον.

### Odyss. IX.91–93

επήγαν κ' επλησίασαν τους Λωτοφάγους άνδραις,
και τούτοι των συντρόφων μας κακό δεν μελετούσαν
κανένα, αλλά τους έδωσαν λωτό να δοκιμάσουν.

### Odyss. IX.94–97

και άμα εγευόνταν τον καρπό, 'που ήταν γλυκός 'σαν μέλι,
να γύρουν πλειά δεν έστεργαν, ουδ' είδησι να φέρουν.
αλλά να μένουν ήθελαν σιμά των Λωτοφάγων,
λωτό να τρώγουν, την γλυκειά πατρίδα λησμονώντας.

### Odyss. IX.98–104

εις τα καράβια εγώ με βια τους γύρισα κ' εκλαίαν,
και εις τα ζυγ' αποκάτωθε τους έσυρα δεμένους.
ν' αναιβούν τότ' επρόσταξα των άλλων των συντρόφων
'ς τα γοργά πλοία με σπουδή, μη κάποιος απ' εκείνους
φάγη λωτό, και την γλυκειά πατρίδα λησμονήση.
εμπήκαν, αραδιάσθηκαν εις τα σανίδια κείνοι,
και την λευκή την θάλασσα με τα κουπιά βροντούσαν.

### Odyss. IX.105–111

Εκείθ' επλέαμεν εμπρός με την ψυχή θλιμμένη.
και των Κυκλώπων εις την γη, των υβριστών, ανόμων,
εφθάσαμε, οπού 'ς των θεών την δύναμι θαρρώντας,
ούτε φυτό φυτεύουσιν, ούτε πότ' αλατρεύουν,
αλλ' άσπαρτ', αναλάτρευτα, τα πάντα εκεί φυτρόνουν,
σίτοι, κριθάρια, και άμπελοι, και δίδει κρασί πλήθος
ο μεγαστάφυλος καρπός, καθώς τον βρέχει ο Δίας.

### Odyss. IX.112–115

βουλών δεν έχουν αγοραίς, και νόμους δεν γνωρίζουν,
αλλά ταις άκραις κατοικούν βουνών υψηλοτάτων
εις βαθειά σπήλαια, και καθείς 'ς την σύντροφο, 'ς τα τέκνα
είναι κριτής, ουδέποτε προσέχει προς τον άλλον.

### Odyss. IX.116–121

Άγριον απλόνεται νησί παρέξω απ' τον λιμένα,
ούτε σιμά, και ούτε μακράν της χώρας των Κυκλώπων,
σύδενδρο, και αγριόγιδα 'ς εκείνο μέσα βόσκουν,
αμέτρητα• ότι πάτημα δεν τα εμποδίζει ανθρώπων,
ουδέ κει μπαίνουν κυνηγοί, 'που συνηθούν 'ς τα δάση
να δέρνωνται, αναβαίνοντας ράχαις και κορφοβούνια.

### Odyss. IX.122–124

ποίμνια δεν το σκεπάζουσι, και αλέτρια δεν το σχίζουν,
αλλ' άσπαρτο, αναλάτρευτο, και ολόρφανο απ' ανθρώπους
ολοκαιρής, είναι βοσκή 'ς τα γίδια 'που βελάζουν.

### Odyss. IX.125–129

τι πλοία κοκκινόπλωρα οι Κύκλωπες δεν έχουν,
ούτ' έχουν πλοίων ξυλουργούς, 'που εκείνων θα εμορφόναν
καλόστρωτα πλεούμενα, χρήσιμα να 'ναι εις όλα,
'ς ταις πολιτείαις φθάνοντας, ως τους ανθρώπους βλέπεις
το πέλαο να συχνοπερνούν απ' το 'να εις τ' άλλο μέρος•

### Odyss. IX.130–133

και αυτοί θα τους εσύσταιναν καλόκτιστην την νήσο.
κακή δεν είναι• θα 'φερνε κάθε καρπό 'ς την ώρα,
ότι της λευκής θάλασσας 'ς την άκρη τα λειβάδια
υγρά θωρείς και μαλακά• και άφθαρτ' αμπέλια θα 'χε•

### Odyss. IX.134–139

και για τ' αλέτρ' είναι ομαλή• τον σίτο 'ς τον καιρό του
βαθειά πολύ θα εθέριζαν, ότ' είναι η γη παχεία.
κ' έχει λιμέν' ακίνδυνον, οπού σχοινιά δεν θέλει,
είτε να ρίχνουν άγκυραν, είτε να δένουν πρύμη,
αλλ' αραγμένοι προς την γη να μένουν, ως 'που οι ναύταις
να ξεκινήσουν πρόθυμα, άμα φυσήση πρύμος.

### Odyss. IX.140–141

και εις του λιμένα την κορφή νερό καθάριο ρέει,
άντρο αποκάτω μια πηγή, και ολόγυρα έχει λεύκαις.

### Odyss. IX.142–145

αυτού εμπαίναμε• θεός κάποιος μας οδηγούσε,
'ς το σκότος μέσα της νυκτός, 'π' αθώρητα ήσαν όλα.
ότι καταχνιά κύκλονε τα πλοία, και η σελήνη
δεν έφεγγε απ' τον ουρανό και νέφη την εκρύβαν.

### Odyss. IX.146–151

και το νησί δεν ξάνοιξε κανείς μας με τα μάτια,
ουδέ τα μακρυά κύματα 'ς την γην όπως κυλούσαν
είδαμε, πριν τα πλοία μας 'ς την άκρα προσαράξουν.
και άμ' άραξαν, εσύραμε κατ' όλα τα πανιά τους,
'ς την γην εβγήκαμε κ' εμείς, και, αφού πήραμ' ολίγον
ύπνον, επεριμέναμεν η άφθαρτ' Ηώ να φέξη.

### Odyss. IX.152–155

Εφάν' η ροδοδάκτυλη Ηώ του όρθρου κόρη,
και το νησί θαυμάζοντας γερνούσαμε άνω, κάτω.
και η νύμφαις, κόραις του Διός, απ' τα όρη ξεκινήσαν
τα γίδια, ναύρουν έτοιμο το γεύμα οι σύντροφοί μου.

### Odyss. IX.156–160

τα τόξ' αμέσως τα κυρτά και τα μακρυν' ακόντια
απ' το καράβι πήραμε, και, εις τρεις βαλμένοι τάξεις,
ρίχναμε, κ' έδωσε ο θεός ευφραντικό κυνήγι.
μ' ακολουθούσαν δώδεκα πλοία, και εις το καθένα
εννέα γίδες έμειναν, αφού μου δώσαν δέκα.

### Odyss. IX.161–165

αυτού τότ' εκαθόμασθε, ολημέρα ως το δείλι
μ' άφθονο κρέας, με κρασί γλυκό φαγοποτώντας.
ότι το κόκκινο κρασί δεν είχε λείψει ακόμη
'ς τα πλοία, τ' είχαμε ο καθείς γεμίσει ταις λαγήναις,
την ιερή 'σαν πήραμε την πόλι των Κικόνων.

### Odyss. IX.166–169

και των Κυκλώπων βλέπαμε την γη, 'που ήταν πλησίον,
και τον καπνό, και την φωνήν αυτών και των προβάτων.
και ο ήλιος άμα εβύθισε κ' ήλθε κατόπ' η νύκτα,
εμείς αναπαυθήκαμε 'ς την άκρα της θαλάσσης.

### Odyss. IX.170–176

εφάν' η ροδοδάκτυλη Ηώ του όρθρου κόρη,
κ' έκαμα εγώ συνάθροισι και μέσα εις όλους είπα•
«σεις οι άλλοι φίλοι σύντροφοι, να μείνετ' εδώ τώρα•
εγώ με τα καράβι μου και με τους ιδικούς μου
συντρόφους θέλα πάω να ιδώ να μάθω τίνες είναι
οι άνθρωποι τούτοι, είναι υβρισταίς, άγριοι και όχι δίκαιοι,
ή τε φιλόξενοι και αυτών θεόφοβ' είναι η γνώμη».

### Odyss. IX.177–180

Και εις το καράβι ανέβηκα και των συντρόφων είπα
να λύσουν τα πρυμόσχοινα και ν' αναιβούν• κ' εκείνοι
εμπήκαν και αραδιάσθηκαν ευθύς εις ταις σανίδαις,
και την λευκή την θάλσσα με τα κουπιά βροντούσαν.

"""


def populate_translations_el() -> None:
    polylas = _POLYLAS_I.rstrip("\n") + "\n\n" + _strip_header(_POLYLAS_IX)
    interlinear = _INTERLINEAR_EL_I.rstrip("\n") + "\n\n" + _strip_header(_INTERLINEAR_EL_IX)
    kazantzakis_ref = _KAZANTZAKIS_REF.rstrip("\n")
    body = polylas + "\n\n---\n\n" + interlinear + "\n\n---\n\n" + kazantzakis_ref + "\n"
    sources = [
        Source(id="tr-polylas1875", resource="https://www.openbook.gr/omirou-odysseia-metafrasi/",
               title="Ομήρου Οδύσσεια, Τόμος Α΄", author="Ιάκωβος Πολυλάς"),
        Source(id="tr-polylas1877", resource="https://www.gutenberg.org/files/30614/30614-0.txt",
               title="Ομήρου Οδύσσεια, Τόμος Β΄", author="Ιάκωβος Πολυλάς"),
        _GRC_MURRAY1919_SOURCE,
    ]
    concept = build(
        work="Odyssey", passage="I.1-21, IX.19-180", language="el",
        translators=["Πολυλάς", "interlinear_el", "Καζαντζάκης/Κακριδής (reference only)"],
        body=body, sources=sources,
        description=(
            "el translations of Odyssey I.1-21, IX.19-180: Πολυλάς, "
            "interlinear_el, plus a citation-only reference to the "
            "Καζαντζάκης-Κακριδής translation (1965), which is in "
            "copyright -- not reproduced here."
        ),
    )
    write(concept, _TEXTS_DIR / "translations_el.md")


# Authored fresh 2026-09-14 (not ported -- the abandoned branch's I.1-21
# "interlinear" content was judged unfit, see the 2026-09-08 CHANGELOG
# entry below and the IX.19-38 constant's own comment for why). Word-by-
# word gloss for I.1-21, matching the established format and hyphenation
# convention of the already-verified IX.19-38 interlinear content.
#
# "interlinear" is folded into translations_en.md as its own ## section
# (like every other translator) rather than a separate file -- the only
# per-stanza wrinkle is that each Greek source line is echoed as an
# HTML-comment annotation (<!-- grc: ... -->, stripped by GreekUtils.
# strip_comment_lines()) rather than appearing as visible text, so the
# gloss line that follows it reads as the section's actual "translation".
_INTERLINEAR_EN_I = """\
## interlinear_en

### Odyss. I.1–5

<!-- grc: Ἄνδρα μοι ἔννεπε, μοῦσα, πολύτροπον, ὃς μάλα πολλὰ -->
man to-me tell, Muse, much-wandering, who very much

<!-- grc: πλάγχθη, ἐπεὶ Τροίης ἱερὸν πτολίεθρον ἔπερσεν· -->
wandered, when of-Troy sacred citadel he-sacked;

<!-- grc: πολλῶν δ' ἀνθρώπων ἴδεν ἄστεα καὶ νόον ἔγνω, -->
of-many and of-men he-saw cities and mind he-learned,

<!-- grc: πολλὰ δ' ὅ γ' ἐν πόντῳ πάθεν ἄλγεα ὃν κατὰ θυμόν, -->
many-things and he indeed in sea he-suffered pains in his-own heart,

<!-- grc: ἀρνύμενος ἥν τε ψυχὴν καὶ νόστον ἑταίρων. -->
striving-to-win his-own life and return of-comrades.

### Odyss. I.6–10

<!-- grc: ἀλλ' οὐδ' ὣς ἑτάρους ἐρρύσατο, ἱέμενός περ· -->
but not-even so comrades he-saved, eager though;

<!-- grc: αὐτῶν γὰρ σφετέρῃσιν ἀτασθαλίῃσιν ὄλοντο, -->
of-themselves for by-their-own recklessness they-perished,

<!-- grc: νήπιοι, οἳ κατὰ βοῦς Ὑπερίονος Ἠελίοιο -->
fools, who up cattle of-Hyperion Helios

<!-- grc: ἤσθιον· αὐτὰρ ὁ τοῖσιν ἀφείλετο νόστιμον ἦμαρ. -->
were-eating; but he from-them took-away the-day of-return.

<!-- grc: τῶν ἁμόθεν γε, θεά, θύγατερ Διός, εἰπὲ καὶ ἡμῖν. -->
of-these from-some-point indeed, goddess, daughter of-Zeus, tell also to-us.

### Odyss. I.11–15

<!-- grc: Ἔνθ' ἄλλοι μὲν πάντες, ὅσοι φύγον αἰπὺν ὄλεθρον, -->
then others all, as-many-as escaped sheer destruction,

<!-- grc: οἴκοι ἔσαν, πόλεμόν τε πεφευγότες ἠδὲ θάλασσαν· -->
at-home were, war and having-escaped and sea;

<!-- grc: τὸν δ' οἶον νόστου κεχρημένον ἠδὲ γυναικὸς -->
him but alone of-return longing and of-wife

<!-- grc: νύμφη πότνι' ἔρυκε Καλυψὼ δῖα θεάων -->
nymph lady was-holding, Calypso, divine of-goddesses,

<!-- grc: ἐν σπέσσι γλαφυροῖσι, λιλαιομένη πόσιν εἶναι. -->
in caves hollow, longing husband to-be.

### Odyss. I.16–21

<!-- grc: ἀλλ' ὅτε δὴ ἔτος ἦλθε περιπλομένων ἐνιαυτῶν, -->
but when indeed the-year came, the-seasons revolving,

<!-- grc: τῷ οἱ ἐπεκλώσαντο θεοὶ οἰκόνδε νέεσθαι -->
in-which for-him ordained the-gods homeward to-return,

<!-- grc: εἰς Ἰθάκην, οὐδ' ἔνθα πεφυγμένος ἦεν ἀέθλων -->
to Ithaca, not-even there escaped was he from-trials

<!-- grc: καὶ μετὰ οἷσι φίλοισι. θεοὶ δ' ἐλέαιρον ἅπαντες -->
even among his-own friends. the-gods and pitied all,

<!-- grc: νόσφι Ποσειδάωνος· ὁ δ' ἀσπερχὲς μενέαινεν -->
except Poseidon; he but ceaselessly raged

<!-- grc: ἀντιθέῳ Ὀδυσῆι πάρος ἥν γαῖαν ἱκέσθαι. -->
at-godlike Odysseus, before his-own land he-reached.

"""

# IX.19-38 half of the same interlinear_en section -- originally its own
# file (interlinear_en.md, 2026-09-08/09), refit into the new <!-- grc: -->
# marker (was bold **Greek line**) and merged here alongside I.1-21 above,
# same _strip_header() pattern as every other translator's _I/_IX split.
_INTERLINEAR_EN_IX = """\
## interlinear_en

### Odyss. IX.19–24

<!-- grc: εἶμ' Ὀδυσεὺς Λαερτιάδης, ὃς πᾶσι δόλοισιν -->
I-am Odysseus Laertiades, who with-all wiles

<!-- grc: ἀνθρώποισι μέλω, καί μευ κλέος οὐρανὸν ἵκει. -->
among-men am-known, and my fame heaven reaches.

<!-- grc: ναιετάω δ' Ἰθάκην εὐδείελον· ἐν δ' ὄρος αὐτῇ -->
I-dwell in Ithaca sun-bright; in it a mountain there

<!-- grc: Νήριτον εἰνοσίφυλλον, ἀριπρεπές· ἀμφὶ δὲ νῆσοι -->
Neritos leaf-quivering, conspicuous; around it islands

<!-- grc: πολλαὶ ναιετάουσι μάλα σχεδὸν ἀλλήλῃσι, -->
many dwell very close to-one-another,

<!-- grc: Δουλίχιόν τε Σάμη τε καὶ ὑλήεσσα Ζάκυνθος. -->
Doulichion and Same and wooded Zakynthos.

### Odyss. IX.25–28

<!-- grc: αὐτὴ δὲ χθαμαλὴ πανυπερτάτη εἰν ἁλὶ κεῖται -->
itself but low, most-remote in the sea lies

<!-- grc: πρὸς ζόφον, αἱ δέ τ' ἄνευθε πρὸς ἠῶ τ' ἠέλιόν τε, -->
toward the west; those further toward dawn and sun,

<!-- grc: τρηχεῖ', ἀλλ' ἀγαθὴ κουροτρόφος· οὔ τοι ἐγώ γε -->
rugged, yet good nurse-of-youth; truly I at-least

<!-- grc: ἧς γαίης δύναμαι γλυκερώτερον ἄλλο ἰδέσθαι. -->
of-my-own land can sweeter other see.

### Odyss. IX.29–33

<!-- grc: ἦ μέν μ' αὐτόθ' ἔρυκε Καλυψώ, δῖα θεάων, -->
truly indeed me there held Kalypso, glorious of-goddesses,

<!-- grc: ἐν σπέσσι γλαφυροῖσι, λιλαιομένη πόσιν εἶναι· -->
in caves hollow, longing husband to-be;

<!-- grc: ὣς δ' αὔτως Κίρκη κατερήτυεν ἐν μεγάροισιν -->
so likewise Kirke kept-back in her halls

<!-- grc: Αἰαίη δολόεσσα, λιλαιομένη πόσιν εἶναι· -->
Aiaian crafty, longing husband to-be;

<!-- grc: ἀλλ' ἐμὸν οὔ ποτε θυμὸν ἐνὶ στήθεσσιν ἔπειθον. -->
but my heart never in my breast could-they-persuade.

### Odyss. IX.34–38

<!-- grc: ὣς οὐδὲν γλύκιον ἧς πατρίδος οὐδὲ τοκήων -->
so nothing sweeter than one's-own homeland and parents

<!-- grc: γίγνεται, εἴ περ καί τις ἀπόπροθι πίονα οἶκον -->
is, even if someone afar a rich house

<!-- grc: γαίῃ ἐν ἀλλοδαπῇ ναίει ἀπάνευθε τοκήων. -->
in-land in foreign dwells far-from parents.

<!-- grc: εἰ δ' ἄγε τοι καὶ νόστον ἐμὸν πολυκηδέ' ἐνίσπω, -->
but come let-me-tell you my return full-of-cares,

<!-- grc: ὅν μοι Ζεὺς ἐφέηκεν ἀπὸ Τροίηθεν ἰόντι. -->
which to-me Zeus sent from Troy departing.

### Odyss. IX.39–42

<!-- grc: Ἰλιόθεν με φέρων ἄνεμος Κικόνεσσι πέλασσεν, -->
from-Ilion me carrying wind to-the-Cicones drove-near,

<!-- grc: Ἰσμάρῳ. ἔνθα δ᾽ ἐγὼ πόλιν ἔπραθον, ὤλεσα δ᾽ αὐτούς: -->
to-Ismarus. there and I city sacked, destroyed and them:

<!-- grc: ἐκ πόλιος δ᾽ ἀλόχους καὶ κτήματα πολλὰ λαβόντες -->
from city and wives and possessions many having-taken

<!-- grc: δασσάμεθ᾽, ὡς μή τίς μοι ἀτεμβόμενος κίοι ἴσης. -->
we-divided, so-that not anyone from-me being-deprived might-go of-equal-share.

### Odyss. IX.43–46

<!-- grc: ἔνθ᾽ ἦ τοι μὲν ἐγὼ διερῷ ποδὶ φευγέμεν ἡμέας -->
then indeed I with-nimble foot to-flee us

<!-- grc: ἠνώγεα, τοὶ δὲ μέγα νήπιοι οὐκ ἐπίθοντο. -->
was-urging, but-they greatly foolish not obeyed.

<!-- grc: ἔνθα δὲ πολλὸν μὲν μέθυ πίνετο, πολλὰ δὲ μῆλα -->
and-there much indeed wine was-being-drunk, and-many sheep

<!-- grc: ἔσφαζον παρὰ θῖνα καὶ εἰλίποδας ἕλικας βοῦς: -->
they-were-slaughtering beside shore, and shambling-footed curved-horned cattle:

### Odyss. IX.47–50

<!-- grc: τόφρα δ᾽ ἄρ᾽ οἰχόμενοι Κίκονες Κικόνεσσι γεγώνευν, -->
meanwhile then having-gone-off Cicones to-Cicones were-calling-out,

<!-- grc: οἵ σφιν γείτονες ἦσαν, ἅμα πλέονες καὶ ἀρείους, -->
who to-them neighbors were, both more-numerous and braver,

<!-- grc: ἤπειρον ναίοντες, ἐπιστάμενοι μὲν ἀφ᾽ ἵππων -->
mainland dwelling, knowing-how indeed from horses

<!-- grc: ἀνδράσι μάρνασθαι καὶ ὅθι χρὴ πεζὸν ἐόντα. -->
with-men to-fight, and where it-is-necessary on-foot being.

### Odyss. IX.51–55

<!-- grc: ἦλθον ἔπειθ᾽ ὅσα φύλλα καὶ ἄνθεα γίγνεται ὥρῃ, -->
they-came then, as-many-as leaves and flowers come-to-be in-season,

<!-- grc: ἠέριοι: τότε δή ῥα κακὴ Διὸς αἶσα παρέστη -->
at-dawn: then indeed evil of-Zeus fate came-upon

<!-- grc: ἡμῖν αἰνομόροισιν, ἵν᾽ ἄλγεα πολλὰ πάθοιμεν. -->
us ill-fated, so-that pains many we-might-suffer.

<!-- grc: στησάμενοι δ᾽ ἐμάχοντο μάχην παρὰ νηυσὶ θοῇσι, -->
having-drawn-up and they-fought battle beside ships swift,

<!-- grc: βάλλον δ᾽ ἀλλήλους χαλκήρεσιν ἐγχείῃσιν. -->
they-were-striking and one-another with-bronze-tipped spears.

### Odyss. IX.56–61

<!-- grc: ὄφρα μὲν ἠὼς ἦν καὶ ἀέξετο ἱερὸν ἦμαρ, -->
as-long-as dawn was and was-growing sacred day,

<!-- grc: τόφρα δ᾽ ἀλεξόμενοι μένομεν πλέονάς περ ἐόντας. -->
so-long defending-ourselves we-stood-firm, though-more-numerous being.

<!-- grc: ἦμος δ᾽ ἠέλιος μετενίσσετο βουλυτόνδε, -->
but-when sun was-turning-towards ox-loosing-time (evening),

<!-- grc: καὶ τότε δὴ Κίκονες κλῖναν δαμάσαντες Ἀχαιούς. -->
and then indeed Cicones turned-back, having-overpowered Achaeans.

<!-- grc: ἓξ δ᾽ ἀφ᾽ ἑκάστης νηὸς ἐυκνήμιδες ἑταῖροι -->
six and from each ship well-greaved comrades

<!-- grc: ὤλονθ᾽: οἱ δ᾽ ἄλλοι φύγομεν θάνατόν τε μόρον τε. -->
perished: and-the others we-escaped both-death and-doom.

### Odyss. IX.62–66

<!-- grc: ἔνθεν δὲ προτέρω πλέομεν ἀκαχήμενοι ἦτορ, -->
and-from-there onward we-sailed, grieving in-heart,

<!-- grc: ἄσμενοι ἐκ θανάτοιο, φίλους ὀλέσαντες ἑταίρους. -->
glad from death, dear having-lost comrades.

<!-- grc: οὐδ᾽ ἄρα μοι προτέρω νῆες κίον ἀμφιέλισσαι, -->
and-not indeed my onward ships went, curved-at-both-ends,

<!-- grc: πρίν τινα τῶν δειλῶν ἑτάρων τρὶς ἕκαστον ἀῦσαι, -->
before someone of-the wretched comrades, thrice each, to-call-out,

<!-- grc: οἳ θάνον ἐν πεδίῳ Κικόνων ὕπο δῃωθέντες. -->
who died on plain, by-Cicones having-been-slain.

### Odyss. IX.67–71

<!-- grc: νηυσὶ δ᾽ ἐπῶρσ᾽ ἄνεμον Βορέην νεφεληγερέτα Ζεὺς -->
and-upon-ships roused North-wind, cloud-gathering Zeus,

<!-- grc: λαίλαπι θεσπεσίῃ, σὺν δὲ νεφέεσσι κάλυψε -->
with-supernatural storm-blast, and-together-with clouds covered

<!-- grc: γαῖαν ὁμοῦ καὶ πόντον: ὀρώρει δ᾽ οὐρανόθεν νύξ. -->
earth together-and sea: had-risen and from-heaven night.

<!-- grc: αἱ μὲν ἔπειτ᾽ ἐφέροντ᾽ ἐπικάρσιαι, ἱστία δέ σφιν -->
they (ships) indeed then were-carried aslant, and-their sails

<!-- grc: τριχθά τε καὶ τετραχθὰ διέσχισεν ἲς ἀνέμοιο. -->
into-three and into-four tore-apart force of-wind.

### Odyss. IX.72–75

<!-- grc: καὶ τὰ μὲν ἐς νῆας κάθεμεν, δείσαντες ὄλεθρον, -->
and them (sails) indeed into ships we-lowered, having-feared destruction,

<!-- grc: αὐτὰς δ᾽ ἐσσυμένως προερέσσαμεν ἤπειρόνδε. -->
and-them (ships) hastily we-rowed-forward toward-mainland.

<!-- grc: ἔνθα δύω νύκτας δύο τ᾽ ἤματα συνεχὲς αἰεὶ -->
there two nights and-two days continuously always

<!-- grc: κείμεθ᾽, ὁμοῦ καμάτῳ τε καὶ ἄλγεσι θυμὸν ἔδοντες. -->
we-lay, together with-toil and with-pains heart consuming.

### Odyss. IX.76–78

<!-- grc: ἀλλ᾽ ὅτε δὴ τρίτον ἦμαρ ἐυπλόκαμος τέλεσ᾽ Ἠώς, -->
but when indeed third day fair-tressed brought-to-completion Dawn,

<!-- grc: ἱστοὺς στησάμενοι ἀνά θ᾽ ἱστία λεύκ᾽ ἐρύσαντες -->
masts having-set-up, and-up white-sails having-hoisted,

<!-- grc: ἥμεθα, τὰς δ᾽ ἄνεμός τε κυβερνῆταί τ᾽ ἴθυνον. -->
we-sat, and-them both-wind and-helmsmen were-steering.

### Odyss. IX.79–81

<!-- grc: καί νύ κεν ἀσκηθὴς ἱκόμην ἐς πατρίδα γαῖαν: -->
and now indeed unharmed I-would-have-reached fatherland:

<!-- grc: ἀλλά με κῦμα ῥόος τε περιγνάμπτοντα Μάλειαν -->
but me wave and-current, rounding Malea,

<!-- grc: καὶ Βορέης ἀπέωσε, παρέπλαγξεν δὲ Κυθήρων. -->
and North-wind drove-off, and-drove-astray past-Cythera.

### Odyss. IX.82–86

<!-- grc: ἔνθεν δ᾽ ἐννῆμαρ φερόμην ὀλοοῖς ἀνέμοισιν -->
and-from-there for-nine-days I-was-borne by-destructive winds

<!-- grc: πόντον ἐπ᾽ ἰχθυόεντα: ἀτὰρ δεκάτῃ ἐπέβημεν -->
over fish-teeming sea: but on-tenth (day) we-landed

<!-- grc: γαίης Λωτοφάγων, οἵ τ᾽ ἄνθινον εἶδαρ ἔδουσιν. -->
on-land of-Lotus-eaters, who flowery food eat.

<!-- grc: ἔνθα δ᾽ ἐπ᾽ ἠπείρου βῆμεν καὶ ἀφυσσάμεθ᾽ ὕδωρ, -->
and-there onto mainland we-stepped and we-drew water,

<!-- grc: αἶψα δὲ δεῖπνον ἕλοντο θοῇς παρὰ νηυσὶν ἑταῖροι. -->
and-quickly meal took, beside swift ships, comrades.

### Odyss. IX.87–90

<!-- grc: αὐτὰρ ἐπεὶ σίτοιό τ᾽ ἐπασσάμεθ᾽ ἠδὲ ποτῆτος, -->
but when of-food we-partook and of-drink,

<!-- grc: δὴ τοτ᾽ ἐγὼν ἑτάρους προΐειν πεύθεσθαι ἰόντας, -->
then indeed I comrades sent-forth to-inquire, going,

<!-- grc: οἵ τινες ἀνέρες εἶεν ἐπὶ χθονὶ σῖτον ἔδοντες -->
what-sort-of men might-be, upon this-land grain-eating

<!-- grc: ἄνδρε δύω κρίνας, τρίτατον κήρυχ᾽ ἅμ᾽ ὀπάσσας. -->
two-men having-chosen, as-third a-herald together having-sent-along.

### Odyss. IX.91–93

<!-- grc: οἱ δ᾽ αἶψ᾽ οἰχόμενοι μίγεν ἀνδράσι Λωτοφάγοισιν: -->
and-they quickly having-gone mingled with-men Lotus-eaters:

<!-- grc: οὐδ᾽ ἄρα Λωτοφάγοι μήδονθ᾽ ἑτάροισιν ὄλεθρον -->
and-not indeed Lotus-eaters were-plotting for-comrades destruction

<!-- grc: ἡμετέροις, ἀλλά σφι δόσαν λωτοῖο πάσασθαι. -->
our, but to-them gave of-lotus to-taste.

### Odyss. IX.94–97

<!-- grc: τῶν δ᾽ ὅς τις λωτοῖο φάγοι μελιηδέα καρπόν, -->
and-of-them whoever of-lotus might-eat honey-sweet fruit,

<!-- grc: οὐκέτ᾽ ἀπαγγεῖλαι πάλιν ἤθελεν οὐδὲ νέεσθαι, -->
no-longer to-report back wished, nor to-return,

<!-- grc: ἀλλ᾽ αὐτοῦ βούλοντο μετ᾽ ἀνδράσι Λωτοφάγοισι -->
but there wished, among men Lotus-eaters,

<!-- grc: λωτὸν ἐρεπτόμενοι μενέμεν νόστου τε λαθέσθαι. -->
lotus grazing-on, to-remain and of-return to-forget.

### Odyss. IX.98–104

<!-- grc: τοὺς μὲν ἐγὼν ἐπὶ νῆας ἄγον κλαίοντας ἀνάγκῃ, -->
them indeed I to ships led, weeping, by-force,

<!-- grc: νηυσὶ δ᾽ ἐνὶ γλαφυρῇσιν ὑπὸ ζυγὰ δῆσα ἐρύσσας. -->
and-in hollow ships under benches I-bound, having-dragged.

<!-- grc: αὐτὰρ τοὺς ἄλλους κελόμην ἐρίηρας ἑταίρους -->
but the others I-urged, trusty comrades,

<!-- grc: σπερχομένους νηῶν ἐπιβαινέμεν ὠκειάων, -->
hastening, of-ships to-board, swift,

<!-- grc: μή πώς τις λωτοῖο φαγὼν νόστοιο λάθηται. -->
lest somehow anyone of-lotus having-eaten, of-return should-forget.

<!-- grc: οἱ δ᾽ αἶψ᾽ εἴσβαινον καὶ ἐπὶ κληῖσι καθῖζον, -->
and-they quickly were-boarding, and upon benches were-sitting,

<!-- grc: ἑξῆς δ᾽ ἑζόμενοι πολιὴν ἅλα τύπτον ἐρετμοῖς. -->
and-in-order seated, gray sea were-striking with-oars.

### Odyss. IX.105–111

<!-- grc: ἔνθεν δὲ προτέρω πλέομεν ἀκαχήμενοι ἦτορ: -->
and-from-there onward we-sailed, grieving in-heart:

<!-- grc: Κυκλώπων δ᾽ ἐς γαῖαν ὑπερφιάλων ἀθεμίστων -->
and-to land of-Cyclopes, arrogant, lawless,

<!-- grc: ἱκόμεθ᾽, οἵ ῥα θεοῖσι πεποιθότες ἀθανάτοισιν -->
we-came, who indeed trusting in-immortal gods

<!-- grc: οὔτε φυτεύουσιν χερσὶν φυτὸν οὔτ᾽ ἀρόωσιν, -->
neither plant with-hands a-plant, nor plow,

<!-- grc: ἀλλὰ τά γ᾽ ἄσπαρτα καὶ ἀνήροτα πάντα φύονται, -->
but these, unsown and unplowed, all grow,

<!-- grc: πυροὶ καὶ κριθαὶ ἠδ᾽ ἄμπελοι, αἵ τε φέρουσιν -->
wheat and barley and vines, which bear

<!-- grc: οἶνον ἐριστάφυλον, καί σφιν Διὸς ὄμβρος ἀέξει. -->
wine rich-clustered, and for-them Zeus's rain makes-grow.

### Odyss. IX.112–115

<!-- grc: τοῖσιν δ᾽ οὔτ᾽ ἀγοραὶ βουληφόροι οὔτε θέμιστες, -->
and-for-them neither counsel-bearing assemblies nor laws,

<!-- grc: ἀλλ᾽ οἵ γ᾽ ὑψηλῶν ὀρέων ναίουσι κάρηνα -->
but they, of-high mountains, inhabit peaks

<!-- grc: ἐν σπέσσι γλαφυροῖσι, θεμιστεύει δὲ ἕκαστος -->
in hollow caves, and-each-one lays-down-law

<!-- grc: παίδων ἠδ᾽ ἀλόχων, οὐδ᾽ ἀλλήλων ἀλέγουσιν. -->
over-children and wives, and-not for-one-another do-they-care.

### Odyss. IX.116–121

<!-- grc: νῆσος ἔπειτα λάχεια παρὲκ λιμένος τετάνυσται, -->
an-island, moreover, wooded, alongside harbor stretches,

<!-- grc: γαίης Κυκλώπων οὔτε σχεδὸν οὔτ᾽ ἀποτηλοῦ, -->
of-land of-Cyclopes neither near nor far,

<!-- grc: ὑλήεσσ᾽: ἐν δ᾽ αἶγες ἀπειρέσιαι γεγάασιν -->
wooded: and-on-it goats countless live,

<!-- grc: ἄγριαι: οὐ μὲν γὰρ πάτος ἀνθρώπων ἀπερύκει, -->
wild: for indeed no path of-men keeps-away,

<!-- grc: οὐδέ μιν εἰσοιχνεῦσι κυνηγέται, οἵ τε καθ᾽ ὕλην -->
nor it do-visit hunters, who through woods

<!-- grc: ἄλγεα πάσχουσιν κορυφὰς ὀρέων ἐφέποντες. -->
sufferings endure, peaks of-mountains roaming-over.

### Odyss. IX.122–124

<!-- grc: οὔτ᾽ ἄρα ποίμνῃσιν καταΐσχεται οὔτ᾽ ἀρότοισιν, -->
nor indeed with-flocks is-it-occupied nor with-plowed-fields,

<!-- grc: ἀλλ᾽ ἥ γ᾽ ἄσπαρτος καὶ ἀνήροτος ἤματα πάντα -->
but it, unsown and unplowed, always

<!-- grc: ἀνδρῶν χηρεύει, βόσκει δέ τε μηκάδας αἶγας. -->
of-men is-bereft, but-feeds bleating goats.

### Odyss. IX.125–129

<!-- grc: οὐ γὰρ Κυκλώπεσσι νέες πάρα μιλτοπάρῃοι, -->
for not to-Cyclopes ships are-at-hand, red-painted,

<!-- grc: οὐδ᾽ ἄνδρες νηῶν ἔνι τέκτονες, οἵ κε κάμοιεν -->
nor men among-them ship-builders, who might-build

<!-- grc: νῆας ἐυσσέλμους, αἵ κεν τελέοιεν ἕκαστα -->
well-benched ships, which might-accomplish each-thing

<!-- grc: ἄστε᾽ ἐπ᾽ ἀνθρώπων ἱκνεύμεναι, οἷά τε πολλὰ -->
to-cities of-men reaching, such-as many

<!-- grc: ἄνδρες ἐπ᾽ ἀλλήλους νηυσὶν περόωσι θάλασσαν: -->
men to-one-another by-ships cross sea:

### Odyss. IX.130–133

<!-- grc: οἵ κέ σφιν καὶ νῆσον ἐυκτιμένην ἐκάμοντο. -->
who would-have for-them island well-settled made.

<!-- grc: οὐ μὲν γάρ τι κακή γε, φέροι δέ κεν ὥρια πάντα: -->
for it-is not at-all bad, and-would-bear all seasonable-crops:

<!-- grc: ἐν μὲν γὰρ λειμῶνες ἁλὸς πολιοῖο παρ᾽ ὄχθας -->
for-on-it indeed meadows, of-gray sea along banks,

<!-- grc: ὑδρηλοὶ μαλακοί: μάλα κ᾽ ἄφθιτοι ἄμπελοι εἶεν. -->
well-watered, soft: very would-be unfailing vines.

### Odyss. IX.134–139

<!-- grc: ἐν δ᾽ ἄροσις λείη: μάλα κεν βαθὺ λήιον αἰεὶ -->
and-in-it plowland smooth: very-would deep grain always

<!-- grc: εἰς ὥρας ἀμῷεν, ἐπεὶ μάλα πῖαρ ὑπ᾽ οὖδας. -->
in-due-season they-would-reap, since very rich beneath soil.

<!-- grc: ἐν δὲ λιμὴν ἐύορμος, ἵν᾽ οὐ χρεὼ πείσματός ἐστιν, -->
and-in-it harbor good-for-mooring, where there-is-no need of-hawser,

<!-- grc: οὔτ᾽ εὐνὰς βαλέειν οὔτε πρυμνήσι᾽ ἀνάψαι, -->
nor anchor-stones to-cast, nor stern-cables to-fasten,

<!-- grc: ἀλλ᾽ ἐπικέλσαντας μεῖναι χρόνον εἰς ὅ κε ναυτέων -->
but having-beached, to-wait for-time until of-sailors

<!-- grc: θυμὸς ἐποτρύνῃ καὶ ἐπιπνεύσωσιν ἀῆται. -->
heart urges, and blow winds.

### Odyss. IX.140–141

<!-- grc: αὐτὰρ ἐπὶ κρατὸς λιμένος ῥέει ἀγλαὸν ὕδωρ, -->
but at head of-harbor flows bright water,

<!-- grc: κρήνη ὑπὸ σπείους: περὶ δ᾽ αἴγειροι πεφύασιν. -->
a-spring beneath cave: and-around poplars have-grown.

### Odyss. IX.142–145

<!-- grc: ἔνθα κατεπλέομεν, καί τις θεὸς ἡγεμόνευεν -->
there we-sailed-in, and some god was-guiding

<!-- grc: νύκτα δι᾽ ὀρφναίην, οὐδὲ προυφαίνετ᾽ ἰδέσθαι: -->
through murky night, nor did-it-appear to-see:

<!-- grc: ἀὴρ γὰρ περὶ νηυσὶ βαθεῖ᾽ ἦν, οὐδὲ σελήνη -->
for mist around ships deep was, nor moon

<!-- grc: οὐρανόθεν προύφαινε, κατείχετο δὲ νεφέεσσιν. -->
from-heaven shone-forth, but-was-covered by-clouds.

### Odyss. IX.146–151

<!-- grc: ἔνθ᾽ οὔ τις τὴν νῆσον ἐσέδρακεν ὀφθαλμοῖσιν, -->
there no-one the island saw with-eyes,

<!-- grc: οὔτ᾽ οὖν κύματα μακρὰ κυλινδόμενα προτὶ χέρσον -->
nor then long waves rolling toward shore

<!-- grc: εἰσίδομεν, πρὶν νῆας ἐυσσέλμους ἐπικέλσαι. -->
did-we-see, before well-benched ships to-run-aground.

<!-- grc: κελσάσῃσι δὲ νηυσὶ καθείλομεν ἱστία πάντα, -->
and-when-beached ships, we-took-down all sails,

<!-- grc: ἐκ δὲ καὶ αὐτοὶ βῆμεν ἐπὶ ῥηγμῖνι θαλάσσης: -->
and-out ourselves too we-stepped upon breaking-surf of-sea:

<!-- grc: ἔνθα δ᾽ ἀποβρίξαντες ἐμείναμεν Ἠῶ δῖαν. -->
and-there having-fallen-asleep, we-awaited divine Dawn.

### Odyss. IX.152–155

<!-- grc: ἦμος δ᾽ ἠριγένεια φάνη ῥοδοδάκτυλος Ἠώς, -->
and-when early-born appeared rosy-fingered Dawn,

<!-- grc: νῆσον θαυμάζοντες ἐδινεόμεσθα κατ᾽ αὐτήν. -->
island marveling-at, we-roamed-about over it.

<!-- grc: ὦρσαν δὲ νύμφαι, κοῦραι Διὸς αἰγιόχοιο, -->
and-roused nymphs, daughters of-Zeus aegis-bearing,

<!-- grc: αἶγας ὀρεσκῴους, ἵνα δειπνήσειαν ἑταῖροι. -->
mountain-dwelling goats, so-that might-dine comrades.

### Odyss. IX.156–160

<!-- grc: αὐτίκα καμπύλα τόξα καὶ αἰγανέας δολιχαύλους -->
at-once curved bows and long-shafted javelins

<!-- grc: εἱλόμεθ᾽ ἐκ νηῶν, διὰ δὲ τρίχα κοσμηθέντες -->
we-took from-ships, and-having-arranged-ourselves into-three-groups

<!-- grc: βάλλομεν: αἶψα δ᾽ ἔδωκε θεὸς μενοεικέα θήρην. -->
we-shot: and-quickly gave god satisfying game.

<!-- grc: νῆες μέν μοι ἕποντο δυώδεκα, ἐς δὲ ἑκάστην -->
ships indeed me followed, twelve, and-for each

<!-- grc: ἐννέα λάγχανον αἶγες: ἐμοὶ δὲ δέκ᾽ ἔξελον οἴῳ. -->
nine fell-as-share goats: but-to-me alone ten they-set-apart.

### Odyss. IX.161–165

<!-- grc: ὣς τότε μὲν πρόπαν ἦμαρ ἐς ἠέλιον καταδύντα -->
so then the-whole day, until sun setting,

<!-- grc: ἥμεθα δαινύμενοι κρέα τ᾽ ἄσπετα καὶ μέθυ ἡδύ: -->
we-sat feasting on-meat abundant and wine sweet:

<!-- grc: οὐ γάρ πω νηῶν ἐξέφθιτο οἶνος ἐρυθρός, -->
for not-yet of-ships had-run-out wine red,

<!-- grc: ἀλλ᾽ ἐνέην: πολλὸν γὰρ ἐν ἀμφιφορεῦσιν ἕκαστοι -->
but there-was-in: for-much, in jars, each

<!-- grc: ἠφύσαμεν Κικόνων. ἱερὸν πτολίεθρον ἑλόντες. -->
we-had-drawn, of-Cicones, sacred citadel having-taken.

### Odyss. IX.166–169

<!-- grc: Κυκλώπων δ᾽ ἐς γαῖαν ἐλεύσσομεν ἐγγὺς ἐόντων, -->
and-to land of-Cyclopes we-looked, being nearby,

<!-- grc: καπνόν τ᾽ αὐτῶν τε φθογγὴν ὀίων τε καὶ αἰγῶν. -->
and-their smoke and sound of-sheep and of-goats.

<!-- grc: ἦμος δ᾽ ἠέλιος κατέδυ καὶ ἐπὶ κνέφας ἦλθε, -->
and-when sun set and darkness came,

<!-- grc: δὴ τότε κοιμήθημεν ἐπὶ ῥηγμῖνι θαλάσσης. -->
then indeed we-lay-down-to-sleep on breaking-surf of-sea.

### Odyss. IX.170–176

<!-- grc: ἦμος δ᾽ ἠριγένεια φάνη ῥοδοδάκτυλος Ἠώς, -->
and-when early-born appeared rosy-fingered Dawn,

<!-- grc: καὶ τότ᾽ ἐγὼν ἀγορὴν θέμενος μετὰ πᾶσιν ἔειπον: -->
and then I, assembly having-held, among all spoke:

<!-- grc: ‘ἄλλοι μὲν νῦν μίμνετ᾽, ἐμοὶ ἐρίηρες ἑταῖροι: -->
"the-rest now remain, my trusty comrades:

<!-- grc: αὐτὰρ ἐγὼ σὺν νηί τ᾽ ἐμῇ καὶ ἐμοῖς ἑτάροισιν -->
but I, with my-ship and my comrades,

<!-- grc: ἐλθὼν τῶνδ᾽ ἀνδρῶν πειρήσομαι, οἵ τινές εἰσιν, -->
having-gone, of-these men will-make-trial, who they-are,

<!-- grc: ἤ ῥ᾽ οἵ γ᾽ ὑβρισταί τε καὶ ἄγριοι οὐδὲ δίκαιοι, -->
whether they are-insolent and wild and-not just,

<!-- grc: ἦε φιλόξεινοι, καί σφιν νόος ἐστὶ θεουδής. -->
or hospitable, and-their mind is god-fearing."

### Odyss. IX.177–180

<!-- grc: ’ ὣς εἰπὼν ἀνὰ νηὸς ἔβην, ἐκέλευσα δ᾽ ἑταίρους -->
so having-spoken, aboard ship I-went, and-I-ordered comrades

<!-- grc: αὐτούς τ᾽ ἀμβαίνειν ἀνά τε πρυμνήσια λῦσαι. -->
themselves to-embark and stern-cables to-loose.

<!-- grc: οἱ δ᾽ αἶψ᾽ εἴσβαινον καὶ ἐπὶ κληῖσι καθῖζον, -->
and-they quickly were-boarding, and upon benches were-sitting,

<!-- grc: ἑξῆς δ᾽ ἑζόμενοι πολιὴν ἅλα τύπτον ἐρετμοῖς. -->
and-in-order seated, gray sea were-striking with-oars.

"""

# Authored fresh 2026-09-14, same rationale/convention as _INTERLINEAR_EN_I
# above (I.1-21, not ported from the abandoned branch's unfit content).
_INTERLINEAR_EL_I = """\
## interlinear_el

### Odyss. I.1–5

<!-- grc: Ἄνδρα μοι ἔννεπε, μοῦσα, πολύτροπον, ὃς μάλα πολλὰ -->
Τον άντρα σε μένα πες, μούσα, τον πολύτροπο, που πάρα πολύ

<!-- grc: πλάγχθη, ἐπεὶ Τροίης ἱερὸν πτολίεθρον ἔπερσεν· -->
περιπλανήθηκε, αφού της Τροίας το ιερό κάστρο κατέστρεψε·

<!-- grc: πολλῶν δ' ἀνθρώπων ἴδεν ἄστεα καὶ νόον ἔγνω, -->
πολλών και ανθρώπων είδε τις πόλεις και τον νου γνώρισε,

<!-- grc: πολλὰ δ' ὅ γ' ἐν πόντῳ πάθεν ἄλγεα ὃν κατὰ θυμόν, -->
πολλά και αυτός στη θάλασσα υπέφερε πόνους στη δική του καρδιά,

<!-- grc: ἀρνύμενος ἥν τε ψυχὴν καὶ νόστον ἑταίρων. -->
αγωνιζόμενος για τη δική του ζωή και την επιστροφή των συντρόφων.

### Odyss. I.6–10

<!-- grc: ἀλλ' οὐδ' ὣς ἑτάρους ἐρρύσατο, ἱέμενός περ· -->
αλλά ούτε έτσι τους συντρόφους έσωσε, αν και το επιθυμούσε·

<!-- grc: αὐτῶν γὰρ σφετέρῃσιν ἀτασθαλίῃσιν ὄλοντο, -->
οι ίδιοι γιατί από τη δική τους αλαζονεία χάθηκαν,

<!-- grc: νήπιοι, οἳ κατὰ βοῦς Ὑπερίονος Ἠελίοιο -->
ανόητοι, που τα βόδια του Υπερίωνα Ήλιου

<!-- grc: ἤσθιον· αὐτὰρ ὁ τοῖσιν ἀφείλετο νόστιμον ἦμαρ. -->
έτρωγαν· αλλά αυτός από αυτούς αφαίρεσε την ημέρα της επιστροφής.

<!-- grc: τῶν ἁμόθεν γε, θεά, θύγατερ Διός, εἰπὲ καὶ ἡμῖν. -->
γι' αυτά από κάπου, θεά, κόρη του Δία, πες και σε εμάς.

### Odyss. I.11–15

<!-- grc: Ἔνθ' ἄλλοι μὲν πάντες, ὅσοι φύγον αἰπὺν ὄλεθρον, -->
τότε οι άλλοι όλοι, όσοι απέφυγαν τον απότομο όλεθρο,

<!-- grc: οἴκοι ἔσαν, πόλεμόν τε πεφευγότες ἠδὲ θάλασσαν· -->
στο σπίτι ήταν, τον πόλεμο και έχοντας γλιτώσει και τη θάλασσα·

<!-- grc: τὸν δ' οἶον νόστου κεχρημένον ἠδὲ γυναικὸς -->
αυτόν όμως μόνο, της επιστροφής έχοντας ανάγκη και της γυναίκας,

<!-- grc: νύμφη πότνι' ἔρυκε Καλυψὼ δῖα θεάων -->
η νύμφη η κυρά τον κρατούσε, η Καλυψώ, θεϊκή ανάμεσα στις θεές,

<!-- grc: ἐν σπέσσι γλαφυροῖσι, λιλαιομένη πόσιν εἶναι. -->
σε σπηλιές βαθιές, λαχταρώντας σύζυγος να γίνει.

### Odyss. I.16–21

<!-- grc: ἀλλ' ὅτε δὴ ἔτος ἦλθε περιπλομένων ἐνιαυτῶν, -->
αλλά όταν πια το έτος ήρθε, καθώς κύλησαν οι χρόνοι,

<!-- grc: τῷ οἱ ἐπεκλώσαντο θεοὶ οἰκόνδε νέεσθαι -->
στο οποίο σε αυτόν όρισαν οι θεοί προς το σπίτι να επιστρέψει,

<!-- grc: εἰς Ἰθάκην, οὐδ' ἔνθα πεφυγμένος ἦεν ἀέθλων -->
στην Ιθάκη, ούτε εκεί απαλλαγμένος ήταν από άθλους

<!-- grc: καὶ μετὰ οἷσι φίλοισι. θεοὶ δ' ἐλέαιρον ἅπαντες -->
ακόμη και ανάμεσα στους δικούς του φίλους. οι θεοί και λυπήθηκαν όλοι,

<!-- grc: νόσφι Ποσειδάωνος· ὁ δ' ἀσπερχὲς μενέαινεν -->
εκτός από τον Ποσειδώνα· αυτός όμως ασταμάτητα οργιζόταν

<!-- grc: ἀντιθέῳ Ὀδυσῆι πάρος ἥν γαῖαν ἱκέσθαι. -->
εναντίον του ισόθεου Οδυσσέα, πριν στη δική του γη φτάσει.

"""

# IX.19-38 half of the same interlinear_el section -- see
# _INTERLINEAR_EN_IX's own comment for the format/history explanation.
_INTERLINEAR_EL_IX = """\
## interlinear_el

### Odyss. IX.19–24

<!-- grc: εἶμ' Ὀδυσεὺς Λαερτιάδης, ὃς πᾶσι δόλοισιν -->
Είμαι ο Οδυσσέας Λαερτιάδης, που με όλα τα τεχνάσματα

<!-- grc: ἀνθρώποισι μέλω, καί μευ κλέος οὐρανὸν ἵκει. -->
στους ανθρώπους είμαι γνωστός, και η δόξα μου τον ουρανό φτάνει.

<!-- grc: ναιετάω δ' Ἰθάκην εὐδείελον· ἐν δ' ὄρος αὐτῇ -->
Κατοικώ στην Ιθάκη την ηλιόλουστη· σ' αυτή βουνό

<!-- grc: Νήριτον εἰνοσίφυλλον, ἀριπρεπές· ἀμφὶ δὲ νῆσοι -->
το Νήριτο φυλλοσείστης, ξακουστό· και γύρω νησιά

<!-- grc: πολλαὶ ναιετάουσι μάλα σχεδὸν ἀλλήλῃσι, -->
πολλά κατοικούν, πολύ κοντά το ένα στ' άλλο,

<!-- grc: Δουλίχιόν τε Σάμη τε καὶ ὑλήεσσα Ζάκυνθος. -->
Δουλίχι και Σάμη και η δασώδης Ζάκυνθος.

### Odyss. IX.25–28

<!-- grc: αὐτὴ δὲ χθαμαλὴ πανυπερτάτη εἰν ἁλὶ κεῖται -->
Αυτή δε χαμηλή, η πιο απόμακρη στη θάλασσα κείται,

<!-- grc: πρὸς ζόφον, αἱ δέ τ' ἄνευθε πρὸς ἠῶ τ' ἠέλιόν τε, -->
προς τη δύση, εκείνες δε μακριά προς αυγή και ήλιο,

<!-- grc: τρηχεῖ', ἀλλ' ἀγαθὴ κουροτρόφος· οὔ τοι ἐγώ γε -->
τραχεία, μα καλή τροφός νέων· κι εγώ βέβαια

<!-- grc: ἧς γαίης δύναμαι γλυκερώτερον ἄλλο ἰδέσθαι. -->
της γης μου δεν μπορώ γλυκύτερο άλλο να δω.

### Odyss. IX.29–33

<!-- grc: ἦ μέν μ' αὐτόθ' ἔρυκε Καλυψώ, δῖα θεάων, -->
Αλήθεια εμένα εκεί κρατούσε η Καλυψώ, θεϊκή θεά,

<!-- grc: ἐν σπέσσι γλαφυροῖσι, λιλαιομένη πόσιν εἶναι· -->
σε σπήλαια βαθιά, λαχταρώντας σύζυγος να γίνει·

<!-- grc: ὣς δ' αὔτως Κίρκη κατερήτυεν ἐν μεγάροισιν -->
έτσι κι η Κίρκη με κρατούσε στα μέγαρά της

<!-- grc: Αἰαίη δολόεσσα, λιλαιομένη πόσιν εἶναι· -->
η Αιαία η δολερή, λαχταρώντας σύζυγος να γίνει·

<!-- grc: ἀλλ' ἐμὸν οὔ ποτε θυμὸν ἐνὶ στήθεσσιν ἔπειθον. -->
μα ποτέ την ψυχή μου στο στήθος δεν έπειθαν.

### Odyss. IX.34–38

<!-- grc: ὣς οὐδὲν γλύκιον ἧς πατρίδος οὐδὲ τοκήων -->
Έτσι τίποτα γλυκύτερο από την πατρίδα κι από τους γονείς

<!-- grc: γίγνεται, εἴ περ καί τις ἀπόπροθι πίονα οἶκον -->
δεν γίνεται, έστω κι αν κάποιος μακριά πλούσιο σπίτι

<!-- grc: γαίῃ ἐν ἀλλοδαπῇ ναίει ἀπάνευθε τοκήων. -->
σε ξένη γη κατοικεί μακριά από γονείς.

<!-- grc: εἰ δ' ἄγε τοι καὶ νόστον ἐμὸν πολυκηδέ' ἐνίσπω, -->
Αλλά άγε, θα σου πω και τον νόστο μου τον πολύπικρο,

<!-- grc: ὅν μοι Ζεὺς ἐφέηκεν ἀπὸ Τροίηθεν ἰόντι. -->
που ο Ζευς μου ετοίμασε αφού έφυγα από Τροία.

### Odyss. IX.39–42

<!-- grc: Ἰλιόθεν με φέρων ἄνεμος Κικόνεσσι πέλασσεν, -->
Από την Ίλιο εμένα φέρνοντας ο άνεμος στους Κίκονες με έφερε κοντά,

<!-- grc: Ἰσμάρῳ. ἔνθα δ᾽ ἐγὼ πόλιν ἔπραθον, ὤλεσα δ᾽ αὐτούς: -->
στην Ίσμαρο. εκεί εγώ την πόλη κατέστρεψα, και τους σκότωσα:

<!-- grc: ἐκ πόλιος δ᾽ ἀλόχους καὶ κτήματα πολλὰ λαβόντες -->
από την πόλη τις γυναίκες και τα υπάρχοντα πολλά παίρνοντας

<!-- grc: δασσάμεθ᾽, ὡς μή τίς μοι ἀτεμβόμενος κίοι ἴσης. -->
τα μοιράσαμε, ώστε κανείς από μένα αδικημένος να μη φύγει, χωρίς το ίσο μερίδιο.

### Odyss. IX.43–46

<!-- grc: ἔνθ᾽ ἦ τοι μὲν ἐγὼ διερῷ ποδὶ φευγέμεν ἡμέας -->
τότε εγώ βέβαια με γρήγορο πόδι να φύγουμε εμείς

<!-- grc: ἠνώγεα, τοὶ δὲ μέγα νήπιοι οὐκ ἐπίθοντο. -->
διέταξα, αλλά αυτοί πολύ ανόητοι δεν με άκουσαν.

<!-- grc: ἔνθα δὲ πολλὸν μὲν μέθυ πίνετο, πολλὰ δὲ μῆλα -->
και εκεί πολύ κρασί πινόταν, και πολλά πρόβατα

<!-- grc: ἔσφαζον παρὰ θῖνα καὶ εἰλίποδας ἕλικας βοῦς: -->
έσφαζαν στην ακτή, και βαρύποδα στριφτόκερα βόδια:

### Odyss. IX.47–50

<!-- grc: τόφρα δ᾽ ἄρ᾽ οἰχόμενοι Κίκονες Κικόνεσσι γεγώνευν, -->
στο μεταξύ όμως φεύγοντας οι Κίκονες στους Κίκονες φώναζαν,

<!-- grc: οἵ σφιν γείτονες ἦσαν, ἅμα πλέονες καὶ ἀρείους, -->
που τους ήταν γείτονες, μαζί περισσότεροι και πιο γενναίοι,

<!-- grc: ἤπειρον ναίοντες, ἐπιστάμενοι μὲν ἀφ᾽ ἵππων -->
στην ενδοχώρα κατοικώντας, γνωρίζοντας βέβαια από τα άλογα

<!-- grc: ἀνδράσι μάρνασθαι καὶ ὅθι χρὴ πεζὸν ἐόντα. -->
με άντρες να πολεμούν, και όπου χρειάζεται πεζοί όντας.

### Odyss. IX.51–55

<!-- grc: ἦλθον ἔπειθ᾽ ὅσα φύλλα καὶ ἄνθεα γίγνεται ὥρῃ, -->
ήρθαν λοιπόν, όσα φύλλα και άνθη γίνονται στην εποχή τους,

<!-- grc: ἠέριοι: τότε δή ῥα κακὴ Διὸς αἶσα παρέστη -->
τα ξημερώματα: τότε λοιπόν κακή του Δία μοίρα μας βρήκε

<!-- grc: ἡμῖν αἰνομόροισιν, ἵν᾽ ἄλγεα πολλὰ πάθοιμεν. -->
εμάς τους κακότυχους, για να πάθουμε πολλούς πόνους.

<!-- grc: στησάμενοι δ᾽ ἐμάχοντο μάχην παρὰ νηυσὶ θοῇσι, -->
παρατάσσοντας τους εαυτούς τους πολεμούσαν μάχη κοντά στα γρήγορα πλοία,

<!-- grc: βάλλον δ᾽ ἀλλήλους χαλκήρεσιν ἐγχείῃσιν. -->
και χτυπούσαν ο ένας τον άλλο με χάλκινες λόγχες.

### Odyss. IX.56–61

<!-- grc: ὄφρα μὲν ἠὼς ἦν καὶ ἀέξετο ἱερὸν ἦμαρ, -->
όσο η αυγή υπήρχε και μεγάλωνε η ιερή μέρα,

<!-- grc: τόφρα δ᾽ ἀλεξόμενοι μένομεν πλέονάς περ ἐόντας. -->
τόσο εμείς αμυνόμενοι κρατούσαμε, αν και ήταν περισσότεροι.

<!-- grc: ἦμος δ᾽ ἠέλιος μετενίσσετο βουλυτόνδε, -->
όταν όμως ο ήλιος γύρισε προς την ώρα του δειλινού,

<!-- grc: καὶ τότε δὴ Κίκονες κλῖναν δαμάσαντες Ἀχαιούς. -->
τότε λοιπόν οι Κίκονες έτρεψαν σε φυγή, νικώντας τους Αχαιούς.

<!-- grc: ἓξ δ᾽ ἀφ᾽ ἑκάστης νηὸς ἐυκνήμιδες ἑταῖροι -->
έξι από κάθε πλοίο, καλοκνημιδωμένοι σύντροφοι,

<!-- grc: ὤλονθ᾽: οἱ δ᾽ ἄλλοι φύγομεν θάνατόν τε μόρον τε. -->
χάθηκαν: και οι υπόλοιποι ξεφύγαμε και τον θάνατο και τη μοίρα.

### Odyss. IX.62–66

<!-- grc: ἔνθεν δὲ προτέρω πλέομεν ἀκαχήμενοι ἦτορ, -->
από εκεί λοιπόν πλέαμε παρακάτω, θλιμμένοι στην καρδιά,

<!-- grc: ἄσμενοι ἐκ θανάτοιο, φίλους ὀλέσαντες ἑταίρους. -->
χαρούμενοι που γλιτώσαμε τον θάνατο, αλλά χάνοντας αγαπημένους συντρόφους.

<!-- grc: οὐδ᾽ ἄρα μοι προτέρω νῆες κίον ἀμφιέλισσαι, -->
και δεν προχώρησαν τα πλοία μου, τα αμφίκυρτα,

<!-- grc: πρίν τινα τῶν δειλῶν ἑτάρων τρὶς ἕκαστον ἀῦσαι, -->
πριν φωνάξουμε κάποιον από τους δύστυχους συντρόφους, τρεις φορές τον καθένα,

<!-- grc: οἳ θάνον ἐν πεδίῳ Κικόνων ὕπο δῃωθέντες. -->
που πέθαναν στην πεδιάδα, από τους Κίκονες σκοτωμένοι.

### Odyss. IX.67–71

<!-- grc: νηυσὶ δ᾽ ἐπῶρσ᾽ ἄνεμον Βορέην νεφεληγερέτα Ζεὺς -->
στα πλοία τότε έστειλε άνεμο Βορέα ο νεφελοσυνάχτης Δίας,

<!-- grc: λαίλαπι θεσπεσίῃ, σὺν δὲ νεφέεσσι κάλυψε -->
με θεσπέσια θύελλα, και μαζί με σύννεφα σκέπασε

<!-- grc: γαῖαν ὁμοῦ καὶ πόντον: ὀρώρει δ᾽ οὐρανόθεν νύξ. -->
τη γη μαζί και τη θάλασσα: και σηκώθηκε από τον ουρανό η νύχτα.

<!-- grc: αἱ μὲν ἔπειτ᾽ ἐφέροντ᾽ ἐπικάρσιαι, ἱστία δέ σφιν -->
αυτά (τα πλοία) τότε παρασύρονταν πλάγια, και τα πανιά τους

<!-- grc: τριχθά τε καὶ τετραχθὰ διέσχισεν ἲς ἀνέμοιο. -->
σε τρία και σε τέσσερα κομμάτια έσκισε η δύναμη του ανέμου.

### Odyss. IX.72–75

<!-- grc: καὶ τὰ μὲν ἐς νῆας κάθεμεν, δείσαντες ὄλεθρον, -->
και αυτά (τα πανιά) τα κατεβάσαμε στα πλοία, φοβούμενοι την καταστροφή,

<!-- grc: αὐτὰς δ᾽ ἐσσυμένως προερέσσαμεν ἤπειρόνδε. -->
και αυτά (τα πλοία) βιαστικά τα κωπηλατήσαμε προς τη στεριά.

<!-- grc: ἔνθα δύω νύκτας δύο τ᾽ ἤματα συνεχὲς αἰεὶ -->
εκεί δύο νύχτες και δύο μέρες συνεχώς πάντα

<!-- grc: κείμεθ᾽, ὁμοῦ καμάτῳ τε καὶ ἄλγεσι θυμὸν ἔδοντες. -->
μέναμε ξαπλωμένοι, μαζί από τον κάματο και τους πόνους την καρδιά τρώγοντας.

### Odyss. IX.76–78

<!-- grc: ἀλλ᾽ ὅτε δὴ τρίτον ἦμαρ ἐυπλόκαμος τέλεσ᾽ Ἠώς, -->
αλλά όταν την τρίτη μέρα η καλλίκομη έφερε η Ηώς,

<!-- grc: ἱστοὺς στησάμενοι ἀνά θ᾽ ἱστία λεύκ᾽ ἐρύσαντες -->
τα κατάρτια στήνοντας και τα λευκά πανιά τραβώντας ψηλά

<!-- grc: ἥμεθα, τὰς δ᾽ ἄνεμός τε κυβερνῆταί τ᾽ ἴθυνον. -->
καθόμασταν, και αυτά (τα πλοία) και ο άνεμος και οι πηδαλιούχοι κατηύθυναν.

### Odyss. IX.79–81

<!-- grc: καί νύ κεν ἀσκηθὴς ἱκόμην ἐς πατρίδα γαῖαν: -->
και τότε ίσως αβλαβής θα έφτανα στην πατρίδα μου:

<!-- grc: ἀλλά με κῦμα ῥόος τε περιγνάμπτοντα Μάλειαν -->
αλλά εμένα το κύμα και το ρεύμα, καθώς έστριβα το ακρωτήριο Μαλέα,

<!-- grc: καὶ Βορέης ἀπέωσε, παρέπλαγξεν δὲ Κυθήρων. -->
και ο Βορέας με έσπρωξαν πίσω, και με παρέσυραν πέρα από τα Κύθηρα.

### Odyss. IX.82–86

<!-- grc: ἔνθεν δ᾽ ἐννῆμαρ φερόμην ὀλοοῖς ἀνέμοισιν -->
από εκεί λοιπόν εννιά μέρες παρασυρόμουν από ολέθριους ανέμους

<!-- grc: πόντον ἐπ᾽ ἰχθυόεντα: ἀτὰρ δεκάτῃ ἐπέβημεν -->
πάνω στη θάλασσα τη γεμάτη ψάρια: αλλά τη δέκατη μέρα φτάσαμε

<!-- grc: γαίης Λωτοφάγων, οἵ τ᾽ ἄνθινον εἶδαρ ἔδουσιν. -->
στη γη των Λωτοφάγων, που τρώνε ανθισμένη τροφή.

<!-- grc: ἔνθα δ᾽ ἐπ᾽ ἠπείρου βῆμεν καὶ ἀφυσσάμεθ᾽ ὕδωρ, -->
εκεί στη στεριά βγήκαμε και αντλήσαμε νερό,

<!-- grc: αἶψα δὲ δεῖπνον ἕλοντο θοῇς παρὰ νηυσὶν ἑταῖροι. -->
και αμέσως γεύμα πήραν κοντά στα γρήγορα πλοία οι σύντροφοι.

### Odyss. IX.87–90

<!-- grc: αὐτὰρ ἐπεὶ σίτοιό τ᾽ ἐπασσάμεθ᾽ ἠδὲ ποτῆτος, -->
αλλά όταν φαγητό και ποτό γευτήκαμε,

<!-- grc: δὴ τοτ᾽ ἐγὼν ἑτάρους προΐειν πεύθεσθαι ἰόντας, -->
τότε εγώ συντρόφους έστειλα να πληροφορηθούν, πηγαίνοντας,

<!-- grc: οἵ τινες ἀνέρες εἶεν ἐπὶ χθονὶ σῖτον ἔδοντες -->
τι είδους άνθρωποι μπορεί να ήταν, σε αυτή τη γη ψωμί τρώγοντας,

<!-- grc: ἄνδρε δύω κρίνας, τρίτατον κήρυχ᾽ ἅμ᾽ ὀπάσσας. -->
δύο άντρες διαλέγοντας, τρίτο κήρυκα μαζί στέλνοντας.

### Odyss. IX.91–93

<!-- grc: οἱ δ᾽ αἶψ᾽ οἰχόμενοι μίγεν ἀνδράσι Λωτοφάγοισιν: -->
αυτοί αμέσως πηγαίνοντας συναναστράφηκαν με τους άντρες Λωτοφάγους:

<!-- grc: οὐδ᾽ ἄρα Λωτοφάγοι μήδονθ᾽ ἑτάροισιν ὄλεθρον -->
και δεν σχεδίαζαν οι Λωτοφάγοι στους συντρόφους καταστροφή

<!-- grc: ἡμετέροις, ἀλλά σφι δόσαν λωτοῖο πάσασθαι. -->
τους δικούς μας, αλλά τους έδωσαν από τον λωτό να γευτούν.

### Odyss. IX.94–97

<!-- grc: τῶν δ᾽ ὅς τις λωτοῖο φάγοι μελιηδέα καρπόν, -->
και όποιος από αυτούς έτρωγε τον λωτό, τον μελιστάλαχτο καρπό,

<!-- grc: οὐκέτ᾽ ἀπαγγεῖλαι πάλιν ἤθελεν οὐδὲ νέεσθαι, -->
δεν ήθελε πια ούτε να αναφέρει πίσω ούτε να γυρίσει,

<!-- grc: ἀλλ᾽ αὐτοῦ βούλοντο μετ᾽ ἀνδράσι Λωτοφάγοισι -->
αλλά εκεί ήθελε ανάμεσα στους άντρες τους Λωτοφάγους

<!-- grc: λωτὸν ἐρεπτόμενοι μενέμεν νόστου τε λαθέσθαι. -->
τον λωτό τρώγοντας να μείνει, και την επιστροφή να ξεχάσει.

### Odyss. IX.98–104

<!-- grc: τοὺς μὲν ἐγὼν ἐπὶ νῆας ἄγον κλαίοντας ἀνάγκῃ, -->
αυτούς εγώ στα πλοία τους οδήγησα κλαίγοντας, με τη βία,

<!-- grc: νηυσὶ δ᾽ ἐνὶ γλαφυρῇσιν ὑπὸ ζυγὰ δῆσα ἐρύσσας. -->
και στα κοίλα πλοία κάτω από τα ζυγά τους έδεσα, σέρνοντάς τους.

<!-- grc: αὐτὰρ τοὺς ἄλλους κελόμην ἐρίηρας ἑταίρους -->
και στους υπόλοιπους διέταξα, τους πιστούς συντρόφους,

<!-- grc: σπερχομένους νηῶν ἐπιβαινέμεν ὠκειάων, -->
βιαστικά στα πλοία να επιβιβαστούν, τα γρήγορα,

<!-- grc: μή πώς τις λωτοῖο φαγὼν νόστοιο λάθηται. -->
μήπως κάποιος από τον λωτό φάγει και την επιστροφή ξεχάσει.

<!-- grc: οἱ δ᾽ αἶψ᾽ εἴσβαινον καὶ ἐπὶ κληῖσι καθῖζον, -->
αυτοί αμέσως επιβιβάστηκαν και στα καθίσματα κάθισαν,

<!-- grc: ἑξῆς δ᾽ ἑζόμενοι πολιὴν ἅλα τύπτον ἐρετμοῖς. -->
και με τη σειρά καθισμένοι τη γκρίζα θάλασσα χτυπούσαν με τα κουπιά.

### Odyss. IX.105–111

<!-- grc: ἔνθεν δὲ προτέρω πλέομεν ἀκαχήμενοι ἦτορ: -->
από εκεί λοιπόν πλέαμε παρακάτω, θλιμμένοι στην καρδιά:

<!-- grc: Κυκλώπων δ᾽ ἐς γαῖαν ὑπερφιάλων ἀθεμίστων -->
και στη γη των Κυκλώπων, των αλαζόνων, των άνομων,

<!-- grc: ἱκόμεθ᾽, οἵ ῥα θεοῖσι πεποιθότες ἀθανάτοισιν -->
φτάσαμε, που στους αθάνατους θεούς έχοντας εμπιστοσύνη

<!-- grc: οὔτε φυτεύουσιν χερσὶν φυτὸν οὔτ᾽ ἀρόωσιν, -->
ούτε φυτεύουν με τα χέρια φυτό ούτε οργώνουν,

<!-- grc: ἀλλὰ τά γ᾽ ἄσπαρτα καὶ ἀνήροτα πάντα φύονται, -->
αλλά όλα αυτά, ασπαρτα και ανόργωτα, φυτρώνουν μόνα τους,

<!-- grc: πυροὶ καὶ κριθαὶ ἠδ᾽ ἄμπελοι, αἵ τε φέρουσιν -->
στάρι και κριθάρι και αμπέλια, που φέρνουν

<!-- grc: οἶνον ἐριστάφυλον, καί σφιν Διὸς ὄμβρος ἀέξει. -->
κρασί από πλούσια τσαμπιά, και σε αυτά η βροχή του Δία τα μεγαλώνει.

### Odyss. IX.112–115

<!-- grc: τοῖσιν δ᾽ οὔτ᾽ ἀγοραὶ βουληφόροι οὔτε θέμιστες, -->
και σε αυτούς ούτε συνελεύσεις με βουλή ούτε νόμοι υπάρχουν,

<!-- grc: ἀλλ᾽ οἵ γ᾽ ὑψηλῶν ὀρέων ναίουσι κάρηνα -->
αλλά αυτοί ψηλών βουνών κατοικούν τις κορυφές

<!-- grc: ἐν σπέσσι γλαφυροῖσι, θεμιστεύει δὲ ἕκαστος -->
σε σπηλιές βαθιές, και νομοθετεί ο καθένας

<!-- grc: παίδων ἠδ᾽ ἀλόχων, οὐδ᾽ ἀλλήλων ἀλέγουσιν. -->
για τα παιδιά και τις γυναίκες του, και ο ένας για τον άλλο δεν νοιάζονται.

### Odyss. IX.116–121

<!-- grc: νῆσος ἔπειτα λάχεια παρὲκ λιμένος τετάνυσται, -->
ένα νησί λοιπόν καταπράσινο δίπλα στο λιμάνι απλώνεται,

<!-- grc: γαίης Κυκλώπων οὔτε σχεδὸν οὔτ᾽ ἀποτηλοῦ, -->
από τη γη των Κυκλώπων ούτε κοντά ούτε μακριά,

<!-- grc: ὑλήεσσ᾽: ἐν δ᾽ αἶγες ἀπειρέσιαι γεγάασιν -->
δασωμένο: και σε αυτό γίδια αναρίθμητα ζουν

<!-- grc: ἄγριαι: οὐ μὲν γὰρ πάτος ἀνθρώπων ἀπερύκει, -->
άγρια: γιατί κανένα μονοπάτι ανθρώπων δεν τα διώχνει,

<!-- grc: οὐδέ μιν εἰσοιχνεῦσι κυνηγέται, οἵ τε καθ᾽ ὕλην -->
και δεν το επισκέπτονται κυνηγοί, που μέσα στο δάσος

<!-- grc: ἄλγεα πάσχουσιν κορυφὰς ὀρέων ἐφέποντες. -->
ταλαιπωρούνται, τις κορυφές των βουνών ακολουθώντας.

### Odyss. IX.122–124

<!-- grc: οὔτ᾽ ἄρα ποίμνῃσιν καταΐσχεται οὔτ᾽ ἀρότοισιν, -->
ούτε λοιπόν με κοπάδια καταλαμβάνεται ούτε με χωράφια οργωμένα,

<!-- grc: ἀλλ᾽ ἥ γ᾽ ἄσπαρτος καὶ ἀνήροτος ἤματα πάντα -->
αλλά αυτό, ασπαρτο και ανόργωτο, όλες τις μέρες

<!-- grc: ἀνδρῶν χηρεύει, βόσκει δέ τε μηκάδας αἶγας. -->
από ανθρώπους είναι έρημο, και βόσκει μηκητικά γίδια.

### Odyss. IX.125–129

<!-- grc: οὐ γὰρ Κυκλώπεσσι νέες πάρα μιλτοπάρῃοι, -->
γιατί οι Κύκλωπες δεν έχουν πλοία βαμμένα με κόκκινο χρώμα,

<!-- grc: οὐδ᾽ ἄνδρες νηῶν ἔνι τέκτονες, οἵ κε κάμοιεν -->
ούτε άντρες πλοιοναυπηγοί ανάμεσά τους, που θα έφτιαχναν

<!-- grc: νῆας ἐυσσέλμους, αἵ κεν τελέοιεν ἕκαστα -->
πλοία με γερά καταστρώματα, που θα κατάφερναν τα πάντα,

<!-- grc: ἄστε᾽ ἐπ᾽ ἀνθρώπων ἱκνεύμεναι, οἷά τε πολλὰ -->
στις πόλεις των ανθρώπων φτάνοντας, όπως πολλοί

<!-- grc: ἄνδρες ἐπ᾽ ἀλλήλους νηυσὶν περόωσι θάλασσαν: -->
άντρες ο ένας στον άλλον με πλοία διασχίζουν τη θάλασσα:

### Odyss. IX.130–133

<!-- grc: οἵ κέ σφιν καὶ νῆσον ἐυκτιμένην ἐκάμοντο. -->
που θα τους έκαναν και το νησί καλοχτισμένο.

<!-- grc: οὐ μὲν γάρ τι κακή γε, φέροι δέ κεν ὥρια πάντα: -->
γιατί δεν είναι καθόλου κακό, και θα έφερνε όλους τους καρπούς της εποχής:

<!-- grc: ἐν μὲν γὰρ λειμῶνες ἁλὸς πολιοῖο παρ᾽ ὄχθας -->
γιατί σε αυτό υπάρχουν λιβάδια, κοντά στις όχθες της γκρίζας θάλασσας,

<!-- grc: ὑδρηλοὶ μαλακοί: μάλα κ᾽ ἄφθιτοι ἄμπελοι εἶεν. -->
νερόβρεχτα, μαλακά: πολύ θα ήταν αμάραντα τα αμπέλια.

### Odyss. IX.134–139

<!-- grc: ἐν δ᾽ ἄροσις λείη: μάλα κεν βαθὺ λήιον αἰεὶ -->
και σε αυτό υπάρχει ομαλό χωράφι: πολύ πλούσια σοδειά πάντα

<!-- grc: εἰς ὥρας ἀμῷεν, ἐπεὶ μάλα πῖαρ ὑπ᾽ οὖδας. -->
στην ώρα της θα θέριζαν, γιατί πολύ πλούσιο είναι το έδαφος από κάτω.

<!-- grc: ἐν δὲ λιμὴν ἐύορμος, ἵν᾽ οὐ χρεὼ πείσματός ἐστιν, -->
και σε αυτό υπάρχει λιμάνι καλό για αγκυροβόλιο, όπου δεν χρειάζεται σχοινί,

<!-- grc: οὔτ᾽ εὐνὰς βαλέειν οὔτε πρυμνήσι᾽ ἀνάψαι, -->
ούτε άγκυρες να ρίξεις ούτε πρυμνήσια σχοινιά να δέσεις,

<!-- grc: ἀλλ᾽ ἐπικέλσαντας μεῖναι χρόνον εἰς ὅ κε ναυτέων -->
αλλά αφού προσαράξεις να περιμένεις χρόνο, μέχρι που των ναυτών

<!-- grc: θυμὸς ἐποτρύνῃ καὶ ἐπιπνεύσωσιν ἀῆται. -->
η καρδιά να τους παρακινήσει και να φυσήξουν οι άνεμοι.

### Odyss. IX.140–141

<!-- grc: αὐτὰρ ἐπὶ κρατὸς λιμένος ῥέει ἀγλαὸν ὕδωρ, -->
και στην κορυφή του λιμανιού ρέει λαμπρό νερό,

<!-- grc: κρήνη ὑπὸ σπείους: περὶ δ᾽ αἴγειροι πεφύασιν. -->
μια πηγή κάτω από σπηλιά: και γύρω λεύκες έχουν φυτρώσει.

### Odyss. IX.142–145

<!-- grc: ἔνθα κατεπλέομεν, καί τις θεὸς ἡγεμόνευεν -->
εκεί αράξαμε, και κάποιος θεός μας οδηγούσε

<!-- grc: νύκτα δι᾽ ὀρφναίην, οὐδὲ προυφαίνετ᾽ ἰδέσθαι: -->
μέσα στη σκοτεινή νύχτα, και τίποτα δεν φαινόταν να δούμε:

<!-- grc: ἀὴρ γὰρ περὶ νηυσὶ βαθεῖ᾽ ἦν, οὐδὲ σελήνη -->
γιατί ομίχλη γύρω από τα πλοία πυκνή ήταν, και το φεγγάρι

<!-- grc: οὐρανόθεν προύφαινε, κατείχετο δὲ νεφέεσσιν. -->
από τον ουρανό δεν έλαμπε, γιατί ήταν κρυμμένο από σύννεφα.

### Odyss. IX.146–151

<!-- grc: ἔνθ᾽ οὔ τις τὴν νῆσον ἐσέδρακεν ὀφθαλμοῖσιν, -->
εκεί κανείς το νησί δεν είδε με τα μάτια,

<!-- grc: οὔτ᾽ οὖν κύματα μακρὰ κυλινδόμενα προτὶ χέρσον -->
ούτε τα μεγάλα κύματα που κυλούσαν προς την ξηρά

<!-- grc: εἰσίδομεν, πρὶν νῆας ἐυσσέλμους ἐπικέλσαι. -->
είδαμε, πριν τα πλοία με τα γερά καταστρώματα προσαράξουν.

<!-- grc: κελσάσῃσι δὲ νηυσὶ καθείλομεν ἱστία πάντα, -->
και όταν προσάραξαν τα πλοία, κατεβάσαμε όλα τα πανιά,

<!-- grc: ἐκ δὲ καὶ αὐτοὶ βῆμεν ἐπὶ ῥηγμῖνι θαλάσσης: -->
και βγήκαμε και εμείς οι ίδιοι στην ακρογιαλιά της θάλασσας:

<!-- grc: ἔνθα δ᾽ ἀποβρίξαντες ἐμείναμεν Ἠῶ δῖαν. -->
εκεί, αφού αποκοιμηθήκαμε, περιμέναμε τη θεϊκή Αυγή.

### Odyss. IX.152–155

<!-- grc: ἦμος δ᾽ ἠριγένεια φάνη ῥοδοδάκτυλος Ἠώς, -->
και όταν η πρωτογέννητη φάνηκε η ροδοδάχτυλη Αυγή,

<!-- grc: νῆσον θαυμάζοντες ἐδινεόμεσθα κατ᾽ αὐτήν. -->
το νησί θαυμάζοντας περιπλανιόμασταν μέσα σε αυτό.

<!-- grc: ὦρσαν δὲ νύμφαι, κοῦραι Διὸς αἰγιόχοιο, -->
και σήκωσαν οι νύμφες, οι κόρες του αιγιδοφόρου Δία,

<!-- grc: αἶγας ὀρεσκῴους, ἵνα δειπνήσειαν ἑταῖροι. -->
τα βουνίσια γίδια, για να δειπνήσουν οι σύντροφοι.

### Odyss. IX.156–160

<!-- grc: αὐτίκα καμπύλα τόξα καὶ αἰγανέας δολιχαύλους -->
αμέσως καμπύλα τόξα και μακρόκαυλα ακόντια

<!-- grc: εἱλόμεθ᾽ ἐκ νηῶν, διὰ δὲ τρίχα κοσμηθέντες -->
πήραμε από τα πλοία, και σε τρία μέρη χωρισμένοι

<!-- grc: βάλλομεν: αἶψα δ᾽ ἔδωκε θεὸς μενοεικέα θήρην. -->
ρίχναμε: και αμέσως έδωσε ο θεός άφθονο κυνήγι.

<!-- grc: νῆες μέν μοι ἕποντο δυώδεκα, ἐς δὲ ἑκάστην -->
πλοία με ακολουθούσαν δώδεκα, και σε κάθε ένα

<!-- grc: ἐννέα λάγχανον αἶγες: ἐμοὶ δὲ δέκ᾽ ἔξελον οἴῳ. -->
εννιά έπεσαν γίδια: και σε μένα μόνο δέκα ξεχώρισαν.

### Odyss. IX.161–165

<!-- grc: ὣς τότε μὲν πρόπαν ἦμαρ ἐς ἠέλιον καταδύντα -->
έτσι τότε όλη τη μέρα μέχρι τη δύση του ήλιου

<!-- grc: ἥμεθα δαινύμενοι κρέα τ᾽ ἄσπετα καὶ μέθυ ἡδύ: -->
καθόμασταν γλεντώντας με κρέας άφθονο και γλυκό κρασί:

<!-- grc: οὐ γάρ πω νηῶν ἐξέφθιτο οἶνος ἐρυθρός, -->
γιατί ακόμα δεν είχε τελειώσει το κόκκινο κρασί στα πλοία,

<!-- grc: ἀλλ᾽ ἐνέην: πολλὸν γὰρ ἐν ἀμφιφορεῦσιν ἕκαστοι -->
αλλά υπήρχε ακόμα: γιατί πολύ, μέσα σε αμφορείς, ο καθένας μας

<!-- grc: ἠφύσαμεν Κικόνων. ἱερὸν πτολίεθρον ἑλόντες. -->
είχαμε αντλήσει από τους Κίκονες, αφού πήραμε την ιερή πόλη.

### Odyss. IX.166–169

<!-- grc: Κυκλώπων δ᾽ ἐς γαῖαν ἐλεύσσομεν ἐγγὺς ἐόντων, -->
και στη γη των Κυκλώπων κοιτάζαμε, καθώς ήταν κοντά,

<!-- grc: καπνόν τ᾽ αὐτῶν τε φθογγὴν ὀίων τε καὶ αἰγῶν. -->
και τον καπνό τους, και τη φωνή προβάτων και γιδιών.

<!-- grc: ἦμος δ᾽ ἠέλιος κατέδυ καὶ ἐπὶ κνέφας ἦλθε, -->
όταν όμως ο ήλιος έδυσε και ήρθε το σκοτάδι,

<!-- grc: δὴ τότε κοιμήθημεν ἐπὶ ῥηγμῖνι θαλάσσης. -->
τότε λοιπόν κοιμηθήκαμε στην ακρογιαλιά της θάλασσας.

### Odyss. IX.170–176

<!-- grc: ἦμος δ᾽ ἠριγένεια φάνη ῥοδοδάκτυλος Ἠώς, -->
και όταν η πρωτογέννητη φάνηκε η ροδοδάχτυλη Αυγή,

<!-- grc: καὶ τότ᾽ ἐγὼν ἀγορὴν θέμενος μετὰ πᾶσιν ἔειπον: -->
και τότε εγώ, συγκέντρωση κάνοντας, σε όλους είπα:

<!-- grc: ‘ἄλλοι μὲν νῦν μίμνετ᾽, ἐμοὶ ἐρίηρες ἑταῖροι: -->
«οι υπόλοιποι τώρα μείνετε, οι δικοί μου πιστοί σύντροφοι:

<!-- grc: αὐτὰρ ἐγὼ σὺν νηί τ᾽ ἐμῇ καὶ ἐμοῖς ἑτάροισιν -->
εγώ όμως με το πλοίο μου και τους συντρόφους μου

<!-- grc: ἐλθὼν τῶνδ᾽ ἀνδρῶν πειρήσομαι, οἵ τινές εἰσιν, -->
πηγαίνοντας, θα δοκιμάσω αυτούς τους ανθρώπους, ποιοι είναι,

<!-- grc: ἤ ῥ᾽ οἵ γ᾽ ὑβρισταί τε καὶ ἄγριοι οὐδὲ δίκαιοι, -->
είτε είναι υβριστές και άγριοι και όχι δίκαιοι,

<!-- grc: ἦε φιλόξεινοι, καί σφιν νόος ἐστὶ θεουδής. -->
είτε φιλόξενοι, και ο νους τους είναι θεοσεβής».

### Odyss. IX.177–180

<!-- grc: ’ ὣς εἰπὼν ἀνὰ νηὸς ἔβην, ἐκέλευσα δ᾽ ἑταίρους -->
έτσι λέγοντας, ανέβηκα στο πλοίο, και διέταξα τους συντρόφους

<!-- grc: αὐτούς τ᾽ ἀμβαίνειν ἀνά τε πρυμνήσια λῦσαι. -->
και οι ίδιοι να επιβιβαστούν και τα πρυμνήσια σχοινιά να λύσουν.

<!-- grc: οἱ δ᾽ αἶψ᾽ εἴσβαινον καὶ ἐπὶ κληῖσι καθῖζον, -->
αυτοί αμέσως επιβιβάστηκαν και στα καθίσματα κάθισαν,

<!-- grc: ἑξῆς δ᾽ ἑζόμενοι πολιὴν ἅλα τύπτον ἐρετμοῖς. -->
και με τη σειρά καθισμένοι τη γκρίζα θάλασσα χτυπούσαν με τα κουπιά.

"""


if __name__ == "__main__":
    populate_translations_en()
    populate_translations_ru()
    populate_translations_el()
