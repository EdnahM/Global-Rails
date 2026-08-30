"""off_ramp tool: convert stablecoins to fiat and pay out to mobile money."""

from pydantic import BaseModel, Field

from off_ramp.client import execute_mobile_payout
from interface import BaseTool, ToolResult


class OffRampInput(BaseModel):
    phone_number: str = Field(description="Recipient mobile money number, international format without plus, e.g. 254712345678")
    amount: float = Field(description="Amount in local fiat currency to pay out")
    currency: str = Field(default="KES", description="Target currency code (e.g. KES, NGN, GHS)")


class OffRampTool(BaseTool):
    name = "off_ramp_payout"
    description = "Pay out local fiat to a mobile money wallet (M-Pesa / MTN MoMo), the last-mile off-ramp from on-chain stablecoins."
    input_schema = OffRampInput

    def execute(self, phone_number: str, amount: float, currency: str = "KES") -> ToolResult:
        try:
            data = execute_mobile_payout(
                phone_number=phone_number, amount_fiat=amount, currency=currency
            )
            return ToolResult(success=True, data=data)
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


off_ramp_tool = OffRampTool()
