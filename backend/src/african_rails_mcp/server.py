import asyncio
from fastmcp import FastMCP

from .prices.tool import get_token_prices, list_supported_tokens
from .onchain.tool import check_balance, send_transaction, get_tx_status, list_supported_chains
from .swaps.tool import quote_swap, execute_swap
from .x402.tool import fetch_paid_resource, check_x402_price, get_x402_wallet_info

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


# --- Vercel ASGI entrypoint ---
app = mcp.http_app()


def main():
    mcp.run()


if __name__ == "__main__":
    main()   
