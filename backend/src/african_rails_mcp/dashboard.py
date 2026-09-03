"""Shared dashboard HTML for the African Rails MCP agent UI.

Extracted from what was originally inline in frontend/app.py so both the
local Flask dev server (frontend/app.py) and the deployed MCP server
(backend/src/african_rails_mcp/server.py) can serve the exact same page
without duplicating 800+ lines of HTML, and without the deployed server
needing Flask as a dependency just to reuse a string constant.
"""
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>African Rails MCP — Agent Dashboard</title>
<style>
:root {
  --bg: #0b0d14; --surface: #13161f; --surface-2: #1a1e2a; --border: #252a3a;
  --border-hover: #353b50; --accent: #4f8ef7; --accent-glow: rgba(79,142,247,0.15);
  --accent2: #a78bfa; --green: #34d399; --green-dim: rgba(52,211,153,0.12);
  --yellow: #fbbf24; --yellow-dim: rgba(251,191,36,0.12); --red: #f87171;
  --red-dim: rgba(248,113,113,0.12); --text: #e2e8f0; --text-secondary: #94a3b8;
  --muted: #64748b; --radius: 12px; --radius-sm: 8px;
  --shadow: 0 4px 24px rgba(0,0,0,0.4);
  --transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: 'Inter','Segoe UI',system-ui,sans-serif; font-size: 14px; line-height: 1.5; -webkit-font-smoothing: antialiased; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-hover); }
.layout { display: grid; grid-template-columns: 280px 1fr; min-height: 100vh; }
aside { background: var(--surface); border-right: 1px solid var(--border); padding: 24px 18px; display: flex; flex-direction: column; gap: 20px; position: sticky; top: 0; height: 100vh; overflow-y: auto; }
.logo { font-size: 20px; font-weight: 800; background: linear-gradient(135deg, var(--accent), var(--accent2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: flex; align-items: center; gap: 10px; }
.logo-icon { width: 36px; height: 36px; background: linear-gradient(135deg, var(--accent), var(--accent2)); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; -webkit-text-fill-color: initial; color: #fff; }
.logo span { color: var(--muted); font-weight: 500; font-size: 11px; display: block; margin-top: 2px; letter-spacing: 0.05em; text-transform: uppercase; }
label { font-size: 11px; color: var(--muted); display: block; margin-bottom: 6px; font-weight: 600; letter-spacing: 0.03em; text-transform: uppercase; }
input, select, textarea { width: 100%; background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 10px 12px; border-radius: var(--radius-sm); font-size: 13px; outline: none; transition: var(--transition); font-family: inherit; }
input:focus, select:focus, textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
input::placeholder, textarea::placeholder { color: var(--muted); opacity: 0.6; }
.divider { border: none; border-top: 1px solid var(--border); }
.link { color: var(--muted); font-size: 12px; text-decoration: none; display: flex; align-items: center; gap: 6px; padding: 6px 8px; border-radius: 6px; transition: var(--transition); }
.link:hover { color: var(--accent); background: var(--accent-glow); }
main { padding: 28px 32px; overflow-y: auto; max-height: 100vh; }
h1 { font-size: 22px; margin-bottom: 4px; font-weight: 700; }
.subtitle { color: var(--muted); font-size: 13px; margin-bottom: 24px; }
.tabs { display: flex; gap: 4px; margin-bottom: 24px; border-bottom: 1px solid var(--border); flex-wrap: wrap; }
.tab { padding: 10px 18px; cursor: pointer; color: var(--muted); border-radius: 8px 8px 0 0; border: 1px solid transparent; border-bottom: none; font-size: 13px; font-weight: 500; transition: var(--transition); display: flex; align-items: center; gap: 6px; white-space: nowrap; }
.tab:hover { color: var(--text-secondary); background: rgba(255,255,255,0.03); }
.tab.active { color: var(--text); border-color: var(--border); background: var(--surface); margin-bottom: -1px; }
.panel { display: none; animation: fadeIn 0.25s ease; }
.panel.active { display: block; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; margin-bottom: 16px; transition: var(--transition); }
.card:hover { border-color: var(--border-hover); }
.card h3 { font-size: 12px; color: var(--muted); margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; display: flex; align-items: center; gap: 8px; }
.row { display: grid; gap: 14px; margin-bottom: 14px; }
.row-2 { grid-template-columns: 1fr 1fr; }
.row-3 { grid-template-columns: 1fr 1fr 1fr; }
.row-4 { grid-template-columns: 1fr 1fr 1fr 1fr; }
.btn { padding: 10px 20px; border-radius: var(--radius-sm); border: none; cursor: pointer; font-size: 13px; font-weight: 600; transition: var(--transition); display: inline-flex; align-items: center; justify-content: center; gap: 6px; white-space: nowrap; }
.btn:hover { transform: translateY(-1px); }
.btn:active { transform: translateY(0); }
.btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }
.btn-primary { background: linear-gradient(135deg, var(--accent), #3b7de4); color: #fff; box-shadow: 0 2px 8px rgba(79,142,247,0.25); }
.btn-primary:hover { box-shadow: 0 4px 16px rgba(79,142,247,0.35); }
.btn-secondary { background: var(--surface-2); border: 1px solid var(--border); color: var(--text); }
.btn-secondary:hover { background: var(--border); }
.btn-danger { background: linear-gradient(135deg, var(--red), #dc2626); color: #fff; box-shadow: 0 2px 8px rgba(248,113,113,0.25); }
.btn-ghost { background: transparent; border: 1px solid var(--border); color: var(--text-secondary); padding: 8px 14px; }
.btn-ghost:hover { background: var(--surface-2); color: var(--text); }
.btn-sm { padding: 7px 14px; font-size: 12px; }
.btn-xs { padding: 4px 10px; font-size: 11px; }
.metrics { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); margin: 12px 0; }
.metric { background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 16px; transition: var(--transition); }
.metric:hover { border-color: var(--border-hover); }
.metric .label { font-size: 11px; color: var(--muted); margin-bottom: 6px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; }
.metric .value { font-size: 18px; font-weight: 700; color: var(--text); word-break: break-all; }
.metric .value.green { color: var(--green); }
.metric .value.yellow { color: var(--yellow); }
.metric .value.red { color: var(--red); }
.metric .value.blue { color: var(--accent); }
.metric .value.purple { color: var(--accent2); }
.badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }
.badge-green { background: var(--green-dim); color: var(--green); }
.badge-yellow { background: var(--yellow-dim); color: var(--yellow); }
.badge-red { background: var(--red-dim); color: var(--red); }
.badge-blue { background: rgba(79,142,247,0.12); color: var(--accent); }
.badge-purple { background: rgba(167,139,250,0.12); color: var(--accent2); }
table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; }
th { text-align: left; color: var(--muted); font-weight: 600; padding: 10px 14px; border-bottom: 1px solid var(--border); font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; }
td { padding: 12px 14px; border-bottom: 1px solid var(--border); }
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(255,255,255,0.02); }
.result { background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px; font-family: 'JetBrains Mono','Fira Code',monospace; font-size: 12px; max-height: 280px; overflow: auto; white-space: pre-wrap; word-break: break-all; margin-top: 12px; color: var(--text-secondary); }
.toast { position: fixed; bottom: 24px; right: 24px; padding: 14px 22px; border-radius: var(--radius-sm); font-size: 13px; z-index: 9999; animation: toastIn 0.3s cubic-bezier(0.4,0,0.2,1); box-shadow: var(--shadow); font-weight: 500; display: flex; align-items: center; gap: 8px; }
.toast-ok { background: var(--green-dim); color: var(--green); border: 1px solid rgba(52,211,153,0.3); }
.toast-err { background: var(--red-dim); color: var(--red); border: 1px solid rgba(248,113,113,0.3); }
.toast-info { background: rgba(79,142,247,0.12); color: var(--accent); border: 1px solid rgba(79,142,247,0.3); }
@keyframes toastIn { from { opacity: 0; transform: translateY(12px) scale(0.95); } to { opacity: 1; transform: none; } }
.spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.2); border-top-color: #fff; border-radius: 50%; animation: spin 0.6s linear infinite; vertical-align: middle; }
@keyframes spin { to { transform: rotate(360deg); } }
.link-ext { color: var(--accent); font-size: 12px; text-decoration: none; font-weight: 500; }
.link-ext:hover { text-decoration: underline; }
.multiselect-container { display: flex; flex-wrap: wrap; gap: 8px; background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 10px; min-height: 48px; }
.chip { background: var(--surface-2); color: var(--text-secondary); padding: 5px 12px; border-radius: 20px; font-size: 12px; cursor: pointer; user-select: none; transition: var(--transition); border: 1px solid transparent; font-weight: 500; }
.chip:hover { background: var(--border); color: var(--text); }
.chip.selected { background: var(--accent); color: #fff; border-color: var(--accent); }
.wallet-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.wallet-dot.ok { background: var(--green); box-shadow: 0 0 8px var(--green); }
.wallet-dot.nok { background: var(--red); }
.wallet-dot.warn { background: var(--yellow); box-shadow: 0 0 8px var(--yellow); }
.copy-btn { background: none; border: none; color: var(--muted); cursor: pointer; font-size: 12px; padding: 2px 6px; border-radius: 4px; transition: var(--transition); }
.copy-btn:hover { color: var(--accent); background: var(--accent-glow); }
.chat-container { display: flex; flex-direction: column; height: 520px; background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.chat-messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.chat-msg { max-width: 85%; padding: 12px 16px; border-radius: var(--radius-sm); font-size: 13px; line-height: 1.6; animation: fadeIn 0.2s ease; }
.chat-msg.user { align-self: flex-end; background: linear-gradient(135deg, var(--accent), #3b7de4); color: #fff; }
.chat-msg.assistant { align-self: flex-start; background: var(--surface-2); border: 1px solid var(--border); color: var(--text); }
.chat-msg.assistant pre { background: var(--bg); padding: 8px; border-radius: 6px; overflow-x: auto; margin: 8px 0; font-size: 12px; }
.chat-msg.assistant code { background: var(--bg); padding: 2px 6px; border-radius: 4px; font-size: 12px; font-family: 'JetBrains Mono',monospace; }
.chat-input-row { display: flex; gap: 8px; padding: 12px 16px; border-top: 1px solid var(--border); background: var(--surface); }
.chat-input-row input { flex: 1; }
.chat-input-row button { padding: 10px 18px; }
.history-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm); margin-bottom: 8px; transition: var(--transition); cursor: pointer; }
.history-item:hover { border-color: var(--border-hover); background: var(--surface-2); }
.history-item .hash { font-family: monospace; font-size: 12px; color: var(--accent); }
.history-item .time { font-size: 11px; color: var(--muted); }
.sidebar-toggle { display: none; position: fixed; top: 16px; left: 16px; z-index: 100; background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 8px 12px; border-radius: var(--radius-sm); cursor: pointer; font-size: 18px; }
.empty-state { text-align: center; padding: 40px 20px; color: var(--muted); }
.empty-state .icon { font-size: 40px; margin-bottom: 12px; opacity: 0.5; }
.ticker-bar { display: flex; gap: 24px; overflow-x: auto; padding: 10px 0; margin-bottom: 16px; border-bottom: 1px solid var(--border); font-size: 12px; white-space: nowrap; }
.ticker-item { display: flex; align-items: center; gap: 6px; }
.ticker-item .sym { font-weight: 700; color: var(--text); }
.ticker-item .price { color: var(--text-secondary); }
.ticker-item .chg { font-weight: 600; }
@media (max-width: 900px) {
  .layout { grid-template-columns: 1fr; }
  aside { position: fixed; left: -280px; top: 0; height: 100vh; z-index: 99; transition: left 0.3s ease; width: 280px; }
  aside.open { left: 0; }
  .sidebar-toggle { display: block; }
  main { padding: 60px 16px 16px; max-height: none; }
  .row-2, .row-3, .row-4 { grid-template-columns: 1fr; }
}
</style>
</head>
<body>
<button class="sidebar-toggle" onclick="toggleSidebar()">☰</button>
<div class="layout">
<aside id="sidebar">
  <div><div class="logo"><div class="logo-icon">🌍</div><div>African Rails<span>MCP Agent Dashboard</span></div></div></div>
  <hr class="divider">
  <div><label>Private Key</label><input type="password" id="privateKey" placeholder="0x..." oninput="walletChanged()"></div>
  <div><label>Wallet Address</label><input type="text" id="walletAddress" placeholder="0x..." oninput="walletChanged()">
    <div style="margin-top:8px;font-size:12px;display:flex;align-items:center;gap:6px;" id="walletStatus"><span class="wallet-dot nok"></span><span style="color:var(--muted)">Not configured</span></div>
  </div>
  <hr class="divider">
  <div><label>Chain</label><select id="chainSelect" onchange="chainChanged()">
    <option value="celo" selected>Celo Mainnet</option><option value="celo-alfajores">Celo Alfajores (testnet)</option>
    <option value="ethereum">Ethereum</option><option value="avalanche">Avalanche</option><option value="avalanche-fuji">Avalanche Fuji (testnet)</option>
  </select></div>
  <hr class="divider">
  <div style="display:flex;flex-direction:column;gap:4px;">
    <a class="link" href="https://faucet.celo.org" target="_blank">🚰 Celo faucet</a>
    <a class="link" href="https://faucet.avax.network" target="_blank">🚰 Fuji faucet</a>
    <a class="link" href="https://celoscan.io" target="_blank">🔍 Celo explorer</a>
    <a class="link" href="https://alfajores.celoscan.io" target="_blank">🔍 Alfajores explorer</a>
    <a class="link" href="https://etherscan.io" target="_blank">🔍 Ethereum explorer</a>
    <a class="link" href="https://snowtrace.io" target="_blank">🔍 Avalanche explorer</a>
  </div>
  <div style="margin-top:auto;padding-top:12px;border-top:1px solid var(--border);"><div style="font-size:11px;color:var(--muted);text-align:center;">v2.0 · Enhanced Edition</div></div>
</aside>
<main>
  <div class="ticker-bar" id="tickerBar"></div>
  <h1>Agent Dashboard</h1>
  <div class="subtitle" id="subtitle">Configure your wallet to begin autonomous settlement.</div>
  <div class="tabs">
    <div class="tab active" onclick="switchTab('overview')">🏠 Overview</div>
    <div class="tab" onclick="switchTab('prices')">💰 Prices</div>
    <div class="tab" onclick="switchTab('balance')">📊 Balance</div>
    <div class="tab" onclick="switchTab('send')">📤 Send</div>
    <div class="tab" onclick="switchTab('swap')">🔄 Swap</div>
    <div class="tab" onclick="switchTab('x402')">⚡ x402</div>
    <div class="tab" onclick="switchTab('status')">🔍 Tx Status</div>
    <div class="tab" onclick="switchTab('history')">📜 History</div>
    <div class="tab" onclick="switchTab('ai')">🤖 AI Assistant</div>
  </div>

  <!-- Overview -->
  <div id="panel-overview" class="panel active">
    <div class="card"><h3>📡 Network Status</h3>
      <div class="metrics" id="overviewMetrics">
        <div class="metric"><div class="label">Chain</div><div class="value blue" id="ovChain">—</div></div>
        <div class="metric"><div class="label">Wallet</div><div class="value" id="ovWallet">—</div></div>
        <div class="metric"><div class="label">Native Balance</div><div class="value green" id="ovNative">—</div></div>
        <div class="metric"><div class="label">Status</div><div class="value" id="ovStatus">—</div></div>
      </div>
      <div style="margin-top:12px;">
        <button class="btn btn-secondary btn-sm" onclick="refreshOverview()">🔄 Refresh</button>
        <button class="btn btn-ghost btn-sm" onclick="copyAddress()">📋 Copy address</button>
      </div>
    </div>
    <div class="card"><h3>⚡ Quick Actions</h3>
      <div style="display:flex;gap:10px;flex-wrap:wrap;">
        <button class="btn btn-primary" onclick="switchTab('send')">📤 Send tokens</button>
        <button class="btn btn-primary" onclick="switchTab('swap')">🔄 Swap tokens</button>
        <button class="btn btn-secondary" onclick="switchTab('balance')">📊 Check balance</button>
        <button class="btn btn-secondary" onclick="switchTab('x402')">⚡ x402 payment</button>
      </div>
    </div>
    <div class="card"><h3>📈 Price Snapshot</h3><div id="overviewPrices"><div class="empty-state"><div class="icon">📊</div>Load prices to see snapshot</div></div></div>
  </div>

  <!-- Prices -->
  <div id="panel-prices" class="panel">
    <div class="card"><h3>Select Tokens</h3><div class="multiselect-container" id="tokenChips"></div>
      <div style="margin-top:14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
        <select id="currency" style="width:130px;"><option value="usd">USD</option><option value="kes">KES</option><option value="eur">EUR</option><option value="gbp">GBP</option></select>
        <button class="btn btn-primary" onclick="fetchPrices()">Fetch prices</button>
        <button class="btn btn-ghost btn-sm" onclick="selectAllTokens()">Select all</button>
        <button class="btn btn-ghost btn-sm" onclick="clearTokens()">Clear</button>
      </div>
    </div>
    <div id="pricesResult"></div>
  </div>

  <!-- Balance -->
  <div id="panel-balance" class="panel">
    <div class="card"><h3>Check Balance</h3>
      <div class="row row-2">
        <div><label>Address</label><div style="display:flex;gap:6px;"><input type="text" id="balAddress" placeholder="0x... (blank = your wallet)"><button class="btn btn-secondary btn-sm" onclick="useSelfBal()">Self</button></div></div>
        <div><label>Token</label><select id="balToken"></select></div>
      </div>
      <button class="btn btn-primary" onclick="checkBalance()">Check balance</button>
    </div>
    <div id="balResult"></div>
  </div>

  <!-- Send -->
  <div id="panel-send" class="panel">
    <div class="card"><h3>Send Transaction</h3>
      <div class="row row-3">
        <div><label>Recipient</label><div style="display:flex;gap:6px;"><input type="text" id="sendTo" placeholder="0x..."><button class="btn btn-secondary btn-sm" onclick="useSelfSend()">Self</button></div></div>
        <div><label>Amount</label><input type="text" id="sendAmount" placeholder="0.001"></div>
        <div><label>Token</label><select id="sendToken"></select></div>
      </div>
      <div style="display:flex;gap:10px;margin-top:4px;flex-wrap:wrap;">
        <button class="btn btn-primary" onclick="sendTx()" id="sendBtn">Send transaction</button>
        <button class="btn btn-ghost btn-sm" onclick="document.getElementById('sendAmount').value=''">Clear</button>
      </div>
    </div>
    <div id="sendResult"></div>
  </div>

  <!-- Swap -->
  <div id="panel-swap" class="panel">
    <div class="card"><h3>Token Swap</h3>
      <div style="display:grid;grid-template-columns:1fr 44px 1fr 1fr;gap:14px;align-items:end;margin-bottom:14px;">
        <div><label>Sell</label><select id="swapIn"></select></div>
        <div style="text-align:center;"><button class="btn btn-secondary btn-sm" onclick="flipSwap()" title="Flip tokens" style="width:40px;height:40px;padding:0;border-radius:50%;">⇄</button></div>
        <div><label>Buy</label><select id="swapOut"></select></div>
        <div><label>Amount in</label><div style="display:flex;gap:6px;"><input type="text" id="swapAmount" placeholder="1.0"><button class="btn btn-secondary btn-sm" onclick="maxSwap()" title="Use max balance">Max</button></div></div>
      </div>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
        <div style="display:flex;align-items:center;gap:8px;"><label style="margin:0;white-space:nowrap;">Slippage %</label><input type="number" id="slippage" value="0.5" min="0.1" max="10" step="0.1" style="width:80px;"></div>
        <label style="display:flex;align-items:center;gap:6px;cursor:pointer;margin:0;"><input type="checkbox" id="preferMento" checked style="width:auto;"><span style="font-size:12px;color:var(--text-secondary);">Prefer Mento on Celo</span></label>
      </div>
      <div style="display:flex;gap:10px;flex-wrap:wrap;">
        <button class="btn btn-secondary" onclick="getQuote()">Get quote</button>
        <button class="btn btn-primary" onclick="execSwap()" id="swapBtn">Execute swap</button>
      </div>
      <div style="margin-top:12px;font-size:12px;color:var(--muted);line-height:1.6;">
        ℹ️ Swaps auto-route through <strong>Mento Broker</strong> for Celo stablecoin pairs (zero price impact) and <strong>Uniswap V3</strong> for everything else. Token approvals are handled automatically.
      </div>
    </div>
    <div id="swapResult"></div>
  </div>

  <!-- x402 -->
  <div id="panel-x402" class="panel">
    <div class="card"><h3>⚡ x402 Micropayment</h3>
      <div class="row"><div><label>URL to fetch</label><input type="text" id="x402Url" placeholder="https://api.example.com/resource"></div></div>
      <div class="row row-2">
        <div><label>HTTP Method</label><select id="x402Method"><option value="GET">GET</option><option value="POST">POST</option></select></div>
        <div><label>Max spend (USD)</label><input type="number" id="x402MaxSpend" value="0.10" step="0.01" min="0.01"></div>
      </div>
      <div style="display:flex;gap:10px;flex-wrap:wrap;">
        <button class="btn btn-secondary" onclick="checkX402Price()">Check price first</button>
        <button class="btn btn-primary" onclick="fetchX402()" id="x402Btn">Fetch with payment</button>
      </div>
    </div>
    <div id="x402Result"></div>
    <div class="card"><h3>💳 x402 Wallet Info</h3><button class="btn btn-secondary btn-sm" onclick="getX402Wallet()">Refresh wallet info</button><div id="x402WalletResult" style="margin-top:12px;"></div></div>
  </div>

  <!-- Tx Status -->
  <div id="panel-status" class="panel">
    <div class="card"><h3>Transaction Status</h3>
      <div class="row"><div><label>Transaction hash</label><input type="text" id="txHash" placeholder="0x..."></div></div>
      <div style="display:flex;gap:10px;flex-wrap:wrap;">
        <button class="btn btn-primary" onclick="checkTx()">Check status</button>
        <button class="btn btn-secondary" onclick="pollTx()">Poll until confirmed</button>
      </div>
    </div>
    <div id="statusResult"></div>
  </div>

  <!-- History -->
  <div id="panel-history" class="panel">
    <div class="card"><h3>📜 Transaction History</h3>
      <div style="display:flex;gap:10px;margin-bottom:16px;">
        <button class="btn btn-danger btn-sm" onclick="clearHistory()">🗑️ Clear all</button>
        <button class="btn btn-ghost btn-sm" onclick="exportHistory()">📥 Export JSON</button>
      </div>
      <div id="historyList"></div>
    </div>
  </div>

  <!-- AI Assistant -->
  <div id="panel-ai" class="panel">
    <div class="card"><h3>🤖 AI Assistant Settings</h3>
      <div class="row row-2">
        <div><label>API Endpoint (OpenAI-compatible)</label><input type="text" id="llmEndpoint" placeholder="https://api.openai.com/v1" value="https://api.openai.com/v1"></div>
        <div><label>API Key</label><input type="password" id="llmKey" placeholder="sk-..."></div>
      </div>
      <div class="row row-2">
        <div><label>Model</label><input type="text" id="llmModel" placeholder="gpt-4o-mini" value="gpt-4o-mini"></div>
        <div><label>Temperature</label><input type="number" id="llmTemp" value="0.7" min="0" max="2" step="0.1"></div>
      </div>
      <div style="font-size:12px;color:var(--muted);margin-top:4px;">The assistant can see your current prices, balances, and suggest swaps. It never sees your private key.</div>
    </div>
    <div class="chat-container">
      <div class="chat-messages" id="chatMessages">
        <div class="chat-msg assistant"><strong>👋 Welcome to African Rails AI</strong><br><br>I can help you:<br>• Analyze token prices and trends<br>• Suggest optimal swap routes<br>• Explain transaction statuses<br>• Guide you through x402 micropayments<br><br>Configure your API key above, then ask me anything!</div>
      </div>
      <div class="chat-input-row"><input type="text" id="chatInput" placeholder="Ask about prices, swaps, or transactions..." onkeydown="if(event.key==='Enter')sendChat()"><button class="btn btn-primary" onclick="sendChat()" id="chatBtn">Send</button></div>
    </div>
  </div>
</main>
</div>

<script>
// ── State ────────────────────────────────────────
let chainData = {};
let allTokens = [];
let selectedPriceTokens = new Set(["CELO","cUSD","cKES","ETH","USDC"]);
let walletOk = false;
let lastPrices = {};
let lastBalances = {};
let txHistory = JSON.parse(localStorage.getItem("ar_tx_history") || "[]");
let chatContext = [];

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
  renderHistory();
  startTicker();
  const savedPk = localStorage.getItem("ar_pk");
  const savedAddr = localStorage.getItem("ar_addr");
  if (savedPk) document.getElementById("privateKey").value = savedPk;
  if (savedAddr) document.getElementById("walletAddress").value = savedAddr;
  if (savedPk && savedAddr) walletChanged();
}

function renderTokenChips() {
  const c = document.getElementById("tokenChips");
  c.innerHTML = allTokens.map(t =>
    `<div class="chip ${selectedPriceTokens.has(t)?"selected":""}" onclick="toggleToken('${t}')">${t}</div>`
  ).join("");
}
function toggleToken(t){ selectedPriceTokens.has(t)?selectedPriceTokens.delete(t):selectedPriceTokens.add(t); renderTokenChips(); }
function selectAllTokens(){ allTokens.forEach(t=>selectedPriceTokens.add(t)); renderTokenChips(); }
function clearTokens(){ selectedPriceTokens.clear(); renderTokenChips(); }
function getChain(){ return document.getElementById("chainSelect").value; }
function chainChanged(){ updateChainTokens(); refreshOverview(); }

function updateChainTokens(){
  const chain = getChain();
  const tokens = chainData[chain]?.tokens || ["native"];
  const swapTokens = tokens.filter(t => t !== "native");
  ["balToken","sendToken"].forEach(id=>{
    const sel = document.getElementById(id); if(!sel) return;
    const curr = sel.value;
    sel.innerHTML = tokens.map(t=>`<option value="${t}">${t}</option>`).join("");
    if(tokens.includes(curr)) sel.value = curr;
  });
  ["swapIn","swapOut"].forEach((id,i)=>{
    const sel = document.getElementById(id); if(!sel) return;
    const curr = sel.value;
    sel.innerHTML = swapTokens.map(t=>`<option value="${t}">${t}</option>`).join("");
    if(swapTokens.includes(curr)) sel.value = curr;
    else if(i===1 && swapTokens.length>1) sel.value = swapTokens[1];
  });
}

function walletChanged(){
  const pk = document.getElementById("privateKey").value.trim();
  const addr = document.getElementById("walletAddress").value.trim();
  walletOk = pk.startsWith("0x") && pk.length>=66 && addr.startsWith("0x") && addr.length===42;
  const el = document.getElementById("walletStatus");
  const subtitle = document.getElementById("subtitle");
  if(walletOk){
    el.innerHTML = `<span class="wallet-dot ok"></span><span style="color:var(--green)">${addr.slice(0,6)}...${addr.slice(-4)}</span>`;
    subtitle.textContent = `Connected: ${addr}`;
    localStorage.setItem("ar_pk", pk);
    localStorage.setItem("ar_addr", addr);
    fetch("/api/config",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({private_key:pk,wallet_address:addr})});
    refreshOverview();
  } else {
    el.innerHTML = `<span class="wallet-dot nok"></span><span style="color:var(--muted)">Not configured</span>`;
    subtitle.textContent = "Configure your wallet to begin autonomous settlement.";
  }
}

function useSelfBal(){ document.getElementById("balAddress").value = document.getElementById("walletAddress").value; }
function useSelfSend(){ document.getElementById("sendTo").value = document.getElementById("walletAddress").value; }

function switchTab(name){
  document.querySelectorAll(".tab").forEach(el=>el.classList.remove("active"));
  const map = {overview:0,prices:1,balance:2,send:3,swap:4,x402:5,status:6,history:7,ai:8};
  const tabs = document.querySelectorAll(".tab");
  if(map[name]!=null && tabs[map[name]]) tabs[map[name]].classList.add("active");
  document.querySelectorAll(".panel").forEach(el=>el.classList.remove("active"));
  document.getElementById("panel-"+name).classList.add("active");
  if(name==="history") renderHistory();
  if(name==="overview") refreshOverview();
}
function toggleSidebar(){ document.getElementById("sidebar").classList.toggle("open"); }

async function api(path, body){
  const res = await fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  return res.json();
}
function loading(id, msg){
  document.getElementById(id).innerHTML = `<div style="padding:20px;color:var(--muted);display:flex;align-items:center;gap:10px;"><span class="spinner"></span>${msg}</div>`;
}
function toast(msg, ok=true){
  const t = document.createElement("div");
  t.className = `toast ${ok==="info"?"toast-info":ok?"toast-ok":"toast-err"}`;
  t.innerHTML = ok==="info"?`ℹ️ ${msg}`:ok?`✅ ${msg}`:`❌ ${msg}`;
  document.body.appendChild(t);
  setTimeout(()=>{t.style.opacity="0";t.style.transform="translateY(12px)";setTimeout(()=>t.remove(),300);},3500);
}
function statusBadge(s){
  const map={confirmed:"badge-green",pending:"badge-yellow",failed:"badge-red",submitted:"badge-blue",success:"badge-green"};
  return `<span class="badge ${map[s]||"badge-yellow"}">${s}</span>`;
}
function explorerLink(url){ return url?`<a href="${url}" target="_blank" class="link-ext">View on explorer →</a>`:""; }
function metricsHtml(items){
  return `<div class="metrics">${items.map(([label,value,cls])=>
    `<div class="metric"><div class="label">${label}</div><div class="value ${cls||""}">${value}</div></div>`
  ).join("")}</div>`;
}
function jsonBlock(data){
  return `<details style="margin-top:10px"><summary style="cursor:pointer;color:var(--muted);font-size:12px;font-weight:600;">Raw response</summary><div class="result">${JSON.stringify(data,null,2)}</div></details>`;
}
function copyText(text){ navigator.clipboard.writeText(text).then(()=>toast("Copied to clipboard",true)); }
function copyAddress(){ const addr=document.getElementById("walletAddress").value.trim(); if(addr) copyText(addr); }

// ── Overview ─────────────────────────────────────
async function refreshOverview(){
  const chain=getChain(), addr=document.getElementById("walletAddress").value.trim();
  document.getElementById("ovChain").textContent=chain;
  document.getElementById("ovWallet").textContent=addr?`${addr.slice(0,8)}...${addr.slice(-6)}`:"—";
  document.getElementById("ovStatus").innerHTML=walletOk?statusBadge("connected"):statusBadge("disconnected");
  if(walletOk && addr){
    try{
      const data=await api("/api/balance",{address:addr,chain,token:"native"});
      const bal=parseFloat(data.balance||0);
      document.getElementById("ovNative").textContent=`${bal.toFixed(4)} ${data.token}`;
      lastBalances["native"]=bal;
    }catch(e){ document.getElementById("ovNative").textContent="Error"; }
  } else { document.getElementById("ovNative").textContent="—"; }
  if(Object.keys(lastPrices).length>0){
    const items=Object.entries(lastPrices).slice(0,4).map(([sym,info])=>{
      const price=info.usd??"—"; const change=info.usd_24h_change;
      const chgHtml=change!=null?`<span style="color:${change>=0?"var(--green)":"var(--red)"}">${change>=0?"▲":"▼"} ${Math.abs(change).toFixed(2)}%</span>`:"";
      return `<div class="metric"><div class="label">${sym}</div><div class="value">$${typeof price==="number"?price.toLocaleString(undefined,{maximumFractionDigits:4}):price}</div><div style="font-size:11px;margin-top:4px;">${chgHtml}</div></div>`;
    }).join("");
    document.getElementById("overviewPrices").innerHTML=`<div class="metrics">${items}</div>`;
  }
}

// ── Prices ───────────────────────────────────────
async function fetchPrices(){
  const symbols=[...selectedPriceTokens];
  if(!symbols.length){toast("Select at least one token",false);return;}
  const cur=document.getElementById("currency").value;
  loading("pricesResult","Fetching prices from CoinGecko...");
  const data=await api("/api/prices",{symbols,currencies:[cur]});
  if(!data.success){
    document.getElementById("pricesResult").innerHTML=`<div class="card" style="color:var(--red)"><strong>${data.error}</strong>: ${data.detail}</div>`;
    return;
  }
  lastPrices=data.prices||{};
  const rows=Object.entries(data.prices).map(([sym,info])=>{
    const price=info[cur]??"—"; const change=info[`${cur}_24h_change`];
    const changeHtml=change!=null?`<span style="color:${change>=0?"var(--green)":"var(--red)"};font-weight:600;">${change>=0?"▲":"▼"} ${Math.abs(change).toFixed(2)}%</span>`:"—";
    const priceStr=typeof price==="number"?price.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:6}):price;
    return `<tr><td><strong>${sym}</strong></td><td>${cur.toUpperCase()} ${priceStr}</td><td>${changeHtml}</td><td><button class="copy-btn" onclick="copyText('${priceStr}')">📋</button></td></tr>`;
  }).join("");
  document.getElementById("pricesResult").innerHTML=`<div class="card"><table><thead><tr><th>Token</th><th>Price (${cur.toUpperCase()})</th><th>24h change</th><th></th></tr></thead><tbody>${rows}</tbody></table></div>`;
  if(document.getElementById("panel-overview").classList.contains("active")) refreshOverview();
}

// ── Balance ──────────────────────────────────────
async function checkBalance(){
  loading("balResult","Querying balance...");
  const data=await api("/api/balance",{address:document.getElementById("balAddress").value.trim(),chain:getChain(),token:document.getElementById("balToken").value});
  if(data.error && !data.balance){
    document.getElementById("balResult").innerHTML=`<div class="card" style="color:var(--red)"><strong>${data.error}</strong>: ${data.detail}</div>`;
    return;
  }
  const bal=parseFloat(data.balance||0);
  lastBalances[data.token]=bal;
  document.getElementById("balResult").innerHTML=`<div class="card">${metricsHtml([["Balance",`${bal.toFixed(6)} ${data.token}`,"green"],["Chain",data.chain],["Address",(data.address||"").slice(0,12)+"..."]])}${data.contract_address?`<div style="font-size:12px;color:var(--muted);margin-top:10px;">Contract: ${data.contract_address} <button class="copy-btn" onclick="copyText('${data.contract_address}')">📋</button></div>`:""}${jsonBlock(data)}</div>`;
}

// ── Send ─────────────────────────────────────────
async function sendTx(){
  if(!walletOk){toast("Configure wallet in sidebar first",false);return;}
  const btn=document.getElementById("sendBtn");
  btn.disabled=true; btn.innerHTML='<span class="spinner"></span>Broadcasting...';
  loading("sendResult","Signing and broadcasting...");
  const data=await api("/api/send",{to:document.getElementById("sendTo").value.trim(),amount:document.getElementById("sendAmount").value.trim(),chain:getChain(),token:document.getElementById("sendToken").value});
  btn.disabled=false; btn.textContent="Send transaction";
  if(data.tx_hash){
    toast("Transaction submitted!");
    addToHistory({type:"send",hash:data.tx_hash,chain:data.chain,token:data.token,amount:data.amount,time:Date.now()});
    document.getElementById("sendResult").innerHTML=`<div class="card">${metricsHtml([["Status",statusBadge(data.status),""],["Token",`${data.amount} ${data.token}`],["Tx Hash",`${data.tx_hash.slice(0,18)}... <button class="copy-btn" onclick="copyText('${data.tx_hash}')">📋</button>`]])}${explorerLink(data.explorer_url)}<div style="margin-top:10px;"><button class="btn btn-secondary btn-sm" onclick="goToStatus('${data.tx_hash}','${data.chain}')">Check status →</button></div>${jsonBlock(data)}</div>`;
  } else {
    toast(data.error||"Error",false);
    document.getElementById("sendResult").innerHTML=`<div class="card" style="color:var(--red)"><strong>${data.error}</strong>: ${data.detail}</div>`;
  }
}

// ── Swap ─────────────────────────────────────────
function flipSwap(){
  const inSel=document.getElementById("swapIn"), outSel=document.getElementById("swapOut");
  const tmp=inSel.value; inSel.value=outSel.value; outSel.value=tmp;
}
async function maxSwap(){
  if(!walletOk){toast("Configure wallet first",false);return;}
  const token=document.getElementById("swapIn").value, chain=getChain();
  try{
    const data=await api("/api/balance",{address:"",chain,token});
    if(data.balance) document.getElementById("swapAmount").value=parseFloat(data.balance).toFixed(6);
  }catch(e){toast("Could not fetch balance",false);}
}
async function getQuote(){
  const tokenIn=document.getElementById("swapIn").value, tokenOut=document.getElementById("swapOut").value;
  const amountIn=document.getElementById("swapAmount").value||"1.0";
  if(!amountIn || parseFloat(amountIn)<=0){toast("Enter an amount",false);return;}
  if(tokenIn===tokenOut){toast("Cannot swap same token",false);return;}
  loading("swapResult","Fetching quote from DEX...");
  const data=await api("/api/quote",{token_in:tokenIn,token_out:tokenOut,amount_in:amountIn,chain:getChain(),prefer_mento:document.getElementById("preferMento").checked});
  if(data.success===false){
    document.getElementById("swapResult").innerHTML=`<div class="card" style="color:var(--red)"><strong>${data.error}</strong>: ${data.detail}</div>`;
    return;
  }
  const dexLabel=data.dex==="mento"?"Mento Broker":"Uniswap V3";
  const feeTierHtml=data.fee_pct!=null?`${data.fee_pct.toFixed(2)}%`:"—";
  const rate=parseFloat(data.amount_out)/parseFloat(data.amount_in);
  document.getElementById("swapResult").innerHTML=`<div class="card"><h3>Quote — ${dexLabel}</h3>${metricsHtml([["You send",`${data.amount_in} ${data.token_in}`],["You get ≈",`${parseFloat(data.amount_out).toFixed(6)} ${data.token_out}`,"green"],["Rate",`1 ${data.token_in} = ${rate.toFixed(4)} ${data.token_out}`],["DEX",dexLabel],["Fee tier",feeTierHtml]])}<div style="margin-top:10px;"><button class="btn btn-primary btn-sm" onclick="execSwap()">Execute this swap →</button></div>${jsonBlock(data)}</div>`;
}
async function execSwap(){
  if(!walletOk){toast("Configure wallet in sidebar first",false);return;}
  const btn=document.getElementById("swapBtn");
  btn.disabled=true; btn.innerHTML='<span class="spinner"></span>Swapping...';
  loading("swapResult","Executing swap...");
  const data=await api("/api/swap",{token_in:document.getElementById("swapIn").value,token_out:document.getElementById("swapOut").value,amount_in:document.getElementById("swapAmount").value,chain:getChain(),slippage_pct:parseFloat(document.getElementById("slippage").value),prefer_mento:document.getElementById("preferMento").checked});
  btn.disabled=false; btn.textContent="Execute swap";
  if(data.tx_hash){
    toast("Swap submitted!");
    addToHistory({type:"swap",hash:data.tx_hash,chain:data.chain,token_in:data.token_in,token_out:data.token_out,amount:data.amount_in,time:Date.now()});
    document.getElementById("swapResult").innerHTML=`<div class="card">${metricsHtml([["Status",statusBadge(data.status),""],["Expected out",`${parseFloat(data.expected_amount_out).toFixed(6)} ${data.token_out}`,"green"],["Min out",`${parseFloat(data.min_amount_out).toFixed(6)} ${data.token_out}`],["DEX",data.dex?.toUpperCase()||"—"]])}${explorerLink(data.explorer_url)}<div style="margin-top:8px;"><button class="btn btn-secondary btn-sm" onclick="goToStatus('${data.tx_hash}','${data.chain}')">Check status →</button></div>${jsonBlock(data)}</div>`;
  } else {
    toast(data.error||"Swap failed",false);
    document.getElementById("swapResult").innerHTML=`<div class="card" style="color:var(--red)"><strong>${data.error}</strong>: ${data.detail}</div>`;
  }
}

// ── x402 ─────────────────────────────────────────
async function checkX402Price(){
  const url=document.getElementById("x402Url").value.trim();
  if(!url){toast("Enter a URL",false);return;}
  loading("x402Result","Checking x402 price...");
  const data=await api("/api/x402/price",{url});
  if(data.payment_required===false){
    document.getElementById("x402Result").innerHTML=`<div class="card"><div style="color:var(--green);font-weight:600;">✅ No payment required</div>${jsonBlock(data)}</div>`;
  } else if(data.error){
    document.getElementById("x402Result").innerHTML=`<div class="card" style="color:var(--red)"><strong>${data.error}</strong>: ${data.detail}</div>`;
  } else {
    document.getElementById("x402Result").innerHTML=`<div class="card">${metricsHtml([["Price",`$${data.price}`,"green"],["Token",data.token],["Network",data.network],["Facilitator",data.facilitator?.slice(0,12)+"..."||"—"]])}${jsonBlock(data)}</div>`;
  }
}
async function fetchX402(){
  if(!walletOk){toast("Configure wallet first",false);return;}
  const url=document.getElementById("x402Url").value.trim();
  if(!url){toast("Enter a URL",false);return;}
  const btn=document.getElementById("x402Btn");
  btn.disabled=true; btn.innerHTML='<span class="spinner"></span>Fetching...';
  loading("x402Result","Fetching with x402 payment...");
  const data=await api("/api/x402/fetch",{url,method:document.getElementById("x402Method").value,max_spend_usd:parseFloat(document.getElementById("x402MaxSpend").value)});
  btn.disabled=false; btn.textContent="Fetch with payment";
  if(data.error){
    document.getElementById("x402Result").innerHTML=`<div class="card" style="color:var(--red)"><strong>${data.error}</strong>: ${data.detail}</div>`;
  } else {
    const paidBadge=data.payment_made?statusBadge("paid"):statusBadge("free");
    document.getElementById("x402Result").innerHTML=`<div class="card">${metricsHtml([["Status",paidBadge,""],["HTTP Status",data.http_status],["Cost",data.cost_usd?`$${data.cost_usd}`:"—"]])}<div style="margin-top:10px;"><strong>Response preview:</strong><div class="result">${JSON.stringify(data.response||{},null,2).slice(0,800)}${JSON.stringify(data.response||{},null,2).length>800?"...":""}</div></div>${jsonBlock(data)}</div>`;
  }
}
async function getX402Wallet(){
  loading("x402WalletResult","Loading x402 wallet...");
  const data=await fetch("/api/x402/wallet").then(r=>r.json());
  if(data.success){
    const balItems=Object.entries(data.balances||{}).map(([k,v])=>[`${k}`,v,"blue"]);
    document.getElementById("x402WalletResult").innerHTML=`<div class="metrics">${metricsHtml([["Wallet",data.wallet_address?.slice(0,14)+"...","purple"],["Max spend","$"+data.max_spend_usd_per_request,"yellow"],...balItems])}</div>${jsonBlock(data)}`;
  } else {
    document.getElementById("x402WalletResult").innerHTML=`<div style="color:var(--red)">${data.error}</div>`;
  }
}

// ── Tx Status ────────────────────────────────────
function goToStatus(hash,chain){
  document.getElementById("txHash").value=hash;
  document.getElementById("chainSelect").value=chain;
  switchTab("status");
  checkTx();
}
async function checkTx(){
  const hash=document.getElementById("txHash").value.trim();
  if(!hash){toast("Enter a tx hash",false);return;}
  loading("statusResult","Querying RPC...");
  const data=await api("/api/tx",{tx_hash:hash,chain:getChain()});
  renderTxStatus(data,hash);
}
function renderTxStatus(data,hash){
  const status=data.status||"unknown";
  document.getElementById("statusResult").innerHTML=`<div class="card"><div style="font-size:20px;margin-bottom:12px;">${statusBadge(status)}</div>${metricsHtml([["Tx Hash",(hash||"").slice(0,16)+"... <button class=\\"copy-btn\\" onclick=\\"copyText('"+hash+"')\\">📋</button>"],["Chain",data.chain||getChain()],...(data.block_number?[["Block",data.block_number.toLocaleString()]]:[]),...(data.gas_used?[["Gas used",data.gas_used.toLocaleString()]]:[])])}${explorerLink(data.explorer_url)}${jsonBlock(data)}</div>`;
}
async function pollTx(){
  const hash=document.getElementById("txHash").value.trim();
  if(!hash){toast("Enter a tx hash",false);return;}
  let attempts=0, max=10;
  loading("statusResult","Polling for confirmation (attempt 1/10)...");
  const interval=setInterval(async()=>{
    attempts++;
    document.getElementById("statusResult").innerHTML=`<div style="padding:16px;color:var(--muted);display:flex;align-items:center;gap:10px;"><span class="spinner"></span>Attempt ${attempts}/${max}...</div>`;
    const data=await api("/api/tx",{tx_hash:hash,chain:getChain()});
    if(data.status==="confirmed"||data.status==="failed"||attempts>=max){
      clearInterval(interval);
      renderTxStatus(data,hash);
      toast(data.status==="confirmed"?"Confirmed!":data.status==="failed"?"Transaction failed":"Still pending after 30s",data.status==="confirmed");
    }
  },3000);
}

// ── History ──────────────────────────────────────
function addToHistory(item){
  txHistory.unshift(item);
  if(txHistory.length>50) txHistory=txHistory.slice(0,50);
  localStorage.setItem("ar_tx_history",JSON.stringify(txHistory));
  renderHistory();
}
function renderHistory(){
  const container=document.getElementById("historyList");
  if(!txHistory.length){ container.innerHTML=`<div class="empty-state"><div class="icon">📭</div>No transactions yet</div>`; return; }
  container.innerHTML=txHistory.map((h,i)=>`
    <div class="history-item" onclick="goToStatus('${h.hash}','${h.chain}')">
      <div><span class="badge ${h.type==='send'?'badge-blue':h.type==='swap'?'badge-purple':'badge-yellow'}">${h.type.toUpperCase()}</span> <span class="hash">${h.hash.slice(0,18)}...</span></div>
      <div class="time">${new Date(h.time).toLocaleString()} · ${h.chain}</div>
    </div>
  `).join("");
}
function clearHistory(){ txHistory=[]; localStorage.removeItem("ar_tx_history"); renderHistory(); toast("History cleared","info"); }
function exportHistory(){
  const blob=new Blob([JSON.stringify(txHistory,null,2)],{type:"application/json"});
  const url=URL.createObjectURL(blob);
  const a=document.createElement("a"); a.href=url; a.download="african_rails_history.json"; a.click(); URL.revokeObjectURL(url);
}

// ── AI Assistant ─────────────────────────────────
async function sendChat(){
  const input=document.getElementById("chatInput");
  const msg=input.value.trim();
  if(!msg) return;
  const endpoint=document.getElementById("llmEndpoint").value.trim()||"https://api.openai.com/v1";
  const key=document.getElementById("llmKey").value.trim();
  const model=document.getElementById("llmModel").value.trim()||"gpt-4o-mini";
  const temp=parseFloat(document.getElementById("llmTemp").value)||0.7;
  if(!key){toast("Enter an API key first",false);return;}
 
  const chatBox=document.getElementById("chatMessages");
  chatBox.innerHTML+=`<div class="chat-msg user">${escapeHtml(msg)}</div>`;
  input.value="";
  chatBox.scrollTop=chatBox.scrollHeight;
 
  const btn=document.getElementById("chatBtn");
  btn.disabled=true; btn.innerHTML='<span class="spinner"></span>';
 
  // Build context from current dashboard state
  const priceContext=Object.entries(lastPrices).slice(0,5).map(([s,p])=>`${s}: $${p.usd??"?"}`).join(", ");
  const balanceContext=Object.entries(lastBalances).map(([t,b])=>`${t}: ${b}`).join(", ");
  const chain=getChain();
 
  const systemPrompt=`You are African Rails AI, an expert blockchain assistant for African markets. You help users with token prices, swaps, transactions, and x402 micropayments. Current context: Chain=${chain}, Prices={${priceContext}}, Balances={${balanceContext}}. Never ask for private keys. Be concise and actionable.`;
 
  chatContext.push({role:"user",content:msg});
  if(chatContext.length>10) chatContext=chatContext.slice(-10);

  try{
    // Route through Flask backend to avoid CORS issues and keep API key off the browser network tab
    const res=await fetch("/api/ai/chat",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        endpoint,
        api_key:key,
        model,
        temperature:temp,
        messages:[{role:"system",content:systemPrompt},...chatContext],
      })
    });
    const data=await res.json();
    if(data.error){ throw new Error(data.error.message||"LLM error"); }
    const reply=data.choices?.[0]?.message?.content||"No response";
    chatContext.push({role:"assistant",content:reply});
    chatBox.innerHTML+=`<div class="chat-msg assistant">${formatMarkdown(escapeHtml(reply))}</div>`;
    chatBox.scrollTop=chatBox.scrollHeight;
  }catch(e){
    chatBox.innerHTML+=`<div class="chat-msg assistant" style="color:var(--red)"><strong>Error:</strong> ${escapeHtml(e.message)}<br><br><em>Tip: Make sure your endpoint and API key are correct.</em></div>`;
    chatBox.scrollTop=chatBox.scrollHeight;
  }
  btn.disabled=false; btn.textContent="Send";
}

function escapeHtml(text){
  const div=document.createElement("div");
  div.textContent=text;
  return div.innerHTML;
}
function formatMarkdown(text){
  // Simple markdown: bold, code blocks, inline code
  return text
    .replace(/\*\*(.*?)\*\*/g,"<strong>$1</strong>")
    .replace(/```([\s\S]*?)```/g,"<pre style='background:var(--bg);padding:8px;border-radius:6px;overflow-x:auto;margin:8px 0;font-size:12px;'>$1</pre>")
    .replace(/`([^`]+)`/g,"<code style='background:var(--bg);padding:2px 6px;border-radius:4px;font-size:12px;'>$1</code>")
    .replace(/\\n/g,"<br>");
}

// ── Ticker ───────────────────────────────────────
function startTicker(){
  const bar=document.getElementById("tickerBar");
  const symbols=["CELO","cUSD","cKES","ETH","USDC","BTC"];
  async function update(){
    try{
      const data=await api("/api/prices",{symbols,currencies:["usd"]});
      if(data.prices){
        bar.innerHTML=Object.entries(data.prices).map(([sym,info])=>{
          const p=info.usd??"?"; const c=info.usd_24h_change;
          const chg=c!=null?`<span class="chg" style="color:${c>=0?"var(--green)":"var(--red)"}">${c>=0?"▲":"▼"}${Math.abs(c).toFixed(1)}%</span>`:"";
          return `<div class="ticker-item"><span class="sym">${sym}</span><span class="price">$${typeof p==="number"?p.toLocaleString(undefined,{maximumFractionDigits:4}):p}</span>${chg}</div>`;
        }).join("");
      }
    }catch(e){}
  }
  update();
  setInterval(update,30000);
}

init();
</script>
</body>
</html>
"""
