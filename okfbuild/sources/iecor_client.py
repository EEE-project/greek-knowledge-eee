"""Loads data/iecor/ancient_greek_cognates.tsv -- a small, committed
extract of lexibank/iecor's (IE-CoR) Ancient Greek entries (Language_ID
110), joined through its cognates.csv/cognatesets.csv to each
headword's Proto-Indo-European (or intermediate) root and the editors'
own justification prose. See references/sources/iecor.md for
provenance, license (CC BY 4.0), and how this extract was produced.
"""

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IECorEntry:
    """One cognate-set analysis for a headword. A headword can have more
    than one (see load_iecor_cognates) -- IE-CoR's comparative wordlist
    occasionally fills two distinct reference-meaning slots with the
    same Greek word (e.g. ὄνυξ for both "fingernail, hoof" and "nail,
    claw, hoof"), each analyzed independently with its own root."""

    gloss: str
    root_form: str
    root_language: str
    justification: str


def load_iecor_cognates(tsv_path: Path) -> dict[str, list[IECorEntry]]:
    """Load the extracted TSV into a headword-keyed dict of IECorEntry
    lists (almost always one entry; see IECorEntry's docstring for the
    rare exception)."""
    result: dict[str, list[IECorEntry]] = {}
    with open(tsv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            entry = IECorEntry(
                gloss=row["gloss"],
                root_form=row["root_form"],
                root_language=row["root_language"],
                justification=row["justification"],
            )
            result.setdefault(row["headword"], []).append(entry)
    return result
