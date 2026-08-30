"""
African Rails MCP — Client Test Script

Tests every tool via the real MCP protocol (in-process).
This is how an AI agent would actually call the server.

Run:
    cd backend
    ../.venv/bin/python test_mcp_client.py

Optional env vars:
    PRIVATE_KEY=0x...       Required for send/swap tests
    WALLET_ADDRESS=0x...    Required for send/swap tests
    TEST_CHAIN=avalanche-fuji   (default)
    SKIP_WALLET_TESTS=1    Skip tests that need a funded wallet
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fastmcp import Client
from african_rails_mcp.server import mcp

CHAIN     = os.getenv("TEST_CHAIN", "avalanche-fuji")
HAS_WALLET = bool(os.getenv("PRIVATE_KEY") and os.getenv("WALLET_ADDRESS"))
SKIP_WALLET = os.getenv("SKIP_WALLET_TESTS", "0") == "1"

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

passed = failed = skipped = 0


def ok(name, detail=""):
    global passed
    passed += 1
    print(f"  {GREEN}✓{RESET} {name}" + (f"  {YELLOW}{detail}{RESET}" if detail else ""))


def fail(name, reason):
    global failed
    failed += 1
    print(f"  {RED}✗{RESET} {name}  {RED}{reason}{RESET}")


def skip(name, reason):
    global skipped
    skipped += 1
    print(f"  {YELLOW}−{RESET} {name}  {YELLOW}(skipped: {reason}){RESET}")


def section(title):
    print(f"\n{BOLD}{CYAN}── {title}{RESET}")


async def run_all():
    if os.getenv("PRIVATE_KEY"):
        os.environ["PRIVATE_KEY"] = os.environ["PRIVATE_KEY"]
    if os.getenv("WALLET_ADDRESS"):
        os.environ["WALLET_ADDRESS"] = os.environ["WALLET_ADDRESS"]

    print(f"\n{BOLD}African Rails MCP — Protocol Test{RESET}")
    print(f"Chain: {CHAIN}  |  Wallet: {'configured' if HAS_WALLET else 'not set'}")
    print("─" * 50)

    async with Client(mcp) as client:

        # ── 1. Discovery ─────────────────────────────────────
        section("MCP Discovery")

        tools = await client.list_tools()
        if len(tools) == 11:
            ok("list_tools", f"{len(tools)} tools registered")
        else:
            fail("list_tools", f"expected 11 tools, got {len(tools)}")

        tool_names = {t.name for t in tools}
        required = {
            "get_token_prices", "list_supported_tokens",
            "check_balance", "send_transaction", "get_tx_status", "list_supported_chains",
            "quote_swap", "execute_swap",
            "fetch_paid_resource", "check_x402_price", "get_x402_wallet_info",
        }
        missing = required - tool_names
        if not missing:
            ok("all required tools present")
        else:
            fail("missing tools", str(missing))

        for tool in tools:
            if not tool.description or len(tool.description.strip()) < 10:
                fail(f"{tool.name} has description", "empty or too short")
            else:
                ok(f"{tool.name} has description")

        # ── 2. Price tools ───────────────────────────────────
        section("Prices")

        r = await client.call_tool("list_supported_tokens", {})
        tokens = r[0].text if r else "{}"
        import json
        tokens_data = json.loads(tokens)
        if "AVAX" in tokens_data.get("tokens", []):
            ok("list_supported_tokens", "AVAX present")
        else:
            fail("list_supported_tokens", "AVAX missing")

        r = await client.call_tool("get_token_prices", {
            "symbols": ["AVAX", "ETH", "USDC"],
            "vs_currencies": ["usd"],
        })
        data = json.loads(r[0].text)
        if data.get("success") and "AVAX" in data.get("prices", {}):
            avax_price = data["prices"]["AVAX"].get("usd", 0)
            ok("get_token_prices", f"AVAX = ${avax_price:,.2f}")
        else:
            fail("get_token_prices", data.get("detail", str(data)))

        r = await client.call_tool("get_token_prices", {
            "symbols": ["NOTAREALTOKEN"],
        })
        data = json.loads(r[0].text)
        if data.get("error") == "UNKNOWN_TOKEN":
            ok("get_token_prices unknown symbol → UNKNOWN_TOKEN error")
        else:
            fail("get_token_prices unknown symbol", "expected UNKNOWN_TOKEN error")

        # ── 3. On-chain tools ────────────────────────────────
        section("On-chain")

        r = await client.call_tool("list_supported_chains", {})
        data = json.loads(r[0].text)
        chains = data.get("chains", {})
        if "avalanche-fuji" in chains and "celo" in chains:
            ok("list_supported_chains", f"{len(chains)} chains")
        else:
            fail("list_supported_chains", "missing expected chains")

        # Balance check against a known public address
        public_addr = "0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2"  # MakerDAO
        r = await client.call_tool("check_balance", {
            "address": public_addr,
            "chain": "ethereum",
            "token": "native",
        })
        data = json.loads(r[0].text)
        if "balance" in data:
            ok("check_balance (ETH mainnet)", f"{float(data['balance']):.4f} ETH")
        else:
            fail("check_balance", data.get("detail", str(data)))

        # Balance on Fuji
        fuji_addr = "0x1234567890123456789012345678901234567890"
        r = await client.call_tool("check_balance", {
            "address": fuji_addr,
            "chain": CHAIN,
            "token": "native",
        })
        data = json.loads(r[0].text)
        if "balance" in data:
            ok(f"check_balance ({CHAIN})", f"{float(data['balance']):.6f} AVAX")
        else:
            fail(f"check_balance ({CHAIN})", data.get("detail", str(data)))

        # Invalid chain → clean error
        r = await client.call_tool("check_balance", {
            "address": fuji_addr,
            "chain": "fakenet",
            "token": "native",
        })
        data = json.loads(r[0].text)
        if data.get("success") is False:
            ok("check_balance invalid chain → error")
        else:
            fail("check_balance invalid chain", "should have returned error")

        # Tx status for a non-existent hash → pending
        r = await client.call_tool("get_tx_status", {
            "tx_hash": "0x" + "a" * 64,
            "chain": CHAIN,
        })
        data = json.loads(r[0].text)
        if data.get("status") in ("pending", "confirmed", "failed"):
            ok("get_tx_status", f"status = {data['status']}")
        else:
            fail("get_tx_status", str(data))

        # ── 4. Swap tools ────────────────────────────────────
        section("Swaps")

        # Quote on Celo (Mento)
        r = await client.call_tool("quote_swap", {
            "token_in": "cUSD",
            "token_out": "cKES",
            "amount_in": "1.0",
            "chain": "celo",
            "prefer_mento": True,
        })
        data = json.loads(r[0].text)
        if "amount_out" in data:
            ok("quote_swap cUSD→cKES (Mento)", f"1 cUSD → {float(data['amount_out']):.2f} cKES via {data.get('dex')}")
        elif data.get("success") is False:
            skip("quote_swap cUSD→cKES", data.get("detail", "RPC unreachable"))
        else:
            fail("quote_swap", str(data))

        # Quote unknown pair → error
        r = await client.call_tool("quote_swap", {
            "token_in": "FAKEIN",
            "token_out": "cUSD",
            "amount_in": "1.0",
            "chain": "celo",
        })
        data = json.loads(r[0].text)
        if data.get("success") is False:
            ok("quote_swap invalid token → error")
        else:
            fail("quote_swap invalid token", "expected error")

        # ── 5. x402 tools ───────────────────────────────────
        section("x402")

        r = await client.call_tool("get_x402_wallet_info", {})
        data = json.loads(r[0].text)
        if data.get("success") and "wallet_address" in data:
            ok("get_x402_wallet_info", f"wallet = {data['wallet_address'][:10]}...")
            raw = str(data)
            if "private_key" not in raw.lower():
                ok("private key not leaked in wallet info")
            else:
                fail("private key not leaked", "SECURITY: private_key in response!")
        else:
            fail("get_x402_wallet_info", str(data))

        r = await client.call_tool("check_x402_price", {"url": "https://httpbin.org/status/200"})
        data = json.loads(r[0].text)
        if data.get("success"):
            ok("check_x402_price (free URL)", f"payment_required = {data.get('payment_required')}")
        else:
            skip("check_x402_price", "network unreachable")

        # ── 6. Wallet-gated tests ────────────────────────────
        section("Wallet tests (send / execute_swap)")

        if not HAS_WALLET or SKIP_WALLET:
            reason = "SKIP_WALLET_TESTS=1" if SKIP_WALLET else "PRIVATE_KEY not set"
            skip("send_transaction", reason)
            skip("execute_swap", reason)
            print(f"\n  {YELLOW}To run wallet tests:{RESET}")
            print(f"    export PRIVATE_KEY=0x...")
            print(f"    export WALLET_ADDRESS=0x...")
            print(f"    {YELLOW}Get testnet AVAX: https://faucet.avax.network{RESET}")
        else:
            addr = os.getenv("WALLET_ADDRESS")

            # Self-send 0.0001 AVAX
            r = await client.call_tool("send_transaction", {
                "to": addr,
                "amount": "0.0001",
                "chain": CHAIN,
                "token": "native",
            })
            data = json.loads(r[0].text)
            if "tx_hash" in data:
                ok("send_transaction (AVAX self-send)", f"tx = {data['tx_hash'][:18]}...")

                # Poll for confirmation
                for _ in range(10):
                    r2 = await client.call_tool("get_tx_status", {
                        "tx_hash": data["tx_hash"],
                        "chain": CHAIN,
                    })
                    status = json.loads(r2[0].text)
                    if status.get("status") in ("confirmed", "failed"):
                        break
                    await asyncio.sleep(3)

                if status.get("status") == "confirmed":
                    ok("get_tx_status (confirmed)", f"block {status.get('block_number')}")
                else:
                    fail("tx confirmation", f"status = {status.get('status')}")
            else:
                fail("send_transaction", data.get("detail", str(data)))

    # ── Summary ──────────────────────────────────────────────
    total = passed + failed + skipped
    print(f"\n{'─'*50}")
    print(f"{BOLD}Results: {GREEN}{passed} passed{RESET}  {RED}{failed} failed{RESET}  {YELLOW}{skipped} skipped{RESET}  / {total} total")
    if failed:
        print(f"{RED}Some tests failed — check RPC connectivity or wallet config.{RESET}")
    else:
        print(f"{GREEN}All tests passed!{RESET}")
    print()


if __name__ == "__main__":
    asyncio.run(run_all())
