import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class ToolResult(BaseModel):
    """Standardized response format for all World Rails SDK tools."""
    success: bool = Field(description="Indicates if the tool execution was successful")
    data: Dict[str, Any] = Field(default_factory=dict, description="Payload containing the result of the tool execution")
    error: Optional[str] = Field(default=None, description="Error message if the execution failed")

    def to_string(self) -> str:
        """Serializes the result to a JSON-formatted string for LLMs."""
        return json.dumps(self.model_dump(), indent=2)

class BaseWorldRailsTool(ABC):
    """Abstract Base Class for all tools in the World Rails SDK."""
    name: str
    description: str

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        pass


# =====================================================================
# QUICK SELF-TEST BLOCK
# =====================================================================
if __name__ == "__main__":
    print("--- Testing interface.py Base Contracts ---\n")

    # 1. Create a mock tool using the NEW interface contract name
    class MockPaymentTool(BaseWorldRailsTool):
        name = "mock_payout"
        description = "Mocks a payment execution for testing."

        def execute(self, amount: float, recipient: str) -> ToolResult:
            if amount <= 0:
                return ToolResult(success=False, error="Amount must be greater than 0")
            return ToolResult(
                success=True,
                data={"transaction_id": "TX_12345", "amount": amount, "recipient": recipient}
            )

    tool = MockPaymentTool()

    # 2. Test Success Execution
    success_response = tool.execute(amount=50.0, recipient="+254712345678")
    print("Test 1 (Success Case Output):")
    print(success_response.to_string())

    # 3. Test Failure Execution
    failure_response = tool.execute(amount=-10.0, recipient="+254712345678")
    print("\nTest 2 (Failure Case Output):")
    print(failure_response.to_string())
    print("\n Interface definitions verified successfully!")
    