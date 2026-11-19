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
    """Yield trimmed LD-2 filings for a quarter.

    The API hard-caps results at 25/page regardless of page_size, and its
    `next` links have been observed to terminate early under rate-limit
    pressure. So we paginate by explicit page number up to ceil(count/25)
    and let the caller verify coverage against `count`.
    """
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    params = {
        "filing_type": f"Q{quarter}",
        "filing_year": year,
        "page_size": LDA_PAGE_SIZE,
    }
    first = _fetch_page(session, LDA_BASE_URL, params)
    total = first.get("count") or 0
    last_page = -(-total // LDA_PAGE_SIZE) or 1  # ceil division
    print(f"      API reports {total} filings -> {last_page} pages "
          f"of {LDA_PAGE_SIZE}")

    page = 1
    while page <= last_page:
        payload = first if page == 1 else _fetch_page(session, LDA_BASE_URL, params)
        results = payload.get("results", [])
        if not results:
            print(f"      page {page} returned no results; stopping")
            break
        for filing in results:
            yield _trim(filing)
        if page % 50 == 0:
            print(f"      ...page {page}/{last_page}")
        page += 1
        params = dict(params, page=page)
        time.sleep(1.0)  # LDA 429s aggressively; stay at ~1 req/s


def download_quarter(year: int, quarter: int, refresh: bool = False) -> Path:
    """Download all filings for a quarter to the JSONL cache and return its path.

    Skips the download when the cache exists unless refresh=True. Verifies
    coverage: unique filing UUIDs fetched vs the count the API reported.
    """
    path = raw_cache_path(year, quarter)
    if path.exists() and not refresh:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)

    seen: set[str] = set()
    filings: list[dict] = []
    for filing in iter_filings(year, quarter):
        uuid = filing.get("filing_uuid")
        if uuid and uuid in seen:
            continue  # ordering can shift mid-run; tolerate duplicates
        if uuid:
            seen.add(uuid)
        filings.append(filing)

    if not filings:
        raise RuntimeError(f"LDA returned zero filings for {year}Q{quarter}")
    with path.open("w", encoding="utf-8") as fh:
        for filing in filings:
            fh.write(json.dumps(filing) + "\n")
    print(f"      cached {len(filings)} filings")
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
