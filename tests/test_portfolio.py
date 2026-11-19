"""Tests for portfolio construction (pure logic, no network)."""

import datetime as dt

from lobbying_bot.portfolio import (
    build_targets,
    diff_holdings,
    equal_weights,
    next_rebalance_date,
)


def test_equal_weights_sum_to_one():
    for n in (1, 3, 10, 30):
        weights = equal_weights(n)
        assert len(weights) == n
        assert abs(sum(weights) - 1.0) < 1e-9


def test_build_targets_capped_at_size_and_equal_weight():
    ranked = [(f"T{i}", f"CLIENT {i}") for i in range(25)]
    targets = build_targets(ranked, size=10)
    assert len(targets) == 10
    assert {t.ticker for t in targets} == {f"T{i}" for i in range(10)}
    assert abs(sum(t.weight for t in targets) - 1.0) < 1e-9


def test_build_targets_fewer_than_size_sums_to_one():
    ranked = [("AAA", "A CORP"), ("BBB", "B CORP")]
    targets = build_targets(ranked, size=10)
    assert len(targets) == 2
    assert abs(sum(t.weight for t in targets) - 1.0) < 1e-9


def test_next_rebalance_is_first_business_day_of_next_month():
    assert next_rebalance_date(dt.date(2026, 11, 19)) == dt.date(2026, 12, 1)
    # Nov 30 2026 is a Monday; Dec 1 is Tuesday -> straight to Dec 1
    assert next_rebalance_date(dt.date(2026, 11, 30)) == dt.date(2026, 12, 1)
    # 2026-01-31 is a Saturday; next month starts Sat Jan 1? No: Feb 1 2026 is a Sunday
    assert next_rebalance_date(dt.date(2026, 1, 15)) == dt.date(2026, 2, 2)


def test_diff_holdings_buys_sells_and_exits():
    current = {"AAA": 0.2, "ZZZ": 0.1}
    targets = build_targets(
        [("AAA", "A"), ("BBB", "B"), ("CCC", "C")], size=3
    )
    diffs = diff_holdings(current, targets)
    by_ticker = {d["ticker"]: d for d in diffs}
    assert by_ticker["AAA"]["action"] == "BUY"      # 1/3 - 0.2
    assert by_ticker["ZZZ"]["action"] == "SELL"     # exit entirely
    assert by_ticker["BBB"]["current"] == 0.0
