# Odyssey — Literary Translation entries

Literary Translation concept files for the Odyssey (I.1-21, IX.19-38):
`translations_en.md` (Pope, Murray, interlinear_en), `translations_ru.md`
(Жуковский, Вересаев), `translations_el.md` (Πολυλάς, interlinear_el).
Each interlinear translator's stanza text echoes its Greek source line as
an `<!-- grc: ... -->` comment (stripped via `GreekUtils.strip_comment_lines()`)
ahead of the plain word-by-word gloss. Populated by
`scripts/populate_odyssey_texts.py`, a one-off, re-runnable script —
not the general build pipeline (`okfbuild/pipeline.py`) — since there
is no live source to query for a human translation; see that script's
own docstring for why this content lives here rather than being
live-queried.
