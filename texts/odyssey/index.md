# Odyssey — Literary Text and Literary Translation entries

Concept files for the Odyssey (I.1-21, IX.19-38): `text.md` (a Literary
Text -- the Ancient Greek original, hand-authored from the `grc:` echo lines
below, not produced by the script mentioned further down),
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

## Reading it

```bash
uv run greek-knowledge query --type texts --work odyssey --language ru --full  # --language grc/en/el for the others, comma-separated for several; drop it for all four
cat texts/odyssey/text.md                       # the Ancient Greek original
cat texts/odyssey/translations_en.md            # Pope, Murray, interlinear_en
cat texts/odyssey/translations_ru.md            # подстрочник, Жуковский, Вересаев
cat texts/odyssey/translations_el.md            # Πολυλάς, interlinear_el
awk '/^## Murray/{f=1;next} /^## /{f=0} f' texts/odyssey/translations_en.md   # one translator's section
```
