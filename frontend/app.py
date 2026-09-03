"""
African Rails MCP — Agent Dashboard
Flask + vanilla JS UI for testing MCP tools.

Run:
    cd frontend
    ../.venv/bin/python app.py

Opens at http://localhost:5050
"""

import sys
import os
import asyncio
import requests as http_requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend/src"))

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)


def run(coro):
    return asyncio.run(coro)


# ─────────────────────────────────────────────────────────────────────────────
# API routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/config", methods=["POST"])
def set_config():
    data = request.json
    if data.get("private_key"):
        os.environ["PRIVATE_KEY"] = data["private_key"]
    if data.get("wallet_address"):
        os.environ["WALLET_ADDRESS"] = data["wallet_address"]
    # Purge every african_rails_mcp module from Python's import cache.
    # Simply reloading config.py isn't enough — other modules hold a direct
    # reference to the OLD settings object. Clearing sys.modules forces a fresh
    # import (with new env vars) on the next call.
    for key in list(sys.modules.keys()):
        if "african_rails_mcp" in key:
            del sys.modules[key]
    return jsonify({"ok": True, "wallet": data.get("wallet_address", "")})


@app.route("/api/prices", methods=["POST"])
def prices():
    data = request.json
    from african_rails_mcp.prices.tool import get_token_prices
    result = run(get_token_prices(data["symbols"], data.get("currencies", ["usd"])))
    return jsonify(result)


@app.route("/api/tokens", methods=["GET"])
def tokens():
    from african_rails_mcp.prices.constants import SUPPORTED_SYMBOLS
    return jsonify({"tokens": SUPPORTED_SYMBOLS})


@app.route("/api/chains", methods=["GET"])
def chains():
    from african_rails_mcp.onchain.constants import CHAINS
    result = {}
    for name, cfg in CHAINS.items():
        result[name] = {
            "chain_id": cfg["chain_id"],
            "native_symbol": cfg["native_symbol"],
            "tokens": ["native"] + list(cfg.get("tokens", {}).keys()),
            "explorer": cfg["block_explorer"],
        }
    return jsonify(result)


@app.route("/api/balance", methods=["POST"])
def balance():
    data = request.json
    from african_rails_mcp.onchain.tool import check_balance
    result = run(check_balance(
        address=data.get("address", ""),
        chain=data.get("chain", "celo"),
        token=data.get("token", "native"),
    ))
    return jsonify(result)


@app.route("/api/send", methods=["POST"])
def send():
    data = request.json
    from african_rails_mcp.onchain.tool import send_transaction
    result = run(send_transaction(
        to=data["to"],
        amount=data["amount"],
        chain=data.get("chain", "celo"),
        token=data.get("token", "native"),
    ))
    return jsonify(result)


@app.route("/api/tx", methods=["POST"])
def tx_status():
    data = request.json
    from african_rails_mcp.onchain.tool import get_tx_status
    result = run(get_tx_status(
        tx_hash=data["tx_hash"],
        chain=data.get("chain", "celo"),
    ))
    return jsonify(result)


@app.route("/api/quote", methods=["POST"])
def quote():
    data = request.json
    from african_rails_mcp.swaps.tool import quote_swap
    result = run(quote_swap(
        token_in=data["token_in"],
        token_out=data["token_out"],
        amount_in=data["amount_in"],
        chain=data.get("chain", "celo"),
        prefer_mento=data.get("prefer_mento", True),
    ))
    return jsonify(result)


@app.route("/api/swap", methods=["POST"])
def swap():
    data = request.json
    from african_rails_mcp.swaps.tool import execute_swap
    result = run(execute_swap(
        token_in=data["token_in"],
        token_out=data["token_out"],
        amount_in=data["amount_in"],
        chain=data.get("chain", "celo"),
        slippage_pct=float(data.get("slippage_pct", 0.5)),
        prefer_mento=data.get("prefer_mento", True),
    ))
    return jsonify(result)


@app.route("/api/x402/price", methods=["POST"])
def x402_price():
    data = request.json
    from african_rails_mcp.x402.tool import check_x402_price
    result = run(check_x402_price(data["url"]))
    return jsonify(result)


@app.route("/api/x402/fetch", methods=["POST"])
def x402_fetch():
    data = request.json
    from african_rails_mcp.x402.tool import fetch_paid_resource
    result = run(fetch_paid_resource(
        url=data["url"],
        method=data.get("method", "GET"),
        body=data.get("body"),
        max_spend_usd=float(data.get("max_spend_usd", 0.10)),
    ))
    return jsonify(result)


@app.route("/api/x402/wallet", methods=["GET"])
def x402_wallet():
    from african_rails_mcp.x402.tool import get_x402_wallet_info
    result = run(get_x402_wallet_info())
    return jsonify(result)


@app.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    """Proxy LLM chat completions server-side to avoid CORS and keep API key off the browser."""
    data = request.json
    endpoint = data.get("endpoint", "https://api.openai.com/v1").rstrip("/")
    api_key = data.get("api_key", "")
    model = data.get("model", "gpt-4o-mini")
    messages = data.get("messages", [])
    temperature = float(data.get("temperature", 0.7))

    if not api_key:
        return jsonify({"error": {"message": "No API key provided"}}), 400

    try:
        resp = http_requests.post(
            f"{endpoint}/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 800,
                "stream": False,
            },
            timeout=60,
        )
        return jsonify(resp.json()), resp.status_code
    except http_requests.exceptions.Timeout:
        return jsonify({"error": {"message": "LLM request timed out after 60s"}}), 504
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500


# ─────────────────────────────────────────────────────────────────────────────
# Frontend
# ─────────────────────────────────────────────────────────────────────────────

from african_rails_mcp.dashboard import HTML


@app.route("/")
def index():
    return render_template_string(HTML)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"\n  African Rails MCP Dashboard → http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
