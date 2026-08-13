"""Wraps the already-installed eee_project package.

Backend registration (ancient-greek + unimorph chains) is the caller's
responsibility — this module only wraps the already-registered
get_slot_templates()/inflect_slot() calls, never a backend directly.
"""

import eee_project as eee


def inflect_all_attested(
    lemma: str, pos: str, language: str, backend: str | None = None
) -> dict[str, set[str]]:
    """Return every inflected form eee.inflect() can produce for `lemma`,
    keyed by feature-set description. Thin wrapper — no new logic beyond
    what eee_project already exposes (see claude-research.md §1.2 for the
    full existing API this wraps).

    `backend` selects a named backend variant (eee.get_slot_templates's/
    eee.inflect_slot's own `backend=` parameter) instead of "the default
    backend" for `language`. This is how period-scoped querying works for
    Ancient Greek: e.g. a caller can register
    AncientGreekBackend.for_period("epic") under backend="homeric" and
    AncientGreekBackend.for_period("attic") under backend="attic", then
    query each period independently via backend="homeric"/"attic" — the
    registered backend name is an arbitrary label chosen at registration
    time, unrelated to for_period()'s own argument spelling. If no
    backend is registered under the given name, this returns {} (same as
    the no-templates-found case), not an error — see
    eee.get_slot_templates's own docstring."""
    templates = eee.get_slot_templates(language, pos, "en", backend=backend)
    if not templates:
        return {}

    result = {}
    for template in templates:
        forms = eee.inflect_slot(lemma, template, pos, language=language, backend=backend)
        if forms:
            result[template.label] = forms
    return result
