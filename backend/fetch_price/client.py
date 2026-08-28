import requests

def get_market_price(token: str = "USDC", fiat: str = "KES") -> float:
    """Fetches real-time crypto-to-fiat exchange rates."""
    # Using CoinGecko simple price endpoint as fallback oracle
    url = f"https://api.coingecko.com/api/v3/simple/price?ids=usd-coin,tether&vs_currencies={fiat.lower()}"
    res = requests.get(url, timeout=10)
    res.raise_for_status()
    data = res.json()
    
    mapping = {"USDC": "usd-coin", "USDT": "tether"}
    coin_id = mapping.get(token.upper(), "usd-coin")
    return float(data.get(coin_id, {}).get(fiat.lower(), 130.0))