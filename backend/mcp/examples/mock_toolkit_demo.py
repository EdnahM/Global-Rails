"""Standalone sanity check for the adapter — no real backend needed.

Run:
    python -m backend.mcp.examples.mock_toolkit_demo

This spins up a FastMCP server in-process with two mock tools (mirroring
the shape fetch_price and swap would have), registers them via the same
adapter.register_toolkit used in server.py, and calls list_tools()/
call_tool() directly to prove the wiring works end to end.
"""
import asyncio

from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP

from backend.mcp.adapter import register_toolkit


class FetchPriceInput(BaseModel):
    base: str
    quote: str = "USD"


class MockFetchPriceTool:
    name = "fetch_price"
    description = "Fetch the current exchange rate between two assets."
    input_schema = FetchPriceInput

    async def run(self, base: str, quote: str = "USD"):
        # stand-in for client.py hitting CoinGecko/Binance/Kotani
        return {"base": base, "quote": quote, "price": 1.0, "source": "mock"}


class SwapInput(BaseModel):
    from_token: str
    to_token: str
    amount: float


class MockSwapTool:
    name = "swap"
    description = "Swap one token for another via a DEX/aggregator."
    input_schema = SwapInput

    def run(self, from_token: str, to_token: str, amount: float):
        # stand-in for client.py's on-chain aggregator call
        return {
            "status": "simulated",
            "from_token": from_token,
            "to_token": to_token,
            "amount_in": amount,
        }


async def main() -> None:
    mcp = FastMCP("mock-toolkit-demo")
    registered = register_toolkit(mcp, [MockFetchPriceTool(), MockSwapTool()])
    print("Registered tools:", registered)

    tools = await mcp.list_tools()
    print("MCP sees:", [t.name for t in tools])

    result = await mcp.call_tool("fetch_price", {"base": "USDC", "quote": "KES"})
    print("fetch_price ->", result)

    result = await mcp.call_tool(
        "swap", {"from_token": "USDC", "to_token": "USDT", "amount": 25.0}
    )
    print("swap ->", result)


if __name__ == "__main__":
    asyncio.run(main())
