import { useState } from "react";
import { callTool } from "../api";

// Matches what's actually configured on avalanche-fuji (chains.py) — USDT
// was never in that token set, so offering it here would fail outright.
const TOKENS = ["USDC", "LINK", "AVAX"];

function SwapPage({ onExecuted }) {
  const [fromToken, setFromToken] = useState("USDC");
  const [toToken, setToToken] = useState("LINK");
  const [amount, setAmount] = useState("10");
  const [slippage, setSlippage] = useState("0.5");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const runSwap = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await callTool("swap_tokens", {
        from_token: fromToken,
        to_token: toToken,
        amount: parseFloat(amount),
        slippage: parseFloat(slippage),
        // avalanche-fuji is the only chain with real execution wired up
        // right now (see backend/swap/client.py) — previously no chain
        // was sent at all, silently falling through to the tool's own
        // mainnet default, which is always simulated regardless of what
        // was picked here.
        chain: "avalanche-fuji",
      });

      if (res.success) {
        setResult(res.data);
        onExecuted({
          icon: "⇄",
          title: "Token Swap",
          detail: `${res.data.from_token} → ${res.data.to_token}`,
          amount: `+${res.data.amount_out} ${res.data.to_token}`,
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
        Swap one token for another on-chain via the swap_tokens tool — this
        calls the same backend the AI Agent uses, directly, no chat required.
      </p>

      <div className="card">
        <div className="card-heading">
          <div>
            <span className="card-label">TOKEN EXCHANGE</span>
            <h3>Swap tokens</h3>
          </div>
        </div>

        <div className="form-row">
          <label className="form-field">
            <span>From</span>
            <select value={fromToken} onChange={(event) => setFromToken(event.target.value)}>
              {TOKENS.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </label>

          <label className="form-field">
            <span>To</span>
            <select value={toToken} onChange={(event) => setToToken(event.target.value)}>
              {TOKENS.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </label>

          <label className="form-field">
            <span>Amount</span>
            <input
              type="number"
              min="0"
              step="any"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
            />
          </label>

          <label className="form-field">
            <span>Slippage %</span>
            <input
              type="number"
              min="0"
              step="0.1"
              value={slippage}
              onChange={(event) => setSlippage(event.target.value)}
            />
          </label>

          <button
            className="primary-button"
            onClick={runSwap}
            disabled={loading || fromToken === toToken || !amount}
          >
            {loading ? "Swapping..." : "Swap"}
          </button>
        </div>

        {fromToken === toToken && (
          <p className="form-error">Pick two different tokens.</p>
        )}

        {error && <p className="form-error">Swap failed: {error}</p>}

        {result && (
          <div className="result-card">
            <div className="result-row">
              <span>Status</span>
              <span>{result.status}</span>
            </div>
            <div className="result-row">
              <span>Sent</span>
              <span>{result.amount_in} {result.from_token}</span>
            </div>
            <div className="result-row">
              <span>Received</span>
              <span>{result.amount_out} {result.to_token}</span>
            </div>
            <div className="result-row">
              <span>Slippage tolerance</span>
              <span>{result.slippage_tolerance}</span>
            </div>
            <div className="result-row">
              <span>Chain</span>
              <span>{result.chain}</span>
            </div>
            <div className="result-row">
              <span>Tx hash</span>
              <span>{result.tx_hash}</span>
            </div>
            {result.explorer_url && (
              <div className="result-row">
                <span>Verify</span>
                <a href={result.explorer_url} target="_blank" rel="noopener noreferrer" className="msg-link">{result.explorer_url}</a>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

export default SwapPage;
