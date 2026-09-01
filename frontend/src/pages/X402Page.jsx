import { useState } from "react";
import { callTool } from "../api";

function X402Page({ onExecuted }) {
  const [url, setUrl] = useState("https://example.com/protected-resource");
  const [token, setToken] = useState("USDC");
  const [amount, setAmount] = useState("1.0");

  const [invoice, setInvoice] = useState(null);
  const [proof, setProof] = useState(null);
  const [error, setError] = useState(null);
  const [loadingStep, setLoadingStep] = useState(null); // "invoice" | "settle" | null

  const getInvoice = async () => {
    setLoadingStep("invoice");
    setError(null);
    setInvoice(null);
    setProof(null);

    try {
      const res = await callTool("x402_get_invoice", {
        url,
        token,
        amount: parseFloat(amount),
      });

      if (res.success) {
        setInvoice(res.data);
      } else {
        setError(res.error || "Unknown error");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingStep(null);
    }
  };

  const settle = async () => {
    if (!invoice) return;
    setLoadingStep("settle");
    setError(null);

    try {
      const res = await callTool("x402_settle_invoice", {
        invoice_id: invoice.invoice_id,
      });

      if (res.success) {
        setProof(res.data);
        onExecuted({
          icon: "₿",
          title: "x402 Payment",
          detail: new URL(url).hostname,
          amount: `-${invoice.amount} ${invoice.token}`,
        });
      } else {
        setError(res.error || "Unknown error");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingStep(null);
    }
  };

  return (
    <section className="content">
      <p className="page-intro">
        L402 / HTTP 402 agent-to-agent payments, split into two steps so you
        see the cost before paying: resolve a 402 challenge into an invoice,
        then settle it for proof of payment.
      </p>

      <div className="card">
        <div className="card-heading">
          <div>
            <span className="card-label">AGENT-TO-AGENT PAYMENTS</span>
            <h3>1. Resolve a 402 challenge</h3>
          </div>
        </div>

        <div className="form-row">
          <label className="form-field" style={{ flexBasis: "100%" }}>
            <span>Resource URL</span>
            <input
              type="text"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
            />
          </label>
        </div>

        <div className="form-row">
          <label className="form-field">
            <span>Token</span>
            <input
              type="text"
              value={token}
              onChange={(event) => setToken(event.target.value)}
            />
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

          <button className="primary-button" onClick={getInvoice} disabled={loadingStep !== null}>
            {loadingStep === "invoice" ? "Resolving..." : "Get invoice"}
          </button>
        </div>

        {error && <p className="form-error">{error}</p>}

        {invoice && (
          <div className="result-card">
            <div className="result-row">
              <span>Invoice</span>
              <span>{invoice.invoice_id}</span>
            </div>
            <div className="result-row">
              <span>Amount due</span>
              <span>{invoice.amount} {invoice.token}</span>
            </div>
            <div className="result-row">
              <span>Chain</span>
              <span>{invoice.chain}</span>
            </div>
            <div className="result-row">
              <span>Status</span>
              <span>{proof ? "PAID" : invoice.status}</span>
            </div>
          </div>
        )}
      </div>

      {invoice && (
        <div className="card" style={{ marginTop: 18 }}>
          <div className="card-heading">
            <div>
              <span className="card-label">STEP 2</span>
              <h3>Settle the invoice</h3>
            </div>
          </div>

          {!proof ? (
            <button
              className="primary-button"
              style={{ marginTop: 18 }}
              onClick={settle}
              disabled={loadingStep !== null}
            >
              {loadingStep === "settle" ? "Paying..." : `Pay ${invoice.amount} ${invoice.token}`}
            </button>
          ) : (
            <div className="result-card">
              <div className="result-row">
                <span>Status</span>
                <span>{proof.status}</span>
              </div>
              <div className="result-row">
                <span>Payment hash</span>
                <span>{proof.payment_hash}</span>
              </div>
              <div className="result-row">
                <span>Auth header</span>
                <span>{proof.auth_header}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default X402Page;
