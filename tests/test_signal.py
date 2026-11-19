"""Tests for signal aggregation and ranking (pure logic, no network)."""

from lobbying_bot.signal import (
    aggregate_spend,
    filing_spend,
    rank_clients,
    spend_ties_at_cutoff,
)


def _filing(client, income=None, expenses=None):
    return {"client": client, "income": income, "expenses": expenses}


def test_filing_spend_sums_income_and_expenses():
    assert filing_spend(_filing("X", income=20_000, expenses=10_000)) == 30_000


def test_aggregate_combines_firm_and_in_house_filings():
    """A client paying a firm (income) AND lobbying in-house (expenses) sums both."""
    filings = [
        _filing("AMAZON.COM SERVICES LLC", income=1_000_000),   # via firm
        _filing("AMAZON.COM SERVICES LLC", expenses=4_000_000),  # in-house
        _filing("OTHER CORP", income=500_000),
    ]
    ranked = rank_clients(aggregate_spend(filings))
    assert ranked[0].client == "AMAZON.COM SERVICES LLC"
    assert ranked[0].spend == 5_000_000
    assert ranked[0].filings == 2
    assert ranked[1].client == "OTHER CORP"


def test_rank_breaks_ties_alphabetically():
    filings = [
        _filing("BETA CORP", income=100),
        _filing("ALPHA INC", income=100),
        _filing("GAMMA LLC", income=300),
    ]
    ranked = rank_clients(aggregate_spend(filings))
    assert [c.client for c in ranked] == ["GAMMA LLC", "ALPHA INC", "BETA CORP"]


def test_aggregate_ignores_blank_clients():
    assert aggregate_spend([_filing(None, income=5)]) == []


def test_ties_at_cutoff_detects_tied_spends():
    filings = [
        _filing("A", income=100), _filing("B", income=100),
        _filing("C", income=100), _filing("D", income=50),
    ]
    ranked = rank_clients(aggregate_spend(filings))
    assert spend_ties_at_cutoff(ranked, cutoff=2) == ["A", "B", "C"]
