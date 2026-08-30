from .client import get_x402_client
from ..config import settings
from ..onchain.transactions import get_balance


async def fetch_paid_resource(
    url: str,
    method: str = "GET",
    body: dict | None = None,
    max_spend_usd: float = 0.10,
) -> dict:
    """
    Fetch an HTTP resource that may require an x402 micropayment.

    The x402 protocol (HTTP 402 Payment Required) allows AI agents to
    autonomously pay for API access. This tool handles the full flow:
    1. Makes the initial request
    2. If server returns 402, creates an EIP-3009 off-chain payment signature
    3. Retries with X-PAYMENT header - no transaction needed upfront

    Args:
        url: The URL to fetch (may or may not require payment)
        method: HTTP method - "GET", "POST", etc.
        body: Optional JSON body for POST/PUT requests
        max_spend_usd: Maximum USD this call is allowed to spend (default $0.10)

    Returns:
        Response body, HTTP status, and whether a payment was made
    """
    client = get_x402_client()
    client.max_spend_usd = max_spend_usd
    return await client.fetch(url, method=method, body=body)


async def check_x402_price(url: str) -> dict:
    """
    Check the payment requirement for an x402-protected URL without paying.

    Useful before calling fetch_paid_resource to verify the cost and ensure
    the wallet has sufficient USDC balance.

    Args:
        url: URL to check for payment requirements

    Returns:
        Payment info: price, accepted token, network, and facilitator address
        If no payment required, returns {"payment_required": false}
    """
    client = get_x402_client()
    return await client.check_price(url)


async def get_x402_wallet_info() -> dict:
    """
    Return the wallet address and token balances used for x402 payments.

    Check this before calling fetch_paid_resource to ensure sufficient funds.
    The wallet needs USDC on the appropriate network to make x402 payments.

    Returns:
        Wallet address, USDC balance on Ethereum and Celo, and spend limit
    """
    wallet = settings.wallet_address
    max_spend = settings.x402_max_spend_usd
    balances = {}

    for chain, token in [("ethereum", "USDC"), ("celo", "USDC")]:
        try:
            result = get_balance(wallet, chain, token)
            balances[f"{chain}_{token.lower()}"] = result.get("balance", "0")
        except Exception as e:
            balances[f"{chain}_{token.lower()}"] = f"error: {str(e)}"

    return {
        "success": True,
        "wallet_address": wallet,
        "balances": balances,
        "max_spend_usd_per_request": max_spend,
    }
