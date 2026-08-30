# Maps token symbols to CoinGecko coin IDs
COINGECKO_IDS: dict[str, str] = {
    "ETH": "ethereum",
    "BTC": "bitcoin",
    "USDC": "usd-coin",
    "USDT": "tether",
    "cUSD": "celo-dollar",
    "cKES": "celo-kenyan-shilling",
    "cEUR": "celo-euro",
    "CELO": "celo",
    "DAI": "dai",
    "WBTC": "wrapped-bitcoin",
    "MATIC": "matic-network",
    "SOL": "solana",
    "BNB": "binancecoin",
    "AVAX": "avalanche-2",
    "WAVAX": "wrapped-avax",
}

SUPPORTED_SYMBOLS = list(COINGECKO_IDS.keys())
