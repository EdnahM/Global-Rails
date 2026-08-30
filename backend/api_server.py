"""
African Rails MCP - HTTP REST API Server

Exposes all 11 MCP tools as REST endpoints with auto-generated OpenAPI docs.

Run:
    cd backend
    ../.venv/bin/python api_server.py

Docs:     http://localhost:8000/docs        (Swagger UI — try every endpoint)
Alt docs: http://localhost:8000/redoc       (ReDoc)
Health:   http://localhost:8000/health
Tools:    http://localhost:8000/tools
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn

# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="African Rails MCP API",
    description=(
        "REST API wrapper for the African Rails MCP server.\n\n"
        "Exposes all 11 MCP tools as HTTP endpoints for testing and integration.\n\n"
        "**Chains supported:** `ethereum`, `celo`, `celo-alfajores`, `avalanche`, `avalanche-fuji`\n\n"
        "**Configure wallet** via `POST /config` before calling send/swap endpoints."
    ),
    version="0.1.0",
    contact={"name": "African Rails"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────────────────────────────────────

class ConfigRequest(BaseModel):
    private_key: str = Field(..., description="EVM private key (0x-prefixed hex)")
    wallet_address: str = Field(..., description="EVM wallet address (0x-prefixed)")

class PricesRequest(BaseModel):
    symbols: list[str] = Field(
        default=["AVAX", "ETH", "USDC", "CELO"],
        description="Token symbols e.g. ['AVAX', 'ETH', 'cKES', 'cUSD']",
        examples=[["AVAX", "ETH", "cKES"]],
    )
    vs_currencies: list[str] = Field(
        default=["usd"],
        description="Quote currencies e.g. ['usd', 'kes', 'eur']",
    )

class BalanceRequest(BaseModel):
    address: str = Field(
        default="",
        description="EVM address to check (blank = configured wallet)",
    )
    chain: str = Field(default="avalanche-fuji", description="Chain name")
    token: str = Field(
        default="native",
        description="'native' for AVAX/ETH/CELO, or token symbol e.g. 'USDC', 'cKES'",
    )

class SendRequest(BaseModel):
    to: str = Field(..., description="Recipient EVM address")
    amount: str = Field(..., description="Amount as string e.g. '0.001'")
    chain: str = Field(default="avalanche-fuji", description="Chain name")
    token: str = Field(
        default="native",
        description="'native' or token symbol e.g. 'USDC', 'WAVAX'",
    )

class TxStatusRequest(BaseModel):
    tx_hash: str = Field(..., description="Transaction hash (0x-prefixed)")
    chain: str = Field(default="avalanche-fuji", description="Chain where tx was submitted")

class QuoteRequest(BaseModel):
    token_in: str = Field(..., description="Token to sell e.g. 'WAVAX'")
    token_out: str = Field(..., description="Token to buy e.g. 'USDC'")
    amount_in: str = Field(..., description="Amount to sell as string e.g. '1.0'")
    chain: str = Field(default="avalanche-fuji", description="Chain name")
    prefer_mento: bool = Field(
        default=True,
        description="Prefer Mento Broker on Celo for stablecoin pairs",
    )

class SwapRequest(BaseModel):
    token_in: str = Field(..., description="Token to sell e.g. 'WAVAX'")
    token_out: str = Field(..., description="Token to buy e.g. 'USDC'")
    amount_in: str = Field(..., description="Amount to sell as string e.g. '1.0'")
    chain: str = Field(default="avalanche-fuji", description="Chain name")
    slippage_pct: float = Field(default=0.5, description="Max slippage % (default 0.5)")
    prefer_mento: bool = Field(default=True, description="Prefer Mento on Celo")

class X402FetchRequest(BaseModel):
    url: str = Field(..., description="URL to fetch (may require x402 payment)")
    method: str = Field(default="GET", description="HTTP method")
    body: Optional[dict] = Field(default=None, description="JSON body for POST/PUT")
    max_spend_usd: float = Field(default=0.10, description="Max USD to spend per call")

class X402PriceRequest(BaseModel):
    url: str = Field(..., description="URL to check for x402 payment requirement")


# ─────────────────────────────────────────────────────────────────────────────
# Helper to reload modules when config changes
# ─────────────────────────────────────────────────────────────────────────────

def _purge_module_cache():
    for key in list(sys.modules.keys()):
        if "african_rails_mcp" in key:
            del sys.modules[key]


# ─────────────────────────────────────────────────────────────────────────────
# System endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"], summary="Health check")
async def health():
    """Returns OK if the server is running."""
    return {"status": "ok", "service": "african-rails-mcp-api"}


@app.get("/tools", tags=["System"], summary="List all available tools")
async def list_tools():
    """Returns all 11 MCP tools with their endpoint, method, and description."""
    return {
        "total": 11,
        "tools": [
            # Prices
            {"name": "get_token_prices",     "endpoint": "POST /prices",           "module": "prices",  "description": "Fetch live token prices from CoinGecko"},
            {"name": "list_supported_tokens","endpoint": "GET  /tokens",            "module": "prices",  "description": "List all supported token symbols"},
            # On-chain
            {"name": "check_balance",        "endpoint": "POST /balance",           "module": "onchain", "description": "Get native or ERC-20 balance for an address"},
            {"name": "send_transaction",     "endpoint": "POST /send",              "module": "onchain", "description": "Submit native or ERC-20 token transfer"},
            {"name": "get_tx_status",        "endpoint": "POST /tx/status",         "module": "onchain", "description": "Check confirmation status of a transaction"},
            {"name": "list_supported_chains","endpoint": "GET  /chains",            "module": "onchain", "description": "List supported chains and their tokens"},
            # Swaps
            {"name": "quote_swap",           "endpoint": "POST /swap/quote",        "module": "swaps",   "description": "Get price quote for a token swap (no execution)"},
            {"name": "execute_swap",         "endpoint": "POST /swap/execute",      "module": "swaps",   "description": "Execute a token swap via Mento or Uniswap V3"},
            # x402
            {"name": "fetch_paid_resource",  "endpoint": "POST /x402/fetch",        "module": "x402",    "description": "Fetch URL with automatic x402 micropayment handling"},
            {"name": "check_x402_price",     "endpoint": "POST /x402/price",        "module": "x402",    "description": "Check payment requirement of an x402-protected URL"},
            {"name": "get_x402_wallet_info", "endpoint": "GET  /x402/wallet",       "module": "x402",    "description": "Get wallet address and USDC balance for x402 payments"},
        ],
    }


@app.post(
    "/config",
    tags=["System"],
    summary="Configure wallet credentials",
    description=(
        "Set the private key and wallet address used for sending transactions, "
        "executing swaps, and x402 payments.\n\n"
        "⚠️ Only use this in a local dev/test environment. Never expose this endpoint publicly."
    ),
)
async def set_config(req: ConfigRequest):
    os.environ["PRIVATE_KEY"] = req.private_key
    os.environ["WALLET_ADDRESS"] = req.wallet_address
    _purge_module_cache()
    return {
        "ok": True,
        "wallet": req.wallet_address,
        "message": "Wallet configured. All subsequent calls will use these credentials.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Price endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post(
    "/prices",
    tags=["Prices"],
    summary="Fetch live token prices",
    description="Get real-time prices for one or more tokens from CoinGecko.",
)
async def get_prices(req: PricesRequest):
    from african_rails_mcp.prices.tool import get_token_prices
    return await get_token_prices(req.symbols, req.vs_currencies)


@app.get(
    "/tokens",
    tags=["Prices"],
    summary="List supported tokens",
    description="Returns all token symbols that can be used with `POST /prices`.",
)
async def list_tokens():
    from african_rails_mcp.prices.tool import list_supported_tokens
    return await list_supported_tokens()


# ─────────────────────────────────────────────────────────────────────────────
# On-chain endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get(
    "/chains",
    tags=["On-chain"],
    summary="List supported chains",
    description="Returns all supported blockchain networks with their native tokens and available ERC-20 tokens.",
)
async def list_chains():
    from african_rails_mcp.onchain.tool import list_supported_chains
    return await list_supported_chains()


@app.post(
    "/balance",
    tags=["On-chain"],
    summary="Check token balance",
    description=(
        "Get the native or ERC-20 token balance for any address.\n\n"
        "Leave `address` blank to check your configured wallet.\n\n"
        "Use `token: 'native'` for AVAX/ETH/CELO, or a token symbol like `'USDC'`, `'cKES'`."
    ),
)
async def check_balance(req: BalanceRequest):
    from african_rails_mcp.onchain.tool import check_balance
    return await check_balance(
        address=req.address,
        chain=req.chain,
        token=req.token,
    )


@app.post(
    "/send",
    tags=["On-chain"],
    summary="Send a transaction",
    description=(
        "Submit a native token or ERC-20 transfer.\n\n"
        "Returns `tx_hash` immediately — transaction may not be confirmed yet. "
        "Use `POST /tx/status` to poll for confirmation.\n\n"
        "Requires wallet configured via `POST /config`.\n\n"
        "**Testnet tip:** Use `native` (AVAX/CELO) instead of USDC to avoid blacklist errors."
    ),
)
async def send_tx(req: SendRequest):
    from african_rails_mcp.onchain.tool import send_transaction
    return await send_transaction(
        to=req.to,
        amount=req.amount,
        chain=req.chain,
        token=req.token,
    )


@app.post(
    "/tx/status",
    tags=["On-chain"],
    summary="Check transaction status",
    description="Poll the confirmation status of a submitted transaction. Returns `pending`, `confirmed`, or `failed`.",
)
async def tx_status(req: TxStatusRequest):
    from african_rails_mcp.onchain.tool import get_tx_status
    return await get_tx_status(
        tx_hash=req.tx_hash,
        chain=req.chain,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Swap endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post(
    "/swap/quote",
    tags=["Swaps"],
    summary="Get swap quote",
    description=(
        "Get a price quote for swapping one token to another. **No transaction is submitted.**\n\n"
        "On Celo, stablecoin pairs (`cUSD`, `cKES`, `cEUR`, `CELO`) automatically route "
        "through **Mento Broker** for better rates. All other pairs use **Uniswap V3** "
        "with automatic fee-tier selection."
    ),
)
async def quote_swap(req: QuoteRequest):
    from african_rails_mcp.swaps.tool import quote_swap
    return await quote_swap(
        token_in=req.token_in,
        token_out=req.token_out,
        amount_in=req.amount_in,
        chain=req.chain,
        prefer_mento=req.prefer_mento,
    )


@app.post(
    "/swap/execute",
    tags=["Swaps"],
    summary="Execute a token swap",
    description=(
        "Execute a token swap on-chain.\n\n"
        "Routing is automatic: Mento Broker for Celo stablecoin pairs, Uniswap V3 otherwise.\n\n"
        "Returns `tx_hash` immediately. Use `POST /tx/status` to confirm.\n\n"
        "Requires wallet configured via `POST /config`."
    ),
)
async def execute_swap(req: SwapRequest):
    from african_rails_mcp.swaps.tool import execute_swap
    return await execute_swap(
        token_in=req.token_in,
        token_out=req.token_out,
        amount_in=req.amount_in,
        chain=req.chain,
        slippage_pct=req.slippage_pct,
        prefer_mento=req.prefer_mento,
    )


# ─────────────────────────────────────────────────────────────────────────────
# x402 endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get(
    "/x402/wallet",
    tags=["x402"],
    summary="Get x402 wallet info",
    description=(
        "Returns the wallet address and USDC balances used for x402 micropayments.\n\n"
        "Check this before calling `POST /x402/fetch` to ensure sufficient funds."
    ),
)
async def x402_wallet():
    from african_rails_mcp.x402.tool import get_x402_wallet_info
    return await get_x402_wallet_info()


@app.post(
    "/x402/price",
    tags=["x402"],
    summary="Check x402 payment requirement",
    description=(
        "Inspect the payment requirement of an x402-protected URL **without paying**.\n\n"
        "Returns the price, accepted token, network, and facilitator address "
        "if the URL requires payment, or `payment_required: false` if it's free."
    ),
)
async def x402_price(req: X402PriceRequest):
    from african_rails_mcp.x402.tool import check_x402_price
    return await check_x402_price(url=req.url)


@app.post(
    "/x402/fetch",
    tags=["x402"],
    summary="Fetch x402-protected resource",
    description=(
        "Fetch an HTTP resource that may require an x402 micropayment.\n\n"
        "If the server returns `HTTP 402`, this tool automatically:\n"
        "1. Parses the payment requirement\n"
        "2. Creates an EIP-3009 off-chain payment signature (no gas needed)\n"
        "3. Retries the request with the `X-PAYMENT` header\n\n"
        "Use `max_spend_usd` to cap the maximum amount paid per request."
    ),
)
async def x402_fetch(req: X402FetchRequest):
    from african_rails_mcp.x402.tool import fetch_paid_resource
    return await fetch_paid_resource(
        url=req.url,
        method=req.method,
        body=req.body,
        max_spend_usd=req.max_spend_usd,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 8007))
    print(f"""
  African Rails MCP API
  ─────────────────────────────────
  Swagger UI  →  http://localhost:{port}/docs
  ReDoc       →  http://localhost:{port}/redoc
  Health      →  http://localhost:{port}/health
  Tools list  →  http://localhost:{port}/tools
  ─────────────────────────────────
""")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
