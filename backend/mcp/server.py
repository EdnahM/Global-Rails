"""Entry point for the MCP layer.

Run with:
    python -m backend.mcp.server
        -> stdio transport (default) — use this for Claude Desktop / Claude Code

    MCP_TRANSPORT=streamable-http python -m backend.mcp.server
        -> runs as a remote/host-able MCP server on MCP_HOST:MCP_PORT

This module does not implement any tool logic. It imports the already-built
unified toolkit from backend/__init__.py and exposes each tool over MCP.
"""
from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from . import config
from .adapter import register_toolkit

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
        "    from .x402.tool import x402_tool\n\n"
        "    TOOLKIT = [fetch_price_tool, swap_tool, transfer_tool, x402_tool]"
    ) from exc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.mcp.server")

mcp = FastMCP(config.MCP_SERVER_NAME, host=config.MCP_HOST, port=config.MCP_PORT)

_toolkit_items = TOOLKIT.values() if isinstance(TOOLKIT, dict) else TOOLKIT
_registered = register_toolkit(mcp, _toolkit_items)
logger.info("Registered %d MCP tools: %s", len(_registered), ", ".join(_registered))


def main() -> None:
    mcp.run(transport=config.MCP_TRANSPORT)


if __name__ == "__main__":
    main()
