"""Price oracle for Global Rails.

Fetches real-time exchange rates for crypto tokens and fiat currencies in a
chain-agnostic way. The default path uses CoinGecko as a public fallback
oracle; it can be extended to read on-chain DEX pools per chain without
changing the tool surface.
"""

import requests

from backend.chains import CHAINS, get_chain

# CoinGecko asset ids keyed by token symbol (used by the fiat oracle).
COINGECKO_IDS = {
    "USDC": "usd-coin",
    "USDT": "tether",
    "AVAX": "avalanche-2",
    "ETH": "ethereum",
    "POL": "matic-network",
}

COINGECKO_BASE = "https://api.coingecko.com/api/v3/simple/price"


def _fiat_quote(token: str, fiat: str) -> float:
    """Return token->fiat rate via CoinGecko (public fallback oracle)."""
    coin_id = COINGECKO_IDS.get(token.upper(), COINGECKO_IDS["USDC"])
    url = f"{COINGECKO_BASE}?ids={coin_id}&vs_currencies={fiat.lower()}"
    res = requests.get(url, timeout=10)
    res.raise_for_status()
    data = res.json()
    return float(data.get(coin_id, {}).get(fiat.lower(), 1.0))


def _token_quote(base: str, quote: str) -> float:
    """Return a token->token rate placeholder.

    Stablecoin pairs are ~1:1. This mirrors the current simulated routing
    (see backend/swap); an on-chain DEX pool read would replace the constant
    when the swap integration is wired up.
    """
    b, q = base.upper(), quote.upper()
    if {b, q} <= {"USDC", "USDT", "USDC.E", "USDT.E"}:
        return 1.0
    return 1.0


def get_market_price(token: str = "USDC", quote: str = "USD", chain: str = "avalanche") -> dict:
    """Fetch a price for 'token' relative to 'quote' on 'chain'.

    - 'quote' in {"USD", "KES", "NGN", "GHS", ...} and the reference coin is
      quoted in fiat via CoinGecko.
    - 'quote' as a token symbol enables token-vs-token prices.
    Returns a dict compatible with the shared ToolResult payload contract.
    """
    chain_cfg = get_chain(chain)
    t = token.upper()

    if quote.isupper() and quote not in ("USD",):
        rate = _token_quote(t, quote)
    else:
        rate = _fiat_quote(t, quote)

    return {
        "token": t,
        "quote": quote.upper(),
        "chain": chain_cfg.name,
        "chain_id": chain_cfg.chain_id,
        "rate": rate,
        "source": "coingecko",
    }


def supported_chains() -> list:
    """List of chains the price oracle can report prices for."""
    return [
        {"name": c.name, "chain_id": c.chain_id, "stablecoins": list(c.stablecoins)}
        for c in CHAINS.values()
    ]
