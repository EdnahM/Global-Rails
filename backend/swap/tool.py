from langchain_core.tools import tool
from pydantic import BaseModel, Field
from backend.interface import BaseWorldRailsTool, ToolResult
from backend.swap.client import execute_token_swap

class SwapInput(BaseModel):
    from_token: str = Field(description="Symbol of the source token to convert from, e.g., 'USDT' or 'ETH'")
    to_token: str = Field(description="Symbol of the target token to convert to, e.g., 'USDC'")
    amount: float = Field(description="Amount of the source token to swap")
    slippage: float = Field(default=0.5, description="Maximum allowed slippage percentage (default: 0.5)")

class SwapSkill(BaseWorldRailsTool):
    name = "swap_tokens"
    description = "Executes an on-chain DEX token swap (e.g., USDT to USDC) based on optimal routing and slippage parameters."

    def execute(self, from_token: str, to_token: str, amount: float, slippage: float = 0.5) -> ToolResult:
        try:
            swap_res = execute_token_swap(
                from_token=from_token,
                to_token=to_token,
                amount=amount,
                slippage_percent=slippage
            )
            return ToolResult(success=True, data=swap_res)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

@tool("swap_tokens", args_schema=SwapInput)
def swap_tool(from_token: str, to_token: str, amount: float, slippage: float = 0.5) -> str:
    """Swaps crypto tokens on-chain using DEX aggregator routing."""
    skill = SwapSkill()
    res = skill.execute(from_token=from_token, to_token=to_token, amount=amount, slippage=slippage)
    return res.to_string()
