"""Central configuration: paths and API endpoints."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

# Lobbying Disclosure Act API (lda.gov; the legacy lda.senate.gov is deprecated).
# Quarterly LD-2 activity reports are filing_type=Q1..Q4. Firms report `income`
# (what the client paid them); in-house lobbying filings report `expenses`.
LDA_BASE_URL = "https://lda.gov/api/v1/filings/"
# The API hard-caps results at 25/page regardless of the requested page_size.
LDA_PAGE_SIZE = 25
# Be polite: LDA/SEC both want a identifying User-Agent.
USER_AGENT = "lobbying-spenders-bot/0.1 (github.com/WiredMind2/lobbying-spenders-bot)"

# SEC EDGAR ticker <-> company-name mapping.
EDGAR_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
EDGAR_CACHE = DATA_DIR / "company_tickers.json"

# Manual client-name -> ticker overrides (wins over fuzzy matching).
OVERRIDES_CSV = PROJECT_ROOT / "mappings_overrides.csv"

# Latest computed signal + portfolio, consumed by the web UI.
STATE_FILE = DATA_DIR / "state.json"

PORTFOLIO_SIZE = 10


def raw_cache_path(year: int, quarter: int) -> Path:
    return RAW_DIR / f"{year}Q{quarter}.jsonl"
