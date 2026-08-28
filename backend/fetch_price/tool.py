from langchain_core.tools import tool
from pydantic import BaseModel, Field
from backend.interface import BaseWorldRailsTool, ToolResult
from backend.fetch_price.client import get_market_price

class FetchPriceInput(BaseModel):
    token: str = Field(default="USDC", description="Token ticker symbol (e.g., USDC, USDT)")
    fiat: str = Field(default="KES", description="African fiat currency code (e.g., KES, NGN, GHS)")

class FetchPriceSkill(BaseWorldRailsTool):
    name = "fetch_market_price"
    description = "Fetches the real-time conversion price between crypto stablecoins and African fiat."

    def execute(self, token: str = "USDC", fiat: str = "KES") -> ToolResult:
        try:
            rate = get_market_price(token=token, fiat=fiat)
            return ToolResult(
                success=True,
                data={"token": token, "fiat": fiat, "rate": rate}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

@tool("fetch_market_price", args_schema=FetchPriceInput)
def fetch_price_tool(token: str = "USDC", fiat: str = "KES") -> str:
    """Fetches current exchange rate between crypto stablecoins and African local fiat."""
    skill = FetchPriceSkill()
    res = skill.execute(token=token, fiat=fiat)
    return res.to_string()