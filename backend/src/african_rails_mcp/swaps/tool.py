from .uniswap_v3 import quote_swap_uniswap, execute_swap_uniswap
from .mento import quote_swap_mento, execute_swap_mento, can_use_mento
from .lfj import quote_swap_lfj, execute_swap_lfj, can_use_lfj
from ..config import settings


async def quote_swap(
    token_in: str,
    token_out: str,
    amount_in: str,
    chain: str = "celo",
    prefer_mento: bool = True,
) -> dict:
    """
    Get a price quote for swapping one token to another without executing.

    On Celo, automatically prefers Mento for stablecoin pairs (better rates,
    no price impact). Uses LFJ on avalanche-fuji (Avalanche's native DEX —
    Uniswap V3 isn't configured there). Falls back to Uniswap V3 elsewhere.

    Args:
        token_in: Input token symbol e.g. "cUSD", "USDC", "CELO", "AVAX"
        token_out: Output token symbol e.g. "cKES", "cUSD", "ETH", "LINK"
        amount_in: Amount to swap as string e.g. "10.5"
        chain: Chain name - "ethereum", "celo", "celo-alfajores", "avalanche", "avalanche-fuji"
        prefer_mento: On Celo, use Mento for eligible stablecoin pairs (default True)

    Returns:
        Quote with expected output amount, DEX used, and fee info
    """
    try:
        use_mento = (
            prefer_mento
            and chain in ("celo", "celo-alfajores")
            and can_use_mento(token_in, token_out)
        )

        if use_mento:
            return quote_swap_mento(chain, token_in, token_out, amount_in)
        elif can_use_lfj(chain):
            return quote_swap_lfj(chain, token_in, token_out, amount_in)
        else:
            return quote_swap_uniswap(chain, token_in, token_out, amount_in)
    except ValueError as e:
        return {"success": False, "error": "INVALID_INPUT", "detail": str(e)}
    except Exception as e:
        return {"success": False, "error": "QUOTE_ERROR", "detail": str(e)}


async def execute_swap(
    token_in: str,
    token_out: str,
    amount_in: str,
    chain: str = "celo",
    slippage_pct: float = 0.5,
    prefer_mento: bool = True,
) -> dict:
    """
    Execute a token swap. Automatically selects the best DEX.

    On Celo, uses Mento for stablecoin pairs (cUSD, cKES, cEUR, cBRL, CELO)
    as it provides better rates with no price impact within bucket limits.
    Uses LFJ on avalanche-fuji (Avalanche's native DEX). Uses Uniswap V3 for
    all other pairs.

    Args:
        token_in: Input token symbol e.g. "cUSD", "USDC", "CELO", "AVAX"
        token_out: Output token symbol e.g. "cKES", "cUSD", "ETH", "LINK"
        amount_in: Amount to swap as string e.g. "10.5"
        chain: Chain name - "ethereum", "celo", "celo-alfajores", "avalanche", "avalanche-fuji"
        slippage_pct: Maximum acceptable slippage percentage (default 0.5%)
        prefer_mento: On Celo, prefer Mento for eligible stablecoin pairs

    Returns:
        Transaction hash, explorer URL, and expected output amount
    """
    try:
        use_mento = (
            prefer_mento
            and chain in ("celo", "celo-alfajores")
            and can_use_mento(token_in, token_out)
        )

        if use_mento:
            return execute_swap_mento(chain, token_in, token_out, amount_in, slippage_pct)
        elif can_use_lfj(chain):
            return execute_swap_lfj(chain, token_in, token_out, amount_in, slippage_pct)
        else:
            return execute_swap_uniswap(chain, token_in, token_out, amount_in, slippage_pct)
    except ValueError as e:
        return {"success": False, "error": "INVALID_INPUT", "detail": str(e)}
    except Exception as e:
        return {"success": False, "error": "SWAP_ERROR", "detail": str(e)}
