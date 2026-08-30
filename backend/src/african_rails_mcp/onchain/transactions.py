from decimal import Decimal
from web3 import Web3
from eth_account import Account
from .client import get_web3, get_chain_config
from .constants import ERC20_ABI
from ..config import settings

# Local nonce cache to handle rapid sequential transactions
_nonce_cache: dict[str, int] = {}


def _get_nonce(w3: Web3, address: str) -> int:
    on_chain = w3.eth.get_transaction_count(address, "pending")
    cached = _nonce_cache.get(address.lower(), 0)
    nonce = max(on_chain, cached)
    _nonce_cache[address.lower()] = nonce + 1
    return nonce


def _token_address(chain: str, token: str) -> str:
    cfg = get_chain_config(chain)
    tokens = cfg.get("tokens", {})
    if token not in tokens:
        raise ValueError(
            f"Token '{token}' not found on {chain}. "
            f"Available: {list(tokens.keys())}"
        )
    return tokens[token]


def get_balance(address: str, chain: str, token: str = "native") -> dict:
    w3 = get_web3(chain)
    cfg = get_chain_config(chain)
    checksum_address = w3.to_checksum_address(address)

    if token == "native":
        raw = w3.eth.get_balance(checksum_address)
        decimals = cfg["native_decimals"]
        symbol = cfg["native_symbol"]
        balance = Decimal(raw) / Decimal(10 ** decimals)
        return {
            "address": address,
            "chain": chain,
            "token": symbol,
            "balance": str(balance),
            "balance_raw": str(raw),
            "decimals": decimals,
        }

    token_addr = _token_address(chain, token)
    contract = w3.eth.contract(
        address=w3.to_checksum_address(token_addr), abi=ERC20_ABI
    )
    decimals: int = contract.functions.decimals().call()
    raw = contract.functions.balanceOf(checksum_address).call()
    balance = Decimal(raw) / Decimal(10 ** decimals)

    return {
        "address": address,
        "chain": chain,
        "token": token,
        "balance": str(balance),
        "balance_raw": str(raw),
        "decimals": decimals,
        "contract_address": token_addr,
    }


def send_native(to: str, amount_str: str, chain: str) -> dict:
    w3 = get_web3(chain)
    cfg = get_chain_config(chain)
    private_key = settings.private_key.get_secret_value()
    sender = w3.to_checksum_address(settings.wallet_address)
    recipient = w3.to_checksum_address(to)

    amount_wei = w3.to_wei(Decimal(amount_str), "ether")

    gas_price = w3.eth.gas_price
    gas_price_buffered = int(gas_price * 1.1)

    tx = {
        "from": sender,
        "to": recipient,
        "value": amount_wei,
        "gas": 21000,
        "gasPrice": gas_price_buffered,
        "nonce": _get_nonce(w3, sender),
        "chainId": cfg["chain_id"],
    }

    signed = Account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    tx_hash_hex = tx_hash.hex()

    return {
        "tx_hash": tx_hash_hex,
        "explorer_url": f"{cfg['block_explorer']}/tx/{tx_hash_hex}",
        "chain": chain,
        "from": sender,
        "to": recipient,
        "amount": amount_str,
        "token": cfg["native_symbol"],
        "status": "submitted",
    }


def send_erc20(to: str, amount_str: str, chain: str, token: str) -> dict:
    w3 = get_web3(chain)
    cfg = get_chain_config(chain)
    private_key = settings.private_key.get_secret_value()
    sender = w3.to_checksum_address(settings.wallet_address)
    recipient = w3.to_checksum_address(to)

    token_addr = _token_address(chain, token)
    contract = w3.eth.contract(
        address=w3.to_checksum_address(token_addr), abi=ERC20_ABI
    )

    decimals: int = contract.functions.decimals().call()
    amount_units = int(Decimal(amount_str) * Decimal(10 ** decimals))

    gas_price = w3.eth.gas_price
    gas_price_buffered = int(gas_price * 1.1)
    nonce = _get_nonce(w3, sender)

    transfer_fn = contract.functions.transfer(recipient, amount_units)
    gas_estimate = transfer_fn.estimate_gas({"from": sender})

    tx = transfer_fn.build_transaction(
        {
            "from": sender,
            "gas": int(gas_estimate * 1.2),
            "gasPrice": gas_price_buffered,
            "nonce": nonce,
            "chainId": cfg["chain_id"],
        }
    )

    signed = Account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    tx_hash_hex = tx_hash.hex()

    return {
        "tx_hash": tx_hash_hex,
        "explorer_url": f"{cfg['block_explorer']}/tx/{tx_hash_hex}",
        "chain": chain,
        "from": sender,
        "to": recipient,
        "amount": amount_str,
        "token": token,
        "contract_address": token_addr,
        "status": "submitted",
    }


def get_transaction_status(tx_hash: str, chain: str) -> dict:
    w3 = get_web3(chain)
    cfg = get_chain_config(chain)

    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except Exception:
        receipt = None

    if receipt is None:
        return {
            "tx_hash": tx_hash,
            "chain": chain,
            "status": "pending",
            "explorer_url": f"{cfg['block_explorer']}/tx/{tx_hash}",
        }

    status = "confirmed" if receipt["status"] == 1 else "failed"
    return {
        "tx_hash": tx_hash,
        "chain": chain,
        "status": status,
        "block_number": receipt["blockNumber"],
        "gas_used": receipt["gasUsed"],
        "explorer_url": f"{cfg['block_explorer']}/tx/{tx_hash}",
    }
