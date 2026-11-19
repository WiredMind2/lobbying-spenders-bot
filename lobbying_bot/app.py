"""FastAPI web app: dashboard page + JSON API over data/state.json."""

from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import PROJECT_ROOT, STATE_FILE

app = FastAPI(title="lobbying-spenders-bot")
app.mount("/static", StaticFiles(directory=PROJECT_ROOT / "web"), name="static")


def _load_state() -> dict | None:
    if not STATE_FILE.exists():
        return None
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


@app.get("/")
def index() -> FileResponse:
    return FileResponse(PROJECT_ROOT / "web" / "index.html")


@app.get("/api/signal")
def signal() -> dict:
    state = _load_state()
    if state is None:
        return {"ok": False, "reason": "no data - run `python run_ingest.py` first"}
    return {"ok": True, **state}
