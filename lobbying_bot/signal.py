"""Signal: aggregate quarterly lobbying spend by client and rank.

Lobbying firms report `income` (paid by the client); in-house filings report
`expenses`. A client's total spend for a quarter is the sum of both across all
filings naming them as client.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def filing_spend(filing: dict) -> float:
    income = filing.get("income") or 0
    expenses = filing.get("expenses") or 0
    return float(income) + float(expenses)


@dataclass
class ClientSpend:
    client: str
    spend: float = 0.0
    filings: int = 0
    posted_latest: str | None = None


def aggregate_spend(filings: list[dict]) -> list[ClientSpend]:
    """Sum spend per client across a quarter's filings."""
    by_client: dict[str, ClientSpend] = {}
    for filing in filings:
        name = (filing.get("client") or "").strip().upper()
        if not name:
            continue
        entry = by_client.setdefault(name, ClientSpend(client=name))
        entry.spend += filing_spend(filing)
        entry.filings += 1
        posted = filing.get("dt_posted") or ""
        if posted > (entry.posted_latest or ""):
            entry.posted_latest = posted
    return list(by_client.values())


def rank_clients(spenders: list[ClientSpend]) -> list[ClientSpend]:
    """Rank by spend descending; ties broken alphabetically by client name."""
    return sorted(spenders, key=lambda c: (-c.spend, c.client))


def spend_ties_at_cutoff(ranked: list[ClientSpend], cutoff: int) -> list[str]:
    """Names tied in spend with the entry at `cutoff` (0-based index)."""
    if cutoff >= len(ranked):
        return []
    threshold = ranked[cutoff].spend
    return [c.client for c in ranked if c.spend == threshold]
