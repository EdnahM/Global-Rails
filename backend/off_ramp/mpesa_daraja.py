"""Safaricom Daraja STK Push (M-Pesa Express) client.

STK Push is asynchronous *in the payment-flow sense*: initiating a push
only confirms the prompt was sent to the customer's phone, not that they
paid. The actual result arrives later via a callback Safaricom calls on
its own schedule.

This module itself is written with plain synchronous requests calls, not
async/await - deliberately, to match execute_mobile_payout() and the rest
of this codebase's BaseTool.execute() interface, which is synchronous
throughout. Mixing in asyncio.run() here would break the moment this runs
inside a request that's already inside a running event loop (which is
exactly how it's actually invoked, via the async REST routes in
rails_mcp/server.py) - asyncio.run() cannot start a second event loop
inside one that's already running.

Three pieces:
  - initiate_stk_push(): sends the prompt, returns immediately with a
    checkout_request_id to track.
  - handle_callback(): called by the /api/mpesa/callback route when
    Safaricom's servers report the result.
  - get_stk_status(): looked up by the polling status route so the
    frontend can find out what happened.

All state is an in-memory dict, which is fine for a single persistent
Render web service process, but will NOT survive a process restart or
work correctly across multiple instances - a real datastore (Redis, a DB
table) would be needed at that point. Flagging this directly rather than
letting it be a silent surprise later.
"""
from __future__ import annotations

import base64
import time
from datetime import datetime

import requests

from . import config as mpesa_config

_PENDING: dict[str, dict] = {}
_token_cache: dict[str, float | str | None] = {"token": None, "expires_at": 0}


def _configured() -> bool:
    return all([
        mpesa_config.CONSUMER_KEY,
        mpesa_config.CONSUMER_SECRET,
        mpesa_config.SHORTCODE,
        mpesa_config.PASSKEY,
        mpesa_config.CALLBACK_URL,
    ])


def _normalize_phone(phone_number: str) -> str:
    """Daraja requires 254XXXXXXXXX - no +, no leading 0."""
    phone = phone_number.strip().lstrip("+").replace(" ", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif phone.startswith("7") or phone.startswith("1"):
        phone = "254" + phone
    return phone


def _get_access_token() -> str:
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]  # type: ignore[return-value]

    auth = base64.b64encode(
        f"{mpesa_config.CONSUMER_KEY}:{mpesa_config.CONSUMER_SECRET}".encode()
    ).decode()

    resp = requests.get(
        f"{mpesa_config.BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
        headers={"Authorization": f"Basic {auth}"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    token = data["access_token"]
    # expires_in is typically "3599" (~1hr) - refresh a minute early to be safe
    _token_cache["token"] = token
    _token_cache["expires_at"] = now + int(data.get("expires_in", 3599)) - 60
    return token


def _build_password_and_timestamp() -> tuple[str, str]:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"{mpesa_config.SHORTCODE}{mpesa_config.PASSKEY}{timestamp}"
    password = base64.b64encode(raw.encode()).decode()
    return password, timestamp


def initiate_stk_push(
    phone_number: str,
    amount: float,
    account_reference: str = "GlobalRails",
    description: str = "Payment",
) -> dict:
    """Sends the STK prompt. Returns immediately once Safaricom accepts the
    request - this does NOT mean payment succeeded, only that the prompt
    was sent. Poll get_stk_status() with the returned checkout_request_id
    for the actual result."""
    if not _configured():
        missing = [
            name for name, val in [
                ("MPESA_CONSUMER_KEY", mpesa_config.CONSUMER_KEY),
                ("MPESA_CONSUMER_SECRET", mpesa_config.CONSUMER_SECRET),
                ("MPESA_SHORTCODE", mpesa_config.SHORTCODE),
                ("MPESA_PASSKEY", mpesa_config.PASSKEY),
                ("MPESA_CALLBACK_URL", mpesa_config.CALLBACK_URL),
            ] if not val
        ]
        return {
            "success": False,
            "error": "MPESA_NOT_CONFIGURED",
            "detail": f"Missing environment variable(s): {', '.join(missing)}",
        }

    phone = _normalize_phone(phone_number)

    try:
        token = _get_access_token()
    except Exception as exc:
        return {"success": False, "error": "AUTH_ERROR", "detail": str(exc)}

    password, timestamp = _build_password_and_timestamp()

    payload = {
        "BusinessShortCode": mpesa_config.SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": mpesa_config.SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": mpesa_config.CALLBACK_URL,
        "AccountReference": account_reference[:12],
        "TransactionDesc": description[:13],
    }

    try:
        resp = requests.post(
            f"{mpesa_config.BASE_URL}/mpesa/stkpush/v1/processrequest",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        data = resp.json()
    except Exception as exc:
        return {"success": False, "error": "REQUEST_FAILED", "detail": str(exc)}

    if resp.status_code != 200 or "CheckoutRequestID" not in data:
        return {
            "success": False,
            "error": "STK_PUSH_REJECTED",
            "detail": data.get("errorMessage") or data.get("ResponseDescription") or str(data),
        }

    checkout_id = data["CheckoutRequestID"]
    _PENDING[checkout_id] = {"status": "PENDING", "created_at": time.time()}

    return {
        "success": True,
        "checkout_request_id": checkout_id,
        "merchant_request_id": data.get("MerchantRequestID"),
        "status": "PENDING",
        "message": "Prompt sent - check your phone",
    }


def handle_callback(payload: dict) -> None:
    """Called by the /api/mpesa/callback route. Safaricom's callback shape
    wraps everything in Body.stkCallback, with successful-payment details
    buried in a list of {Name, Value} dicts rather than a clean object."""
    try:
        cb = payload["Body"]["stkCallback"]
        checkout_id = cb["CheckoutRequestID"]
        result_code = cb["ResultCode"]

        if result_code == 0:
            items = {
                item["Name"]: item.get("Value")
                for item in cb.get("CallbackMetadata", {}).get("Item", [])
            }
            _PENDING[checkout_id] = {
                "status": "SUCCESS",
                "amount": items.get("Amount"),
                "mpesa_receipt": items.get("MpesaReceiptNumber"),
                "phone_number": items.get("PhoneNumber"),
                "transaction_date": items.get("TransactionDate"),
            }
        else:
            _PENDING[checkout_id] = {
                "status": "FAILED",
                "result_code": result_code,
                "result_desc": cb.get("ResultDesc", "Payment failed or was cancelled"),
            }
    except (KeyError, TypeError):
        # Malformed/unexpected callback shape - nothing sensible to store,
        # but this must never raise, since Safaricom expects a clean ack
        # response regardless.
        pass


def get_stk_status(checkout_request_id: str) -> dict:
    result = _PENDING.get(checkout_request_id)
    if result is None:
        return {"success": False, "error": "NOT_FOUND", "detail": "Unknown checkout_request_id"}
    return {"success": True, **result}
