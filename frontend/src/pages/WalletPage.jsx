// There's no get_balance tool in the backend yet — TOOLKIT only exposes
// fetch_market_price, transfer, swap_tokens, off_ramp_payout, and the x402
// pair (see backend/__init__.py). Wallet holdings shown here are the same
// demo figures as the Overview page. When a real balance tool exists, swap
// this static array for a callTool("get_balance", {}) call.
const HOLDINGS = [
  { symbol: "USDC", amount: "842.10", usdValue: "842.10" },
  { symbol: "USDT", amount: "406.22", usdValue: "406.22" },
];

function WalletPage() {
  const total = HOLDINGS.reduce((sum, h) => sum + parseFloat(h.usdValue), 0);

  return (
    <section className="content">
      <p className="page-intro">
        Demo balances on Avalanche testnet. There's no balance-reading tool
        wired up in the backend yet — this reflects the same figures shown
        on Overview, not a live wallet query.
      </p>

      <div className="balance-card">
        <div>
          <span className="card-label">TOTAL PORTFOLIO</span>
          <h3>${total.toFixed(2)}</h3>
          <span className="positive">Testnet · Avalanche C-Chain</span>
        </div>
      </div>

      <div className="wallet-assets">
        {HOLDINGS.map((h) => (
          <div className="wallet-asset" key={h.symbol}>
            <span>{h.symbol}</span>
            <strong>{h.amount}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

export default WalletPage;
