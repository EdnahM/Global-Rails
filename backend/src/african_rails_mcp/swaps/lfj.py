"""LFJ (formerly Trader Joe) router swaps — Avalanche's native DEX.

Uniswap V3 isn't configured for avalanche-fuji at all (see swaps/constants.py),
and even where V3 exists, testnet liquidity is typically minimal-to-nonexistent.
LFJ is Avalanche's own DEX and has real, faucet-connected liquidity on Fuji,
which is why this exists as a separate path rather than trying to force V3
onto a chain it was never configured for.

The router/quote logic here (direct pool first, then via WAVAX, matching
`find_route`'s two-hop strategy) and the Transfer-log amount reading (instead
of a pre/post balanceOf diff, which can race a lagging RPC node) are adapted
directly from a working bot's implementation, generalized from its
AVAX-only buy/sell pair into full token-to-token swaps — e.g. USDC to LINK,
not just AVAX <-> token — since quote_swap()/execute_swap() promise that for
every DEX path, not just this one.
"""
from decimal import Decimal

from eth_account import Account
from web3 import Web3

from ..onchain.client import get_web3, get_chain_config
from ..onchain.constants import ERC20_ABI
from ..onchain.transactions import _get_nonce
from ..config import settings
from .constants import LFJ_ROUTER

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

ROUTER_ABI = [
    {"inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "path", "type": "address[]"}],
     "name": "getAmountsOut", "outputs": [{"name": "amounts", "type": "uint256[]"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "amountOutMin", "type": "uint256"}, {"name": "path", "type": "address[]"},
                {"name": "to", "type": "address"}, {"name": "deadline", "type": "uint256"}],
     "name": "swapExactAVAXForTokens", "outputs": [{"name": "amounts", "type": "uint256[]"}],
     "stateMutability": "payable", "type": "function"},
    {"inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "amountOutMin", "type": "uint256"},
                {"name": "path", "type": "address[]"}, {"name": "to", "type": "address"},
                {"name": "deadline", "type": "uint256"}],
     "name": "swapExactTokensForAVAX", "outputs": [{"name": "amounts", "type": "uint256[]"}],
     "stateMutability": "nonpayable", "type": "function"},
    # Standard V2-router function, not present in the source bot (it only
    # ever traded against native AVAX) — needed here for genuine
    # token-to-token pairs like USDC->LINK. Every V2-style router exposes
    # this alongside the AVAX-specific variants above; LFJ's own docs list
    # the same getAmountsOut/path/deadline signature the bot already uses,
    # which is the same router family this belongs to.
    {"inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "amountOutMin", "type": "uint256"},
                {"name": "path", "type": "address[]"}, {"name": "to", "type": "address"},
                {"name": "deadline", "type": "uint256"}],
     "name": "swapExactTokensForTokens", "outputs": [{"name": "amounts", "type": "uint256[]"}],
     "stateMutability": "nonpayable", "type": "function"},
]


def _is_native(chain_cfg: dict, symbol: str) -> bool:
    return symbol.upper() in (chain_cfg["native_symbol"].upper(), "AVAX", "NATIVE")


def _resolve_token(w3: Web3, chain: str, symbol: str) -> tuple[str, int]:
    """Returns (checksum_address, decimals). Raises for unknown symbols —
    same contract as uniswap_v3._resolve_token_address, kept as this
    module's own copy rather than a cross-import, matching how mento.py and
    uniswap_v3.py are each self-contained."""
    cfg = get_chain_config(chain)
    tokens = cfg.get("tokens", {})
    if symbol not in tokens:
        raise ValueError(f"Token '{symbol}' not found on {chain}. Available: {list(tokens.keys())}")
    addr = w3.to_checksum_address(tokens[symbol])
    contract = w3.eth.contract(address=addr, abi=ERC20_ABI)
    return addr, contract.functions.decimals().call()


def _wavax_address(w3: Web3, chain: str) -> str:
    cfg = get_chain_config(chain)
    tokens = cfg.get("tokens", {})
    if "WAVAX" not in tokens:
        raise ValueError(f"WAVAX not configured on {chain} — required as the routing hub for LFJ swaps")
    return w3.to_checksum_address(tokens["WAVAX"])


def can_use_lfj(chain: str) -> bool:
    return chain in LFJ_ROUTER


def _find_route(
    w3: Web3, router, chain: str, addr_in: str, addr_out: str, amount_in_raw: int
) -> tuple[list[str], int]:
    """Direct pool first, then via WAVAX — same two-hop strategy as the
    source bot's find_route(), generalized from "always ends/starts at
    WAVAX" to any token pair (WAVAX is skipped as a hop when it's already
    one side of the direct pair)."""
    wavax = _wavax_address(w3, chain)
    candidates = [[addr_in, addr_out]]
    if wavax not in (addr_in, addr_out):
        candidates.append([addr_in, wavax, addr_out])
    for path in candidates:
        try:
            amounts = router.functions.getAmountsOut(amount_in_raw, path).call()
            out = int(amounts[-1])
            if out > 0:
                return path, out
        except Exception:
            continue
    return [], 0


def _amount_from_receipt(receipt: dict, token_addr: str, recipient: str) -> int:
    """Reads the exact received amount from the Transfer log rather than a
    balanceOf() diff — avoids the race the source bot's docstring calls out:
    a diff taken right after the swap can read a lagging RPC node's
    pre-swap balance. Only used for the swapExactTokensForAVAX /
    swapExactTokensForTokens paths; the AVAX-out amount for a *from*-AVAX
    swap comes from the router's own returned `amounts`, not a token log."""
    total, token_addr, recipient = 0, token_addr.lower(), recipient.lower()
    for log in receipt.get("logs", []):
        try:
            if log["address"].lower() != token_addr:
                continue
            topics = log.get("topics") or []
            if len(topics) < 3 or topics[0].hex().lower() != TRANSFER_TOPIC.lower():
                continue
            if ("0x" + topics[2].hex()[-40:]).lower() != recipient:
                continue
            total += int.from_bytes(log["data"], "big") if isinstance(log["data"], bytes) else int(log["data"], 16)
        except Exception:
            continue
    return total


def quote_swap_lfj(chain: str, token_in: str, token_out: str, amount_in_str: str) -> dict:
    if chain not in LFJ_ROUTER:
        raise ValueError(f"LFJ not available on chain '{chain}'")

    w3 = get_web3(chain)
    cfg = get_chain_config(chain)
    router = w3.eth.contract(address=w3.to_checksum_address(LFJ_ROUTER[chain]), abi=ROUTER_ABI)

    native_in, native_out = _is_native(cfg, token_in), _is_native(cfg, token_out)
    if native_in and native_out:
        raise ValueError("token_in and token_out can't both be the native asset")

    if native_in:
        addr_in, decimals_in = _wavax_address(w3, chain), 18
    else:
        addr_in, decimals_in = _resolve_token(w3, chain, token_in)
    if native_out:
        addr_out, decimals_out = _wavax_address(w3, chain), 18
    else:
        addr_out, decimals_out = _resolve_token(w3, chain, token_out)

    amount_in_raw = int(Decimal(amount_in_str) * Decimal(10 ** decimals_in))

    path, amount_out_raw = _find_route(w3, router, chain, addr_in, addr_out, amount_in_raw)
    if not path:
        raise ValueError(f"No LFJ route found for {token_in}/{token_out} on {chain}")

    return {
        "dex": "lfj",
        "chain": chain,
        "token_in": token_in,
        "token_out": token_out,
        "amount_in": amount_in_str,
        "amount_out": str(Decimal(amount_out_raw) / Decimal(10 ** decimals_out)),
        "route_hops": len(path) - 1,
    }


def execute_swap_lfj(
    chain: str, token_in: str, token_out: str, amount_in_str: str, slippage_pct: float = 0.5
) -> dict:
    if chain not in LFJ_ROUTER:
        raise ValueError(f"LFJ not available on chain '{chain}'")

    w3 = get_web3(chain)
    cfg = get_chain_config(chain)
    router_address = w3.to_checksum_address(LFJ_ROUTER[chain])
    router = w3.eth.contract(address=router_address, abi=ROUTER_ABI)
    private_key = settings.private_key.get_secret_value()
    sender = w3.to_checksum_address(settings.wallet_address)

    native_in, native_out = _is_native(cfg, token_in), _is_native(cfg, token_out)
    if native_in and native_out:
        raise ValueError("token_in and token_out can't both be the native asset")

    if native_in:
        addr_in, decimals_in = _wavax_address(w3, chain), 18
    else:
        addr_in, decimals_in = _resolve_token(w3, chain, token_in)
    if native_out:
        addr_out, decimals_out = _wavax_address(w3, chain), 18
    else:
        addr_out, decimals_out = _resolve_token(w3, chain, token_out)

    amount_in_raw = int(Decimal(amount_in_str) * Decimal(10 ** decimals_in))

    path, expected_out = _find_route(w3, router, chain, addr_in, addr_out, amount_in_raw)
    if not path:
        raise ValueError(f"No LFJ route found for {token_in}/{token_out} on {chain}")
    min_out = int(expected_out * (1 - slippage_pct / 100))
    deadline = int(w3.eth.get_block("latest")["timestamp"]) + 300
    gas_price = int(w3.eth.gas_price * 1.1)

    # Approve the router for a non-native input — not needed when paying in
    # AVAX itself, since swapExactAVAXForTokens takes the input as msg.value.
    if not native_in:
        token_in_contract = w3.eth.contract(address=addr_in, abi=ERC20_ABI)
        allowance = token_in_contract.functions.allowance(sender, router_address).call()
        if allowance < amount_in_raw:
            approve_fn = token_in_contract.functions.approve(router_address, amount_in_raw)
            approve_gas = approve_fn.estimate_gas({"from": sender})
            approve_tx = approve_fn.build_transaction({
                "from": sender, "gas": int(approve_gas * 1.2), "gasPrice": gas_price,
                "nonce": _get_nonce(w3, sender), "chainId": cfg["chain_id"],
            })
            signed_approve = Account.sign_transaction(approve_tx, private_key)
            w3.eth.send_raw_transaction(signed_approve.raw_transaction)

    if native_in:
        swap_fn = router.functions.swapExactAVAXForTokens(min_out, path, sender, deadline)
        extra = {"value": amount_in_raw}
    elif native_out:
        swap_fn = router.functions.swapExactTokensForAVAX(amount_in_raw, min_out, path, sender, deadline)
        extra = {}
    else:
        swap_fn = router.functions.swapExactTokensForTokens(amount_in_raw, min_out, path, sender, deadline)
        extra = {}

    swap_gas = swap_fn.estimate_gas({"from": sender, **extra})
    swap_tx = swap_fn.build_transaction({
        "from": sender, "gas": int(swap_gas * 1.3), "gasPrice": gas_price,
        "nonce": _get_nonce(w3, sender), "chainId": cfg["chain_id"], **extra,
    })
    signed_swap = Account.sign_transaction(swap_tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_swap.raw_transaction)
    tx_hash_hex = tx_hash.hex()

    # Confirm and read the real received amount off the Transfer log when the
    # output is a token (not needed when swapping *to* native AVAX for the
    # headline amount, but harmless either way for the receipt itself).
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    if receipt["status"] != 1:
        raise ValueError(f"Swap reverted: {cfg['block_explorer']}/tx/{tx_hash_hex}")

    amount_out_human = str(Decimal(expected_out) / Decimal(10 ** decimals_out))
    if not native_out:
        actual_raw = _amount_from_receipt(dict(receipt), addr_out, sender)
        if actual_raw > 0:
            amount_out_human = str(Decimal(actual_raw) / Decimal(10 ** decimals_out))

    return {
        "dex": "lfj",
        "tx_hash": tx_hash_hex,
        "explorer_url": f"{cfg['block_explorer']}/tx/{tx_hash_hex}",
        "chain": chain,
        "token_in": token_in,
        "token_out": token_out,
        "amount_in": amount_in_str,
        "expected_amount_out": amount_out_human,
        "min_amount_out": str(Decimal(min_out) / Decimal(10 ** decimals_out)),
        "slippage_pct": slippage_pct,
        "status": "submitted",
    }
