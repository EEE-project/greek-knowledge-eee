"""Wraps the already-installed eee_project package.

Backend registration (ancient-greek + unimorph chains) is the caller's
responsibility — this module only wraps the already-registered
get_slot_templates()/inflect_slot() calls, never a backend directly.
"""

import eee_project as eee


def inflect_all_attested(lemma: str, pos: str, language: str) -> dict[str, set[str]]:
    """Return every inflected form eee.inflect() can produce for `lemma`,
    keyed by feature-set description. Thin wrapper — no new logic beyond
    what eee_project already exposes (see claude-research.md §1.2 for the
    full existing API this wraps)."""
    templates = eee.get_slot_templates(language, pos, "en")
    if not templates:
        return {}

    result = {}
    for template in templates:
        forms = eee.inflect_slot(lemma, template, pos, language=language)
        if forms:
            result[template.label] = forms
    return result
