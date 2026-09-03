import React, { useState, useEffect } from "react";
import "./App.css";
import { callTool } from "./api";
import MarketDataPage from "./pages/MarketDataPage";
import WalletPage from "./pages/WalletPage";
import SwapPage from "./pages/SwapPage";
import TransferPage from "./pages/TransferPage";
import X402Page from "./pages/X402Page";
import ActivityPage from "./pages/ActivityPage";
import DeveloperPage from "./pages/DeveloperPage";

// Maps a free-text request to one of the backend's registered tools plus its
// payload, and how to describe a successful result. This is a lightweight
// keyword/regex router, not an LLM call — it's what lets each quick-reply
// suggestion (and reasonable free-typed variants) actually hit a different
// tool instead of every message calling fetch_market_price regardless of
// what was typed. Swapping this for a real LLM tool-call later only means
// replacing the body of this function; sendMessage() and the fetch call
// don't need to change.
// Turns any http(s) URL inside a plain message string into a real,
// clickable link when rendered — used for both the keyword router's
// describe() strings and the Groq agent's replies, since both just
// produce plain text and neither needs to know this exists.
function linkify(text) {
  const urlRegex = /(https?:\/\/[^\s)]+)/g;
  const parts = [];
  let lastIndex = 0;
  let match;
  while ((match = urlRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const url = match[0];
    const linkKey = match.index;
    parts.push(React.createElement("a", { key: linkKey, href: url, target: "_blank", rel: "noopener noreferrer", className: "msg-link" }, url));
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts;
}

function pickToolFromMessage(text) {
  // "Swap 100 USDT to USDC"
  const swapMatch = text.match(
    /swap\s+([\d.]+)\s*([a-zA-Z.]+)\s+(?:to|for|into)\s+([a-zA-Z.]+)/i
  );
  if (swapMatch) {
    return {
      tool: "swap_tokens",
      payload: {
        amount: parseFloat(swapMatch[1]),
        from_token: swapMatch[2].toUpperCase(),
        to_token: swapMatch[3].toUpperCase(),
      },
      describe: (d) =>
        d.explorer_url
          ? `Swapped ${d.amount_in} ${d.from_token} for ${d.amount_out} ${d.to_token} on ${d.chain} via ${d.dex}. Verify: ${d.explorer_url}`
          : `Swapped ${d.amount_in} ${d.from_token} for ${d.amount_out} ${d.to_token} on ${d.chain} (tx ${d.tx_hash.slice(0, 10)}...).`,
    };
  }

  // "Send 20 USDC to M-Pesa 0712345678" or "Send 20 KES to 254712345678"
  if (/m-?pesa|momo|mobile money|off.?ramp|payout/i.test(text)) {
    const amountMatch = text.match(/([\d.]+)\s*([a-zA-Z]+)/);
    // Kenyan mobile format: 07XXXXXXXX / 01XXXXXXXX / 2547XXXXXXXX / +254...
    const phoneMatch = text.match(/(?:\+?254|0)([71]\d{8})\b/);
    return {
      tool: "off_ramp_payout",
      payload: {
        amount: amountMatch ? parseFloat(amountMatch[1]) : 20,
        currency: "KES",
        // Falls back to the demo placeholder only when no real number was
        // typed (e.g. the quick-reply button's canned message) — was
        // previously hardcoded unconditionally, silently ignoring any
        // number the user actually specified.
        phone_number: phoneMatch ? phoneMatch[0] : "254700000000",
      },
      describe: (d) =>
        d.status === "PENDING"
          ? `${d.message} (tracking ID: ${d.checkout_request_id})`
          : `Paid out ${d.amount_delivered} ${d.currency} to ${d.recipient} via ${d.network} (ref ${d.transaction_id}).`,
    };
  }

  // "Pay the x402 request"
  if (/x402|invoice|payment request/i.test(text)) {
    return {
      tool: "x402_get_invoice",
      payload: { url: "https://example.com/protected-resource", token: "USDC" },
      describe: (d) =>
        `Resolved invoice ${d.invoice_id}: ${d.amount} ${d.token} on ${d.chain} (status ${d.status}).`,
    };
  }

  // An explicit destination address implies a transfer.
  const addressMatch = text.match(/0x[a-fA-F0-9]{6,}/);
  if (addressMatch) {
    const amountMatch = text.match(/([\d.]+)\s*([a-zA-Z]+)/);
    return {
      tool: "transfer",
      payload: {
        to_address: addressMatch[0],
        amount: amountMatch ? parseFloat(amountMatch[1]) : 1,
        token: amountMatch ? amountMatch[2].toUpperCase() : "USDC",
      },
      describe: (d) =>
        `Sent ${d.amount} ${d.token} to ${d.to_address} (gas ${d.gas_fee_usdc} USDC).`,
    };
  }

  // Default: a price/rate lookup. Try to pull a "X to Y" or "X/Y" pair out
  // of the text; otherwise fall back to USDC/KES.
  const pairMatch = text.match(
    /\b([a-zA-Z]{2,6})\b\s*(?:\/|to|vs\.?)\s*\b([a-zA-Z]{2,6})\b/i
  );
  const token = pairMatch ? pairMatch[1].toUpperCase() : "USDC";
  const quote = pairMatch ? pairMatch[2].toUpperCase() : "KES";
  return {
    tool: "fetch_market_price",
    payload: { token, quote },
    describe: (d) => `1 ${d.token} = ${d.rate} ${d.quote} on ${d.chain}.`,
  };
}

// Icon + display title per tool, used when logging a successful call (from
// chat, either routing path, or a dedicated page) into the shared activity
// feed that Overview, the Activity page, and LAST EXECUTION all read from.
const TOOL_META = {
  fetch_market_price: { icon: "◈", title: "Market Data" },
  swap_tokens: { icon: "⇄", title: "Token Swap" },
  transfer: { icon: "↗", title: "Transfer" },
  off_ramp_payout: { icon: "↗", title: "M-Pesa Payout" },
  x402_get_invoice: { icon: "₿", title: "x402 Invoice" },
  x402_settle_invoice: { icon: "₿", title: "x402 Payment" },
};

function App() {
  const [activePage, setActivePage] = useState("Overview");

  const [messages, setMessages] = useState([
    {
      role: "agent",
      text: "Hello. I'm your Global Rails financial agent. I can check market rates, swap tokens, transfer funds, and handle x402 payments.",
    },
  ]);

  const [input, setInput] = useState("");

  // Shared across the AI Agent chat (both the Groq path and the keyword
  // fallback) and every dedicated tool page, so Overview, the Activity
  // page, and the "LAST EXECUTION" panel all reflect the same real history
  // no matter which surface triggered the call.
  const [activities, setActivities] = useState([]);

  const logActivity = (entry) => {
    setActivities((current) => [
      { id: `${Date.now()}-${Math.random().toString(36).slice(2)}`, timestamp: Date.now(), ...entry },
      ...current,
    ]);
  };

  // Overview's Market Data card already says "● LIVE" in its label — this
  // makes that true. Same fetch_market_price call MarketDataPage's own
  // "Fetch prices" button makes, just triggered automatically on load
  // instead of waiting for a click, since Overview has no button for it.
  const [overviewRate, setOverviewRate] = useState(null);
  const [overviewRateError, setOverviewRateError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    callTool("fetch_market_price", { token: "USDC", quote: "KES" })
      .then((res) => {
        if (cancelled) return;
        if (res.success) {
          setOverviewRate(res.data);
        } else {
          setOverviewRateError(res.error || "Unknown error");
        }
      })
      .catch((err) => {
        if (!cancelled) setOverviewRateError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

 const sendMessage = async () => {
  if (!input.trim()) return;

  const userText = input.trim();

  setMessages((current) => [
    ...current,
    {
      role: "user",
      text: userText,
    },
  ]);

  setInput("");

  // Real LLM-based routing first (Groq, server-side) — falls back to the
  // keyword router below if GROQ_API_KEY isn't set on the backend yet, or
  // if the LLM call itself fails for any reason, so the agent keeps
  // working either way instead of hitting a dead end.
  try {
    const history = messages.slice(-8).map((m) => ({
      role: m.role === "agent" ? "assistant" : "user",
      content: m.text,
    }));

    const agentResponse = await fetch("/api/agent/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userText, history }),
    });
    const agentResult = await agentResponse.json();

    if (agentResult.configured && !agentResult.error) {
      if (agentResult.tool_used && agentResult.tool_result?.success) {
        const meta = TOOL_META[agentResult.tool_used] || { icon: "✦", title: agentResult.tool_used };
        logActivity({
          icon: meta.icon,
          title: meta.title,
          detail: "via AI Agent chat",
          amount: agentResult.reply.length > 40 ? `${agentResult.reply.slice(0, 40)}...` : agentResult.reply,
        });
      }
      setMessages((current) => [
        ...current,
        { role: "agent", text: agentResult.reply },
      ]);
      return;
    }
    // configured === false (no GROQ_API_KEY yet) or a Groq-side error —
    // fall through to the keyword router rather than stopping here.
  } catch {
    // Couldn't even reach /api/agent/chat — also fall through.
  }

  const { tool, payload, describe } = pickToolFromMessage(userText);

  try {
    const result = await callTool(tool, payload);

    const agentText = result.success
      ? describe(result.data)
      : `I couldn't complete that (${tool}): ${result.error || "Unknown error"}`;

    if (result.success) {
      const meta = TOOL_META[tool] || { icon: "✦", title: tool };
      logActivity({
        icon: meta.icon,
        title: meta.title,
        detail: "via AI Agent chat",
        amount: agentText.length > 40 ? `${agentText.slice(0, 40)}...` : agentText,
      });
    }

    setMessages((current) => [
      ...current,
      {
        role: "agent",
        text: agentText,
      },
    ]);
  } catch (error) {
    setMessages((current) => [
      ...current,
      {
        role: "agent",
        text: `I couldn't connect to the Global Rails backend: ${error.message}`,
      },
    ]);
  }
};

  const applySuggestion = (text) => {
    setInput(text);
  };

  const navigation = [
    { name: "Overview", icon: "⌂" },
    { name: "AI Agent", icon: "✦", special: true },
    { name: "Market Data", icon: "◈" },
    { name: "Wallet", icon: "◫" },
    { name: "Swap", icon: "⇄" },
    { name: "Transfer", icon: "↗" },
    { name: "x402 Payments", icon: "₿" },
    { name: "Activity", icon: "◷" },
    { name: "Developer", icon: "⚙" },
  ];

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-mark">
            <svg width="26" height="26" viewBox="-16 -16 32 32" aria-hidden="true">
              <circle cx="0" cy="0" r="15" fill="none" stroke="#101400" strokeWidth="1.6" />
              <path d="M 0,-15 A 11.49,15 0 0 1 0,15" fill="none" stroke="#101400" strokeWidth="1" opacity="0.75" />
              <path d="M 0,-15 A 11.49,15 0 0 0 0,15" fill="none" stroke="#101400" strokeWidth="1" opacity="0.75" />
              <path d="M -13.75 -6 Q 0 -3.3 13.75 -6" fill="none" stroke="#101400" strokeWidth="1.6" strokeLinecap="round" />
              <path d="M -15 0 L 15 0" fill="none" stroke="#101400" strokeWidth="1.6" strokeLinecap="round" />
              <path d="M -13.75 6 Q 0 3.3 13.75 6" fill="none" stroke="#101400" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </div>

          <div className="logo-text">
            <h1>Global Rails</h1>
            <span>Agent Finance</span>
          </div>
        </div>

        <nav className="navigation">
          <p className="nav-label">WORKSPACE</p>

          {navigation.map((item) => (
            <button
              key={item.name}
              className={`nav-item ${
                activePage === item.name ? "active" : ""
              } ${item.special ? "agent-nav" : ""}`}
              onClick={() => setActivePage(item.name)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.name}</span>

              {item.special && (
                <span className="agent-new">AI</span>
              )}
            </button>
          ))}
        </nav>

        <div className="agent-status">
          <div className="status-dot"></div>

          <div>
            <strong>Agent Online</strong>
            <span>Ready for execution</span>
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <span className="eyebrow">GLOBAL RAILS</span>
            <h2>{activePage}</h2>
          </div>

          <div className="topbar-right">
            <div className="network">
              <span className="network-dot"></span>
              Testnet
            </div>

            <div className="avatar">M</div>
          </div>
        </header>

        {activePage === "AI Agent" ? (
          <section className="agent-page">
            <div className="agent-page-header">
              <div>
                <div className="large-agent-icon">✦</div>

                <span className="eyebrow">
                  AUTONOMOUS FINANCIAL AGENT
                </span>

                <h1>What can I execute for you?</h1>

                <p>
                  Use natural language to interact with Global Rails.
                  Your agent can fetch prices, swap assets, transfer
                  funds and settle x402 payments.
                </p>
              </div>

              <div className="connection-badge">
                <span></span>
                MCP CONNECTED
              </div>
            </div>

            <div className="agent-workspace">
              <div className="chat-panel">
                <div className="chat-panel-header">
                  <div className="agent-identity">
                    <div className="mini-agent-icon">✦</div>

                    <div>
                      <strong>Global Rails Agent</strong>
                      <span>Autonomous financial execution</span>
                    </div>
                  </div>

                  <div className="online-label">
                    <span></span>
                    Online
                  </div>
                </div>

                <div className="chat-messages large-chat">
                  {messages.map((message, index) => (
                    <div
                      key={index}
                      className={`chat-message ${message.role}`}
                    >
                      <div className="message-label">
                        {message.role === "agent"
                          ? "GLOBAL RAILS AGENT"
                          : "YOU"}
                      </div>

                      <div className="message-text">
                        {linkify(message.text)}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="chat-suggestions">
                  <button
                    onClick={() =>
                      applySuggestion(
                        "What's the current USDC to KES rate?"
                      )
                    }
                  >
                    What's the USDC/KES rate?
                  </button>

                  <button
                    onClick={() =>
                      applySuggestion(
                        "Swap 100 USDT to USDC"
                      )
                    }
                  >
                    Swap 100 USDT
                  </button>

                  <button
                    onClick={() =>
                      applySuggestion(
                        "Send 20 USDC to M-Pesa"
                      )
                    }
                  >
                    Send to M-Pesa
                  </button>

                  <button
                    onClick={() =>
                      applySuggestion(
                        "Pay the x402 request"
                      )
                    }
                  >
                    Pay x402 request
                  </button>
                </div>

                <div className="large-chat-input">
                  <input
                    type="text"
                    value={input}
                    onChange={(event) =>
                      setInput(event.target.value)
                    }
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        sendMessage();
                      }
                    }}
                    placeholder="Tell your agent what you want to do..."
                  />

                  <button onClick={sendMessage}>
                    ↑
                  </button>
                </div>

                <p className="input-hint">
                  Press Enter to send · Your agent executes
                  financial tools through MCP
                </p>
              </div>

              <aside className="tool-panel">
                <div className="tool-panel-title">
                  <span className="card-label">
                    AGENT CAPABILITIES
                  </span>

                  <h3>Available tools</h3>
                </div>

                <div className="tool">
                  <div className="tool-icon">◈</div>

                  <div>
                    <strong>fetch_price</strong>
                    <span>Market data oracle</span>
                  </div>

                  <i>Ready</i>
                </div>

                <div className="tool">
                  <div className="tool-icon">⇄</div>

                  <div>
                    <strong>swap</strong>
                    <span>Token exchange</span>
                  </div>

                  <i>Ready</i>
                </div>

                <div className="tool">
                  <div className="tool-icon">↗</div>

                  <div>
                    <strong>transfer</strong>
                    <span>Stablecoin settlement</span>
                  </div>

                  <i>Ready</i>
                </div>

                <div className="tool">
                  <div className="tool-icon">₿</div>

                  <div>
                    <strong>x402</strong>
                    <span>Agent-to-agent payments</span>
                  </div>

                  <i>Ready</i>
                </div>

                <div className="execution-card">
                  <span className="card-label">
                    LAST EXECUTION
                  </span>

                  {activities.length === 0 ? (
                    <>
                      <strong>No executions yet</strong>
                      <span>Your agent activity will appear here.</span>
                    </>
                  ) : (
                    <>
                      <strong>{activities[0].title}</strong>
                      <span>{activities[0].amount}</span>
                    </>
                  )}
                </div>
              </aside>
            </div>
          </section>
        ) : activePage === "Market Data" ? (
          <MarketDataPage onExecuted={logActivity} />
        ) : activePage === "Wallet" ? (
          <WalletPage />
        ) : activePage === "Swap" ? (
          <SwapPage onExecuted={logActivity} />
        ) : activePage === "Transfer" ? (
          <TransferPage onExecuted={logActivity} />
        ) : activePage === "x402 Payments" ? (
          <X402Page onExecuted={logActivity} />
        ) : activePage === "Activity" ? (
          <ActivityPage activities={activities} />
        ) : activePage === "Developer" ? (
          <DeveloperPage />
        ) : (
          <section className="content">
            <div className="balance-card">
              <div>
                <span className="card-label">
                  TOTAL PORTFOLIO (DEMO)
                </span>

                <h3>$1,248.32</h3>

                <span className="demo-note">
                  Demo balances — connect a wallet for live figures
                </span>
              </div>

              <div className="balance-assets">
                <div>
                  <span>USDC</span>
                  <strong>842.10</strong>
                </div>

                <div>
                  <span>USDT</span>
                  <strong>406.22</strong>
                </div>
              </div>
            </div>

            <div className="grid">
              <div className="card">
                <div className="card-heading">
                  <div>
                    <span className="card-label">
                      MARKET DATA
                    </span>

                    <h3>USDC / KES</h3>
                  </div>

                  <span className="live">● LIVE</span>
                </div>

                <div className="rate">
                  <strong>{overviewRate ? overviewRate.rate : overviewRateError ? "—" : "…"}</strong>
                  <span>KES</span>
                </div>

                <div className="rate-footer">
                  <span>1 USDC</span>
                  <span>
                    {overviewRate
                      ? "Updated just now"
                      : overviewRateError
                        ? "Rate temporarily unavailable"
                        : "Loading…"}
                  </span>
                </div>
              </div>

              <div className="card">
                <div className="card-heading">
                  <div>
                    <span className="card-label">
                      RECENT ACTIVITY
                    </span>

                    <h3>Latest executions</h3>
                  </div>
                </div>

                {activities.length === 0 ? (
                  <p className="empty-state">
                    Nothing yet — try a quick-reply in the AI Agent tab, or
                    run a swap/transfer/x402 payment from their pages.
                  </p>
                ) : (
                  activities.slice(0, 3).map((item) => (
                    <div className="activity" key={item.id}>
                      <div className="activity-icon">{item.icon}</div>

                      <div>
                        <strong>{item.title}</strong>
                        <span>{item.detail}</span>
                      </div>

                      <b>{item.amount}</b>
                    </div>
                  ))
                )}
              </div>
            </div>

            <section className="dashboard-agent">
              <div>
                <div className="dashboard-agent-icon">
                  ✦
                </div>

                <span className="card-label">
                  AI FINANCIAL AGENT
                </span>

                <h3>Your autonomous financial assistant</h3>

                <p>
                  Ask Global Rails to check rates, swap tokens,
                  transfer funds or handle an x402 payment.
                </p>
              </div>

              <button
                className="open-agent-button"
                onClick={() => setActivePage("AI Agent")}
              >
                Open AI Agent →
              </button>
            </section>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;