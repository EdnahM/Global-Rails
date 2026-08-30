"""
African Rails MCP - Test Dashboard
Flask + vanilla JS UI for testing MCP tools against Avalanche Fuji (or any chain).

Run:
    cd frontend
    ../.venv/bin/python app.py

Opens at http://localhost:5050
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend/src"))

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)


def run(coro):
    return asyncio.run(coro)


# ─────────────────────────────────────────────────────────────────────────────
# API routes — each maps to one MCP tool
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/config", methods=["POST"])
def set_config():
    data = request.json
    if data.get("private_key"):
        os.environ["PRIVATE_KEY"] = data["private_key"]
    if data.get("wallet_address"):
        os.environ["WALLET_ADDRESS"] = data["wallet_address"]

    # Purge every african_rails_mcp module from Python's import cache.
    # Simply reloading config.py isn't enough — other modules like transactions.py
    # hold a direct reference to the OLD settings object from their initial import.
    # Clearing sys.modules forces a fresh import (with new env vars) on the next call.
    for key in list(sys.modules.keys()):
        if "african_rails_mcp" in key:
            del sys.modules[key]

    return jsonify({"ok": True, "wallet": data.get("wallet_address", "")})


@app.route("/api/prices", methods=["POST"])
def prices():
    data = request.json
    from african_rails_mcp.prices.tool import get_token_prices
    result = run(get_token_prices(data["symbols"], data.get("currencies", ["usd"])))
    return jsonify(result)


@app.route("/api/tokens", methods=["GET"])
def tokens():
    from african_rails_mcp.prices.constants import SUPPORTED_SYMBOLS
    return jsonify({"tokens": SUPPORTED_SYMBOLS})


@app.route("/api/chains", methods=["GET"])
def chains():
    from african_rails_mcp.onchain.constants import CHAINS
    result = {}
    for name, cfg in CHAINS.items():
        result[name] = {
            "chain_id": cfg["chain_id"],
            "native_symbol": cfg["native_symbol"],
            "tokens": ["native"] + list(cfg.get("tokens", {}).keys()),
            "explorer": cfg["block_explorer"],
        }
    return jsonify(result)


@app.route("/api/balance", methods=["POST"])
def balance():
    data = request.json
    from african_rails_mcp.onchain.tool import check_balance
    result = run(check_balance(
        address=data.get("address", ""),
        chain=data.get("chain", "avalanche-fuji"),
        token=data.get("token", "native"),
    ))
    return jsonify(result)


@app.route("/api/send", methods=["POST"])
def send():
    data = request.json
    from african_rails_mcp.onchain.tool import send_transaction
    result = run(send_transaction(
        to=data["to"],
        amount=data["amount"],
        chain=data.get("chain", "avalanche-fuji"),
        token=data.get("token", "native"),
    ))
    return jsonify(result)


@app.route("/api/tx", methods=["POST"])
def tx_status():
    data = request.json
    from african_rails_mcp.onchain.tool import get_tx_status
    result = run(get_tx_status(
        tx_hash=data["tx_hash"],
        chain=data.get("chain", "avalanche-fuji"),
    ))
    return jsonify(result)


@app.route("/api/quote", methods=["POST"])
def quote():
    data = request.json
    from african_rails_mcp.swaps.tool import quote_swap
    result = run(quote_swap(
        token_in=data["token_in"],
        token_out=data["token_out"],
        amount_in=data["amount_in"],
        chain=data.get("chain", "avalanche-fuji"),
        prefer_mento=data.get("prefer_mento", True),
    ))
    return jsonify(result)


@app.route("/api/swap", methods=["POST"])
def swap():
    data = request.json
    from african_rails_mcp.swaps.tool import execute_swap
    result = run(execute_swap(
        token_in=data["token_in"],
        token_out=data["token_out"],
        amount_in=data["amount_in"],
        chain=data.get("chain", "avalanche-fuji"),
        slippage_pct=float(data.get("slippage_pct", 0.5)),
        prefer_mento=data.get("prefer_mento", True),
    ))
    return jsonify(result)


# ─────────────────────────────────────────────────────────────────────────────
# Frontend — single-page app served inline
# ─────────────────────────────────────────────────────────────────────────────

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>African Rails MCP</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: #2d3148;
    --accent: #4f8ef7;
    --accent2: #7c5cbf;
    --green: #22c55e;
    --yellow: #f59e0b;
    --red: #ef4444;
    --text: #e2e8f0;
    --muted: #64748b;
    --radius: 10px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; font-size: 14px; }

  .layout { display: grid; grid-template-columns: 260px 1fr; min-height: 100vh; }

  /* Sidebar */
  aside { background: var(--surface); border-right: 1px solid var(--border); padding: 24px 16px; display: flex; flex-direction: column; gap: 20px; }
  .logo { font-size: 18px; font-weight: 700; color: var(--accent); }
  .logo span { color: var(--muted); font-weight: 400; font-size: 12px; display: block; margin-top: 2px; }
  label { font-size: 12px; color: var(--muted); display: block; margin-bottom: 4px; }
  input, select { width: 100%; background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 8px 10px; border-radius: 6px; font-size: 13px; outline: none; }
  input:focus, select:focus { border-color: var(--accent); }
  .divider { border: none; border-top: 1px solid var(--border); }
  .link { color: var(--muted); font-size: 11px; text-decoration: none; }
  .link:hover { color: var(--accent); }

  /* Main */
  main { padding: 28px; overflow-y: auto; }
  h1 { font-size: 20px; margin-bottom: 20px; }

  /* Tabs */
  .tabs { display: flex; gap: 4px; margin-bottom: 24px; border-bottom: 1px solid var(--border); }
  .tab { padding: 8px 18px; cursor: pointer; color: var(--muted); border-radius: 6px 6px 0 0; border: 1px solid transparent; border-bottom: none; font-size: 13px; }
  .tab.active { color: var(--text); border-color: var(--border); background: var(--surface); margin-bottom: -1px; }
  .panel { display: none; }
  .panel.active { display: block; }

  /* Cards */
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 16px; }
  .card h3 { font-size: 13px; color: var(--muted); margin-bottom: 14px; text-transform: uppercase; letter-spacing: .05em; }

  /* Grid */
  .row { display: grid; gap: 12px; margin-bottom: 12px; }
  .row-2 { grid-template-columns: 1fr 1fr; }
  .row-3 { grid-template-columns: 1fr 1fr 1fr; }

  /* Buttons */
  .btn { padding: 9px 18px; border-radius: 6px; border: none; cursor: pointer; font-size: 13px; font-weight: 600; transition: opacity .15s; }
  .btn:hover { opacity: .85; }
  .btn:disabled { opacity: .4; cursor: not-allowed; }
  .btn-primary { background: var(--accent); color: #fff; }
  .btn-secondary { background: var(--surface); border: 1px solid var(--border); color: var(--text); }
  .btn-danger { background: var(--red); color: #fff; }
  .btn-sm { padding: 6px 12px; font-size: 12px; }

  /* Metrics */
  .metrics { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); margin: 12px 0; }
  .metric { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 12px; }
  .metric .label { font-size: 11px; color: var(--muted); margin-bottom: 4px; }
  .metric .value { font-size: 16px; font-weight: 700; color: var(--text); word-break: break-all; }
  .metric .value.green { color: var(--green); }
  .metric .value.yellow { color: var(--yellow); }
  .metric .value.red { color: var(--red); }
  .metric .value.blue { color: var(--accent); }

  /* Status badges */
  .badge { display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 600; }
  .badge-green { background: #14532d; color: var(--green); }
  .badge-yellow { background: #451a03; color: var(--yellow); }
  .badge-red { background: #450a0a; color: var(--red); }
  .badge-blue { background: #1e3a5f; color: var(--accent); }

  /* Table */
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; color: var(--muted); font-weight: 500; padding: 8px 12px; border-bottom: 1px solid var(--border); font-size: 11px; text-transform: uppercase; }
  td { padding: 10px 12px; border-bottom: 1px solid var(--border); }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,.02); }

  /* Misc */
  .result { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 12px; font-family: monospace; font-size: 12px; max-height: 220px; overflow: auto; white-space: pre-wrap; word-break: break-all; margin-top: 12px; }
  .toast { position: fixed; bottom: 24px; right: 24px; padding: 12px 20px; border-radius: 8px; font-size: 13px; z-index: 999; animation: fadein .2s; }
  .toast-ok { background: #14532d; color: var(--green); border: 1px solid var(--green); }
  .toast-err { background: #450a0a; color: var(--red); border: 1px solid var(--red); }
  @keyframes fadein { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
  .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid rgba(255,255,255,.3); border-top-color: #fff; border-radius: 50%; animation: spin .6s linear infinite; vertical-align: middle; margin-right: 6px; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .link-ext { color: var(--accent); font-size: 12px; }
  .multiselect-container { display: flex; flex-wrap: wrap; gap: 6px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 8px; min-height: 42px; }
  .chip { background: var(--border); color: var(--text); padding: 3px 8px; border-radius: 20px; font-size: 12px; cursor: pointer; user-select: none; }
  .chip.selected { background: var(--accent); color: #fff; }
  .wallet-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
  .wallet-dot.ok { background: var(--green); }
  .wallet-dot.nok { background: var(--red); }
</style>
</head>
<body>
<div class="layout">

<!-- ── Sidebar ─────────────────────────────────── -->
<aside>
  <div>
    <div class="logo">🌍 African Rails
      <span>MCP Test Dashboard</span>
    </div>
  </div>

  <hr class="divider">

  <div>
    <label>Private Key</label>
    <input type="password" id="privateKey" placeholder="0x..." oninput="walletChanged()">
  </div>
  <div>
    <label>Wallet Address</label>
    <input type="text" id="walletAddress" placeholder="0x..." oninput="walletChanged()">
    <div style="margin-top:6px;font-size:11px;" id="walletStatus">
      <span class="wallet-dot nok"></span>Not configured
    </div>
  </div>

  <hr class="divider">

  <div>
    <label>Chain</label>
    <select id="chainSelect" onchange="chainChanged()">
      <option value="avalanche-fuji" selected>Avalanche Fuji (testnet)</option>
      <option value="avalanche">Avalanche</option>
      <option value="celo-alfajores">Celo Alfajores (testnet)</option>
      <option value="celo">Celo</option>
      <option value="ethereum">Ethereum</option>
    </select>
  </div>

  <hr class="divider">

  <div style="display:flex;flex-direction:column;gap:6px;">
    <a class="link" href="https://faucet.avax.network" target="_blank">🚰 Fuji faucet (AVAX)</a>
    <a class="link" href="https://faucet.celo.org" target="_blank">🚰 Alfajores faucet (CELO)</a>
    <a class="link" href="https://testnet.snowtrace.io" target="_blank">🔍 Fuji explorer</a>
    <a class="link" href="https://alfajores.celoscan.io" target="_blank">🔍 Alfajores explorer</a>
  </div>
</aside>

<!-- ── Main ────────────────────────────────────── -->
<main>
  <h1>Test Dashboard</h1>

  <div class="tabs">
    <div class="tab active" onclick="switchTab('prices')">💰 Prices</div>
    <div class="tab" onclick="switchTab('balance')">📊 Balance</div>
    <div class="tab" onclick="switchTab('send')">📤 Send</div>
    <div class="tab" onclick="switchTab('swap')">🔄 Swap</div>
    <div class="tab" onclick="switchTab('status')">🔍 Tx Status</div>
  </div>

  <!-- ── Prices ── -->
  <div id="panel-prices" class="panel active">
    <div class="card">
      <h3>Select Tokens</h3>
      <div class="multiselect-container" id="tokenChips"></div>
      <div style="margin-top:12px;display:flex;gap:8px;align-items:center;">
        <select id="currency" style="width:120px;">
          <option value="usd">USD</option>
          <option value="kes">KES</option>
          <option value="eur">EUR</option>
          <option value="gbp">GBP</option>
        </select>
        <button class="btn btn-primary" onclick="fetchPrices()">Fetch prices</button>
      </div>
    </div>
    <div id="pricesResult"></div>
  </div>

  <!-- ── Balance ── -->
  <div id="panel-balance" class="panel">
    <div class="card">
      <h3>Check Balance</h3>
      <div class="row row-2">
        <div>
          <label>Address</label>
          <input type="text" id="balAddress" placeholder="0x... (blank = your wallet)">
        </div>
        <div>
          <label>Token</label>
          <select id="balToken"></select>
        </div>
      </div>
      <button class="btn btn-primary" onclick="checkBalance()">Check balance</button>
    </div>
    <div id="balResult"></div>
  </div>

  <!-- ── Send ── -->
  <div id="panel-send" class="panel">
    <div class="card">
      <h3>Send Transaction</h3>
      <div class="row row-3">
        <div>
          <label>Recipient</label>
          <div style="display:flex;gap:6px;">
            <input type="text" id="sendTo" placeholder="0x...">
            <button class="btn btn-secondary btn-sm" onclick="useSelf()">Self</button>
          </div>
        </div>
        <div>
          <label>Amount</label>
          <input type="text" id="sendAmount" placeholder="0.001">
        </div>
        <div>
          <label>Token</label>
          <select id="sendToken"></select>
        </div>
      </div>
      <div style="display:flex;gap:8px;margin-top:4px;">
        <button class="btn btn-primary" onclick="sendTx()" id="sendBtn">Send transaction</button>
      </div>
    </div>
    <div id="sendResult"></div>
  </div>

  <!-- ── Swap ── -->
  <div id="panel-swap" class="panel">
    <div class="card">
      <h3>Token Swap</h3>
      <div style="display:grid;grid-template-columns:1fr 40px 1fr 1fr;gap:12px;align-items:end;margin-bottom:12px;">
        <div>
          <label>Sell</label>
          <select id="swapIn"></select>
        </div>
        <div style="text-align:center;">
          <button class="btn btn-secondary btn-sm" onclick="flipSwap()" title="Flip tokens" style="width:36px;padding:6px;">⇄</button>
        </div>
        <div>
          <label>Buy</label>
          <select id="swapOut"></select>
        </div>
        <div>
          <label>Amount in</label>
          <input type="text" id="swapAmount" placeholder="1.0">
        </div>
      </div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
        <div style="display:flex;align-items:center;gap:6px;">
          <label style="margin:0;white-space:nowrap;">Slippage %</label>
          <input type="number" id="slippage" value="0.5" min="0.1" max="10" step="0.1" style="width:80px;">
        </div>
        <button class="btn btn-secondary" onclick="getQuote()">Get quote</button>
        <button class="btn btn-primary" onclick="execSwap()" id="swapBtn">Execute swap</button>
      </div>
      <div style="margin-top:10px;font-size:11px;color:var(--muted);">
        ℹ️ Use wrapped tokens for swaps (e.g. WAVAX not native, WETH not ETH). Mento auto-routes Celo stablecoin pairs.
      </div>
    </div>
    <div id="swapResult"></div>
  </div>

  <!-- ── Tx Status ── -->
  <div id="panel-status" class="panel">
    <div class="card">
      <h3>Transaction Status</h3>
      <div class="row">
        <div>
          <label>Transaction hash</label>
          <input type="text" id="txHash" placeholder="0x...">
        </div>
      </div>
      <div style="display:flex;gap:8px;">
        <button class="btn btn-primary" onclick="checkTx()">Check status</button>
        <button class="btn btn-secondary" onclick="pollTx()">Poll until confirmed</button>
      </div>
    </div>
    <div id="statusResult"></div>
  </div>

</main>
</div>

<script>
// ── State ────────────────────────────────────────
let chainData = {};
let allTokens = [];
let selectedPriceTokens = new Set(["AVAX", "ETH", "USDC", "CELO"]);
let walletOk = false;

// ── Init ─────────────────────────────────────────
async function init() {
  const [chainsRes, tokensRes] = await Promise.all([
    fetch("/api/chains").then(r => r.json()),
    fetch("/api/tokens").then(r => r.json()),
  ]);
  chainData = chainsRes;
  allTokens = tokensRes.tokens;
  renderTokenChips();
  updateChainTokens();
}

function renderTokenChips() {
  const c = document.getElementById("tokenChips");
  c.innerHTML = allTokens.map(t =>
    `<div class="chip ${selectedPriceTokens.has(t) ? "selected" : ""}" onclick="toggleToken('${t}')">${t}</div>`
  ).join("");
}

function toggleToken(t) {
  selectedPriceTokens.has(t) ? selectedPriceTokens.delete(t) : selectedPriceTokens.add(t);
  renderTokenChips();
}

function getChain() { return document.getElementById("chainSelect").value; }

function chainChanged() {
  updateChainTokens();
}

function updateChainTokens() {
  const chain = getChain();
  const tokens = chainData[chain]?.tokens || ["native"];
  // Swap dropdowns exclude "native" — swaps need ERC20 contract addresses (use WAVAX, WETH etc.)
  const swapTokens = tokens.filter(t => t !== "native");

  ["balToken", "sendToken"].forEach(id => {
    const sel = document.getElementById(id);
    if (!sel) return;
    const curr = sel.value;
    sel.innerHTML = tokens.map(t => `<option value="${t}">${t}</option>`).join("");
    if (tokens.includes(curr)) sel.value = curr;
  });

  ["swapIn", "swapOut"].forEach((id, i) => {
    const sel = document.getElementById(id);
    if (!sel) return;
    const curr = sel.value;
    sel.innerHTML = swapTokens.map(t => `<option value="${t}">${t}</option>`).join("");
    if (swapTokens.includes(curr)) sel.value = curr;
    // default swapOut to second token if available
    else if (i === 1 && swapTokens.length > 1) sel.value = swapTokens[1];
  });
}

function walletChanged() {
  const pk = document.getElementById("privateKey").value.trim();
  const addr = document.getElementById("walletAddress").value.trim();
  walletOk = pk.startsWith("0x") && pk.length >= 66 && addr.startsWith("0x") && addr.length === 42;
  const el = document.getElementById("walletStatus");
  el.innerHTML = walletOk
    ? `<span class="wallet-dot ok"></span>${addr.slice(0,6)}...${addr.slice(-4)}`
    : `<span class="wallet-dot nok"></span>Not configured`;
  if (walletOk) {
    fetch("/api/config", {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ private_key: pk, wallet_address: addr }),
    });
  }
}

function useSelf() {
  document.getElementById("sendTo").value = document.getElementById("walletAddress").value;
}

function switchTab(name) {
  document.querySelectorAll(".tab").forEach((el, i) => {
    el.classList.toggle("active", el.textContent.toLowerCase().includes(name) || (name==="prices"&&i===0));
  });
  document.querySelectorAll(".panel").forEach(el => el.classList.remove("active"));
  document.getElementById("panel-" + name).classList.add("active");
}

// ── API helpers ──────────────────────────────────
async function api(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body),
  });
  return res.json();
}

function loading(id, msg) {
  document.getElementById(id).innerHTML =
    `<div style="padding:16px;color:var(--muted)"><span class="spinner"></span>${msg}</div>`;
}

function toast(msg, ok=true) {
  const t = document.createElement("div");
  t.className = `toast ${ok ? "toast-ok" : "toast-err"}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

function statusBadge(s) {
  const map = {confirmed:"badge-green",pending:"badge-yellow",failed:"badge-red",submitted:"badge-blue"};
  return `<span class="badge ${map[s]||"badge-yellow"}">${s}</span>`;
}

function explorerLink(url) {
  return url ? `<a href="${url}" target="_blank" class="link-ext">View on explorer →</a>` : "";
}

function metricsHtml(items) {
  return `<div class="metrics">${items.map(([label,value,cls])=>
    `<div class="metric"><div class="label">${label}</div><div class="value ${cls||""}">${value}</div></div>`
  ).join("")}</div>`;
}

function jsonBlock(data) {
  return `<details style="margin-top:8px"><summary style="cursor:pointer;color:var(--muted);font-size:12px;">Raw response</summary>
    <div class="result">${JSON.stringify(data, null, 2)}</div></details>`;
}

// ── Prices ───────────────────────────────────────
async function fetchPrices() {
  const symbols = [...selectedPriceTokens];
  if (!symbols.length) { toast("Select at least one token", false); return; }
  const cur = document.getElementById("currency").value;
  loading("pricesResult", "Fetching prices from CoinGecko...");

  const data = await api("/api/prices", { symbols, currencies: [cur] });
  if (!data.success) {
    document.getElementById("pricesResult").innerHTML =
      `<div class="card" style="color:var(--red)">${data.error}: ${data.detail}</div>`;
    return;
  }

  const rows = Object.entries(data.prices).map(([sym, info]) => {
    const price = info[cur] ?? "—";
    const change = info[`${cur}_24h_change`];
    const changeHtml = change != null
      ? `<span style="color:${change>=0?"var(--green)":"var(--red)"}">${change>=0?"+":""}${change.toFixed(2)}%</span>`
      : "—";
    return `<tr><td><strong>${sym}</strong></td>
      <td>${cur.toUpperCase()} ${typeof price === "number" ? price.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:6}) : price}</td>
      <td>${changeHtml}</td></tr>`;
  }).join("");

  document.getElementById("pricesResult").innerHTML = `
    <div class="card">
      <table>
        <thead><tr><th>Token</th><th>Price (${cur.toUpperCase()})</th><th>24h change</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

// ── Balance ──────────────────────────────────────
async function checkBalance() {
  loading("balResult", "Querying balance...");
  const data = await api("/api/balance", {
    address: document.getElementById("balAddress").value.trim(),
    chain: getChain(),
    token: document.getElementById("balToken").value,
  });
  if (data.error && !data.balance) {
    document.getElementById("balResult").innerHTML =
      `<div class="card" style="color:var(--red)">${data.error}: ${data.detail}</div>`;
    return;
  }
  const bal = parseFloat(data.balance || 0);
  document.getElementById("balResult").innerHTML = `
    <div class="card">
      ${metricsHtml([
        ["Balance", `${bal.toFixed(6)} ${data.token}`, "green"],
        ["Chain", data.chain],
        ["Address", (data.address||"").slice(0,10)+"..."],
      ])}
      ${data.contract_address ? `<div style="font-size:11px;color:var(--muted);margin-top:8px;">Contract: ${data.contract_address}</div>` : ""}
      ${jsonBlock(data)}
    </div>`;
}

// ── Send ─────────────────────────────────────────
async function sendTx() {
  if (!walletOk) { toast("Configure wallet in sidebar first", false); return; }
  const btn = document.getElementById("sendBtn");
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>Broadcasting...';
  loading("sendResult", "Signing and broadcasting...");

  const data = await api("/api/send", {
    to: document.getElementById("sendTo").value.trim(),
    amount: document.getElementById("sendAmount").value.trim(),
    chain: getChain(),
    token: document.getElementById("sendToken").value,
  });

  btn.disabled = false; btn.textContent = "Send transaction";

  if (data.tx_hash) {
    toast("Transaction submitted!");
    // store for status tab
    window._lastTxHash = data.tx_hash;
    window._lastChain = data.chain;
    document.getElementById("sendResult").innerHTML = `
      <div class="card">
        ${metricsHtml([
          ["Status", statusBadge(data.status), ""],
          ["Token", `${data.amount} ${data.token}`],
          ["Tx Hash", data.tx_hash.slice(0,16)+"..."],
        ])}
        ${explorerLink(data.explorer_url)}
        <div style="margin-top:8px;">
          <button class="btn btn-secondary btn-sm" onclick="goToStatus('${data.tx_hash}','${data.chain}')">Check status →</button>
        </div>
        ${jsonBlock(data)}
      </div>`;
  } else {
    toast(data.error || "Error", false);
    document.getElementById("sendResult").innerHTML =
      `<div class="card" style="color:var(--red)">${data.error}: ${data.detail}</div>`;
  }
}

// ── Swap ─────────────────────────────────────────
function flipSwap() {
  const inSel = document.getElementById("swapIn");
  const outSel = document.getElementById("swapOut");
  const tmp = inSel.value;
  inSel.value = outSel.value;
  outSel.value = tmp;
}

async function getQuote() {
  const tokenIn = document.getElementById("swapIn").value;
  const tokenOut = document.getElementById("swapOut").value;
  const amountIn = document.getElementById("swapAmount").value || "1.0";
  if (!amountIn || parseFloat(amountIn) <= 0) { toast("Enter an amount", false); return; }

  loading("swapResult", "Fetching quote from DEX...");
  const data = await api("/api/quote", {
    token_in: tokenIn,
    token_out: tokenOut,
    amount_in: amountIn,
    chain: getChain(),
  });
  if (data.success === false) {
    document.getElementById("swapResult").innerHTML =
      `<div class="card" style="color:var(--red)"><strong>${data.error}</strong>: ${data.detail}</div>`;
    return;
  }
  const dexLabel = data.dex === "mento" ? "Mento Broker" : "Uniswap V3";
  // fee_pct is already in percent (e.g. 0.05 = 0.05%), not a fraction
  const feeTierHtml = data.fee_pct != null ? `${data.fee_pct.toFixed(2)}%` : "—";
  document.getElementById("swapResult").innerHTML = `
    <div class="card">
      <h3>Quote — ${dexLabel}</h3>
      ${metricsHtml([
        ["You send", `${data.amount_in} ${data.token_in}`],
        ["You get ≈", `${parseFloat(data.amount_out).toFixed(6)} ${data.token_out}`, "green"],
        ["Rate", `1 ${data.token_in} = ${(parseFloat(data.amount_out)/parseFloat(data.amount_in)).toFixed(4)} ${data.token_out}`],
        ["DEX", dexLabel],
        ["Fee tier", feeTierHtml],
      ])}
      <div style="margin-top:10px;">
        <button class="btn btn-primary btn-sm" onclick="execSwap()">Execute this swap →</button>
      </div>
      ${jsonBlock(data)}
    </div>`;
}

async function execSwap() {
  if (!walletOk) { toast("Configure wallet in sidebar first", false); return; }
  const btn = document.getElementById("swapBtn");
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>Swapping...';
  loading("swapResult", "Executing swap...");

  const data = await api("/api/swap", {
    token_in: document.getElementById("swapIn").value,
    token_out: document.getElementById("swapOut").value,
    amount_in: document.getElementById("swapAmount").value,
    chain: getChain(),
    slippage_pct: parseFloat(document.getElementById("slippage").value),
  });

  btn.disabled = false; btn.textContent = "Execute swap";

  if (data.tx_hash) {
    toast("Swap submitted!");
    document.getElementById("swapResult").innerHTML = `
      <div class="card">
        ${metricsHtml([
          ["Status", statusBadge(data.status), ""],
          ["Expected out", `${parseFloat(data.expected_amount_out).toFixed(6)} ${data.token_out}`, "green"],
          ["Min out", `${parseFloat(data.min_amount_out).toFixed(6)} ${data.token_out}`],
          ["DEX", data.dex?.toUpperCase() || "—"],
        ])}
        ${explorerLink(data.explorer_url)}
        <div style="margin-top:8px;">
          <button class="btn btn-secondary btn-sm" onclick="goToStatus('${data.tx_hash}','${data.chain}')">Check status →</button>
        </div>
        ${jsonBlock(data)}
      </div>`;
  } else {
    toast(data.error || "Swap failed", false);
    document.getElementById("swapResult").innerHTML =
      `<div class="card" style="color:var(--red)">${data.error}: ${data.detail}</div>`;
  }
}

// ── Tx Status ────────────────────────────────────
function goToStatus(hash, chain) {
  document.getElementById("txHash").value = hash;
  document.getElementById("chainSelect").value = chain;
  switchTab("status");
  checkTx();
}

async function checkTx() {
  const hash = document.getElementById("txHash").value.trim();
  if (!hash) { toast("Enter a tx hash", false); return; }
  loading("statusResult", "Querying RPC...");

  const data = await api("/api/tx", { tx_hash: hash, chain: getChain() });
  renderTxStatus(data, hash);
}

function renderTxStatus(data, hash) {
  const status = data.status || "unknown";
  document.getElementById("statusResult").innerHTML = `
    <div class="card">
      <div style="font-size:20px;margin-bottom:12px;">${statusBadge(status)}</div>
      ${metricsHtml([
        ["Tx Hash", (hash||"").slice(0,16)+"..."],
        ["Chain", data.chain || getChain()],
        ...(data.block_number ? [["Block", data.block_number.toLocaleString()]] : []),
        ...(data.gas_used ? [["Gas used", data.gas_used.toLocaleString()]] : []),
      ])}
      ${explorerLink(data.explorer_url)}
      ${jsonBlock(data)}
    </div>`;
}

async function pollTx() {
  const hash = document.getElementById("txHash").value.trim();
  if (!hash) { toast("Enter a tx hash", false); return; }

  let attempts = 0;
  const max = 10;
  loading("statusResult", "Polling for confirmation (attempt 1/10)...");

  const interval = setInterval(async () => {
    attempts++;
    document.getElementById("statusResult").innerHTML =
      `<div style="padding:16px;color:var(--muted)"><span class="spinner"></span>Attempt ${attempts}/${max}...</div>`;

    const data = await api("/api/tx", { tx_hash: hash, chain: getChain() });

    if (data.status === "confirmed" || data.status === "failed" || attempts >= max) {
      clearInterval(interval);
      renderTxStatus(data, hash);
      toast(
        data.status === "confirmed" ? "Confirmed!" :
        data.status === "failed" ? "Transaction failed" : "Still pending after 30s",
        data.status === "confirmed"
      );
    }
  }, 3000);
}

init();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"\n  African Rails MCP Dashboard → http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
