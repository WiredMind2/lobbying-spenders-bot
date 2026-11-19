# lobbying-spenders-bot

Replicates the QuiverQuant "Top Lobbying Spenders" strategy: equal-weight top-10
US publicly-traded companies by quarterly lobbying spend (LDA LD-2 filings),
rebalanced monthly. Python + FastAPI web dashboard.

## Work register

- Stories live in `docs/work/items/US-XXX.md`. Edit them directly; update
  `Status` as work moves.
- Before minting a new ID, scan `docs/work/items/` and `docs/work/archive/`;
  IDs are stable (`US-012`) and never reused.
- `docs/work/README.md` is the index (items, epics, icebox, archive).
- A story is Done only per `docs/work/definition-of-done.md`.
- Never delete `docs/agile/` or `docs/work/archive/`.

## Conventions

- Data lives in `data/` (gitignored): `raw/*.jsonl` filing caches,
  `company_tickers.json`, `state.json` (latest signal + portfolio).
- Pure logic (signal, portfolio) is stdlib-only and unit-tested; network code is
  thin wrappers with local caching.
- LDA API: `https://lda.gov/api/v1/filings/` — quarterly LD-2s are
  `filing_type=Q1..Q4`; firms report `income`, in-house filings report
  `expenses`; client spend = sum of both.
- EDGAR requires a `User-Agent` header; anonymous requests get rate-limited.
