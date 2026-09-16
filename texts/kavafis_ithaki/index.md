# Kavafis, Ithaka — Literary Translation entries

Literary Translation concept files for Cavafy's «Ithaka» (1911), στ. 1-23
of 40 (the same span used in created_with_eee's kavafis_ithaki course
lessons): `translations_el.md` (the Greek original), `translations_en.md`
(a freshly-authored interlinear gloss), `translations_ru.md` (the course's
own подстрочник). Each interlinear file echoes its Greek source line as an
`<!-- el: ... -->` comment ahead of the plain word-by-word gloss, same
convention `texts/odyssey/` uses with `<!-- grc: ... -->`.

Four named literary translations are known (Valassopoulo 1924; the
course's own Шмаков/Бродский, Ильинская, Левитов) but not reproduced in
full -- each still under copyright except Valassopoulo (public domain,
but no complete reliable text source was found). Each gets a
"(reference only, not reproduced)" `##` section instead: translator,
citation, and a one-line copyright-status note, no poem text -- see the
`{en,ru}.md` files' own reference sections.

Hand-authored directly (see [`templates/literary-translation.md`](../../templates/literary-translation.md)
and `templates/README.md`), not generated -- `uv run greek-knowledge
check` validates frontmatter shape here the same way it does for
grammar/ and culture/.
