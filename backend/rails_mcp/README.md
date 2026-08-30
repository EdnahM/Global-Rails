# MCP layer for the stablecoin/agent toolkit

This adds an `mcp/` package under `backend/` that exposes
`fetch_price`, `swap`, `transfer`, and `x402` tools over the Model Context
Protocol, so Claude Desktop, Claude Code, or any other MCP client can call
them directly — no LangChain/CrewAI agent loop required in between.

```
backend/
├── interface.py
├── fetch_price/ swap/ transfer/ x402/ 
├── __init__.py                          # — must export TOOLKIT
└── mcp/                                 # 
    ├── __init__.py
    ├── config.py       # transport/host/port env vars
    ├── adapter.py       # generic BaseTool -> MCP tool bridge
    ├── server.py        # entry point (`python -m backend.mcp.server`)
    ├── requirements.txt
    └── examples/
        └── mock_toolkit_demo.py   # runnable, no real backend needed
```

## How it works

1. `server.py` imports `TOOLKIT` from `backend/__init__.py` — the same
   unified list your `__init__.py` docstring says it exports.
2. For each tool instance, `adapter.py`:
   - finds its input schema by checking, in order:
     `input_schema` → `args_schema` → `InputSchema` → `schema_cls`
     (covers your own `interface.py` contract as well as LangChain's
     `args_schema` convention). If none of these exist, it falls back to a
     generic `payload: dict` argument and logs a warning — the tool still
     works, just without a typed schema for clients to introspect.
   - finds a way to call it by checking, in order:
     `ainvoke`/`invoke` (LangChain Runnable-style) → `arun`/`aexecute` →
     `run`/`execute`/`__call__` (sync or async, detected automatically).
   - builds an MCP tool whose parameters are the **flat fields** of the
     input schema (not nested under a `params` key), so a client calling
     `fetch_market_price` sends `{"token": "USDC", "quote": "KES"}` directly.
   - catches exceptions from the underlying tool and returns them as
     structured data (`{"error": ..., "type": ..., "tool": ...}`) instead
     of crashing the whole MCP server — one bad `swap` or `transfer` call
     shouldn't take `fetch_price` and `x402` down with it.
3. Nothing in `interface.py`, `client.py`, or `tool.py` needs to change.
   Add a new tool folder the same way you added `x402/`, add its instance
   to `TOOLKIT` in `backend/__init__.py`, and it's automatically exposed —
   `adapter.py` never needs to know a new tool exists.

## Assumption about `backend/__init__.py`

`server.py` expects `backend/__init__.py` to export a `TOOLKIT` — a list or
dict of tool instances, each following the shared contract in
`backend/interface.py` (`name`, `description`, `input_schema`, `execute`).
The current toolkit exports:

```python
# backend/__init__.py
from .fetch_price.tool import fetch_price_tool
from .swap.tool import swap_tool
from .transfer.tool import transfer_tool
from .off_ramp.tool import off_ramp_tool
from .x402.tool import x402_get_invoice_tool, x402_settle_invoice_tool

TOOLKIT = {
    "fetch_market_price": fetch_price_tool,
    "transfer": transfer_tool,
    "swap_tokens": swap_tool,
    "off_ramp_payout": off_ramp_tool,
    "x402_get_invoice": x402_get_invoice_tool,
    "x402_settle_invoice": x402_settle_invoice_tool,
}

# a plain list [tool_a, tool_b, ...] also works
```

If your export is named differently, either rename it to `TOOLKIT` or
change the one import line at the top of `server.py`.

## Running it

```bash
pip install -r backend/mcp/requirements.txt

# stdio transport — what Claude Desktop / Claude Code expect for a local server
python -m backend.mcp.server

# remote/host-able transport
MCP_TRANSPORT=streamable-http MCP_PORT=8765 python -m backend.mcp.server
```

Try it without touching your real backend at all:

```bash
python -m backend.mcp.examples.mock_toolkit_demo
```

Inspect it interactively with the official MCP inspector:

```bash
mcp dev backend/mcp/server.py
```

### Wiring into Claude Desktop

```json
{
  "mcpServers": {
    "stablecoin-agent-toolkit": {
      "command": "python",
      "args": ["-m", "backend.mcp.server"],
      "cwd": "/absolute/path/to/your/repo"
    }
  }
}
```

## Things worth deciding before this hits production

- **`x402`/L402 flows are multi-step** (get a 402 + invoice, pay it, retry
  with proof). The toolkit already splits this into two MCP tools so an
  agent can *see* the invoice before paying: `x402_get_invoice` resolves a
  402 challenge into an invoice, and `x402_settle_invoice` pays it and
  returns the proof/auth header.
- **`transfer`, `swap`, and `off_ramp` move real assets/money.** Nothing here
  adds confirmation, spend limits, or dry-run mode — if you want an
  "are you sure" step before an MCP client can trigger a payout, that
  belongs in the tool's `tool.py` (e.g. requiring an `idempotency_key` or a
  separate `confirm=True` field in its schema, as `transfer` already accepts
  an `idempotency_key`), since MCP tools are otherwise called directly
  without a human in the loop.
- **mcp SDK v2 exists** (released 2026-07-28, renames `FastMCP` →
  `MCPServer`, moves `mcp.server.fastmcp` → `mcp.server.mcpserver`). This
  layer pins `mcp[cli]<2` deliberately since v2 is very new; migrating
  later only touches the two import lines in `server.py`.
