"""Portfolio: equal-weight targets and monthly rebalance helpers."""

from __future__ import annotations

import calendar
import datetime as dt
from dataclasses import dataclass


def equal_weights(n: int) -> list[float]:
    """n equal weights that sum exactly to 1.0 (remainder spread onto the front).

    Uses integer basis points to avoid float drift; error is at most 1e-4 on
    the earliest entries.
    """
    if n <= 0:
        return []
    if n > 10_000:
        raise ValueError("n above 10000 would break basis-point weights")
    bps_total = 10_000
    base = bps_total // n
    weights_bps = [base] * n
    for i in range(bps_total - base * n):
        weights_bps[i] += 1
    return [w / 10_000 for w in weights_bps]


@dataclass(frozen=True)
class Target:
    ticker: str
    client: str
    weight: float


def build_targets(ranked_mapped: list[tuple[str, str]], size: int) -> list[Target]:
    """(ticker, client) pairs ranked by spend -> equal-weight target list."""
    selected = ranked_mapped[:size]
    weights = equal_weights(len(selected))
    return [
        Target(ticker=ticker, client=client, weight=weight)
        for (ticker, client), weight in zip(selected, weights)
    ]


def next_rebalance_date(today: dt.date | None = None) -> dt.date:
    """First business day of the next month after `today` (default: today)."""
    day = today or dt.date.today()
    year, month = (day.year + 1, 1) if day.month == 12 else (day.year, day.month + 1)
    d = dt.date(year, month, 1)
    while d.weekday() >= 5:  # Sat/Sun -> slide to Monday
        d += dt.timedelta(days=1)
    return d


def diff_holdings(current: dict[str, float], targets: list[Target]) -> list[dict]:
    """Weight diff between current holdings {ticker: weight} and targets."""
    target_weights = {t.ticker: t.weight for t in targets}
    tickers = set(current) | set(target_weights)
    diffs = []
    for ticker in sorted(tickers):
        cur = current.get(ticker, 0.0)
        tgt = target_weights.get(ticker, 0.0)
        delta = round(tgt - cur, 6)
        if abs(delta) < 1e-9:
            continue
        diffs.append({
            "ticker": ticker,
            "current": cur,
            "target": tgt,
            "delta": delta,
            "action": "BUY" if delta > 0 else "SELL",
        })
    return diffs
