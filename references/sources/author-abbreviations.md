# Ancient-author abbreviation lists (LSJ, OCD)

Two reference lists for abbreviating ancient authors and works in
citations. The maintainer's note (`analisys/sources.md`) names them as
the convention for this KB: abbreviations of ancient authors follow the
OCD and LSJ.

- **LSJ, "Authors and Works"** —
  `http://stephanus.tlg.uci.edu/lsj/01-authors_and_works.html`
  (redirects to https), hosted alongside the TLG. One static HTML page
  (about 550 KB) listing the authors LSJ cites, each with its
  abbreviation in brackets, a date, and the standard edition, e.g.
  `Abydenus Historicus [ Abyd. ] ii A D. (?) Ed. C. Müller, FHG iv p.
  279.` It is LSJ's own key to the author abbreviations that appear in
  its entries, the same field [`okfbuild/sources/lsj_index.py`](../../okfbuild/sources/lsj_index.py) records as
  each citation's `author_abbreviation`.
- **OCD 4th edition, "Abbreviations List"** —
  `https://oxfordre.com/classics/fileasset/images/ORECLA/OCD.ABBREVIATIONS.pdf`,
  a 39-page PDF: general abbreviations first, then abbreviations for
  ancient authors and works (e.g. `M. Aur. Med.` = Marcus Aurelius,
  *Meditations*), periodicals, reference works, and inscription and
  papyrus corpora. The live URL answered HTTP 403 to a scripted request
  (checked 2026-09-21); the Wayback Machine copy
  `https://web.archive.org/web/20260312043057/https://oxfordre.com/classics/fileasset/images/ORECLA/OCD.ABBREVIATIONS.pdf`
  downloads normally (HTTP 200, `application/pdf`) — a concrete case of
  the maintainer's tip to look in `web.archive.org` when a source cannot
  be reached.

**Status: convention only, not integrated as data.** Neither list has a
bulk download or API, and their licence terms were not checked. Use them
to decide how an ancient author or work is abbreviated in a citation;
the OCD and LSJ abbreviation systems are separate lists and were not
compared entry by entry.
