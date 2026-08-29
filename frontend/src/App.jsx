import { useState } from "react";
import "./App.css";

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

  try {
    const response = await fetch("http://localhost:8000/tool/fetch_market_price", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token: "USDC",
        quote: "KES",
      }),
    });

    const result = await response.json();

    let agentText;

    if (result.success) {
      agentText = `USDC/KES market data: ${JSON.stringify(result.data)}`;
    } else {
      agentText = `I couldn't fetch the market price: ${result.error || "Unknown error"}`;
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
                      useSuggestion(
                        "What's the current USDC to KES rate?"
                      )
                    }
                  >
                    What's the USDC/KES rate?
                  </button>

                  <button
                    onClick={() =>
                      useSuggestion(
                        "Swap 100 USDT to USDC"
                      )
                    }
                  >
                    Swap 100 USDT
                  </button>

                  <button
                    onClick={() =>
                      useSuggestion(
                        "Send 20 USDC to M-Pesa"
                      )
                    }
                  >
                    Send to M-Pesa
                  </button>

                  <button
                    onClick={() =>
                      useSuggestion(
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