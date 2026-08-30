"""Global Rails backend toolkit.

Exports the unified 'TOOLKIT' of tool instances consumed by the MCP layer
(backend/rails_mcp/) and any LangChain/CrewAI/agent host. Each tool follows
the shared contract in backend/interface.py: 'name', 'description',
'input_schema' (pydantic), and 'execute()' returning a 'ToolResult'.

The MCP adapter auto-discovers and registers every tool listed here — adding
a new tool means (1) implementing it in a folder under backend/ and (2)
listing its instance in 'TOOLKIT'. No MCP code needs to change.

Tool domains and their roles:
  * fetch_price  - token/fiat prices, multi-chain
  * transfer     - send stablecoins on-chain (fixed USDC gas via paymaster)
  * swap         - on-chain token swap, multi-chain
  * off_ramp     - last-mile fiat payout to mobile money (M-Pesa / MoMo)
  * x402         - HTTP 402 agent paywalls (get_invoice + settle_invoice)

NOTE on imports: this file is deliberately NOT backend/__init__.py. On
Vercel, vercel.json sets "root": "backend" for this service, which means
Vercel deploys the *contents* of backend/ flattened to the function's own
root directory — backend/toolkit.py becomes /var/task/toolkit.py, backend/
itself is never an importable package name in that environment, and nothing
imports a bare package root by name. Putting this logic in __init__.py
would make it unreachable once deployed. Every internal import below (and
throughout backend/) is a bare top-level import for the same reason — see
the comment in backend/interface.py for the fuller explanation.
"""

from fetch_price.tool import fetch_price_tool
from transfer.tool import transfer_tool
from swap.tool import swap_tool
from off_ramp.tool import off_ramp_tool
from x402.tool import (
    x402_get_invoice_tool,
    x402_settle_invoice_tool,
)

TOOLKIT = {
    "fetch_market_price": fetch_price_tool,
    "transfer": transfer_tool,
    "swap_tokens": swap_tool,
    "off_ramp_payout": off_ramp_tool,
    "x402_get_invoice": x402_get_invoice_tool,
    "x402_settle_invoice": x402_settle_invoice_tool,
}

__all__ = ["TOOLKIT"]