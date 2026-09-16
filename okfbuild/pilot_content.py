"""One-off curated enrichment for a single Lexical Entry.

Grammatical Rule and Cultural Context entries used to be curated here too
(as Python specs run through a builder), but that content is now
hand-authored directly under grammar/ and culture/ (see templates/ for the
expected shape) and validated by okfbuild/check.py instead of generated.
lexical_entry.build() has no parameter for a page-locator citation like
Beekes' etymology dictionary, so this module still rebuilds one word's
entry directly, the same way pipeline.py's own auto-extraction loop builds
every other Lexical Entry.
"""

from pathlib import Path

from okfbuild import okf
from okfbuild.concepts import lexical_entry
from okfbuild.sources import SourceBundle

# Matches pipeline.py's own _ALL_PERIODS -- duplicated rather than imported
# since that name is private to pipeline.py (this module only rebuilds one
# specific lemma's entry, not a general-purpose pipeline helper).
_ALL_PERIODS = ["homeric", "attic", "byzantine", "modern"]

# Per section-07-pilot.md's post-section-01 amendment: νόστος is this
# pilot's headline word and should exercise the beekes_citation mechanism
# section-04 added. lexical_entry.build() has no separate parameter for a
# page locator -- the citation embeds its own, as scholarly prose would.
# Own paraphrase of the etymology (not a verbatim quote from Beekes'
# copyrighted text), cross-checked against Wiktionary's own citation of the
# same page before writing this summary.
NOSTOS_BEEKES_CITATION = (
    "νόστος is an o-grade derivative of the PIE root *nes- (\"to return home\") "
    "plus the suffix -τος, from the same root as the verb νέομαι (\"to go/come "
    "back\") (Beekes 2010, p. 1024)"
)


def enrich_nostos_with_beekes(repo_root: Path, sources: SourceBundle) -> bool:
    """Rebuild words/νόστος.md with an Etymology section and write it back
    via okf.write() (verification-preserving, same as every other write in
    this pipeline). pipeline.py's own auto-extraction loop has no plumbing
    for a per-lemma curated citation, and adding that plumbing to
    already-reviewed section-05 code for one word's one optional field
    isn't proportionate, so this rebuilds the same entry directly instead.
    pos/level/tags match the real vocab_I_1-21.tsv row for νόστος exactly
    (pos=noun; the Odyssey vocab TSV schema has no level/tags columns).
    Returns okf.write()'s own bool (True if the file changed)."""
    concept = lexical_entry.build(
        "νόστος",
        "noun",
        _ALL_PERIODS,
        sources,
        level=[],
        tags=[],
        beekes_citation=NOSTOS_BEEKES_CITATION,
    )
    return okf.write(concept, repo_root / "words" / "νόστος.md")
