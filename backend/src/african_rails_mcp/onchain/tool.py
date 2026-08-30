from .transactions import get_balance, send_native, send_erc20, get_transaction_status
from .constants import SUPPORTED_CHAINS
from ..config import settings

_REVERT_HINTS = {
    "blacklisted": "Address is blacklisted by the token contract (common with USDC/USDT). Use WAVAX or native AVAX for testnet testing instead.",
    "insufficient allowance": "Token allowance too low — the spender needs approval first.",
    "transfer amount exceeds balance": "Insufficient token balance.",
    "execution reverted": "Contract reverted the transaction.",
}


def _decode_revert(error: str) -> str:
    lower = error.lower()
    for key, hint in _REVERT_HINTS.items():
        if key in lower:
            return hint
    return error


async def check_balance(
    address: str = "",
    chain: str = "celo",
    token: str = "native",
) -> dict:
    """
    Get the native or ERC-20 token balance for an address.

    Args:
        address: EVM wallet address (defaults to the configured wallet)
        chain: Chain name - "ethereum", "celo", or "celo-alfajores"
        token: "native" for ETH/CELO, or token symbol like "USDC", "cKES", "cUSD"

    Returns:
        Balance info including human-readable amount and raw wei value
    """
    try:
        target = address or settings.wallet_address
        return get_balance(target, chain, token)
    except ValueError as e:
        return {"success": False, "error": "INVALID_INPUT", "detail": str(e)}
    except Exception as e:
        return {"success": False, "error": "RPC_ERROR", "detail": str(e)}


async def send_transaction(
    to: str,
    amount: str,
    chain: str = "celo",
    token: str = "native",
) -> dict:
    """
    Send native tokens (ETH/CELO) or ERC-20 tokens to an address.

    Args:
        to: Recipient EVM address
        amount: Amount as string to avoid float precision issues e.g. "0.01"
        chain: Chain name - "ethereum", "celo", or "celo-alfajores"
        token: "native" or token symbol like "USDC", "cKES", "cUSD"

    Returns:
        Transaction hash and explorer URL. Transaction is submitted but
        may not be confirmed yet - use get_tx_status to check confirmation.
    """
    try:
        if token == "native":
            return send_native(to, amount, chain)
        else:
            return send_erc20(to, amount, chain, token)
    except ValueError as e:
        return {"success": False, "error": "INVALID_INPUT", "detail": str(e)}
    except Exception as e:
        return {"success": False, "error": "TX_ERROR", "detail": _decode_revert(str(e))}


async def get_tx_status(tx_hash: str, chain: str = "celo") -> dict:
    """
    Check the confirmation status of a transaction by its hash.

    Args:
        tx_hash: Transaction hash (0x-prefixed hex string)
        chain: Chain name where the transaction was submitted

    Returns:
        Status: "pending", "confirmed", or "failed", plus block number and gas used
    """
    try:
        return get_transaction_status(tx_hash, chain)
    except Exception as e:
        return {"success": False, "error": "RPC_ERROR", "detail": str(e)}


async def list_supported_chains() -> dict:
    """
    List all supported blockchain networks.

    Returns:
        List of supported chain names and their native tokens
    """
    from .constants import CHAINS
    return {
        "success": True,
        "chains": {
            name: {
                "chain_id": cfg["chain_id"],
                "native_symbol": cfg["native_symbol"],
                "block_explorer": cfg["block_explorer"],
                "available_tokens": list(cfg.get("tokens", {}).keys()),
            }
            for name, cfg in CHAINS.items()
        },
    }
