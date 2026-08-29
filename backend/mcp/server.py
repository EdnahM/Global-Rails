from __future__ import annotations
import sys
import os

# Adds project root (Global-Rails) to Python's import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import logging
from mcp.server.fastmcp import FastMCP
from backend.mcp import config
from backend.mcp.adapter import register_toolkit 
try:
    from backend import TOOLKIT
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Could not import TOOLKIT from backend/__init__.py. Make sure "
        "backend/__init__.py exports the combined list (or dict) of tool "
        "instances, e.g.:\n\n"
        "    from .fetch_price.tool import fetch_price_tool\n"
        "    from .swap.tool import swap_tool\n"
        "    from .transfer.tool import transfer_tool\n"
        "    from .off_ramp.tool import off_ramp_tool\n"
        "    from .x402.tool import x402_get_invoice_tool, x402_settle_invoice_tool\n\n"
        "    TOOLKIT = [fetch_price_tool, swap_tool, transfer_tool, off_ramp_tool,\n"
        "               x402_get_invoice_tool, x402_settle_invoice_tool]"
    ) from exc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.mcp.server")

mcp = FastMCP(config.MCP_SERVER_NAME, host=config.MCP_HOST, port=config.MCP_PORT)

_toolkit_items = TOOLKIT.values() if isinstance(TOOLKIT, dict) else TOOLKIT
_registered = register_toolkit(mcp, _toolkit_items)
logger.info("Registered %d MCP tools: %s", len(_registered), ", ".join(_registered))


app = mcp.http_app(path="/api/mcp")

def main() -> None:
    mcp.run(transport=config.MCP_TRANSPORT)


if __name__ == "__main__":
    main()
