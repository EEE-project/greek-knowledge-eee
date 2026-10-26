# Odyssey — Literary Text and Literary Translation entries

Concept files for the Odyssey (I.1-21, IX.19-180): `text.md` (a Literary
Text -- the Ancient Greek original, hand-authored from the `grc:` echo lines
below, not produced by the script mentioned further down),
`translations_en.md` (Pope, Murray, Chapman, interlinear_en), `translations_ru.md`
(Жуковский, Вересаев, interlinear_ru), `translations_el.md` (Πολυλάς, interlinear_el).
Each interlinear translator's stanza text echoes its Greek source line as
an `<!-- grc: ... -->` comment (stripped via `GreekUtils.strip_comment_lines()`)
ahead of the plain word-by-word gloss. Populated by
`scripts/populate_odyssey_texts.py`, a one-off, re-runnable script —
not the general build pipeline ([`okfbuild/pipeline.py`](../../okfbuild/pipeline.py)) — since there
is no live source to query for a human translation; see that script's
own docstring for why this content lives here rather than being
live-queried.

## Reading it

```bash
uv run greek-knowledge query --type texts --work odyssey --language ru --full  # --language grc/en/el for the others, comma-separated for several; drop it for all four
cat texts/odyssey/text.md                       # the Ancient Greek original
cat texts/odyssey/translations_en.md            # Pope, Murray, Chapman, interlinear_en
cat texts/odyssey/translations_ru.md            # interlinear_ru, Жуковский, Вересаев
cat texts/odyssey/translations_el.md            # Πολυλάς, interlinear_el
awk '/^## Murray/{f=1;next} /^## /{f=0} f' texts/odyssey/translations_en.md   # one translator's section
```

## Sources of the translations

Every section of a named translator in `translations_{en,ru,el}.md` is taken word for word from the source in the third column; the files hold no line that the source does not hold. The interlinear sections are not listed: they were written for this knowledge base. The "second host" is a different site with the same text, compared line by line. A bilingual publication shows the Greek original beside the translation. An archived copy is an existing snapshot on web.archive.org; where there is none, the table says so.

| Translator | Passages | Text taken from | Second host (same text) | Bilingual publication | Archived copies |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Pope | I.1-21, IX.19-180 | [en.wikisource, Odyssey (Pope)](https://en.wikisource.org/wiki/Odyssey_(Pope)), wikitext of Book 1 and Book 9 | none | No: English only | [main page, 22.09.2026](https://web.archive.org/web/20260922110929/https://en.wikisource.org/wiki/Odyssey_(Pope)); [Book 1, 04.08.2026](https://web.archive.org/web/20260804060643/https://en.wikisource.org/wiki/Odyssey_(Pope)/Book_1); [Book 9, 04.06.2025](https://web.archive.org/web/20250604190128/https://en.wikisource.org/wiki/Odyssey_(Pope)/Book_9) |
| Murray (1919) | I.1-21, IX.19-180 | [Perseus Digital Library](https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0136); the English text is the TEI file `perseus-eng3` ([GitHub](https://github.com/PerseusDL/canonical-greekLit/blob/master/data/tlg0012/tlg002/tlg0012.tlg002.perseus-eng3.xml)) | none | Yes, on Perseus: the Greek text of the Loeb edition (Murray, 1919) beside the English | [Perseus, 22.09.2026](https://web.archive.org/web/20260922111108/https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0136); TEI file: no snapshot yet |
| Chapman | I.1-21, IX.19-38 | [Project Gutenberg #48895](https://www.gutenberg.org/ebooks/48895) | none | No: English only (the notes quote single Greek words) | [ebook page, 21.04.2026](https://web.archive.org/web/20260421005400/https://gutenberg.org/ebooks/48895); [text file, 24.07.2026](https://web.archive.org/web/20260724160436/https://www.gutenberg.org/files/48895/48895-0.txt) |
| Zhukovsky (translation published 1849) | I.1-21, IX.19-180 | [ru.wikisource, song 1](https://ru.wikisource.org/wiki/%D0%9E%D0%B4%D0%B8%D1%81%D1%81%D0%B5%D1%8F_%28%D0%93%D0%BE%D0%BC%D0%B5%D1%80%3B_%D0%96%D1%83%D0%BA%D0%BE%D0%B2%D1%81%D0%BA%D0%B8%D0%B9%29/%D0%9F%D0%B5%D1%81%D0%BD%D1%8C_%D0%BF%D0%B5%D1%80%D0%B2%D0%B0%D1%8F) and [song 9](https://ru.wikisource.org/wiki/%D0%9E%D0%B4%D0%B8%D1%81%D1%81%D0%B5%D1%8F_%28%D0%93%D0%BE%D0%BC%D0%B5%D1%80%3B_%D0%96%D1%83%D0%BA%D0%BE%D0%B2%D1%81%D0%BA%D0%B8%D0%B9%29/%D0%9F%D0%B5%D1%81%D0%BD%D1%8C_%D0%B4%D0%B5%D0%B2%D1%8F%D1%82%D0%B0%D1%8F); edition: Собрание сочинений В. Жуковского, 6-е изд., СПб: Типография Императорской академии наук, 1869, Т. 5: Гомерова Одиссея, изд. 2-е | none | No: Russian only | [main page, 22.09.2026](https://web.archive.org/web/20260922110724/https://ru.wikisource.org/wiki/%D0%9E%D0%B4%D0%B8%D1%81%D1%81%D0%B5%D1%8F_(%D0%93%D0%BE%D0%BC%D0%B5%D1%80;_%D0%96%D1%83%D0%BA%D0%BE%D0%B2%D1%81%D0%BA%D0%B8%D0%B9)); [song 1, 15.03.2025](https://web.archive.org/web/20250315123528/https://ru.wikisource.org/wiki/%D0%9E%D0%B4%D0%B8%D1%81%D1%81%D0%B5%D1%8F_(%D0%93%D0%BE%D0%BC%D0%B5%D1%80;_%D0%96%D1%83%D0%BA%D0%BE%D0%B2%D1%81%D0%BA%D0%B8%D0%B9)/%D0%9F%D0%B5%D1%81%D0%BD%D1%8C_%D0%BF%D0%B5%D1%80%D0%B2%D0%B0%D1%8F); [song 9, 02.10.2025](https://web.archive.org/web/20251002003935/https://ru.wikisource.org/wiki/%D0%9E%D0%B4%D0%B8%D1%81%D1%81%D0%B5%D1%8F_(%D0%93%D0%BE%D0%BC%D0%B5%D1%80;_%D0%96%D1%83%D0%BA%D0%BE%D0%B2%D1%81%D0%BA%D0%B8%D0%B9)/%D0%9F%D0%B5%D1%81%D0%BD%D1%8C_%D0%B4%D0%B5%D0%B2%D1%8F%D1%82%D0%B0%D1%8F) |
| Veresaev (1953) | I.1-21, IX.19-180 | [az.lib.ru](http://az.lib.ru/g/gomer/text_0070.shtml); edition: Moscow, Гос. изд-во худож. лит-ры, 1953 | [ancientrome.ru](https://ancientrome.ru/antlitr/homer/index.htm), songs [1](https://ancientrome.ru/antlitr/t.htm?a=1344030001) and [9](https://ancientrome.ru/antlitr/t.htm?a=1344030009): word for word the same | Yes, on ancientrome.ru: the Greek text of Murray (Heinemann, 1919) beside the Russian, with a button that hides it; az.lib.ru is Russian only | [az.lib.ru, 22.09.2026](https://web.archive.org/web/20260922110540/http://az.lib.ru/g/gomer/text_0070.shtml); [ancientrome.ru index, 01.07.2026](https://web.archive.org/web/20260701005606/https://ancientrome.ru/antlitr/homer/index.htm); [song 1, 12.07.2026](https://web.archive.org/web/20260712122841/https://ancientrome.ru/antlitr/t.htm?a=1344030001); [song 9, 11.05.2026](https://web.archive.org/web/20260511120345/https://ancientrome.ru/antlitr/t.htm?a=1344030009) |
| Polylas | I.1-21, IX.19-180 | Project Gutenberg [#30613](https://www.gutenberg.org/files/30613/30613-0.txt) (Book I) and [#30614](https://www.gutenberg.org/files/30614/30614-0.txt) (Book IX) | none | Gutenberg: no, modern Greek only. The school site [users.sch.gr](https://users.sch.gr/ipap/Ellinikos%20Politismos/Yliko/OMHROS%20ODYSSEIA/01.htm) ([09.htm](https://users.sch.gr/ipap/Ellinikos%20Politismos/Yliko/OMHROS%20ODYSSEIA/09.htm)) is bilingual (each ancient Greek line is followed by Polylas's line), but its spelling is modernized, so it is not word for word the same (Book I: 7 of 21 lines, Book IX: 74 of 162) and is not a source of this text; no snapshot yet | [#30613, 15.01.2026](https://web.archive.org/web/20260115063413/https://www.gutenberg.org/files/30613/30613-0.txt); [#30614, 22.09.2026](https://web.archive.org/web/20260922111612/https://www.gutenberg.org/files/30614/30614-0.txt) |
