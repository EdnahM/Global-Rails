from __future__ import annotations

import logging
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
from rails_mcp import config
from rails_mcp.adapter import register_toolkit
from rest_handlers import execute_tool_payload, health_payload, list_tools_payload
try:
    from toolkit import TOOLKIT
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Could not import TOOLKIT from backend/toolkit.py. Make sure "
        "backend/toolkit.py exports the combined list (or dict) of tool "
        "instances, e.g.:\n\n"
        "    from fetch_price.tool import fetch_price_tool\n"
        "    from swap.tool import swap_tool\n"
        "    from transfer.tool import transfer_tool\n"
        "    from off_ramp.tool import off_ramp_tool\n"
        "    from x402.tool import x402_get_invoice_tool, x402_settle_invoice_tool\n\n"
        "    TOOLKIT = [fetch_price_tool, swap_tool, transfer_tool, off_ramp_tool,\n"
        "               x402_get_invoice_tool, x402_settle_invoice_tool]"
    ) from exc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rails_mcp.server")

# NOTE on streamable_http_path: this mcp[cli]<2 (mcp.server.fastmcp.FastMCP)
# has no `http_app(path=...)` method — that's the API of the separate
# "fastmcp" PyPI project, not the official SDK pinned in requirements.txt.
# The equivalent here is the `streamable_http_path` constructor kwarg plus
# `.streamable_http_app()` (no path arg) below.
mcp = FastMCP(
    config.MCP_SERVER_NAME,
    host=config.MCP_HOST,
    port=config.MCP_PORT,
    streamable_http_path=config.MCP_HTTP_PATH,
)

_toolkit_items = TOOLKIT.values() if isinstance(TOOLKIT, dict) else TOOLKIT
_registered = register_toolkit(mcp, _toolkit_items)
logger.info("Registered %d MCP tools: %s", len(_registered), ", ".join(_registered))


# ---------------------------------------------------------------------------
# REST convenience routes — same handlers backend/api.py uses locally, added
# directly onto the FastMCP-managed Starlette app via its own custom_route
# hook. This is what lets ONE deployed service answer both the real MCP
# protocol (at config.MCP_HTTP_PATH) and the frontend's plain fetch() calls,
# without mounting a second ASGI app and having to hand-wire its lifespan.
# ---------------------------------------------------------------------------
@mcp.custom_route("/api/", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse(health_payload())


@mcp.custom_route("/api/tools", methods=["GET"])
async def list_tools_route(request: Request) -> JSONResponse:
    return JSONResponse(list_tools_payload())


@mcp.custom_route("/api/tool/{tool_name}", methods=["POST"])
async def execute_tool_route(request: Request) -> JSONResponse:
    tool_name = request.path_params["tool_name"]
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    return JSONResponse(execute_tool_payload(tool_name, payload))


app = mcp.streamable_http_app()

def main() -> None:
    mcp.run(transport=config.MCP_TRANSPORT)


if __name__ == "__main__":
    main()