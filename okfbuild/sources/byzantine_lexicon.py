"""Reads greek-inflexion-eee's byzantine_verbs_lexicon.yaml as data.

That file lives in a separate repo checkout; resolving its path on disk
is the caller's responsibility — this module only parses it once handed
a path.
"""

from pathlib import Path

import yaml


def load_byzantine_forms(yaml_path: Path) -> dict[str, dict[str, str | list[str]]]:
    """Load greek_inflexion_eee's byzantine_verbs_lexicon.yaml into a
    lemma-keyed dict of {paradigm-cell-tag: attested form(s)}."""
    data = yaml.safe_load(Path(yaml_path).read_text(encoding="utf-8"))
    return {lemma: entry["forms"] for lemma, entry in (data or {}).items()}
