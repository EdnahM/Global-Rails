"""MCP (Model Context Protocol) exposure layer for the backend toolkit.

This package turns the LangChain/CrewAI-style tools already defined under
backend/{fetch_price,swap,transfer,x402}/tool.py into MCP tools, so any
MCP-compatible client (Claude Desktop, Claude Code, other MCP hosts) can
call them directly.

It does NOT reimplement any tool logic — it only adapts backend.TOOLKIT
(as exported from backend/toolkit.py) onto an MCP server instance.

Deliberately empty otherwise — no `from .server import mcp` re-export here.
That created a circular import (server.py needs `config` from this
package's __init__, while __init__ needed `mcp` back from server.py) that
a normal `import rails_mcp.server` tolerates, because Python loads the
parent package fully before the child module. Vercel's entrypoint loader
doesn't follow that path — it loads server.py directly by file path,
skipping the parent-first order — so the cycle breaks there specifically.
Nothing else in this codebase imports `mcp` from the package level (only
from `rails_mcp.server` or `rails_mcp.adapter` directly), so removing the
re-export costs nothing and removes the cycle entirely.
"""