"""EDGAR company-ticker cache and fuzzy client-name -> ticker matching."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import requests
from difflib import get_close_matches

from .config import EDGAR_CACHE, EDGAR_TICKERS_URL, USER_AGENT

# Suffixes/articles stripped before comparison. Order matters (longest first).
_LEGAL_SUFFIXES = [
    "INCORPORATED", "CORPORATION", "COMPANIES", "COMPANY", "HOLDINGS",
    "GROUP", "PARTNERS", "TRUST", "INC", "CORP", "LLC", "L L C", "LTD",
    "PLC", "LP", "LLP", "CO", "NV", "SA", "AG", "SE", "USA", "INTERNATIONAL",
]
_SUFFIX_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in _LEGAL_SUFFIXES) + r")\b\.?",
    re.IGNORECASE,
)


def normalize_name(name: str) -> str:
    """Uppercase, strip punctuation/legal suffixes, collapse whitespace."""
    s = (name or "").upper()
    s = re.sub(r"[^\w\s]", " ", s)  # punctuation -> space (keeps A-B, B&O readable-ish)
    s = _SUFFIX_RE.sub(" ", s)
    return " ".join(s.split())


@dataclass(frozen=True)
class TickerMap:
    """Normalized EDGAR company names keyed for matching."""
    by_name: dict[str, str]  # normalized name -> ticker

    @classmethod
    def from_edgar(cls, payload: dict) -> "TickerMap":
        by_name: dict[str, str] = {}
        for entry in payload.values():
            title = entry.get("title")
            ticker = entry.get("ticker")
            if title and ticker:
                by_name.setdefault(normalize_name(title), ticker)
        return cls(by_name=by_name)


def fetch_edgar_tickers(refresh: bool = False) -> dict:
    """Download (or reuse cached) EDGAR company_tickers.json as a raw dict."""
    if EDGAR_CACHE.exists() and not refresh:
        return json.loads(EDGAR_CACHE.read_text(encoding="utf-8"))
    resp = requests.get(
        EDGAR_TICKERS_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    EDGAR_CACHE.parent.mkdir(parents=True, exist_ok=True)
    EDGAR_CACHE.write_text(json.dumps(payload), encoding="utf-8")
    return payload


class ClientMapper:
    """Resolve lobbying client names to tickers.

    Priority: manual override > exact normalized match > fuzzy match.
    """

    def __init__(self, ticker_map: TickerMap, overrides: dict[str, str]):
        self._ticker_map = ticker_map
        self._overrides = overrides

    def match(self, client_name: str) -> tuple[str | None, str]:
        """Return (ticker, method) where method is override|exact|fuzzy|none."""
        override = self._overrides.get(client_name.upper().strip())
        if override:
            return override, "override"

        norm = normalize_name(client_name)
        if not norm:
            return None, "none"
        exact = self._ticker_map.by_name.get(norm)
        if exact:
            return exact, "exact"

        # Fuzzy: only accept tight matches to avoid wrong-company trades.
        close = get_close_matches(norm, self._ticker_map.by_name.keys(), n=1, cutoff=0.92)
        if close:
            return self._ticker_map.by_name[close[0]], "fuzzy"
        return None, "none"
