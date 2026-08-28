"""Fiat off-ramp client.

Converts on-chain stablecoins into local fiat and pays out to a mobile money
wallet (M-Pesa / MTN MoMo) via infrastructure providers such as HoneyCoin or
Kotani Pay. This is the "last mile" / wide-rails layer that connects Global
Rails' on-chain stablecoin settlement to real-world mobile money.

The provider call is currently simulated. The production payload shape used
by HoneyCoin is documented inline and can be wired without changing the tool
surface.
"""

import uuid


def execute_mobile_payout(phone_number: str, amount_fiat: float, currency: str = "KES") -> dict:
    """Trigger a fiat payout to a mobile money wallet.

    Returns a simulated successful response matching HoneyCoin's b2b fiat
    payout contract.
    """
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
