"""CLI: ingest LDA filings for a quarter, map clients, write data/state.json.

Usage:
    python run_ingest.py --year 2026 --quarter 3 [--refresh]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys

from lobbying_bot.config import PORTFOLIO_SIZE, STATE_FILE
from lobbying_bot.edgar import ClientMapper, TickerMap, fetch_edgar_tickers
from lobbying_bot.lda import download_quarter, load_quarter
from lobbying_bot.mappings import load_overrides
from lobbying_bot.portfolio import build_targets, next_rebalance_date
from lobbying_bot.signal import aggregate_spend, rank_clients, spend_ties_at_cutoff


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--quarter", type=int, choices=[1, 2, 3, 4], required=True)
    parser.add_argument(
        "--refresh", action="store_true",
        help="re-download caches even if they exist",
    )
    args = parser.parse_args()

    print(f"[1/4] Downloading LDA filings for {args.year}Q{args.quarter}...")
    path = download_quarter(args.year, args.quarter, refresh=args.refresh)
    filings = load_quarter(args.year, args.quarter)
    print(f"      {len(filings)} filings cached at {path}")

    print("[2/4] Building ticker map (EDGAR + overrides)...")
    edgar_ok = True
    try:
        edgar = fetch_edgar_tickers(refresh=args.refresh)
        ticker_map = TickerMap.from_edgar(edgar)
        print(f"      EDGAR map: {len(ticker_map.by_name)} companies")
    except Exception as exc:  # noqa: BLE001 - degrade to overrides-only
        edgar_ok = False
        ticker_map = TickerMap(by_name={})
        print(f"      WARNING: EDGAR unavailable ({exc}); using overrides only")
    overrides = load_overrides()
    print(f"      Manual overrides: {len(overrides)}")
    mapper = ClientMapper(ticker_map, overrides)

    print("[3/4] Aggregating spend by client...")
    ranked = rank_clients(aggregate_spend(filings))

    top_spenders = []
    for rank, entry in enumerate(ranked[:30], start=1):
        ticker, method = mapper.match(entry.client)
        top_spenders.append({
            "rank": rank,
            "client": entry.client,
            "spend": round(entry.spend, 2),
            "filings": entry.filings,
            "ticker": ticker,
            "match_method": method,
        })

    mapped_ranked = [
        (t["ticker"], t["client"])
        for t in top_spenders
        if t["ticker"] and t["rank"] <= 25  # only search public names near the top
    ]
    mapped_ranked = mapped_ranked[:PORTFOLIO_SIZE]

    ties = spend_ties_at_cutoff(ranked, cutoff=len(mapped_ranked))

    print("[4/4] Building portfolio targets...")
    targets = build_targets(mapped_ranked, PORTFOLIO_SIZE)

    state = {
        "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "year": args.year,
        "quarter": args.quarter,
        "filing_count": len(filings),
        "edgar_available": edgar_ok,
        "top_spenders": top_spenders,
        "portfolio": [
            {"ticker": t.ticker, "client": t.client, "weight": t.weight}
            for t in targets
        ],
        "unmapped_top": [t["client"] for t in top_spenders[:15] if not t["ticker"]],
        "spend_ties_at_cutoff": ties,
        "next_rebalance": next_rebalance_date().isoformat(),
        "notes": [
            "Spend = income paid to lobbying firms + in-house expenses (LDA LD-2).",
            "Amounts are rounded by filers to the nearest $10,000, so exact ties occur.",
            "Demo mapping quality depends on EDGAR fuzzy matching + manual overrides.",
        ],
    }
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

    print(f"\nTop spenders {args.year}Q{args.quarter} (top 10 shown):")
    for t in top_spenders[:10]:
        tick = t["ticker"] or "unmapped"
        print(f"  {t['rank']:>2}. {t['client'][:45]:<45} "
              f"${t['spend']:>12,.0f}  {tick}")
    print(f"\nPortfolio: {len(targets)} holdings, weights sum "
          f"{sum(t.weight for t in targets):.4f}")
    print(f"State written to {STATE_FILE}")
    if not edgar_ok:
        print("NOTE: EDGAR was unavailable; mapping used overrides only.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
