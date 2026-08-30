"""MCP (Model Context Protocol) exposure layer for the backend toolkit.

This package turns the LangChain/CrewAI-style tools already defined under
backend/{fetch_price,swap,transfer,x402}/tool.py into MCP tools, so any
MCP-compatible client (Claude Desktop, Claude Code, other MCP hosts) can
call them directly.

It does NOT reimplement any tool logic — it only adapts backend.TOOLKIT
(as exported from backend/__init__.py) onto an MCP server instance.
"""
from .server import mcp

__all__ = ["mcp"]
