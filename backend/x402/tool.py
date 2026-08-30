"""x402 tools: split into get_invoice + settle_invoice for agent visibility.

An HTTP 402 / L402 payment is naturally multi-step: an agent must first see
the invoice (how much, in what token, on which chain) before paying. We
expose two tools so the agent can review the cost and then settle it,
returning a proof-of-payment header.
"""

from pydantic import BaseModel, Field

from chains import DEFAULT_CHAIN
from x402.client import get_invoice, settle_invoice
from interface import BaseTool, ToolResult


class X402GetInvoiceInput(BaseModel):
    url: str = Field(description="The URL / endpoint that returned an HTTP 402 Payment Required challenge")
    token: str = Field(default="USDC", description="Stablecoin used to pay the invoice (e.g. USDC)")
    amount: float = Field(default=1.0, description="Expected invoice amount in `token`. Used until the real 402 header is parsed.")
    chain: str = Field(default=DEFAULT_CHAIN, description="Network the invoice is denominated on")


class X402GetInvoiceTool(BaseTool):
    name = "x402_get_invoice"
    description = "Resolve an HTTP 402 payment challenge / URL into an invoice (amount, token, chain) so an agent can see the cost before paying."
    input_schema = X402GetInvoiceInput

    def execute(self, url: str, token: str = "USDC", amount: float = 1.0, chain: str = DEFAULT_CHAIN) -> ToolResult:
        try:
            return ToolResult(success=True, data=get_invoice(url, token, amount, chain))
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


class X402SettleInvoiceInput(BaseModel):
    invoice_id: str = Field(description="Invoice id returned by x402_get_invoice")
    chain: str = Field(default=DEFAULT_CHAIN, description="Network the invoice is denominated on")


class X402SettleInvoiceTool(BaseTool):
    name = "x402_settle_invoice"
    description = "Pay a previously-issued x402 invoice and return proof of payment (preimage / auth header) for retrying the protected request."
    input_schema = X402SettleInvoiceInput

    def execute(self, invoice_id: str, chain: str = DEFAULT_CHAIN) -> ToolResult:
        try:
            return ToolResult(success=True, data=settle_invoice(invoice_id, chain))
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))


x402_get_invoice_tool = X402GetInvoiceTool()
x402_settle_invoice_tool = X402SettleInvoiceTool()
