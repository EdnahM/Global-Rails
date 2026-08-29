import pytest
from backend import TOOLKIT
from backend.swap.tool import swap_tool
from backend.swap.client import execute_token_swap

def test_toolkit_contains_all_skills():
    tool_names = [tool.name for tool in TOOLKIT]
    assert "fetch_market_price" in tool_names
    assert "mobile_money_payout" in tool_names
    assert "swap_tokens" in tool_names
    assert "pay_l402_paywall" in tool_names

def test_swap_client_directly():
    result = execute_token_swap(from_token="USDT", to_token="USDC", amount=100.0)
    assert result["status"] == "CONFIRMED"
    assert result["amount_in"] == 100.0
    assert "tx_hash" in result

def test_swap_tool_invocation():
    output = swap_tool.invoke({"from_token": "USDT", "to_token": "USDC", "amount": 50.0})
    assert "CONFIRMED" in output

def test_all_tools_invoke_without_error():
    fetch_tool = next(t for t in TOOLKIT if t.name == "fetch_market_price")
    transfer_tool = next(t for t in TOOLKIT if t.name == "mobile_money_payout")
    x402_tool = next(t for t in TOOLKIT if t.name == "pay_l402_paywall")

    assert "USDC" in fetch_tool.invoke({"token": "USDC", "fiat": "KES"})
    assert "254712345678" in transfer_tool.invoke({"phone_number": "254712345678", "amount": 100.0, "currency": "KES"})
    assert "payment_hash" in x402_tool.invoke({"invoice_token": "lnbc100n1p...", "max_amount_sats": 500})
