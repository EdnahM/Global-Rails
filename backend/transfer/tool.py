from langchain_core.tools import tool
from pydantic import BaseModel, Field
from backend.interface import BaseWorldRailsTool, ToolResult
from backend.transfer.client import execute_mobile_payout

class TransferInput(BaseModel):
    phone_number: str = Field(
        description="Recipient mobile money number in international format without the plus, e.g., 254712345678"
    )
    amount: float = Field(description="Amount in local fiat currency to payout")
    currency: str = Field(default="KES", description="Target currency code (e.g., KES, NGN, GHS)")

class TransferSkill(BaseWorldRailsTool):
    name = "mobile_money_payout"
    description = "Triggers a last-mile mobile money (M-Pesa / MTN) payout to a recipient phone number."

    def execute(self, phone_number: str, amount: float, currency: str = "KES") -> ToolResult:
        try:
            payout_res = execute_mobile_payout(
                phone_number=phone_number, 
                amount_fiat=amount, 
                currency=currency
            )
            return ToolResult(success=True, data=payout_res)
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))

@tool("mobile_money_payout", args_schema=TransferInput)
def transfer_tool(phone_number: str, amount: float, currency: str = "KES") -> str:
    """Triggers an automated fiat payout directly to a local mobile money wallet (M-Pesa, MTN)."""
    skill = TransferSkill()
    res = skill.execute(phone_number=phone_number, amount=amount, currency=currency)
    
    # Returning the serialized string so LangChain/CrewAI can parse the JSON
    return res.to_string()