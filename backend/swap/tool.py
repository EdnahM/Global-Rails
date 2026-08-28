# removed langchain_core since we literary don't use it, adapter handles it already
# we can't be redudant here

"""swap tool: on-chain token swap, multi-chain."""

from pydantic import BaseModel, Field

from backend.chains import DEFAULT_CHAIN
from backend.swap.client import execute_token_swap
from backend.interface import BaseTool, ToolResult


class SwapInput(BaseModel):
    from_token: str = Field(description="Source token symbol, e.g. USDT, USDC, AVAX")
    to_token: str = Field(description="Target token symbol, e.g. USDC, USDT")
    amount: float = Field(description="Amount of the source token to swap")
    slippage: float = Field(default=0.5, description="Maximum allowed slippage percentage")
    chain: str = Field(default=DEFAULT_CHAIN, description="Network to swap on (currently avalanche)")


class SwapTool(BaseTool):
    name = "swap_tokens"
    description = "Swap one token for another on-chain (e.g. USDT to USDC) on the given chain, with optimal routing and a slippage cap."
    input_schema = SwapInput

    def execute(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        slippage: float = 0.5,
        chain: str = DEFAULT_CHAIN,
    ) -> ToolResult:
        try:
            data = execute_token_swap(
                from_token=from_token,
                to_token=to_token,
                amount=amount,
                slippage_percent=slippage,
                chain=chain,
            )
            return ToolResult(success=True, data=data)
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))
        
# simplify swap_tool
swap_tool = SwapTool()
