"""Read-only, cross-source word lookup for interactive exploration
(examples/lookup_word.py, okfbuild/cli.py's `lookup` subcommand) --
NOT a building block for the real pipeline, which goes through
okfbuild/concepts/*.py's build() functions instead, for the citation/
footnote bookkeeping this module doesn't do. Builds no ConceptFile,
writes nothing.
"""

from okfbuild.sources import SourceBundle


def lookup_word(lemma: str, sources: SourceBundle, pos: str = "noun") -> dict[str, object]:
    """Queries every lemma-keyed source in `sources` for `lemma` and
    returns {source_name: result}, omitting any source that found
    nothing. Wikipedia is deliberately excluded -- it's keyed by
    topic/person for Cultural Context entries, not by lexeme."""
    results: dict[str, object] = {}

    homeric = sources.eee_engine.collect_slot_forms(lemma, pos, "grc", backend="homeric")
    if homeric:
        results["eee_engine (homeric)"] = homeric
    attic = sources.eee_engine.collect_slot_forms(lemma, pos, "grc", backend="attic")
    if attic:
        results["eee_engine (attic)"] = attic
    modern = sources.eee_engine.collect_slot_forms(lemma, pos, "el")
    if modern:
        results["eee_engine (modern)"] = modern

    morpheus_readings = sources.morpheus.analyze(lemma)
    if morpheus_readings:
        results["morpheus"] = morpheus_readings

    lsj_entry = sources.lsj.lookup(lemma)
    if lsj_entry:
        results["lsj"] = lsj_entry

    wiktextract_entry = sources.wiktextract.lookup(lemma)
    if wiktextract_entry:
        results["wiktextract"] = wiktextract_entry

    byzantine = sources.byzantine_forms.get(lemma)
    if byzantine:
        results["byzantine_lexicon"] = byzantine

    if sources.iecor:
        iecor_entries = sources.iecor.get(lemma)
        if iecor_entries:
            results["iecor"] = iecor_entries

    return results
