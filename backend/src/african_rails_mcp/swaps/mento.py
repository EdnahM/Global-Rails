from decimal import Decimal
from eth_account import Account
from web3 import Web3
from ..onchain.client import get_web3, get_chain_config
from ..onchain.constants import ERC20_ABI
from ..config import settings
from .constants import (
    MENTO_BROKER_ADDRESS,
    MENTO_BROKER_ABI,
    EXCHANGE_PROVIDER_ABI,
    MENTO_STABLE_SYMBOLS,
)

# Cache for exchange providers and their exchange IDs
_exchange_cache: dict[str, list[dict]] = {}


def _resolve_token_address(w3: Web3, chain: str, symbol: str) -> tuple[str, int]:
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


def _get_exchanges(w3: Web3) -> list[dict]:
    global _exchange_cache
    cache_key = "celo"
    if cache_key in _exchange_cache:
        return _exchange_cache[cache_key]

    broker = w3.eth.contract(
        address=w3.to_checksum_address(MENTO_BROKER_ADDRESS), abi=MENTO_BROKER_ABI
    )
    providers = broker.functions.getExchangeProviders().call()

    exchanges = []
    for provider_addr in providers:
        provider = w3.eth.contract(
            address=w3.to_checksum_address(provider_addr), abi=EXCHANGE_PROVIDER_ABI
        )
        try:
            provider_exchanges = provider.functions.getExchanges().call()
            for exc in provider_exchanges:
                exchanges.append(
                    {
                        "provider": provider_addr,
                        "exchange_id": exc[0],
                        "assets": [w3.to_checksum_address(a) for a in exc[1]],
                    }
                )
        except Exception:
            continue

    _exchange_cache[cache_key] = exchanges
    return exchanges


def _find_exchange(w3: Web3, addr_in: str, addr_out: str) -> dict | None:
    exchanges = _get_exchanges(w3)
    for exc in exchanges:
        assets = [a.lower() for a in exc["assets"]]
        if addr_in.lower() in assets and addr_out.lower() in assets:
            return exc
    return None


def can_use_mento(token_in: str, token_out: str) -> bool:
    return token_in in MENTO_STABLE_SYMBOLS and token_out in MENTO_STABLE_SYMBOLS


def quote_swap_mento(
    chain: str,
    token_in: str,
    token_out: str,
    amount_in_str: str,
) -> dict:
    if chain not in ("celo", "celo-alfajores"):
        raise ValueError("Mento is only available on Celo")
    if not can_use_mento(token_in, token_out):
        raise ValueError(
            f"Mento only supports Celo stablecoins: {MENTO_STABLE_SYMBOLS}"
        )

    w3 = get_web3(chain)
    addr_in, decimals_in = _resolve_token_address(w3, chain, token_in)
    addr_out, decimals_out = _resolve_token_address(w3, chain, token_out)
    amount_in_raw = int(Decimal(amount_in_str) * Decimal(10 ** decimals_in))

    exchange = _find_exchange(w3, addr_in, addr_out)
    if not exchange:
        raise ValueError(f"No Mento exchange found for {token_in}/{token_out}")

    broker = w3.eth.contract(
        address=w3.to_checksum_address(MENTO_BROKER_ADDRESS), abi=MENTO_BROKER_ABI
    )
    amount_out_raw = broker.functions.getAmountOut(
        exchange["provider"],
        exchange["exchange_id"],
        addr_in,
        addr_out,
        amount_in_raw,
    ).call()

    amount_out_human = str(Decimal(amount_out_raw) / Decimal(10 ** decimals_out))
    return {
        "dex": "mento",
        "chain": chain,
        "token_in": token_in,
        "token_out": token_out,
        "amount_in": amount_in_str,
        "amount_out": amount_out_human,
        "exchange_id": exchange["exchange_id"].hex(),
        "provider": exchange["provider"],
    }


def execute_swap_mento(
    chain: str,
    token_in: str,
    token_out: str,
    amount_in_str: str,
    slippage_pct: float = 0.5,
) -> dict:
    if chain not in ("celo", "celo-alfajores"):
        raise ValueError("Mento is only available on Celo")

    w3 = get_web3(chain)
    cfg = get_chain_config(chain)
    private_key = settings.private_key.get_secret_value()
    sender = w3.to_checksum_address(settings.wallet_address)

    addr_in, decimals_in = _resolve_token_address(w3, chain, token_in)
    addr_out, decimals_out = _resolve_token_address(w3, chain, token_out)
    amount_in_raw = int(Decimal(amount_in_str) * Decimal(10 ** decimals_in))

    exchange = _find_exchange(w3, addr_in, addr_out)
    if not exchange:
        raise ValueError(f"No Mento exchange found for {token_in}/{token_out}")

    broker_address = w3.to_checksum_address(MENTO_BROKER_ADDRESS)
    broker = w3.eth.contract(address=broker_address, abi=MENTO_BROKER_ABI)

    # Get quote for min amount
    amount_out_raw = broker.functions.getAmountOut(
        exchange["provider"],
        exchange["exchange_id"],
        addr_in,
        addr_out,
        amount_in_raw,
    ).call()
    min_amount_out = int(amount_out_raw * (1 - slippage_pct / 100))

    # Approve broker
    token_in_contract = w3.eth.contract(address=addr_in, abi=ERC20_ABI)
    allowance = token_in_contract.functions.allowance(sender, broker_address).call()
    if allowance < amount_in_raw:
        from ..onchain.transactions import _get_nonce
        gas_price = int(w3.eth.gas_price * 1.1)
        approve_fn = token_in_contract.functions.approve(broker_address, amount_in_raw)
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
    from ..onchain.transactions import _get_nonce
    gas_price = int(w3.eth.gas_price * 1.1)
    swap_fn = broker.functions.swapIn(
        exchange["provider"],
        exchange["exchange_id"],
        addr_in,
        addr_out,
        amount_in_raw,
        min_amount_out,
    )
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

    amount_out_human = str(Decimal(amount_out_raw) / Decimal(10 ** decimals_out))
    return {
        "dex": "mento",
        "tx_hash": tx_hash_hex,
        "explorer_url": f"{cfg['block_explorer']}/tx/{tx_hash_hex}",
        "chain": chain,
        "token_in": token_in,
        "token_out": token_out,
        "amount_in": amount_in_str,
        "expected_amount_out": amount_out_human,
        "min_amount_out": str(Decimal(min_amount_out) / Decimal(10 ** decimals_out)),
        "slippage_pct": slippage_pct,
        "status": "submitted",
    }
