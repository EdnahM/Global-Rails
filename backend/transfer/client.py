"""On-chain stablecoin transfer client.

Sends a stablecoin (USDC by default) from an agent-controlled wallet to a
destination address on a given chain. Gas is settled through an ERC-4337
paymaster in USDC at a fixed, predictable rate — the "know the fee before you
send" promise of Global Rails.

The on-chain broadcast (web3.py / MPC / bundler) is currently simulated.
Production integration points are documented inline and can be wired without
changing the tool surface.
"""

import uuid

from chains import DEFAULT_CHAIN, get_chain, quote_gas_fee_usdc


def execute_transfer(
    to_address: str,
    token: str,
    amount: float,
    chain: str = DEFAULT_CHAIN,
    idempotency_key: str | None = None,
    pays_gas_in: str = "USDC",
) -> dict:
    """Send 'amount' of 'token' to 'to_address' on 'chain'.

    Returns transfer metadata plus the fixed USDC gas fee (paymaster).
    """
    chain_cfg = get_chain(chain)
    key = idempotency_key or f"tx-{uuid.uuid4().hex[:24]}"
    gas_fee_usdc = quote_gas_fee_usdc(chain)

    # ---------------------------------------------------------------------
    # PRODUCTION INTEGRATION EXAMPLE (ERC-4337 + paymaster bundler)
    # ---------------------------------------------------------------------
    # 1. Build UserOperation calling the token's transfer(to, amount).
    # 2. Submit to a bundler (e.g. pimlico/alchemy). The paymaster signs and
    #    credits gas in USDC — so the cost to the agent is exactly
    #    `quote_gas_fee_usdc(chain)` USDC, not unpredictable native gas.
    # 3. Poll for the UserOperation receipt, return its tx hash.
    # tx_hash = send_user_operation(user_op, paymaster=usdc_paymaster)
    # ---------------------------------------------------------------------

    return {
        "status": "SIMULATED",
        "tx_hash": f"0x{uuid.uuid4().hex}",
        "to_address": to_address,
        "token": token.upper(),
        "amount": amount,
        "chain": chain_cfg.name,
        "chain_id": chain_cfg.chain_id,
        "native_asset": chain_cfg.native_asset,
        "pays_gas_in": pays_gas_in.upper(),
        "gas_fee_usdc": gas_fee_usdc,
        "idempotency_key": key,
    }
