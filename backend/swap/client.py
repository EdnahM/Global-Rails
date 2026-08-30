"""On-chain token swap client (multi-chain).

Routes a token-to-token swap through a DEX aggregator on the requested
chain. Currently simulated; the aggregator call (e.g. 1inch) can be wired
without changing the tool surface.
"""

import uuid

from backend.chains import DEFAULT_CHAIN, get_chain


def execute_token_swap(
    from_token: str,
    to_token: str,
    amount: float,
    slippage_percent: float = 0.5,
    chain: str = DEFAULT_CHAIN,
) -> dict:
    """Swap 'amount' of 'from_token' to 'to_token' on 'chain'.

    Returns simulated routing metadata plus a quote of the expected output.
    """
    chain_cfg = get_chain(chain)
    tx_hash = f"0x{uuid.uuid4().hex}{uuid.uuid4().hex[:32]}"

    from_sym = from_token.upper()
    to_sym = to_token.upper()
    # Stablecoin pairs route ~1:1; non-stable pairs get a small simulated
    # slippage-adjusted rate until a real DEX quote/route is wired.
    rate = 1.0 if ({from_sym, to_sym} <= {"USDC", "USDT", "USDC.E", "USDT.E"}) else 0.98
    expected_out = round(amount * rate, 4)

    # ---------------------------------------------------------------------
    # PRODUCTION INTEGRATION EXAMPLE (e.g., 1inch / other aggregator)
    # ---------------------------------------------------------------------
    # quote = requests.get(
    #     f"https://api.1inch.dev/swap/v5.2/{chain_cfg.chain_id}/swap"
    #     f"?src={from_sym}&dst={to_sym}&amount={amount}&slippage={slippage_percent}"
    # )
    # tx = send_raw_transaction(quote.json()["tx"])
    # ---------------------------------------------------------------------

    return {
        "status": "CONFIRMED",
        "tx_hash": tx_hash,
        "from_token": from_sym,
        "to_token": to_sym,
        "amount_in": amount,
        "amount_out": expected_out,
        "slippage_tolerance": f"{slippage_percent}%",
        "chain": chain_cfg.name,
        "chain_id": chain_cfg.chain_id,
        "native_asset": chain_cfg.native_asset,
    }