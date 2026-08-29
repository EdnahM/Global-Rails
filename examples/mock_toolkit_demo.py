import sys
import os

# Ensure the root project folder is in Python's path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend import TOOLKIT

def main():
    print("=== World Rails SDK Toolkit Demo ===")
    print(f"Loaded {len(TOOLKIT)} tools from backend.TOOLKIT:\n")

    for tool in TOOLKIT:
        print(f"- Tool: {tool.name}")
        print(f"  Description: {tool.description}")

    print("\n" + "="*40)
    print("       TESTING TOOL EXECUTIONS       ")
    print("="*40 + "\n")

    # 1. Test fetch_price
    fetch_tool = next(t for t in TOOLKIT if t.name == "fetch_market_price")
    print("1. Fetch Market Price:")
    print(fetch_tool.invoke({"token": "USDC", "fiat": "KES"}))

    # 2. Test transfer
    transfer_tool = next(t for t in TOOLKIT if t.name == "mobile_money_payout")
    print("\n2. Mobile Money Payout:")
    print(transfer_tool.invoke({"phone_number": "254712345678", "amount": 1500.0, "currency": "KES"}))

    # 3. Test swap
    swap_tool = next(t for t in TOOLKIT if t.name == "swap_tokens")
    print("\n3. Token Swap:")
    print(swap_tool.invoke({"from_token": "USDT", "to_token": "USDC", "amount": 100.0}))

    # 4. Test x402
    x402_tool = next(t for t in TOOLKIT if t.name == "pay_l402_paywall")
    print("\n4. L402 Paywall Micro-Payment:")
    print(x402_tool.invoke({"invoice_token": "lnbc100n1p...", "max_amount_sats": 500}))

if __name__ == "__main__":
    main()
