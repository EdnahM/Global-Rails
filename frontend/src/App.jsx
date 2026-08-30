import { useState } from "react";
import "./App.css";

// Maps a free-text request to one of the backend's registered tools plus its
// payload, and how to describe a successful result. This is a lightweight
// keyword/regex router, not an LLM call — it's what lets each quick-reply
// suggestion (and reasonable free-typed variants) actually hit a different
// tool instead of every message calling fetch_market_price regardless of
// what was typed. Swapping this for a real LLM tool-call later only means
// replacing the body of this function; sendMessage() and the fetch call
// don't need to change.
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
        `Swapped ${d.amount_in} ${d.from_token} for ${d.amount_out} ${d.to_token} on ${d.chain} (tx ${d.tx_hash.slice(0, 10)}...).`,
    };
  }

  // "Send 20 USDC to M-Pesa"
  if (/m-?pesa|momo|mobile money|off.?ramp|payout/i.test(text)) {
    const amountMatch = text.match(/([\d.]+)\s*([a-zA-Z]+)/);
    return {
      tool: "off_ramp_payout",
      payload: {
        amount: amountMatch ? parseFloat(amountMatch[1]) : 20,
        currency: "KES",
        phone_number: "254700000000", // demo recipient — testnet/simulated only
      },
      describe: (d) =>
        `Paid out ${d.amount_delivered} ${d.currency} to ${d.recipient} via ${d.network} (ref ${d.transaction_id}).`,
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

function App() {
  const [activePage, setActivePage] = useState("Overview");

  const [messages, setMessages] = useState([
    {
      role: "agent",
      text: "Hello. I'm your Global Rails financial agent. I can check market rates, swap tokens, transfer funds, and handle x402 payments.",
    },
  ]);

  const [input, setInput] = useState("");

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

  const { tool, payload, describe } = pickToolFromMessage(userText);

  try {
    // Relative path: routed to the backend service in both local dev
    // (via a dev proxy) and production (via the "/api" rewrite in
    // vercel.json) — a hardcoded localhost URL only ever works on one
    // machine.
    const response = await fetch(`/api/tool/${tool}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const result = await response.json();

    const agentText = result.success
      ? describe(result.data)
      : `I couldn't complete that (${tool}): ${result.error || "Unknown error"}`;

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

<<<<<<< Updated upstream
  const applySuggestion = (text) => {
=======
  const useSuggestion = (text) => {
>>>>>>> Stashed changes
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
          <div className="logo-mark">G</div>

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
                        {message.text}
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

                  <strong>No executions yet</strong>

                  <span>
                    Your agent activity will appear here.
                  </span>
                </div>
              </aside>
            </div>
          </section>
        ) : (
          <section className="content">
            <div className="balance-card">
              <div>
                <span className="card-label">
                  TOTAL PORTFOLIO
                </span>

                <h3>$1,248.32</h3>

                <span className="positive">
                  +2.84% today
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
                  <strong>129.42</strong>
                  <span>KES</span>
                </div>

                <div className="rate-footer">
                  <span>1 USDC</span>
                  <span>Updated just now</span>
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

                <div className="activity">
                  <div className="activity-icon">↗</div>

                  <div>
                    <strong>M-Pesa Transfer</strong>
                    <span>50 USDC · Kenya</span>
                  </div>

                  <b>-50 USDC</b>
                </div>

                <div className="activity">
                  <div className="activity-icon">⇄</div>

                  <div>
                    <strong>Token Swap</strong>
                    <span>100 USDT → USDC</span>
                  </div>

                  <b>+99.72 USDC</b>
                </div>

                <div className="activity">
                  <div className="activity-icon">₿</div>

                  <div>
                    <strong>x402 Payment</strong>
                    <span>API access</span>
                  </div>

                  <b>-0.02 USDC</b>
                </div>
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