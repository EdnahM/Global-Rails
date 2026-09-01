import { useState } from "react";
import { callTool } from "../api";

const TOKENS = ["USDC", "USDT", "AVAX", "ETH", "POL"];
const QUOTES = ["USD", "KES", "NGN", "GHS", "USDT", "USDC"];

function MarketDataPage({ onExecuted }) {
  const [token, setToken] = useState("USDC");
  const [quote, setQuote] = useState("KES");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const getRate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await callTool("fetch_market_price", { token, quote });

      if (res.success) {
        setResult(res.data);
        onExecuted({
          icon: "◈",
          title: "Market Data",
          detail: `${res.data.token} / ${res.data.quote}`,
          amount: `${res.data.rate} ${res.data.quote}`,
        });
      } else {
        setError(res.error || "Unknown error");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="content">
      <p className="page-intro">
        Real-time fiat-to-crypto and token-to-token pricing via the
        fetch_market_price tool — the same oracle the AI Agent uses when you
        ask it for a rate.
      </p>

      <div className="card">
        <div className="card-heading">
          <div>
            <span className="card-label">MARKET DATA ORACLE</span>
            <h3>Check a live rate</h3>
          </div>
        </div>

        <div className="form-row">
          <label className="form-field">
            <span>Token</span>
            <select value={token} onChange={(event) => setToken(event.target.value)}>
              {TOKENS.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </label>

          <label className="form-field">
            <span>Quote</span>
            <select value={quote} onChange={(event) => setQuote(event.target.value)}>
              {QUOTES.map((q) => (
                <option key={q} value={q}>{q}</option>
              ))}
            </select>
          </label>

          <button className="primary-button" onClick={getRate} disabled={loading}>
            {loading ? "Checking..." : "Get rate"}
          </button>
        </div>

        {error && <p className="form-error">Couldn't fetch that rate: {error}</p>}

        {result && (
          <div className="rate">
            <strong>{result.rate}</strong>
            <span>
              {result.quote} per {result.token} · {result.chain}
            </span>
          </div>
        )}
      </div>
    </section>
  );
}

export default MarketDataPage;
