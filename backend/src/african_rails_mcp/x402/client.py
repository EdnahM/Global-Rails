import httpx
from typing import Any
from ..config import settings


class X402PaymentClient:
    """
    Handles x402 (HTTP 402 Payment Required) micropayment flows.

    The x402 protocol allows AI agents to autonomously pay for API resources
    that require payment. When a server returns HTTP 402, this client:
    1. Parses the payment requirement from the response body
    2. Creates an EIP-3009 off-chain payment signature
    3. Retries the request with the X-PAYMENT header

    This enables agent-initiated micropayments without human approval per call.
    """

    def __init__(self, max_spend_usd: float | None = None):
        self.max_spend_usd = max_spend_usd or settings.x402_max_spend_usd
        self._wallet_address = settings.wallet_address
        self._private_key = settings.private_key.get_secret_value()

    async def fetch(
        self,
        url: str,
        method: str = "GET",
        headers: dict | None = None,
        body: dict | Any = None,
    ) -> dict:
        """
        Fetch a URL, automatically handling x402 payment if required.
        Returns the response body or an error dict.
        """
        try:
            from x402.client import Client as X402Client
        except ImportError:
            return await self._fetch_without_x402(url, method, headers, body)

        try:
            client = X402Client(
                private_key=self._private_key,
                max_value=self.max_spend_usd,
            )
            response = await client.fetch(url, method=method, headers=headers or {}, json=body)

            if hasattr(response, "json"):
                try:
                    resp_body = response.json()
                except Exception:
                    resp_body = response.text if hasattr(response, "text") else str(response)
            else:
                resp_body = str(response)

            status = response.status_code if hasattr(response, "status_code") else 200
            return {
                "success": True,
                "status": status,
                "body": resp_body,
                "paid": True,
                "url": url,
            }
        except Exception as e:
            error_str = str(e)
            if "402" in error_str or "payment" in error_str.lower():
                return {
                    "success": False,
                    "error": "PAYMENT_REQUIRED",
                    "detail": error_str,
                    "url": url,
                }
            return {
                "success": False,
                "error": "FETCH_ERROR",
                "detail": error_str,
                "url": url,
            }

    async def check_price(self, url: str) -> dict:
        """
        Check payment requirement for a URL without paying.
        Sends a request and inspects the 402 response if present.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 402:
                    try:
                        payment_info = resp.json()
                        return {"success": True, "payment_required": True, **payment_info}
                    except Exception:
                        return {
                            "success": True,
                            "payment_required": True,
                            "raw_response": resp.text,
                        }
                return {
                    "success": True,
                    "payment_required": False,
                    "status": resp.status_code,
                }
            except Exception as e:
                return {"success": False, "error": "FETCH_ERROR", "detail": str(e)}

    async def _fetch_without_x402(
        self, url: str, method: str, headers: dict | None, body: Any
    ) -> dict:
        """Fallback: standard HTTP fetch without x402 support."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            req_kwargs: dict = {"headers": headers or {}}
            if body:
                req_kwargs["json"] = body

            resp = await client.request(method, url, **req_kwargs)
            if resp.status_code == 402:
                return {
                    "success": False,
                    "error": "PAYMENT_REQUIRED",
                    "detail": "x402 library not installed. Install with: pip install x402",
                    "payment_info": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
                }

            try:
                resp_body = resp.json()
            except Exception:
                resp_body = resp.text

            return {
                "success": resp.status_code < 400,
                "status": resp.status_code,
                "body": resp_body,
                "paid": False,
                "url": url,
            }


_client: X402PaymentClient | None = None


def get_x402_client() -> X402PaymentClient:
    global _client
    if _client is None:
        _client = X402PaymentClient()
    return _client
