"""x402 (HTTP 402 / L402-style) client.

Implements the agent-payment flow over the HTTP "402 Payment Required"
protocol: a client first resolves a 402 challenge into a structurable
invoice, and can then settle it, returning a proof of payment (a preimage /
macaroon) used to retry the protected request.

Both steps are currently simulated. The underlying payment network can be
Lightning (L402) or any stablecoin/x402 provider; the tool surface stays the
same.
"""

import uuid

from chains import DEFAULT_CHAIN, get_chain


def get_invoice(url: str, token: str = "USDC", amount: float = 1.0, chain: str = DEFAULT_CHAIN) -> dict:
    """Resolve a 402 challenge / resource URL into a payable invoice.

    Returns the invoice (id, amount, token, chain) so an agent can review the
    cost before paying.
    """
    chain_cfg = get_chain(chain)
    # ---------------------------------------------------------------------
    # PRODUCTION: perform an HTTP request to `url`; on a 402, parse the
    # WWW-Authenticate / x402 challenge header into an invoice (amount,
    # currency/token, network).
    # ---------------------------------------------------------------------
    return {
        "invoice_id": f"inv-{uuid.uuid4().hex[:12]}",
        "url": url,
        "token": token.upper(),
        "amount": amount,
        "chain": chain_cfg.name,
        "chain_id": chain_cfg.chain_id,
        "status": "PENDING",
    }


def settle_invoice(invoice_id: str, chain: str = DEFAULT_CHAIN) -> dict:
    """Pay a previously-issued invoice and return proof of payment."""
    chain_cfg = get_chain(chain)
    payment_hash = f"hash_{uuid.uuid4().hex[:16]}"
    preimage = f"preimage_{uuid.uuid4().hex}"

    # ---------------------------------------------------------------------
    # PRODUCTION: submit payment for `invoice_id` via the payment network
    # (e.g. Alby / LNURL / Lightning node for L402, or a stablecoin x402
    # provider). On success, return the preimage used to build the L402
    # auth header.
    # ---------------------------------------------------------------------

    return {
        "invoice_id": invoice_id,
        "status": "PAID",
        "token": "USDC",
        "chain": chain_cfg.name,
        "chain_id": chain_cfg.chain_id,
        "payment_hash": payment_hash,
        "preimage": preimage,
        "auth_header": f"L402 {preimage}:{payment_hash}",
    }
