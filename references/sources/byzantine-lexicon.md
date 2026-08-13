# Byzantine verb lexicon

`greek-inflexion-eee`'s `byzantine_verbs_lexicon.yaml`
(`src/greek_inflexion_eee/data/byzantine_verbs_lexicon.yaml`), sourced
from a manual transcription of Sophocles' 1887 *Greek Lexicon of the Roman
and Byzantine Periods*. 61 verb lemmas at the time this repo was created,
growing to include the -οσαν imperfect/aorist pattern via
section-06-byzantine-mining.

No live API exists for Byzantine Greek at all (LBG/DIAL-G/Lampe/Du Cange
are all human-search-only, no bulk export) — this file is read directly
as a local data file by `build/sources/byzantine_lexicon.py` (added in
section-03-source-clients), not queried over the network.
