from okfbuild.periods import PERIOD_ORDER


def test_period_order_includes_koine_between_attic_and_byzantine():
    assert PERIOD_ORDER.index("attic") < PERIOD_ORDER.index("koine") < PERIOD_ORDER.index("byzantine")


def test_period_order_still_has_the_four_periods_lexical_entry_building_uses():
    # lexical_entry.py's own period dispatch (okfbuild/concepts/lexical_entry.py)
    # only recognizes these four — this list must always be a superset of them,
    # never define lexical-entry's own default period sweep. This test exists
    # to catch a future edit that accidentally re-creates the Task 1 regression
    # (see the plan's Task 1 for what happened the first time).
    for period in ("homeric", "attic", "byzantine", "modern"):
        assert period in PERIOD_ORDER
