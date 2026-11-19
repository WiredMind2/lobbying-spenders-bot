# lobbying-spenders-bot

Replication of the [QuiverQuant "Top Lobbying Spenders" strategy](
https://www.quiverquant.com/strategies/s/Top%20Lobbying%20Spenders/): an
equal-weight portfolio of the **10 US publicly-traded companies with the highest
quarterly lobbying spend**, rebalanced monthly.

Hypothetical research tool — **not investment advice**.

## How it works

```
LDA API (lda.gov)  ──►  data/raw/<year>Q<q>.jsonl   (quarterly LD-2 filings)
                              │
SEC EDGAR tickers  ──►  client name ──► ticker      (exact → fuzzy → manual)
mappings_overrides.csv ──┘         │
                                   ▼
            rank by spend (income + expenses) ──► top 10 equal-weight targets
                                   │
                                   ▼
                     data/state.json ──► FastAPI dashboard (web/)
```

- **Spend definition**: lobbying firms report `income` (paid by the client);
  in-house filings report `expenses`. Client spend = sum of both across all
  filings naming them. Filers round amounts to the nearest $10,000, so exact
  ties at the cutoff are possible and are surfaced in the UI.
- **Mapping**: exact match on normalized names against EDGAR
  `company_tickers.json`, then tight fuzzy matching (cutoff 0.92), then
  `mappings_overrides.csv` (wins over everything). Associations, unions and
  private companies stay "unmapped" and are excluded.
- **Caveat**: LD-2s are due ~20 days after quarter end, so the signal is
  inherently ~3–6 weeks stale.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (source .venv/bin/activate on POSIX)
pip install -r requirements.txt
```

## Usage

```bash
# 1. Ingest a quarter and compute the portfolio (writes data/state.json)
python run_ingest.py --year 2026 --quarter 3        # add --refresh to re-download

# 2. Serve the dashboard
uvicorn lobbying_bot.app:app --reload --port 8000   # http://127.0.0.1:8000

# 3. Tests
python -m pytest
```

## Data sources

| Source | Endpoint | Notes |
|---|---|---|
| LDA filings | `https://lda.gov/api/v1/filings/?filing_type=Q1..Q4&filing_year=YYYY` | No auth; ~0.2s/page politeness delay |
| SEC EDGAR | `https://www.sec.gov/files/company_tickers.json` | Requires a `User-Agent` header; IP rate-limits anonymous bursts — cached locally after first fetch |

## Repo layout

- `lobbying_bot/` — package (`lda`, `edgar`, `mappings`, `signal`, `portfolio`, `app`)
- `web/` — vanilla HTML/CSS/JS dashboard (mounted at `/static`, served at `/`)
- `tests/` — pytest unit tests for the pure logic
- `docs/work/` — work register (stories, definition of done)
- `data/` — gitignored caches and `state.json`

## Status / roadmap

- [x] US-001 quarterly LDA ingestion with cache
- [~] US-002 client → ticker mapping (logic done + unit-tested; live EDGAR
      fetch unverified — SEC rate-limited (403) the build machine's IP for the
      whole session; seeded `mappings_overrides.csv` covers 2026Q3's public
      top-30)
- [x] US-003 top-10 equal-weight targets
- [x] US-004 web dashboard
- [ ] Icebox: point-in-time backtest (2009→, bulk LDA XML archives, vs SPY)
- [ ] Icebox: Alpaca paper-trading executor on the monthly rebalance date
- [ ] Icebox: subsidiary rollup (one parent company per name group)
