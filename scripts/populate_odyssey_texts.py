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


def populate_translations_en() -> None:
    body = _POPE_SECTION.rstrip("\n") + "\n\n---\n\n" + _MURRAY_SECTION.rstrip("\n") + "\n"
    sources = [
        Source(id="tr-pope", resource="https://en.wikisource.org/wiki/Odyssey_(Pope)",
               title="The Odyssey of Homer", author="Alexander Pope"),
        Source(id="tr-murray1919", resource="https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0136",
               title="The Odyssey", author="A. T. Murray"),
        _GRC_MURRAY1919_SOURCE,
    ]
    concept = build(
        work="Odyssey", passage="I.1-21, IX.19-38", language="en",
        translators=["Pope", "Murray"], body=body, sources=sources,
    )
    write(concept, _TEXTS_DIR / "translations_en.md")


# Copied verbatim via:
#   git -C ~/work/greek/git/codeberg.org/EEE-project/created_with_eee \
#     show translations:odyssey/2026_06_01/translations_ru.md
# -- the "## Жуковский" section only (up to, not including, "## Вересаев").
_ZHUKOVSKY_I = """\
## Жуковский

<!-- Жуковский В. А. Одиссея. СПб., 1849 · https://ru.wikisource.org/wiki/Одиссея_(Гомер;_Жуковский) -->
<!-- **Жуковский, 1849** · [wikisource.org ↗](https://ru.wikisource.org/wiki/Одиссея_(Гомер;_Жуковский)) · рус., белый стих (пятистопный ямб) · романтический возвышенный стиль · первый классический стихотворный перевод на русский -->

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
<!-- **Жуковский, 1849** · [wikisource.org ↗](https://ru.wikisource.org/wiki/Одиссея_(Гомер;_Жуковский)) · рус., белый стих (пятистопный ямб) · романтический возвышенный стиль · первый классический стихотворный перевод на русский -->

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

"""

# Copied verbatim via:
#   git -C ~/work/greek/git/codeberg.org/EEE-project/created_with_eee \
#     show translations:odyssey/2026_06_01/translations_ru.md
# -- the "## Вересаев" section only (to end of file).
_VERESAEV_I = """\
## Вересаев

<!-- Вересаев В. В. Одиссея. М., 1953 · http://az.lib.ru/g/gomer/text_0070.shtml -->
<!-- **Вересаев, 1953** · [az.lib.ru ↗](http://az.lib.ru/g/gomer/text_0070.shtml) · рус., проза · ясный современный язык · ориентирован на смысловую точность · стандартный учебный перевод -->

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
<!-- **Вересаев, 1953** · [az.lib.ru ↗](http://az.lib.ru/g/gomer/text_0070.shtml) · рус., проза · ясный современный язык · ориентирован на смысловую точность · стандартный учебный перевод -->

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
"""


def populate_translations_ru() -> None:
    zhukovsky = _ZHUKOVSKY_I.rstrip("\n") + "\n\n" + _strip_header(_ZHUKOVSKY_IX)
    veresaev = _VERESAEV_I.rstrip("\n") + "\n\n" + _strip_header(_VERESAEV_IX)
    body = zhukovsky + "\n\n---\n\n" + veresaev + "\n"
    sources = [
        Source(id="tr-zhukovsky1849", resource="https://ru.wikisource.org/wiki/Одиссея_(Гомер;_Жуковский)",
               title="Одиссея", author="В. А. Жуковский"),
        Source(id="tr-veresaev1953", resource="http://az.lib.ru/g/gomer/text_0070.shtml",
               title="Одиссея", author="В. В. Вересаев"),
        _GRC_MURRAY1919_SOURCE,
    ]
    concept = build(
        work="Odyssey", passage="I.1-21, IX.19-38", language="ru",
        translators=["Жуковский", "Вересаев"],
        body=body, sources=sources,
    )
    write(concept, _TEXTS_DIR / "translations_ru.md")


# Copied verbatim via:
#   git -C ~/work/greek/git/codeberg.org/EEE-project/created_with_eee \
#     show translations:odyssey/2026_06_01/translations_el.md
# -- the "## Πολυλάς" section only (up to, not including, "## Καζαντζάκης–Κακριδής").
_POLYLAS_I = """\
## Πολυλάς

<!-- Πολυλάς Ι. Ὀδύσσεια. Ἀθήνα, 1875 · https://www.openbook.gr/omirou-odysseia-metafrasi/ -->
<!-- **Πολυλάς, 1875/1877** · I.1-21 [openbook.gr ↗](https://www.openbook.gr/omirou-odysseia-metafrasi/) · IX.19-38 [gutenberg.org ↗](https://www.gutenberg.org/files/30614/30614-0.txt) · ν.ε., Καθαρεύουσα · κανονική νεοελληνική μετάφραση του 19ου αι. · κλασικό λογοτεχνικό ύφος -->

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
"""


def populate_translations_el() -> None:
    body = _POLYLAS_I.rstrip("\n") + "\n\n" + _strip_header(_POLYLAS_IX) + "\n"
    sources = [
        Source(id="tr-polylas1875", resource="https://www.openbook.gr/omirou-odysseia-metafrasi/",
               title="Ομήρου Οδύσσεια, Τόμος Α΄", author="Ιάκωβος Πολυλάς"),
        Source(id="tr-polylas1877", resource="https://www.gutenberg.org/files/30614/30614-0.txt",
               title="Ομήρου Οδύσσεια, Τόμος Β΄", author="Ιάκωβος Πολυλάς"),
        _GRC_MURRAY1919_SOURCE,
    ]
    concept = build(
        work="Odyssey", passage="I.1-21, IX.19-38", language="el",
        translators=["Πολυλάς"], body=body, sources=sources,
    )
    write(concept, _TEXTS_DIR / "translations_el.md")


# Copied verbatim via:
#   git -C ~/work/greek/git/codeberg.org/EEE-project/created_with_eee \
#     show translations:odyssey/2026_06_15/interlenear_en.md
# -- entire file, verbatim (word-by-word EN gloss for IX.19-38 only;
# no *usable* interlinear content exists for I.1-21 on the abandoned
# branch -- content by that name exists there too, but was judged unfit
# for this corpus and deliberately not ported; see CHANGELOG.md).
_INTERLINEAR_EN = """\
### Odyss. IX.19–24

**εἶμ' Ὀδυσεὺς Λαερτιάδης, ὃς πᾶσι δόλοισιν**
I-am Odysseus Laertiades, who with-all wiles

**ἀνθρώποισι μέλω, καί μευ κλέος οὐρανὸν ἵκει.**
among-men am-known, and my fame heaven reaches.

**ναιετάω δ' Ἰθάκην εὐδείελον· ἐν δ' ὄρος αὐτῇ**
I-dwell in Ithaca sun-bright; in it a mountain there

**Νήριτον εἰνοσίφυλλον, ἀριπρεπές· ἀμφὶ δὲ νῆσοι**
Neritos leaf-quivering, conspicuous; around it islands

**πολλαὶ ναιετάουσι μάλα σχεδὸν ἀλλήλῃσι,**
many dwell very close to-one-another,

**Δουλίχιόν τε Σάμη τε καὶ ὑλήεσσα Ζάκυνθος.**
Doulichion and Same and wooded Zakynthos.

### Odyss. IX.25–28

**αὐτὴ δὲ χθαμαλὴ πανυπερτάτη εἰν ἁλὶ κεῖται**
itself but low, most-remote in the sea lies

**πρὸς ζόφον, αἱ δέ τ' ἄνευθε πρὸς ἠῶ τ' ἠέλιόν τε,**
toward the west; those further toward dawn and sun,

**τρηχεῖ', ἀλλ' ἀγαθὴ κουροτρόφος· οὔ τοι ἐγώ γε**
rugged, yet good nurse-of-youth; truly I at-least

**ἧς γαίης δύναμαι γλυκερώτερον ἄλλο ἰδέσθαι.**
of-my-own land can sweeter other see.

### Odyss. IX.29–33

**ἦ μέν μ' αὐτόθ' ἔρυκε Καλυψώ, δῖα θεάων,**
truly indeed me there held Kalypso, glorious of-goddesses,

**ἐν σπέσσι γλαφυροῖσι, λιλαιομένη πόσιν εἶναι·**
in caves hollow, longing husband to-be;

**ὣς δ' αὔτως Κίρκη κατερήτυεν ἐν μεγάροισιν**
so likewise Kirke kept-back in her halls

**Αἰαίη δολόεσσα, λιλαιομένη πόσιν εἶναι·**
Aiaian crafty, longing husband to-be;

**ἀλλ' ἐμὸν οὔ ποτε θυμὸν ἐνὶ στήθεσσιν ἔπειθον.**
but my heart never in my breast could-they-persuade.

### Odyss. IX.34–38

**ὣς οὐδὲν γλύκιον ἧς πατρίδος οὐδὲ τοκήων**
so nothing sweeter than one's-own homeland and parents

**γίγνεται, εἴ περ καί τις ἀπόπροθι πίονα οἶκον**
is, even if someone afar a rich house

**γαίῃ ἐν ἀλλοδαπῇ ναίει ἀπάνευθε τοκήων.**
in-land in foreign dwells far-from parents.

**εἰ δ' ἄγε τοι καὶ νόστον ἐμὸν πολυκηδέ' ἐνίσπω,**
but come let-me-tell you my return full-of-cares,

**ὅν μοι Ζεὺς ἐφέηκεν ἀπὸ Τροίηθεν ἰόντι.**
which to-me Zeus sent from Troy departing.
"""

# Copied verbatim via:
#   git -C ~/work/greek/git/codeberg.org/EEE-project/created_with_eee \
#     show translations:odyssey/2026_06_15/interlenear_el.md
# -- entire file, verbatim (word-by-word EL gloss for IX.19-38 only;
# no *usable* interlinear content exists for I.1-21 on the abandoned
# branch -- content by that name exists there too, but was judged unfit
# for this corpus and deliberately not ported; see CHANGELOG.md).
_INTERLINEAR_EL = """\
### Odyss. IX.19–24

**εἶμ' Ὀδυσεὺς Λαερτιάδης, ὃς πᾶσι δόλοισιν**
Είμαι ο Οδυσσέας Λαερτιάδης, που με όλα τα τεχνάσματα

**ἀνθρώποισι μέλω, καί μευ κλέος οὐρανὸν ἵκει.**
στους ανθρώπους είμαι γνωστός, και η δόξα μου τον ουρανό φτάνει.

**ναιετάω δ' Ἰθάκην εὐδείελον· ἐν δ' ὄρος αὐτῇ**
Κατοικώ στην Ιθάκη την ηλιόλουστη· σ' αυτή βουνό

**Νήριτον εἰνοσίφυλλον, ἀριπρεπές· ἀμφὶ δὲ νῆσοι**
το Νήριτο φυλλοσείστης, ξακουστό· και γύρω νησιά

**πολλαὶ ναιετάουσι μάλα σχεδὸν ἀλλήλῃσι,**
πολλά κατοικούν, πολύ κοντά το ένα στ' άλλο,

**Δουλίχιόν τε Σάμη τε καὶ ὑλήεσσα Ζάκυνθος.**
Δουλίχι και Σάμη και η δασώδης Ζάκυνθος.

### Odyss. IX.25–28

**αὐτὴ δὲ χθαμαλὴ πανυπερτάτη εἰν ἁλὶ κεῖται**
Αυτή δε χαμηλή, η πιο απόμακρη στη θάλασσα κείται,

**πρὸς ζόφον, αἱ δέ τ' ἄνευθε πρὸς ἠῶ τ' ἠέλιόν τε,**
προς τη δύση, εκείνες δε μακριά προς αυγή και ήλιο,

**τρηχεῖ', ἀλλ' ἀγαθὴ κουροτρόφος· οὔ τοι ἐγώ γε**
τραχεία, μα καλή τροφός νέων· κι εγώ βέβαια

**ἧς γαίης δύναμαι γλυκερώτερον ἄλλο ἰδέσθαι.**
της γης μου δεν μπορώ γλυκύτερο άλλο να δω.

### Odyss. IX.29–33

**ἦ μέν μ' αὐτόθ' ἔρυκε Καλυψώ, δῖα θεάων,**
Αλήθεια εμένα εκεί κρατούσε η Καλυψώ, θεϊκή θεά,

**ἐν σπέσσι γλαφυροῖσι, λιλαιομένη πόσιν εἶναι·**
σε σπήλαια βαθιά, λαχταρώντας σύζυγος να γίνει·

**ὣς δ' αὔτως Κίρκη κατερήτυεν ἐν μεγάροισιν**
έτσι κι η Κίρκη με κρατούσε στα μέγαρά της

**Αἰαίη δολόεσσα, λιλαιομένη πόσιν εἶναι·**
η Αιαία η δολερή, λαχταρώντας σύζυγος να γίνει·

**ἀλλ' ἐμὸν οὔ ποτε θυμὸν ἐνὶ στήθεσσιν ἔπειθον.**
μα ποτέ την ψυχή μου στο στήθος δεν έπειθαν.

### Odyss. IX.34–38

**ὣς οὐδὲν γλύκιον ἧς πατρίδος οὐδὲ τοκήων**
Έτσι τίποτα γλυκύτερο από την πατρίδα κι από τους γονείς

**γίγνεται, εἴ περ καί τις ἀπόπροθι πίονα οἶκον**
δεν γίνεται, έστω κι αν κάποιος μακριά πλούσιο σπίτι

**γαίῃ ἐν ἀλλοδαπῇ ναίει ἀπάνευθε τοκήων.**
σε ξένη γη κατοικεί μακριά από γονείς.

**εἰ δ' ἄγε τοι καὶ νόστον ἐμὸν πολυκηδέ' ἐνίσπω,**
Αλλά άγε, θα σου πω και τον νόστο μου τον πολύπικρο,

**ὅν μοι Ζεὺς ἐφέηκεν ἀπὸ Τροίηθεν ἰόντι.**
που ο Ζευς μου ετοίμασε αφού έφυγα από Τροία.
"""


def populate_interlinear() -> None:
    sources = [_GRC_MURRAY1919_SOURCE]
    concept_en = build(
        work="Odyssey", passage="IX.19-38", language="en",
        translators=["interlinear"], body=_INTERLINEAR_EN, sources=sources,
    )
    write(concept_en, _TEXTS_DIR / "interlinear_en.md")

    concept_el = build(
        work="Odyssey", passage="IX.19-38", language="el",
        translators=["interlinear"], body=_INTERLINEAR_EL, sources=sources,
    )
    write(concept_el, _TEXTS_DIR / "interlinear_el.md")


if __name__ == "__main__":
    populate_translations_en()
    populate_translations_ru()
    populate_translations_el()
    populate_interlinear()
