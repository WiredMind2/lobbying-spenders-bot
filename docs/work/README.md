# Work register — lobbying-spenders-bot

Bot that replicates the QuiverQuant "Top Lobbying Spenders" strategy: equal-weight
top-10 US companies by quarterly lobbying spend, rebalanced monthly, with a web
dashboard.

## Items

| ID | Title | Points | Status |
|----|-------|--------|--------|
| [US-001](items/US-001.md) | Cache quarterly LDA filings locally | 5 | Done |
| [US-002](items/US-002.md) | Map lobbying clients to stock tickers | 5 | In progress (live EDGAR fetch unverified: SEC 403 blocked this IP all session) |
| [US-003](items/US-003.md) | Compute top-10 equal-weight portfolio targets | 3 | Done |
| [US-004](items/US-004.md) | Web dashboard for signal and portfolio | 5 | Done |

## Epics / icebox

- **Backtest** (icebox): point-in-time monthly equal-weight backtest vs SPY,
  2009→present, using bulk LDA XML archives. Not yet sized — split into stories
  when picked up.
- **Live execution** (icebox): Alpaca paper-trading connector that diffs target
  vs current positions and places orders on the monthly rebalance date.

## Archive

No collisions. `docs/work/archive/` is empty; there is no prior `docs/agile/` pack.
