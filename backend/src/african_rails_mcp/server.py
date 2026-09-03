import asyncio
import os
import sys

import httpx
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from .prices.tool import get_token_prices, list_supported_tokens
from .onchain.tool import check_balance, send_transaction, get_tx_status, list_supported_chains
from .swaps.tool import quote_swap, execute_swap
from .x402.tool import fetch_paid_resource, check_x402_price, get_x402_wallet_info
from .dashboard import HTML

mcp = FastMCP(
    name="african-rails-mcp",
    instructions=(
        "African Rails MCP - Blockchain payment infrastructure for AI agents operating "
        "in African markets. Provides price feeds, EVM transactions on Ethereum and Celo "
        "(including cKES, cUSD stablecoins), DEX swaps via Uniswap V3 and Mento, "
        "and autonomous x402 micropayment handling. "
        "Designed for agent-triggered settlement without human-in-the-loop confirmation."
    ),
)

# --- Price tools ---
mcp.add_tool(get_token_prices)
mcp.add_tool(list_supported_tokens)

# --- On-chain tools ---
mcp.add_tool(check_balance)
mcp.add_tool(send_transaction)
mcp.add_tool(get_tx_status)
mcp.add_tool(list_supported_chains)

# --- Swap tools ---
mcp.add_tool(quote_swap)
mcp.add_tool(execute_swap)

# --- x402 tools ---
mcp.add_tool(fetch_paid_resource)
mcp.add_tool(check_x402_price)
mcp.add_tool(get_x402_wallet_info)


# ---------------------------------------------------------------------------
# REST routes for the dashboard UI — same logic as frontend/app.py's Flask
# routes (ported to async Starlette handlers so they live on this same
# deployed app, the same pattern used to fix the Global-Rails main branch).
# frontend/app.py itself is unaffected and still works standalone locally;
# these are separate handlers with the same behavior, not a replacement.
# ---------------------------------------------------------------------------

@mcp.custom_route("/", methods=["GET"])
async def dashboard(request: Request) -> HTMLResponse:
    return HTMLResponse(HTML)


@mcp.custom_route("/api/config", methods=["POST"])
async def set_config(request: Request) -> JSONResponse:
    data = await request.json()
    if data.get("private_key"):
        os.environ["PRIVATE_KEY"] = data["private_key"]
    if data.get("wallet_address"):
        os.environ["WALLET_ADDRESS"] = data["wallet_address"]
    # Purge every african_rails_mcp module from Python's import cache so the
    # next call re-reads the new env vars — see frontend/app.py's identical
    # comment for why a plain config reload isn't enough. NOTE: on Vercel,
    # a later request may land on a different warm instance that never saw
    # this call at all — this in-memory approach is carried over as-is from
    # the local Flask version, not something new added here.
    for key in list(sys.modules.keys()):
        if "african_rails_mcp" in key:
            del sys.modules[key]
    return JSONResponse({"ok": True, "wallet": data.get("wallet_address", "")})


@mcp.custom_route("/api/prices", methods=["POST"])
async def prices_route(request: Request) -> JSONResponse:
    data = await request.json()
    result = await get_token_prices(data["symbols"], data.get("currencies", ["usd"]))
    return JSONResponse(result)


@mcp.custom_route("/api/tokens", methods=["GET"])
async def tokens_route(request: Request) -> JSONResponse:
    from .prices.constants import SUPPORTED_SYMBOLS
    return JSONResponse({"tokens": SUPPORTED_SYMBOLS})


@mcp.custom_route("/api/chains", methods=["GET"])
async def chains_route(request: Request) -> JSONResponse:
    from .onchain.constants import CHAINS
    result = {}
    for name, cfg in CHAINS.items():
        result[name] = {
            "chain_id": cfg["chain_id"],
            "native_symbol": cfg["native_symbol"],
            "tokens": ["native"] + list(cfg.get("tokens", {}).keys()),
            "explorer": cfg["block_explorer"],
        }
    return JSONResponse(result)


@mcp.custom_route("/api/balance", methods=["POST"])
async def balance_route(request: Request) -> JSONResponse:
    data = await request.json()
    result = await check_balance(
        address=data.get("address", ""),
        chain=data.get("chain", "celo"),
        token=data.get("token", "native"),
    )
    return JSONResponse(result)


@mcp.custom_route("/api/send", methods=["POST"])
async def send_route(request: Request) -> JSONResponse:
    data = await request.json()
    result = await send_transaction(
        to=data["to"],
        amount=data["amount"],
        chain=data.get("chain", "celo"),
        token=data.get("token", "native"),
    )
    return JSONResponse(result)


@mcp.custom_route("/api/tx", methods=["POST"])
async def tx_status_route(request: Request) -> JSONResponse:
    data = await request.json()
    result = await get_tx_status(
        tx_hash=data["tx_hash"],
        chain=data.get("chain", "celo"),
    )
    return JSONResponse(result)


@mcp.custom_route("/api/quote", methods=["POST"])
async def quote_route(request: Request) -> JSONResponse:
    data = await request.json()
    result = await quote_swap(
        token_in=data["token_in"],
        token_out=data["token_out"],
        amount_in=data["amount_in"],
        chain=data.get("chain", "celo"),
        prefer_mento=data.get("prefer_mento", True),
    )
    return JSONResponse(result)


@mcp.custom_route("/api/swap", methods=["POST"])
async def swap_route(request: Request) -> JSONResponse:
    data = await request.json()
    result = await execute_swap(
        token_in=data["token_in"],
        token_out=data["token_out"],
        amount_in=data["amount_in"],
        chain=data.get("chain", "celo"),
        slippage_pct=float(data.get("slippage_pct", 0.5)),
        prefer_mento=data.get("prefer_mento", True),
    )
    return JSONResponse(result)


@mcp.custom_route("/api/x402/price", methods=["POST"])
async def x402_price_route(request: Request) -> JSONResponse:
    data = await request.json()
    result = await check_x402_price(data["url"])
    return JSONResponse(result)


@mcp.custom_route("/api/x402/fetch", methods=["POST"])
async def x402_fetch_route(request: Request) -> JSONResponse:
    data = await request.json()
    result = await fetch_paid_resource(
        url=data["url"],
        method=data.get("method", "GET"),
        body=data.get("body"),
        max_spend_usd=float(data.get("max_spend_usd", 0.10)),
    )
    return JSONResponse(result)


@mcp.custom_route("/api/x402/wallet", methods=["GET"])
async def x402_wallet_route(request: Request) -> JSONResponse:
    result = await get_x402_wallet_info()
    return JSONResponse(result)


@mcp.custom_route("/api/ai/chat", methods=["POST"])
async def ai_chat_route(request: Request) -> JSONResponse:
    """Proxy LLM chat completions server-side (bring-your-own-key) to avoid
    CORS and keep the user's API key out of the browser's own network calls
    to a third party. Same behavior as frontend/app.py's Flask version,
    using httpx's async client instead of blocking requests since this
    handler is itself async."""
    data = await request.json()
    endpoint = data.get("endpoint", "https://api.openai.com/v1").rstrip("/")
    api_key = data.get("api_key", "")
    model = data.get("model", "gpt-4o-mini")
    messages = data.get("messages", [])
    temperature = float(data.get("temperature", 0.7))

    if not api_key:
        return JSONResponse({"error": {"message": "No API key provided"}}, status_code=400)

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{endpoint}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 800,
                    "stream": False,
                },
            )
            return JSONResponse(resp.json(), status_code=resp.status_code)
    except httpx.TimeoutException:
        return JSONResponse({"error": {"message": "LLM request timed out after 60s"}}, status_code=504)
    except Exception as e:
        return JSONResponse({"error": {"message": str(e)}}, status_code=500)


# --- Vercel ASGI entrypoint ---
app = mcp.http_app()


def main():
    mcp.run()


if __name__ == "__main__":
    main()   
