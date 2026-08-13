# EEE morphology engine

The already-installed `eee_project` package's Python API (`eee.inflect()`,
`eee.analyze()`, `eee.get_slot_templates()`, etc.). No network access, no
download step.

Canonical spec: `eee-project/docs/api-reference.md` and `api-patterns.md`
in the `eee-project` repo.

This KB's wrapper, `build/sources/eee_engine.py` (added in
section-03-source-clients), is a thin wrapper adding no new logic beyond
what `eee_project` already exposes.
