# Kavafis, Ithaka — Literary Text and Literary Translation entries

Concept files for Cavafy's «Ithaka» (1911), which has 36 lines: `text.md`
(a Literary Text -- the Greek original itself, complete), `translations_en.md`
(a freshly-authored interlinear gloss, complete), and `translations_ru.md`
(a literal подстрочник, complete: στ. 1-23 are the kavafis_ithaki course's own text, στ. 24-36 were
authored for this entry in the same manner).
Each interlinear file echoes its Greek source line as an
`<!-- el: ... -->` comment ahead of the plain word-by-word gloss, same
convention [`texts/odyssey/`](../odyssey/index.md) uses with `<!-- grc: ... -->`.

Named literary translations are known -- Valassopoulo (1924),
Keeley/Sherrard (1975), Barnstone (2006) and Mendelsohn (2012) into English,
and into Russian Шмаков/Бродский, Ильинская (1984), Величанский, Колесов,
Якушева, Некляев/Вланес and Левитов -- but not reproduced in full: each is
presumptively still under copyright except Valassopoulo (public domain, but
no complete reliable text source was found). Each gets a "(reference only,
not reproduced)" `##` section instead: translator, citation, an archived
link where one exists, and a one-line copyright-status note, no poem text --
see the `{en,ru}.md` files' own reference sections.

Two recorded readings of the poem (Greek, Grigoris Valtinos; English, Sean Connery)
are linked from [[`culture/cavafy.md`](../../culture/cavafy.md)](../../culture/cavafy.md), not from here.

Hand-authored directly (see [[`templates/literary-text.md`](../../templates/literary-text.md)](../../templates/literary-text.md),
[[`templates/literary-translation.md`](../../templates/literary-translation.md)](../../templates/literary-translation.md) and
[`templates/README.md`](../../templates/README.md)), not generated -- `uv run greek-knowledge
check` validates frontmatter shape here the same way it does for
grammar/ and culture/.

## Reading it

```bash
uv run greek-knowledge query --type texts --work ithaka --language ru --full   # --language el/en for the others, comma-separated for several; drop it for all three
cat texts/kavafis_ithaki/text.md                # the Greek original
cat texts/kavafis_ithaki/translations_en.md     # English interlinear gloss + link to a published translation
cat texts/kavafis_ithaki/translations_ru.md     # Russian подстрочник + links to published translations
awk '/^## подстрочник/{f=1;next} /^## /{f=0} f' texts/kavafis_ithaki/translations_ru.md   # just the подстрочник
```
