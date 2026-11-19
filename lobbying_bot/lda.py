"""LDA API client with a local JSONL cache per year/quarter."""

from __future__ import annotations

import json
import time
from typing import Iterator

import requests

from .config import LDA_BASE_URL, LDA_PAGE_SIZE, USER_AGENT, raw_cache_path


def _trim(filing: dict) -> dict:
    """Keep only the fields the signal needs, flattened."""
    client = filing.get("client") or {}
    registrant = filing.get("registrant") or {}
    return {
        "filing_uuid": filing.get("filing_uuid"),
        "client": client.get("name"),
        "registrant": registrant.get("name"),
        "income": filing.get("income"),
        "expenses": filing.get("expenses"),
        "dt_posted": filing.get("dt_posted"),
        "filing_year": filing.get("filing_year"),
        "filing_period": filing.get("filing_period"),
    }


def _fetch_page(session: requests.Session, url: str, params: dict) -> dict:
    """GET one API page, retrying on 429/5xx with backoff."""
    backoff = 5.0
    for attempt in range(8):
        resp = session.get(url, params=params, timeout=30)
        if resp.status_code in (429, 502, 503, 504):
            retry_after = resp.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else backoff
            print(f"      {resp.status_code}; backing off {delay:.0f}s "
                  f"(attempt {attempt + 1}/8)")
            time.sleep(delay)
            backoff = min(backoff * 2, 120)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"LDA kept rate-limiting {url} after 8 attempts")


def iter_filings(year: int, quarter: int) -> Iterator[dict]:
    """Yield trimmed LD-2 filings for a quarter, paging through the API."""
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    params = {
        "filing_type": f"Q{quarter}",
        "filing_year": year,
        "page_size": LDA_PAGE_SIZE,
    }
    url: str | None = LDA_BASE_URL
    page = 0
    while url:
        payload = _fetch_page(session, url, params)
        for filing in payload.get("results", []):
            yield _trim(filing)
        page += 1
        if page % 25 == 0:
            print(f"      ...page {page}")
        url = payload.get("next")
        params = {}  # `next` already carries the full query string
        time.sleep(1.0)  # LDA 429s aggressively; stay at ~1 req/s


def download_quarter(year: int, quarter: int, refresh: bool = False) -> Path:
    """Download all filings for a quarter to the JSONL cache and return its path.

    Skips the download when the cache exists unless refresh=True. Writes to a
    .part file and renames on success so failures never leave a truncated cache.
    """
    path = raw_cache_path(year, quarter)
    if path.exists() and not refresh:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".jsonl.part")
    count = 0
    with tmp.open("w", encoding="utf-8") as fh:
        for filing in iter_filings(year, quarter):
            fh.write(json.dumps(filing) + "\n")
            count += 1
    if count == 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"LDA returned zero filings for {year}Q{quarter}")
    tmp.replace(path)
    return path


def load_quarter(year: int, quarter: int) -> list[dict]:
    path = raw_cache_path(year, quarter)
    filings = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                filings.append(json.loads(line))
    return filings
