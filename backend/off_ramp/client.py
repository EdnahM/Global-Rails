"""Fiat off-ramp client.

Converts on-chain stablecoins into local fiat and pays out to a mobile money
wallet (M-Pesa / MTN MoMo). For KES specifically, this now uses real
Safaricom Daraja STK Push when configured (see off_ramp/config.py) - the
customer gets an actual prompt on their phone. For other currencies, or
when Daraja isn't configured, this falls back to the existing simulated
provider response.

STK Push is asynchronous in the payment-flow sense - see
mpesa_daraja.py's module docstring. This function returns a PENDING
status immediately when a real push is sent, not SUCCESS, since the
actual result isn't known yet at this point.
"""

import uuid

from . import mpesa_daraja


def execute_mobile_payout(phone_number: str, amount_fiat: float, currency: str = "KES") -> dict:
    """Trigger a fiat payout to a mobile money wallet.

    For KES with Daraja configured: sends a real STK Push, returns PENDING
    with a checkout_request_id to poll via /api/mpesa/status/{id}.
    Otherwise: returns a simulated successful response matching HoneyCoin's
    b2b fiat payout contract, same as before.
    """
    if currency == "KES" and mpesa_daraja._configured():
        result = mpesa_daraja.initiate_stk_push(
            phone_number=phone_number,
            amount=amount_fiat,
            account_reference="GlobalRails",
            description="Off-ramp payout",
        )
        if result.get("success"):
            return {
                "status": "PENDING",
                "checkout_request_id": result["checkout_request_id"],
                "mode": "mobile_money",
                "recipient": phone_number,
                "amount_delivered": amount_fiat,
                "currency": currency,
                "network": "M-Pesa",
                "message": result["message"],
            }
        # Real STK push was attempted but rejected/failed outright (bad
        # credentials, Safaricom down, etc.) - surface that clearly rather
        # than silently falling back to a fake success.
        return {
            "status": "FAILED",
            "error": result.get("error"),
            "detail": result.get("detail"),
            "mode": "mobile_money",
            "recipient": phone_number,
            "currency": currency,
        }

    reference = f"MPESA_{uuid.uuid4().hex[:8].upper()}"

    # ---------------------------------------------------------------------
    # PRODUCTION INTEGRATION EXAMPLE (e.g., HoneyCoin API)
    # ---------------------------------------------------------------------
    # payload = {
    #     "amount": amount_fiat,
    #     "currency": currency,
    #     "country": "KE" if currency == "KES" else "NG",
    #     "externalReference": reference,
    #     "payoutMethod": {"accountNumber": phone_number.replace("+", "")},
    #     "destination": "MoMo",
    # }
    # headers = {"Authorization": "Bearer YOUR_API_KEY"}
    # res = requests.post("https://api-v2.honeycoin.app/api/b2b/fiat/payout", json=payload, headers=headers)
    # res.raise_for_status()
    # return res.json()
    # ---------------------------------------------------------------------

    return {
        "status": "SUCCESS",
        "transaction_id": reference,
        "mode": "mobile_money",
        "recipient": phone_number,
        "amount_delivered": amount_fiat,
        "currency": currency,
        "network": "MoMo",
    }
