"""transfer tool: send stablecoins on-chain with a fixed USDC gas fee."""

from pydantic import BaseModel, Field

from chains import DEFAULT_CHAIN
from transfer.client import execute_transfer
from interface import BaseTool, ToolResult


class TransferInput(BaseModel):
    to_address: str = Field(description="Destination address (0x...) to receive the stablecoins")
    token: str = Field(default="USDC", description="Stablecoin symbol to send (USDC, USDT)")
    amount: float = Field(description="Amount of the token to send")
    chain: str = Field(default=DEFAULT_CHAIN, description="Network to transfer on (currently avalanche)")
    idempotency_key: str | None = Field(default=None, description="Optional key to make the transfer idempotent / confirmable")
    pays_gas_in: str = Field(default="USDC", description="Asset used to settle gas via paymaster (USDC by default)")


class TransferTool(BaseTool):
    name = "transfer"
    description = "Send stablecoins (USDC/USDT) from an agent wallet to a destination address on the given chain, with a fixed USDC gas fee."
    input_schema = TransferInput

    def execute(
        self,
        to_address: str,
        amount: float,
        token: str = "USDC",
        chain: str = DEFAULT_CHAIN,
        idempotency_key: str | None = None,
        pays_gas_in: str = "USDC",
    ) -> ToolResult:
        try:
            data = execute_transfer(
                to_address=to_address,
                token=token,
                amount=amount,
                chain=chain,
                idempotency_key=idempotency_key,
                pays_gas_in=pays_gas_in,
            )
            return ToolResult(success=True, data=data)
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


transfer_tool = TransferTool()
