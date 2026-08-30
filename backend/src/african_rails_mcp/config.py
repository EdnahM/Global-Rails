from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Wallet
    private_key: SecretStr = SecretStr("0x0000000000000000000000000000000000000000000000000000000000000001")
    wallet_address: str = "0x0000000000000000000000000000000000000000"

    # Network
    default_chain: Literal["ethereum", "celo"] = "celo"

    # RPC endpoints
    ethereum_rpc_url: str = "https://eth.llamarpc.com"
    celo_rpc_url: str = "https://forno.celo.org"

    # CoinGecko
    coingecko_api_key: str = ""
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"

    # x402
    x402_max_spend_usd: float = 1.0


settings = Settings()
