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

    # -----------------------------------------------------------------------
    # Real natural-language agent routing via Groq (OpenAI-compatible tool
    # calling), replacing the frontend's keyword/regex matching for anything
    # that doesn't fit its fixed patterns. The tool schemas below are built
    # straight from each tool's own Pydantic input_schema — never hand
    # duplicated — so this can't silently drift out of sync with the real
    # tool definitions as they evolve.
    # -----------------------------------------------------------------------
    def _build_tool_schemas() -> list[dict]:
        schemas = []
        for tool in TOOLKIT.values() if isinstance(TOOLKIT, dict) else TOOLKIT:
            params = tool.input_schema.model_json_schema()
            params.pop("title", None)
            for prop in params.get("properties", {}).values():
                prop.pop("title", None)
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": params,
                },
            })
        return schemas

    def _format_reply(tool_name: str, result: dict) -> str:
        if not result.get("success"):
            return f"I couldn't complete that ({tool_name}): {result.get('error', 'Unknown error')}"
        d = result.get("data", {}) or {}
        if tool_name == "fetch_market_price":
            return f"1 {d.get('token')} = {d.get('rate')} {d.get('quote')} on {d.get('chain')}."
        if tool_name == "swap_tokens":
            return (f"Swapped {d.get('amount_in')} {d.get('from_token')} for "
                    f"{d.get('amount_out')} {d.get('to_token')} on {d.get('chain')} "
                    f"(tx {str(d.get('tx_hash', ''))[:10]}...).")
        if tool_name == "transfer":
            return (f"Sent {d.get('amount')} {d.get('token')} to {d.get('to_address')} "
                    f"(gas {d.get('gas_fee_usdc')} USDC).")
        if tool_name == "off_ramp_payout":
            return (f"Paid out {d.get('amount_delivered')} {d.get('currency')} to "
                    f"{d.get('recipient')} via {d.get('network')} (ref {d.get('transaction_id')}).")
        if tool_name == "x402_get_invoice":
            return (f"Resolved invoice {d.get('invoice_id')}: {d.get('amount')} {d.get('token')} "
                    f"on {d.get('chain')} (status {d.get('status')}).")
        if tool_name == "x402_settle_invoice":
            return f"Invoice settled — status {d.get('status')} (payment hash {str(d.get('payment_hash', ''))[:10]}...)."
        return f"Done ({tool_name})."

    GROQ_SYSTEM_PROMPT = (
        "You are the Global Rails financial agent. You can check market rates, "
        "swap tokens, transfer stablecoins, pay out to mobile money (M-Pesa/MoMo), "
        "and resolve/settle x402 micropayments, by calling the tools provided. "
        "Call a tool whenever the user's request maps to one, filling in every "
        "argument you can infer from their message. Ask a brief clarifying "
        "question only if a required argument is genuinely missing and can't "
        "be reasonably defaulted. For anything else, just respond conversationally."
    )

    @mcp.custom_route("/api/agent/chat", methods=["POST"])
    async def agent_chat_route(request: Request) -> JSONResponse:
        import json
        import os

        import httpx

        data = await request.json()
        message = data.get("message", "")
        history = data.get("history", [])

        groq_key = os.environ.get("GROQ_API_KEY", "")
        if not groq_key:
            return JSONResponse({"configured": False, "error": "GROQ_API_KEY is not set"})

        model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        messages = (
            [{"role": "system", "content": GROQ_SYSTEM_PROMPT}]
            + [{"role": h.get("role", "user"), "content": h.get("content", "")} for h in history]
            + [{"role": "user", "content": message}]
        )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": messages,
                        "tools": _build_tool_schemas(),
                        "tool_choice": "auto",
                        "temperature": 0.3,
                    },
                )
            if resp.status_code != 200:
                try:
                    detail = resp.json().get("error", {}).get("message", resp.text[:200])
                except Exception:
                    detail = resp.text[:200] or f"HTTP {resp.status_code}"
                return JSONResponse({"configured": True, "error": f"Groq returned {resp.status_code}: {detail}"})
            result = resp.json()
        except Exception as exc:
            return JSONResponse({"configured": True, "error": f"LLM request failed: {exc}"})

        if "error" in result:
            return JSONResponse({"configured": True, "error": f"Groq error: {result['error'].get('message', result['error'])}"})

        choice = (result.get("choices") or [{}])[0]
        msg = choice.get("message", {})
        tool_calls = msg.get("tool_calls")

        if not tool_calls:
            return JSONResponse({
                "configured": True,
                "reply": msg.get("content") or "I'm not sure how to help with that.",
                "tool_used": None,
            })

        call = tool_calls[0]
        tool_name = call.get("function", {}).get("name", "")
        try:
            args = json.loads(call.get("function", {}).get("arguments") or "{}")
        except Exception:
            args = {}

        tool_result = execute_tool_payload(tool_name, args)
        return JSONResponse({
            "configured": True,
            "reply": _format_reply(tool_name, tool_result),
            "tool_used": tool_name,
            "tool_args": args,
            "tool_result": tool_result,
        })

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