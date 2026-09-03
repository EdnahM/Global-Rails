"""Real on-chain token swaps via LFJ (formerly Trader Joe) on Avalanche Fuji.

Adapted from the LFJ integration already built and proven on the
global-rails branch (same router address, same token addresses, same
two-hop routing strategy, same Transfer-log amount reading) - not a fresh
guess, a port of code that already executed a real transaction with a
real hash on this exact router.

Only avalanche-fuji is wired to real execution. Every other chain
(including avalanche mainnet) stays on the simulated path in
swap/client.py - see that module's docstring for why.
"""
from decimal import Decimal

from eth_account import Account
from web3 import Web3

import wallet_config
from chains import get_chain

LFJ_ROUTER_ADDRESS = "0xd7f655E3376cE2D7A2b08fF01Eb3B1023191A901"

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

ERC20_ABI = [
    {"name": "balanceOf", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "account", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}]},
    {"name": "approve", "type": "function", "stateMutability": "nonpayable",
     "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
     "outputs": [{"name": "", "type": "bool"}]},
    {"name": "allowance", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
     "outputs": [{"name": "", "type": "uint256"}]},
    {"name": "decimals", "type": "function", "stateMutability": "view",
     "inputs": [], "outputs": [{"name": "", "type": "uint8"}]},
]

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
    {"inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "amountOutMin", "type": "uint256"},
                {"name": "path", "type": "address[]"}, {"name": "to", "type": "address"},
                {"name": "deadline", "type": "uint256"}],
     "name": "swapExactTokensForTokens", "outputs": [{"name": "amounts", "type": "uint256[]"}],
     "stateMutability": "nonpayable", "type": "function"},
]


def is_real_swap_configured() -> bool:
    return bool(wallet_config.PRIVATE_KEY and wallet_config.WALLET_ADDRESS)


def _is_native(chain, symbol: str) -> bool:
    return symbol.upper() in (chain.native_asset.upper(), "AVAX", "NATIVE")


def _resolve_token(w3: Web3, chain, symbol: str) -> tuple[str, int]:
    if symbol not in chain.tokens:
        raise ValueError(f"Token '{symbol}' not found on {chain.name}. Available: {list(chain.tokens.keys())}")
    addr = w3.to_checksum_address(chain.tokens[symbol])
    contract = w3.eth.contract(address=addr, abi=ERC20_ABI)
    return addr, contract.functions.decimals().call()


def _wavax_address(w3: Web3, chain) -> str:
    if "WAVAX" not in chain.tokens:
        raise ValueError(f"WAVAX not configured on {chain.name} - required as the routing hub")
    return w3.to_checksum_address(chain.tokens["WAVAX"])


def _find_route(w3: Web3, router, chain, addr_in: str, addr_out: str, amount_in_raw: int) -> tuple[list[str], int]:
    """Direct pool first, then via WAVAX."""
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


def execute_real_swap(from_token: str, to_token: str, amount: float, slippage_percent: float, chain_name: str) -> dict:
    """Executes a real swap on LFJ. Only called when chain is
    avalanche-fuji AND a wallet is configured - see swap/client.py for
    the dispatch logic."""
    chain = get_chain(chain_name)
    w3 = Web3(Web3.HTTPProvider(chain.rpc_url))
    router_address = w3.to_checksum_address(LFJ_ROUTER_ADDRESS)
    router = w3.eth.contract(address=router_address, abi=ROUTER_ABI)
    private_key = wallet_config.PRIVATE_KEY
    sender = w3.to_checksum_address(wallet_config.WALLET_ADDRESS)

    native_in, native_out = _is_native(chain, from_token), _is_native(chain, to_token)
    if native_in and native_out:
        raise ValueError("from_token and to_token can't both be the native asset")

    if native_in:
        addr_in, decimals_in = _wavax_address(w3, chain), 18
    else:
        addr_in, decimals_in = _resolve_token(w3, chain, from_token)
    if native_out:
        addr_out, decimals_out = _wavax_address(w3, chain), 18
    else:
        addr_out, decimals_out = _resolve_token(w3, chain, to_token)

    amount_in_raw = int(Decimal(str(amount)) * Decimal(10 ** decimals_in))

    path, expected_out = _find_route(w3, router, chain, addr_in, addr_out, amount_in_raw)
    if not path:
        raise ValueError(f"No LFJ route found for {from_token}/{to_token} on {chain.name}")
    min_out = int(expected_out * (1 - slippage_percent / 100))
    deadline = int(w3.eth.get_block("latest")["timestamp"]) + 300
    gas_price = int(w3.eth.gas_price * 1.1)

    if not native_in:
        token_in_contract = w3.eth.contract(address=addr_in, abi=ERC20_ABI)
        allowance = token_in_contract.functions.allowance(sender, router_address).call()
        if allowance < amount_in_raw:
            approve_fn = token_in_contract.functions.approve(router_address, amount_in_raw)
            approve_gas = approve_fn.estimate_gas({"from": sender})
            approve_tx = approve_fn.build_transaction({
                "from": sender, "gas": int(approve_gas * 1.2), "gasPrice": gas_price,
                "nonce": w3.eth.get_transaction_count(sender, "pending"), "chainId": chain.chain_id,
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
        "nonce": w3.eth.get_transaction_count(sender, "pending"), "chainId": chain.chain_id, **extra,
    })
    signed_swap = Account.sign_transaction(swap_tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_swap.raw_transaction)
    tx_hash_hex = tx_hash.hex()

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    if receipt["status"] != 1:
        raise ValueError(f"Swap reverted: {chain.block_explorer}/tx/{tx_hash_hex}")

    amount_out_human = str(Decimal(expected_out) / Decimal(10 ** decimals_out))
    if not native_out:
        actual_raw = _amount_from_receipt(dict(receipt), addr_out, sender)
        if actual_raw > 0:
            amount_out_human = str(Decimal(actual_raw) / Decimal(10 ** decimals_out))

    return {
        "tx_hash": tx_hash_hex,
        "explorer_url": f"{chain.block_explorer}/tx/{tx_hash_hex}",
        "amount_out": amount_out_human,
        "dex": "lfj",
    }
