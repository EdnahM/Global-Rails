from langchain_core.tools import tool
from pydantic import BaseModel, Field
from backend.interface import BaseWorldRailsTool, ToolResult
from backend.x402.client import execute_l402_payment

class X402Input(BaseModel):
    invoice_token: str = Field(description="The L402 payment request string or LN invoice challenge from an HTTP 402 header")
    max_amount_sats: int = Field(default=1000, description="Maximum amount in satoshis/micro-units the agent is authorized to spend")

class X402Skill(BaseWorldRailsTool):
    name = "pay_l402_paywall"
    description = "Executes an L402 (HTTP 402) micropayment to unlock paid API endpoints or machine-to-machine data services."

    def execute(self, invoice_token: str, max_amount_sats: int = 1000) -> ToolResult:
        try:
            pay_res = execute_l402_payment(invoice_token=invoice_token, max_amount_sats=max_amount_sats)
            return ToolResult(success=True, data=pay_res)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

@tool("pay_l402_paywall", args_schema=X402Input)
def x402_tool(invoice_token: str, max_amount_sats: int = 1000) -> str:
    """Pays an HTTP 402 / L402 invoice token to unlock paid AI API access."""
    skill = X402Skill()
    res = skill.execute(invoice_token=invoice_token, max_amount_sats=max_amount_sats)
    return res.to_string()
