"""The ordered period vocabulary for range-containment queries (see
okfbuild/query.py) — NOT the period list lexical_entry.build() sweeps by
default. Those are different things that happen to overlap: this module
adds "koine" for Grammatical Rule/Cultural Context content that spans it
(see okfbuild/pilot_content.py's Koine-sourced entries), but no source
backend can answer a koine-period Lexical Entry query, so pipeline.py's
and pilot_content.py's own default period lists for lexical_entry.build()
must never import from here — keep them as the separate, untouched
4-period list they already are.
"""

PERIOD_ORDER = ["homeric", "attic", "koine", "byzantine", "modern"]
