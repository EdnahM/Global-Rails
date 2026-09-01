import { useState } from "react";
import { callTool } from "../api";

const TOKENS = ["USDC", "USDT"];

function TransferPage({ onExecuted }) {
  const [toAddress, setToAddress] = useState("");
  const [token, setToken] = useState("USDC");
  const [amount, setAmount] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const canSubmit = toAddress.trim().length > 0 && amount && !loading;

  const runTransfer = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await callTool("transfer", {
        to_address: toAddress.trim(),
        token,
        amount: parseFloat(amount),
      });

      if (res.success) {
        setResult(res.data);
        onExecuted({
          icon: "↗",
          title: "Transfer",
          detail: `To ${res.data.to_address.slice(0, 10)}...`,
          amount: `-${res.data.amount} ${res.data.token}`,
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
        Send stablecoins on-chain via the transfer tool, gas settled in a
        fixed amount of USDC through the paymaster — no native gas token
        needed.
      </p>

      <div className="card">
        <div className="card-heading">
          <div>
            <span className="card-label">STABLECOIN SETTLEMENT</span>
            <h3>Send funds</h3>
          </div>
        </div>

        <div className="form-row">
          <label className="form-field" style={{ flexBasis: "100%" }}>
            <span>Destination address</span>
            <input
              type="text"
              placeholder="0x..."
              value={toAddress}
              onChange={(event) => setToAddress(event.target.value)}
            />
          </label>
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
            <span>Amount</span>
            <input
              type="number"
              min="0"
              step="any"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
            />
          </label>

          <button className="primary-button" onClick={runTransfer} disabled={!canSubmit}>
            {loading ? "Sending..." : "Send"}
          </button>
        </div>

        {error && <p className="form-error">Transfer failed: {error}</p>}

        {result && (
          <div className="result-card">
            <div className="result-row">
              <span>Status</span>
              <span>{result.status}</span>
            </div>
            <div className="result-row">
              <span>Sent</span>
              <span>{result.amount} {result.token}</span>
            </div>
            <div className="result-row">
              <span>To</span>
              <span>{result.to_address}</span>
            </div>
            <div className="result-row">
              <span>Gas (paymaster)</span>
              <span>{result.gas_fee_usdc} USDC</span>
            </div>
            <div className="result-row">
              <span>Chain</span>
              <span>{result.chain}</span>
            </div>
            <div className="result-row">
              <span>Tx hash</span>
              <span>{result.tx_hash}</span>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

export default TransferPage;
