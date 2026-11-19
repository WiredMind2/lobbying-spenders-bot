"use strict";

const fetchJson = async (url, timeoutMs = 10_000) => {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status} for ${url}`);
    }
    return await response.json();
  } catch (err) {
    if (err instanceof DOMException && err.name === "TimeoutError") {
      throw new Error(`Request to ${url} timed out after ${timeoutMs}ms`, { cause: err });
    }
    throw err;
  }
};

const usd = (amount) =>
  new Intl.NumberFormat("en-US", {
    style: "currency", currency: "USD", maximumFractionDigits: 0,
  }).format(amount);

const renderSpenders = (spenders, portfolioTickers) => {
  const rows = spenders.toSorted((a, b) => a.rank - b.rank).map((entry) => {
    const tr = document.createElement("tr");
    if (portfolioTickers.has(entry.ticker)) tr.classList.add("in-portfolio");

    const rank = document.createElement("th");
    rank.scope = "row";
    rank.textContent = entry.rank;

    const client = document.createElement("td");
    client.textContent = entry.client;

    const spend = document.createElement("td");
    spend.textContent = usd(entry.spend);

    const filings = document.createElement("td");
    filings.textContent = entry.filings;

    const ticker = document.createElement("td");
    if (entry.ticker) {
      ticker.classList.add("tick");
      ticker.textContent = `${entry.ticker} (${entry.match_method})`;
    } else {
      ticker.classList.add("unmapped");
      ticker.textContent = "unmapped";
    }

    tr.append(rank, client, spend, filings, ticker);
    return tr;
  });
  document.querySelector("#spenders-table tbody").replaceChildren(...rows);
};

const renderPortfolio = (portfolio) => {
  const items = portfolio.map((holding) => {
    const li = document.createElement("li");
    const tick = document.createElement("span");
    tick.className = "tick";
    tick.textContent = holding.ticker;
    const weight = document.createElement("span");
    weight.className = "weight";
    weight.textContent = ` ${(holding.weight * 100).toFixed(1)}%`;
    const name = document.createElement("span");
    name.className = "name";
    name.textContent = holding.client;
    li.append(tick, weight, document.createElement("br"), name);
    return li;
  });
  document.querySelector("#portfolio-list").replaceChildren(...items);
};

const renderMeta = (state) => {
  const meta = document.querySelector("#meta");
  const ok = state.ok ?? false;
  if (!ok) {
    meta.textContent = `No data — ${state.reason ?? "run ingest first"}.`;
    meta.classList.add("unmapped");
    return;
  }
  meta.classList.remove("unmapped");
  const generated = state.generated_at.slice(0, 19).replace("T", " ");
  meta.textContent =
    `${state.year}Q${state.quarter} · ${state.filing_count.toLocaleString("en-US")} filings ` +
    `· generated ${generated} UTC`;
  const rebalance = document.querySelector("#rebalance-info");
  if (rebalance) {
    rebalance.textContent =
      `Next monthly rebalance: ${state.next_rebalance}. ` +
      `${state.portfolio.length} holdings, weights sum ` +
      `${(state.portfolio.reduce((sum, h) => sum + h.weight, 0) * 100).toFixed(1)}%.`;
  }
};

const renderNotes = (state) => {
  const notes = [...(state.notes ?? [])];
  if (state.spend_ties_at_cutoff?.length > 1) {
    notes.push(`Spend tie at the portfolio cutoff among: ${state.spend_ties_at_cutoff.join(", ")}.`);
  }
  const items = notes.map((text) => {
    const li = document.createElement("li");
    li.textContent = text;
    return li;
  });
  document.querySelector("#notes-list").replaceChildren(...items);
};

const main = async () => {
  try {
    const state = await fetchJson("/api/signal");
    renderMeta(state);
    if (state.ok) {
      const tickers = new Set(state.portfolio.map((h) => h.ticker));
      renderSpenders(state.top_spenders, tickers);
      renderPortfolio(state.portfolio);
      renderNotes(state);
    }
  } catch (err) {
    const meta = document.querySelector("#meta");
    meta.textContent = `Failed to load signal: ${err.message}`;
    meta.classList.add("unmapped");
  }
};

main();
