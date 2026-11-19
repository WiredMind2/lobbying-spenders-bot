"""Manual client-name -> ticker overrides (CSV, version-controlled)."""

from __future__ import annotations

import csv

from .config import OVERRIDES_CSV


def load_overrides() -> dict[str, str]:
    """Read mappings_overrides.csv: client_name,ticker[,note] keyed by upper name."""
    if not OVERRIDES_CSV.exists():
        return {}
    overrides: dict[str, str] = {}
    with OVERRIDES_CSV.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            name = (row.get("client_name") or "").strip()
            ticker = (row.get("ticker") or "").strip().upper()
            if name and ticker:
                overrides[name.upper()] = ticker
    return overrides
