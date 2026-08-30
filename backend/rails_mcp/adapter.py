"""Adapts backend tool instances (from interface.py-based tool.py wrappers)
onto an MCP server.

Design goal: this file should NOT need to change when you add a new tool
(e.g. a future `bridge/` or `stake/` folder). As long as the new tool
follows the same interface.py contract as fetch_price/swap/transfer/x402
and is added to backend.TOOLKIT, it gets picked up automatically.

Compatibility: works with
  - LangChain Runnables (StructuredTool/BaseTool with .invoke/.ainvoke)
  - Legacy LangChain tools (.run/.arun)
  - CrewAI tools (.run)
  - Plain custom classes implementing interface.py directly
    (.run/.execute/.arun/.aexecute)

For the input schema, it looks for (in order): input_schema, args_schema,
InputSchema, schema_cls. If your interface.py's BaseTool defines
`input_schema` as a pydantic model, that's picked up first.
"""
import asyncio
import inspect
import logging
from typing import Any, Iterable, Type

from pydantic import BaseModel, Field, create_model

logger = logging.getLogger("backend.mcp.adapter")


def _resolve_input_model(tool: Any, fallback_name: str) -> Type[BaseModel]:
    """Find the pydantic schema describing a tool's arguments."""
    for attr in ("input_schema", "args_schema", "InputSchema", "schema_cls"):
        schema = getattr(tool, attr, None)
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            return schema

    logger.warning(
        "Tool '%s' has no recognizable input schema (checked "
        "input_schema/args_schema/InputSchema/schema_cls). Registering it "
        "with a generic `payload: dict` argument instead — for a properly "
        "typed MCP tool, expose an `input_schema` pydantic model from "
        "interface.py on this tool.",
        fallback_name,
    )
    return create_model(
        f"{fallback_name.title().replace('_', '')}GenericInput",
        payload=(dict, Field(default_factory=dict, description="Raw arguments")),
    )


def _resolve_caller(tool: Any):
    """Return an async callable(kwargs: dict) -> Any for the given tool."""
    if hasattr(tool, "ainvoke"):
        async def call(kwargs: dict) -> Any:
            return await tool.ainvoke(kwargs)
        return call

    if hasattr(tool, "invoke"):
        async def call(kwargs: dict) -> Any:
            return await asyncio.to_thread(tool.invoke, kwargs)
        return call

    # "arun"/"aexecute" are conventionally async; "run"/"execute"/"__call__"
    # could be either, depending on how tool.py wrapped interface.py (e.g. a
    # LangChain BaseTool's `.run` is sync, but a custom interface.py might
    # define `run` as `async def`). Check iscoroutinefunction rather than
    # assuming from the name alone.
    for attr in ("arun", "aexecute", "run", "execute", "__call__"):
        fn = getattr(tool, attr, None)
        if not callable(fn):
            continue
        if inspect.iscoroutinefunction(fn):
            async def call(kwargs: dict, _fn=fn) -> Any:
                return await _fn(**kwargs)
            return call
        async def call(kwargs: dict, _fn=fn) -> Any:
            return await asyncio.to_thread(lambda: _fn(**kwargs))
        return call

    raise TypeError(
        f"Tool {tool!r} exposes none of the expected call methods "
        "(ainvoke/invoke/arun/run/execute)."
    )


def _serialize_result(result: Any) -> Any:
    if isinstance(result, BaseModel):
        return result.model_dump(mode="json")
    if isinstance(result, (list, tuple)):
        return [_serialize_result(item) for item in result]
    return result


def _build_handler(name: str, input_model: Type[BaseModel], caller):
    """Build an async wrapper whose *signature* exposes the input model's
    fields as flat, top-level keyword arguments.

    FastMCP generates each tool's JSON schema straight from
    `inspect.signature(fn)`. If we just wrote `async def handler(params:
    input_model)`, callers would have to send `{"params": {...}}` instead
    of the flat `{"base": "USDC", ...}` shape people (and most MCP clients)
    actually expect. So instead we build the signature dynamically from
    `input_model.model_fields` and stitch the fields back into the model
    inside the function body. `inspect.signature()` honors an explicit
    `__signature__` attribute, which is what makes this work.
    """
    parameters = []
    annotations = {}
    for field_name, field in input_model.model_fields.items():
        default = inspect.Parameter.empty if field.is_required() else field.default
        parameters.append(
            inspect.Parameter(
                field_name,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=default,
                annotation=field.annotation,
            )
        )
        annotations[field_name] = field.annotation

    async def handler(**kwargs):
        try:
            params = input_model(**kwargs)
            result = await caller(params.model_dump())
        except Exception as exc:
            # Surface the failure to the MCP client as data instead of
            # crashing the whole server — a bad swap/transfer/x402 call
            # shouldn't take the other three tools down with it.
            logger.exception("Tool '%s' raised during execution", name)
            return {"error": str(exc), "type": type(exc).__name__, "tool": name}
        return _serialize_result(result)

    handler.__signature__ = inspect.Signature(parameters)
    handler.__annotations__ = annotations
    handler.__name__ = f"tool_{name}"
    return handler


def register_tool(mcp, tool: Any) -> str:
    """Register a single backend tool instance onto an MCP server.

    Returns the registered tool name (mainly for logging a summary).
    """
    name = getattr(tool, "name", None) or type(tool).__name__
    description = getattr(tool, "description", "") or f"{name} tool."

    input_model = _resolve_input_model(tool, name)
    caller = _resolve_caller(tool)
    handler = _build_handler(name, input_model, caller)
    handler.__doc__ = description

    mcp.add_tool(handler, name=name, description=description)
    return name


def register_toolkit(mcp, toolkit: Iterable[Any]) -> list:
    registered = []
    for tool in toolkit:
        try:
            registered.append(register_tool(mcp, tool))
        except Exception:
            logger.exception("Failed to register tool %r onto MCP server", tool)
    return registered
