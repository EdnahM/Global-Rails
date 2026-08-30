from __future__ import annotations

import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rails_mcp.server")

try:
    from mcp.server.fastmcp import FastMCP
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from rails_mcp import config
    from rails_mcp.adapter import register_toolkit
    from rest_handlers import execute_tool_payload, health_payload, list_tools_payload
    from toolkit import TOOLKIT

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

    # -----------------------------------------------------------------------
    # REST convenience routes — same handlers backend/api.py uses locally,
    # added directly onto the FastMCP-managed Starlette app via its own
    # custom_route hook. This is what lets ONE deployed service answer both
    # the real MCP protocol (at config.MCP_HTTP_PATH) and the frontend's
    # plain fetch() calls, without mounting a second ASGI app and having to
    # hand-wire its lifespan.
    # -----------------------------------------------------------------------
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

except Exception as _startup_exc:  # noqa: BLE001 - intentionally broad, see docstring
    _startup_traceback = traceback.format_exc()
    logger.error("STARTUP FAILURE — this is what's actually breaking:\n%s", _startup_traceback)

    from starlette.applications import Starlette
    from starlette.responses import JSONResponse as _JSONResponse
    from starlette.routing import Route as _Route

    # rails_mcp/__init__.py does `from .server import mcp` — without this,
    # that import fails too (a *different* ImportError), which would
    # cascade and hide the real exception being reported below.
    mcp = None

    # `except X as name` unbinds `name` when the except block ends (CPython
    # deletes it to avoid a traceback reference cycle) — the route handler
    # below runs later, at actual request time, well after that. Capture
    # what's needed into plain variables now, and close over those instead
    # of _startup_exc itself, or this NameErrors on the first real request.
    _error_type = type(_startup_exc).__name__
    _error_message = str(_startup_exc)
    _traceback_lines = _startup_traceback.splitlines()

    async def _report_startup_failure(request):
        return _JSONResponse(
            {
                "startup_failed": True,
                "error_type": _error_type,
                "error_message": _error_message,
                "traceback": _traceback_lines,
            },
            status_code=200,
        )

    app = Starlette(
        routes=[_Route("/{path:path}", _report_startup_failure, methods=["GET", "POST"])]
    )


def main() -> None:
    mcp.run(transport=config.MCP_TRANSPORT)


if __name__ == "__main__":
    main()