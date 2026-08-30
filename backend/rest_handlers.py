"""Framework-agnostic REST handler logic for the Global Rails toolkit.

Both `backend/api.py` (a standalone FastAPI app, handy for local dev via
`uvicorn backend.api:app`) and `backend/mcp/server.py` (the actual Vercel
entrypoint, which exposes these same operations as plain HTTP routes
alongside the MCP protocol via `@mcp.custom_route`) call into these three
functions. Keeping the logic here means tool execution is implemented once
and both surfaces stay in sync automatically.
"""
from typing import Any, Dict

from toolkit import TOOLKIT


def get_tools() -> Dict[str, Any]:
    """Return the registered Global Rails tools keyed by name."""
    items = TOOLKIT.values() if isinstance(TOOLKIT, dict) else TOOLKIT
    return {tool.name: tool for tool in items}


def health_payload() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "Global Rails API",
        "tools": list(get_tools().keys()),
    }


def list_tools_payload() -> Dict[str, Any]:
    return {
        "tools": [
            {"name": tool.name, "description": tool.description}
            for tool in get_tools().values()
        ]
    }


def execute_tool_payload(tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute one tool by name and return a JSON-safe result dict."""
    tool = get_tools().get(tool_name)

    if tool is None:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    try:
        result = tool.execute(**(payload or {}))
        if hasattr(result, "to_dict"):
            return result.to_dict()
        return result
    except Exception as exc:
        return {"success": False, "error": str(exc), "tool": tool_name}