"""Manual client-name -> ticker overrides (CSV, version-controlled)."""

from __future__ import annotations

import csv
import re
import sys

from .config import OVERRIDES_CSV

_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")
# Fragments that pass the ticker regex but are almost always unquoted-comma
# parse damage (e.g. "T-MOBILE USA, INC.,TMUS" parsed as ticker "INC.").
_SUFFIX_FRAGMENTS = {"INC", "INC.", "CORP", "CORP.", "LLC", "LTD", "CO",
                     "CO.", "PLC", "LP", "SA", "AG", "NV", "SE", "THE", "AND"}


def load_overrides() -> dict[str, str]:
    """Read mappings_overrides.csv: client_name,ticker[,note] keyed by upper name.

    Client names containing commas must be quoted in the CSV; rows whose
    ticker doesn't look like a ticker are rejected with a warning (they are
    almost always unquoted-comma parse damage).
    """
    if not OVERRIDES_CSV.exists():
        return {}
    overrides: dict[str, str] = {}
    with OVERRIDES_CSV.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            name = (row.get("client_name") or "").strip()
            ticker = (row.get("ticker") or "").strip().upper()
            if not (name and ticker):
                continue
            if ticker in _SUFFIX_FRAGMENTS or not _TICKER_RE.fullmatch(ticker):
                print(
                    f"WARNING: skipping override row with invalid ticker "
                    f"{ticker!r} for {name[:40]!r} - quote the client_name "
                    f"if it contains a comma",
                    file=sys.stderr,
                )
                continue
            overrides[name.upper()] = ticker
    return overrides
