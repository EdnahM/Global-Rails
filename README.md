# African Rails MCP

Blockchain payment infrastructure for AI agents in African markets.

Mobile money APIs like Safaricom's Daraja are built around business KYC — a registered company, a KRA PIN, paybill documentation. That process assumes a human on the other end. African Rails removes that friction: autonomous agents trigger fiat settlement directly, without human-in-the-loop confirmation per transaction.

Built on Celo (cKES, cUSD, cEUR) and Ethereum, routing through Mento Broker and Uniswap V3, with x402 micropayment support.

---

## Project structure

```
blockchain-mcp/
├── backend/                  Python MCP server (African Rails core)
│   ├── pyproject.toml
│   ├── pytest.ini
│   ├── .env.example
│   ├── src/
│   │   └── african_rails_mcp/
│   │       ├── server.py     FastMCP entrypoint — 11 tools registered
│   │       ├── config.py     pydantic-settings, reads .env
│   │       ├── prices/       CoinGecko price feed
│   │       ├── onchain/      EVM transactions (Ethereum + Celo)
│   │       ├── swaps/        Mento Broker + Uniswap V3
│   │       └── x402/         HTTP 402 micropayment client
│   └── tests/
│       ├── conftest.py
│       ├── test_server.py
│       ├── test_prices.py
│       ├── test_onchain.py
│       ├── test_swaps.py
│       └── test_x402.py
└── frontend/                 Agent UI (in progress)
    └── app.py
```

---

## MCP tools

| Tool | Module | Description |
|------|--------|-------------|
| `get_token_prices` | prices | Live prices from CoinGecko (ETH, BTC, USDC, cKES, cUSD, CELO, ...) |
| `list_supported_tokens` | prices | All supported token symbols |
| `check_balance` | onchain | Native or ERC-20 balance for any address |
| `send_transaction` | onchain | Submit native (ETH/CELO) or ERC-20 transfer |
| `get_tx_status` | onchain | Poll confirmation status of a submitted transaction |
| `list_supported_chains` | onchain | Supported networks and their available tokens |
| `quote_swap` | swaps | Price quote for a token swap (read-only, no execution) |
| `execute_swap` | swaps | Execute a swap — auto-routes to Mento or Uniswap V3 |
| `fetch_paid_resource` | x402 | Fetch a URL, handling HTTP 402 micropayments automatically |
| `check_x402_price` | x402 | Inspect payment requirement without paying |
| `get_x402_wallet_info` | x402 | Wallet address and USDC balance for x402 payments |

### Swap routing

On Celo, swaps between `cUSD`, `cKES`, `cEUR`, `cBRL`, and `CELO` route through **Mento Broker** by default — zero price impact within bucket limits. All other pairs use **Uniswap V3** with automatic fee-tier selection (0.01% / 0.05% / 0.3% / 1%).

### x402

When a server returns `HTTP 402`, `fetch_paid_resource` constructs an EIP-3009 off-chain payment signature and retries — no separate on-chain transaction needed upfront. Call `check_x402_price` first to inspect the cost before committing.

---

## Supported networks

| Chain | Chain ID | Native | Stablecoins |
|-------|----------|--------|-------------|
| Celo mainnet | 42220 | CELO | cUSD, cKES, cEUR, cBRL, USDC, USDT |
| Ethereum mainnet | 1 | ETH | USDC, USDT, DAI, WETH, WBTC |
| Celo Alfajores (testnet) | 44787 | CELO | cUSD, cKES, cEUR |

---

## Backend setup

### Requirements

- Python 3.10+
- A funded EVM wallet

### Install

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Configure

```bash
cp .env.example .env
```

Minimum required in `.env`:

```env
PRIVATE_KEY=0xyour_private_key_here
WALLET_ADDRESS=0xyour_wallet_address_here
DEFAULT_CHAIN=celo
```

For testnet, fund at [faucet.celo.org](https://faucet.celo.org).

### Run the MCP server

```bash
african-rails-mcp
```

Runs over stdio (standard MCP transport). To connect from Claude Desktop:

```json
{
  "mcpServers": {
    "african-rails": {
      "command": "/path/to/blockchain-mcp/backend/.venv/bin/african-rails-mcp"
    }
  }
}
```

---

## Testing

### Test layers

| Marker | What it covers | Needs network |
|--------|---------------|---------------|
| `unit` | Pure logic, mocked HTTP + web3 calls | No |
| `integration` | Live RPC + CoinGecko free tier, read-only | Public internet |
| `e2e` | Real transactions on Celo Alfajores testnet | Funded testnet wallet |

By default, `pytest` runs only `unit` tests (e2e excluded via `pytest.ini`).

### Run unit tests

```bash
cd backend
pytest tests/
```

Expected output: **53 passed** across all modules.

### Run integration tests

These call live public RPCs and CoinGecko's free API (no wallet needed):

```bash
cd backend
pytest tests/ -m "unit or integration"
```

Integration tests verify:
- `check_balance` against known Celo Foundation address
- `get_token_prices` for ETH, cKES (checks ~$0.007–0.009 range), cUSD (checks peg near $1.00)
- `get_tx_status` against a historical Celo transaction
- `quote_swap` for cUSD→cKES via live Mento Broker

### Run e2e tests (testnet)

Requires a wallet funded with testnet CELO (get from [faucet.celo.org](https://faucet.celo.org)):

```bash
cd backend
export TEST_PRIVATE_KEY=0x...
export TEST_WALLET_ADDRESS=0x...
pytest tests/ -m e2e -v
```

E2E tests:
1. Checks wallet has enough CELO to run (fails fast with faucet link if not)
2. Sends a 0.0001 CELO self-transfer on Alfajores, polls for confirmation
3. Executes a cUSD→cKES swap via Mento on Alfajores, verifies confirmed status

### What each test file covers

| File | Tests | Key assertions |
|------|-------|---------------|
| `test_server.py` | 11 | All 11 tools registered, descriptions non-empty, server name |
| `test_prices.py` | 15 | cKES/cUSD symbol remapping, error on unknown token, live peg check |
| `test_onchain.py` | 17 | Wei→human conversion, tx status states, invalid chain/token errors, live balance, Alfajores send |
| `test_swaps.py` | 12 | Mento eligibility logic, Uniswap fallback, live cUSD→cKES quote |
| `test_x402.py` | 12 | 402 flow, private key not leaked, spend limit, wallet info structure |

---

## Frontend

The frontend (`frontend/app.py`) is the agent UI layer — currently a placeholder. It will communicate with the MCP server to provide a developer-facing interface for:

- Monitoring agent-triggered transactions
- Inspecting swap quotes before execution
- Viewing wallet balances and x402 payment history

The MCP server exposes all functionality over stdio; the frontend can connect either by spawning the MCP process directly or via an HTTP bridge (SSE transport). To switch the MCP server to HTTP mode, change `mcp.run()` in `server.py`:

```python
mcp.run(transport="sse", host="0.0.0.0", port=8000)
```

Then the frontend hits `http://localhost:8000` instead of stdin/stdout.

---

## Architecture notes

**Amount handling** — all token amounts use `Decimal` and string inputs. Never Python `float` to avoid wei precision loss.

**Nonce cache** — `onchain/transactions.py` maintains a per-address local nonce counter for rapid sequential agent sends without collisions.

**Celo POA** — `ExtraDataToPOAMiddleware` is injected automatically for Celo connections. Required or `get_block()` calls fail.

**Mento exchange discovery** — exchange provider addresses and IDs are fetched from the Mento Broker on first call and cached in-process.

---

## Fiat-to-stablecoin partners

African Rails wraps existing human-facing fiat rails for agent-triggered settlement:

- [Kotani Pay](https://kotanipay.com) — USSD wallet payouts
- [HoneyCoin](https://honeycoin.com) — stablecoin payments across Africa ($4.9M seed)
- [Swypt](https://swypt.io) — fiat-to-crypto on/off ramp
- [Eversend](https://eversend.co) — multi-currency wallet and transfers

---

## Business model

0.2–0.5% micro-transaction fee on agent-triggered settlements. Positioned as infrastructure — revenue weighted toward downstream adoption (developers adopting this as default) rather than maximising per-transaction margin.
