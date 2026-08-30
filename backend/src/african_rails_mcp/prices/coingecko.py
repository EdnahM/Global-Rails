import httpx
from typing import Optional
from .constants import COINGECKO_IDS, SUPPORTED_SYMBOLS
from ..config import settings

# Case-insensitive lookup: "ckes" -> "celo-kenyan-shilling", "eth" -> "ethereum"
_UPPER_TO_COIN_ID = {k.upper(): v for k, v in COINGECKO_IDS.items()}
# Case-insensitive lookup back to canonical symbol: "ckes" -> "cKES"
_UPPER_TO_CANONICAL = {k.upper(): k for k in COINGECKO_IDS}


class CoinGeckoClient:
    def __init__(self):
        self._api_key = settings.coingecko_api_key
        if self._api_key:
            self._base_url = "https://pro-api.coingecko.com/api/v3"
        else:
            self._base_url = settings.coingecko_base_url

    def _headers(self) -> dict:
        if self._api_key:
            return {"x-cg-pro-api-key": self._api_key}
        return {}

    async def get_prices(
        self,
        symbols: list[str],
        vs_currencies: list[str] = ["usd"],
        include_24h_change: bool = True,
    ) -> dict[str, dict[str, float]]:
        unknown = [s for s in symbols if s.upper() not in _UPPER_TO_COIN_ID]
        if unknown:
            raise ValueError(
                f"Unknown token symbol(s): {unknown}. Supported: {SUPPORTED_SYMBOLS}"
            )

        coin_ids = [_UPPER_TO_COIN_ID[s.upper()] for s in symbols]

        params: dict = {
            "ids": ",".join(coin_ids),
            "vs_currencies": ",".join(vs_currencies),
        }
        if include_24h_change:
            params["include_24hr_change"] = "true"

        async with httpx.AsyncClient(headers=self._headers(), timeout=15.0) as client:
            resp = await client.get(f"{self._base_url}/simple/price", params=params)
            resp.raise_for_status()
            raw: dict = resp.json()

        # Remap coin_id -> canonical symbol using the requested symbols
        requested_upper = {s.upper() for s in symbols}
        id_to_symbol = {
            v: _UPPER_TO_CANONICAL[k.upper()]
            for k, v in COINGECKO_IDS.items()
            if k.upper() in requested_upper
        }
        result: dict[str, dict[str, float]] = {}
        for coin_id, data in raw.items():
            symbol = id_to_symbol.get(coin_id, coin_id)
            result[symbol] = data

        return result

    async def get_supported_tokens(self) -> list[str]:
        return SUPPORTED_SYMBOLS


_client: Optional[CoinGeckoClient] = None


def get_coingecko_client() -> CoinGeckoClient:
    global _client
    if _client is None:
        _client = CoinGeckoClient()
    return _client
