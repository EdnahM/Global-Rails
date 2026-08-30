from decimal import Decimal
from eth_account import Account
from web3 import Web3
from ..onchain.client import get_web3, get_chain_config
from ..onchain.constants import ERC20_ABI
from ..config import settings
from .constants import (
    UNISWAP_V3,
    POOL_FEE_TIERS,
    QUOTER_V2_ABI,
    SWAP_ROUTER_ABI,
)


def _resolve_token_address(w3: Web3, chain: str, symbol: str) -> tuple[str, int]:
    """Returns (checksum_address, decimals) for a token symbol."""
    cfg = get_chain_config(chain)
    tokens = cfg.get("tokens", {})
    if symbol not in tokens:
        raise ValueError(
            f"Token '{symbol}' not found on {chain}. Available: {list(tokens.keys())}"
        )
    addr = w3.to_checksum_address(tokens[symbol])
    contract = w3.eth.contract(address=addr, abi=ERC20_ABI)
    decimals = contract.functions.decimals().call()
    return addr, decimals


def quote_swap_uniswap(
    chain: str,
    token_in: str,
    token_out: str,
    amount_in_str: str,
) -> dict:
    if chain not in UNISWAP_V3:
        raise ValueError(f"Uniswap V3 not available on chain '{chain}'")

    w3 = get_web3(chain)
    uni_cfg = UNISWAP_V3[chain]

    addr_in, decimals_in = _resolve_token_address(w3, chain, token_in)
    addr_out, decimals_out = _resolve_token_address(w3, chain, token_out)
    amount_in_raw = int(Decimal(amount_in_str) * Decimal(10 ** decimals_in))

    quoter = w3.eth.contract(
        address=w3.to_checksum_address(uni_cfg["quoter_v2"]),
        abi=QUOTER_V2_ABI,
    )

    best_fee = None
    best_amount_out = 0

    for fee in POOL_FEE_TIERS:
        try:
            result = quoter.functions.quoteExactInputSingle(
                {
                    "tokenIn": addr_in,
                    "tokenOut": addr_out,
                    "amountIn": amount_in_raw,
                    "fee": fee,
                    "sqrtPriceLimitX96": 0,
                }
            ).call()
            amount_out = result[0]
            if amount_out > best_amount_out:
                best_amount_out = amount_out
                best_fee = fee
        except Exception:
            continue

    if best_fee is None or best_amount_out == 0:
        raise ValueError(
            f"No Uniswap V3 pool found for {token_in}/{token_out} on {chain}"
        )

    amount_out_human = str(Decimal(best_amount_out) / Decimal(10 ** decimals_out))
    return {
        "dex": "uniswap_v3",
        "chain": chain,
        "token_in": token_in,
        "token_out": token_out,
        "amount_in": amount_in_str,
        "amount_out": amount_out_human,
        "fee_tier": best_fee,
        "fee_pct": best_fee / 10000,
    }


def execute_swap_uniswap(
    chain: str,
    token_in: str,
    token_out: str,
    amount_in_str: str,
    slippage_pct: float = 0.5,
) -> dict:
    if chain not in UNISWAP_V3:
        raise ValueError(f"Uniswap V3 not available on chain '{chain}'")

    w3 = get_web3(chain)
    cfg = get_chain_config(chain)
    uni_cfg = UNISWAP_V3[chain]
    private_key = settings.private_key.get_secret_value()
    sender = w3.to_checksum_address(settings.wallet_address)

    addr_in, decimals_in = _resolve_token_address(w3, chain, token_in)
    addr_out, decimals_out = _resolve_token_address(w3, chain, token_out)
    amount_in_raw = int(Decimal(amount_in_str) * Decimal(10 ** decimals_in))

    # Get best quote
    quote = quote_swap_uniswap(chain, token_in, token_out, amount_in_str)
    fee = quote["fee_tier"]
    amount_out_raw = int(Decimal(quote["amount_out"]) * Decimal(10 ** decimals_out))
    min_amount_out = int(amount_out_raw * (1 - slippage_pct / 100))

    # Approve router to spend token_in
    router_address = w3.to_checksum_address(uni_cfg["swap_router_v2"])
    token_in_contract = w3.eth.contract(address=addr_in, abi=ERC20_ABI)
    allowance = token_in_contract.functions.allowance(sender, router_address).call()

    if allowance < amount_in_raw:
        gas_price = int(w3.eth.gas_price * 1.1)
        from ..onchain.transactions import _get_nonce
        approve_fn = token_in_contract.functions.approve(router_address, amount_in_raw)
        approve_gas = approve_fn.estimate_gas({"from": sender})
        approve_tx = approve_fn.build_transaction(
            {
                "from": sender,
                "gas": int(approve_gas * 1.2),
                "gasPrice": gas_price,
                "nonce": _get_nonce(w3, sender),
                "chainId": cfg["chain_id"],
            }
        )
        signed_approve = Account.sign_transaction(approve_tx, private_key)
        w3.eth.send_raw_transaction(signed_approve.raw_transaction)

    # Execute swap
    router = w3.eth.contract(address=router_address, abi=SWAP_ROUTER_ABI)
    swap_fn = router.functions.exactInputSingle(
        {
            "tokenIn": addr_in,
            "tokenOut": addr_out,
            "fee": fee,
            "recipient": sender,
            "amountIn": amount_in_raw,
            "amountOutMinimum": min_amount_out,
            "sqrtPriceLimitX96": 0,
        }
    )

    gas_price = int(w3.eth.gas_price * 1.1)
    from ..onchain.transactions import _get_nonce
    swap_gas = swap_fn.estimate_gas({"from": sender})
    swap_tx = swap_fn.build_transaction(
        {
            "from": sender,
            "gas": int(swap_gas * 1.2),
            "gasPrice": gas_price,
            "nonce": _get_nonce(w3, sender),
            "chainId": cfg["chain_id"],
        }
    )

    signed_swap = Account.sign_transaction(swap_tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_swap.raw_transaction)
    tx_hash_hex = tx_hash.hex()

    return {
        "dex": "uniswap_v3",
        "tx_hash": tx_hash_hex,
        "explorer_url": f"{cfg['block_explorer']}/tx/{tx_hash_hex}",
        "chain": chain,
        "token_in": token_in,
        "token_out": token_out,
        "amount_in": amount_in_str,
        "expected_amount_out": quote["amount_out"],
        "min_amount_out": str(Decimal(min_amount_out) / Decimal(10 ** decimals_out)),
        "slippage_pct": slippage_pct,
        "fee_tier": fee,
        "status": "submitted",
    }
