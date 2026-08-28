"""Environment-driven config for the MCP layer only.

This is deliberately separate from any config your client.py files use for
CoinGecko/Binance/Kotani/HoneyCoin/RPC/x402 credentials — those stay exactly
where they are. This file only controls how the MCP server itself is
exposed.
"""
import os

MCP_SERVER_NAME = os.getenv("MCP_SERVER_NAME", "stablecoin-agent-toolkit")

# "stdio"            -> for Claude Desktop / Claude Code (local subprocess)
# "streamable-http"  -> for exposing the toolkit as a remote MCP server
# "sse"              -> legacy remote transport, kept for older clients
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")

MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8765"))
