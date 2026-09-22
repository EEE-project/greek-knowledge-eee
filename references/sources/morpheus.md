# Morpheus

The Perseids Morpheus service
(`https://services.perseids.org/bsp/morphologyservice/analysis/word`),
used for Classical/Koine Ancient Greek morphological analysis.

This KB's client, [`okfbuild/sources/morpheus_client.py`](../../okfbuild/sources/morpheus_client.py) (added in
section-03-source-clients), is a **vendored copy** of
`greek-inflexion-eee/tools/morpheus/query_morpheus.py` — that script
lives under `tools/` in that repo, not its installable package, so
importing it directly isn't possible without depending on that repo's
internal layout. The vendored copy should itself carry a
`# TODO: extract to a shared library` comment (the original script has no
such marker today — this is new tech debt this repo is deliberately
taking on, not an existing one being inherited), so a future reconciliation
into a shared package is easy to find. Caches one JSON file per queried
word, reusing that tool's existing cache-file-per-word convention, so
re-running this repo's build doesn't re-hit the live service.
