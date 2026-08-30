from .coingecko import get_coingecko_client
from .constants import SUPPORTED_SYMBOLS


async def get_token_prices(
    symbols: list[str],
    vs_currencies: list[str] = ["usd"],
) -> dict:
    """
    Fetch live market prices for one or more tokens from CoinGecko.

    Args:
        symbols: List of token symbols e.g. ["ETH", "cKES", "USDC", "CELO"]
        vs_currencies: Quote currencies e.g. ["usd", "kes", "eur"]

    Returns:
        Nested dict mapping symbol -> currency -> price
        e.g. {"ETH": {"usd": 3200.50, "usd_24h_change": -1.2}}
    """
    try:
        client = get_coingecko_client()
        prices = await client.get_prices(symbols, vs_currencies)
        return {
            "success": True,
            "prices": prices,
            "supported_tokens": SUPPORTED_SYMBOLS,
        }
    except ValueError as e:
        return {"success": False, "error": "UNKNOWN_TOKEN", "detail": str(e)}
    except Exception as e:
        return {"success": False, "error": "API_ERROR", "detail": str(e)}


async def list_supported_tokens() -> dict:
    """
    List all token symbols supported for price fetching.

    Returns:
        List of supported token symbols
    """
    return {"success": True, "tokens": SUPPORTED_SYMBOLS}
