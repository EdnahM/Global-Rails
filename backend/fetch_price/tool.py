"""fetch_price tool: real-time token and fiat prices, multi-chain."""

from pydantic import BaseModel, Field

from backend.chains import DEFAULT_CHAIN
from backend.fetch_price.client import get_market_price
from backend.interface import BaseTool, ToolResult


class FetchPriceInput(BaseModel):
    token: str = Field(default="USDC", description="Token symbol, e.g. USDC, USDT, AVAX, ETH")
    quote: str = Field(default="USD", description="Quote currency: a fiat code (USD, KES, NGN, GHS) or another token symbol (USDC, USDT)")
    chain: str = Field(default=DEFAULT_CHAIN, description="Network to price on (currently avalanche)")


class FetchPriceTool(BaseTool):
    name = "fetch_market_price"
    description = "Fetch the real-time price of a token (stablecoin or native asset) in fiat or another token, on the given chain."
    input_schema = FetchPriceInput

    def execute(self, token: str = "USDC", quote: str = "USD", chain: str = DEFAULT_CHAIN) -> ToolResult:
        try:
            data = get_market_price(token=token, quote=quote, chain=chain)
            return ToolResult(success=True, data=data)
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


fetch_price_tool = FetchPriceTool()
