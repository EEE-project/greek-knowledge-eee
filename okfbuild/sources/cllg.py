"""CLLG (Corpus Liberatum Linguae Graecae, https://cllg-project.github.io/): the TLG E texts as TEI files -- the texts
under CC0, their citation structure and metadata under CC-BY 4.0 (see references/sources/cllg.md). Opt-in and
local-only, like the LSJ dump: a sparse git clone of the Freed corpus in data/cllg/freed-corpus (gitignored;
data/cllg/README.md gives the commands), read by `greek-knowledge cllg`. Not part of SourceBundle or `lookup`: a text
corpus is not lemma-keyed.

A text is cited the way its refsDecl declares (`<citeStructure match="..." use="@n">`): by nested elements (book,
chapter and section divs, verse lines `l`) and/or by empty elements, the page breaks `pb` (Eustathius, the
Etymologicum Magnum). A citation is the `n` of each open cited element, outermost first, then the `n` of the last
cited page break: "10.510" (book 10, line 510), "1.2.15" (book, chapter, section), "209" (a page)."""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

REPO_URL = "https://gitlab.inria.fr/almanach/cllg/freed-corpus.git"
_TEXT_ID = re.compile(r"(tlg\d{4})\.(tlg\d{3})")
_UNIT = re.compile(r"""<citeStructure\b[^>]*\bmatch="[^"]*?(\w+)(?:\[@(\w+)='([^']*)'\])?"[^>]*>""")
_TAG = re.compile(r"<(/?)(\w+)([^>]*?)(/?)>")
_N = re.compile(r'\bn="([^"]*)"')


@dataclass(frozen=True)
class Hit:
    ref: str   # the citation of the place, e.g. "10.510"
    text: str  # the matched words and what follows them, without tags


def text_path(corpus: Path, text_id: str) -> Path:
    """tlg0012.tlg002 -> <corpus>/data/tlg0012/tlg002/tlg0012.tlg002.cllg-grc1.xml (the one file name of the corpus)."""
    m = _TEXT_ID.fullmatch(text_id)
    if not m:
        raise ValueError(f"not a CLLG text id: {text_id!r} (the form is tlg0012.tlg002)")
    return corpus / "data" / m.group(1) / m.group(2) / f"{text_id}.cllg-grc1.xml"


def passage(path: Path, ref: str) -> str:
    """The text of one citation, without tags: "10.510" is one line, "10" all of book 10, "209" one page (up to the next
    page break). The first match counts. Raises KeyError for a citation the text does not have."""
    raw = path.read_text(encoding="utf-8")
    want, begin = tuple(ref.split(".")), None
    for start, end, cite in _walk(raw):
        inside = cite[: len(want)] == want
        if begin is None and inside:
            begin = end
        elif begin is not None and not inside:
            return _strip(raw[begin:start])
    if begin is None:
        raise KeyError(f"{ref!r} is not a citation of {path.name}")
    return _strip(raw[begin : raw.find("</body>")])


def find(path: Path, phrase: str, after: int = 160) -> list[Hit]:
    """Every place of phrase in the body of the text. Case, accents and breathings are ignored, and tags and line breaks
    may stand between its words."""
    raw = path.read_text(encoding="utf-8")
    words = _plain(phrase)[0].split()
    if not words:
        raise ValueError("the phrase is empty")
    flat, where = _plain(raw)
    body = raw.find("<body")
    spans = [(where[m.start()], where[m.end() - 1] + 1) for m in re.finditer(r"(?:\s|<[^>]*>)+".join(map(re.escape, words)), flat)]
    spans = [(s, e) for s, e in spans if s > body and raw.rfind("<", 0, s) < raw.rfind(">", 0, s)]  # not in the header, not in a tag
    if not spans:
        return []
    cites, i, cite = [], 0, ()
    for start, _, now in _walk(raw):
        while i < len(spans) and spans[i][0] < start:
            cites.append(cite)
            i += 1
        cite = now
    cites += [cite] * (len(spans) - i)
    return [Hit(".".join(c), _strip(re.sub(r"<[^>]*$", "", raw[s : e + after]))) for (s, e), c in zip(spans, cites)]


def _walk(raw: str):
    """(start, end, citation) after each tag of the body: the citation of the text that follows the tag."""
    units = _UNIT.findall(raw[: raw.find("</teiHeader>")])  # (element, attribute, value), e.g. ("div", "type", "book")

    def cited(name: str, attrs: str) -> str | None:
        n = _N.search(attrs)
        hit = any(name == u and (not a or re.search(rf'\b{a}="{re.escape(v)}"', attrs)) for u, a, v in units)
        return n.group(1) if n and hit else None

    stack, page = [], None
    for m in _TAG.finditer(raw, raw.find("<body")):
        close, name, attrs, empty = m.groups()
        if close:
            while stack and stack.pop()[0] != name:
                pass
        elif empty:
            if name in ("pb", "milestone"):  # an empty cited element of another kind (a lost verse <l n="5"/>) is no page
                page = cited(name, attrs) or page
        else:
            stack.append((name, cited(name, attrs)))
        yield m.start(), m.end(), tuple(n for _, n in stack if n) + ((page,) if page else ())


def _plain(s: str) -> tuple[str, list[int]]:
    """s case-folded (final ς = σ) without accents and breathings, and for each of its characters the index in s it comes from."""
    out, where = [], []
    for i, c in enumerate(s):
        for b in unicodedata.normalize("NFD", c):
            if not unicodedata.combining(b):
                for f in b.casefold():
                    out.append(f)
                    where.append(i)
    return "".join(out), where


def _strip(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", s)).strip()
