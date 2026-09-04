"""Real, gated end-to-end check that LSJPeriodMap + render_lsj_entry()
actually produce sensible period/dialect tags against the live LSJ dump
-- not just against small hand-written fixtures. Requires the real,
gitignored data/lsj/*.xml dump locally; skips cleanly otherwise. Uses
`real_source_bundle` directly (not a separate wrapper fixture) --
`sources.lsj_period_map` is wired conditionally right there, the same
way `sources.lsj` itself is, precisely so this is the same SourceBundle
pilot_build_report's real pipeline.run() call uses to regenerate this
repo's actual words/*.md content.
"""

import pytest

from okfbuild.concepts.lexical_entry import render_lsj_entry
from okfbuild.sources.lsj_index import LSJCitation

pytestmark = pytest.mark.integration


def _require_real_period_map(sources):
    if sources.lsj_period_map is None:
        pytest.skip("real LSJ TEI-XML dump not found locally (see data/lsj/README.md) -- lsj_period_map is None")


def test_real_period_map_resolves_a_known_homeric_citation(real_source_bundle):
    """νόστος's LSJ entry cites the Odyssey -- a citation whose
    tlg_author/tlg_work resolve via Diorisis's real work-level row for
    Homer's Odyssey (tlgAuthor 0012, tlgId 002) should get a real,
    sensible BC century, not None."""
    _require_real_period_map(real_source_bundle)
    segments = real_source_bundle.lsj.lookup("νόστος")
    assert segments is not None, "expected νόστος to be a real LSJ headword"

    odyssey_citations = [
        c for c in segments if isinstance(c, LSJCitation) and c.tlg_author == "0012" and c.tlg_work == "002"
    ]
    assert odyssey_citations, "expected at least one Odyssey citation for νόστος"

    period = real_source_bundle.lsj_period_map.period_for_citation(odyssey_citations[0])
    assert period is not None
    assert period.era == "BC"


def test_real_rendering_produces_at_least_one_real_tag_for_a_richly_dialectal_word(real_source_bundle):
    """βαίνω has real, confirmed dialect-tagged citations (Dor./Ep., per
    this section's own direct dump investigation) -- rendering its real
    segments end-to-end must produce at least one "**[...]**" tag, not
    silently drop all of them."""
    _require_real_period_map(real_source_bundle)
    segments = real_source_bundle.lsj.lookup("βαίνω")
    assert segments is not None

    rendered = render_lsj_entry(segments, real_source_bundle.lsj_period_map)

    assert "**[" in rendered, "expected at least one rendered period/dialect tag for βαίνω"
