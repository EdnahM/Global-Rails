"""Chain configuration for Global Rails backend tools.

Centralizes the supported network(s) so individual tools (transfer, swap,
fetch_price, x402) never hardcode a chain. Global Rails is Avalanche-first:
Avalanche C-Chain is the only configured network today.

The design is multi-chain capable - every tool takes a 'chain' param and
routes through 'get_chain()' - so adding a network later is a one-entry
addition here with no change to the MCP surface.

Avalanche uses an ERC-4337 paymaster model so an agent can pay transaction
gas in USDC at a fixed, predictable rate instead of in the native asset.
"""

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Chain registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Chain:
    name: str                  # canonical slug used in tool `chain` params
    chain_id: int              # EVM chain id
    native_asset: str          # gas/accounting asset symbol
    rpc_url: str = ""          # public RPC (empty -> mock-only)
    stablecoins: tuple[str, ...] = field(default_factory=tuple)
    supports_paymaster: bool = False   # ERC-4337 / account-abstraction gas-in-USDC
    default_stablecoin: str = "USDC"


# Global Rails defaults to Avalanche C-Chain. Paymaster means gas can be
# settled in USDC at a fixed rate (the project's "know the fee" promise).
AVALANCHE = Chain(
    name="avalanche",
    chain_id=43114,
    native_asset="AVAX",
    rpc_url="https://api.avax.network/ext/bc/C/rpc",
    stablecoins=("USDC", "USDT"),
    supports_paymaster=True,
    default_stablecoin="USDC",
)


# any other further network can be added here, like its Avalanche focused, but can add
# other networks here, (e.g. ETHEREUM = Chain(...)) and include in CHAINS
#  and each tool resolves to get_chain(), so new network is easily usable


# Chains known to the toolkit. Keyed by canonical slug.
CHAINS: dict[str, Chain] = {
    c.name: c for c in (AVALANCHE,)
}

DEFAULT_CHAIN = AVALANCHE.name


def get_chain(name: str) -> Chain:
    """Return the 'Chain' for a slug, raising a clear error if unknown."""
    key = (name or DEFAULT_CHAIN).strip().lower()
    if key not in CHAINS:
        raise ValueError(
            f"Unsupported chain '{name}'. Supported: {sorted(CHAINS)}"
        )
    return CHAINS[key]


def default_stablecoin(chain: str) -> str:
    """The default stablecoin for a chain (avalanche -> USDC)."""
    return get_chain(chain).default_stablecoin


def stablecoins(chain: str) -> tuple[str, ...]:
    """Stablecoins available on a chain."""
    return get_chain(chain).stablecoins


# ---------------------------------------------------------------------------
# Paymaster / gas-in-USDC fee model
# ---------------------------------------------------------------------------
# ERC-4337 account abstraction lets an agent settle gas in USDC. The exact
# cost is quoted up-front so a caller sees a fixed, predictable fee. A fixed
# per-transfer base is used here as a placeholder until a real fee oracle +
# paymaster bundler is wired in. Values are in USDC (6 decimals, numeric).
PAYMASTER_FEE_USDC_DEFAULT = 0.05
PAYMASTER_FEE_USDC_BY_CHAIN: dict[str, float] = {
    AVALANCHE.name: 0.05,
}


def quote_gas_fee_usdc(chain: str = DEFAULT_CHAIN) -> float:
    """Fixed USDC gas fee for a transfer on the given chain (paymaster).

    This is the "know the fee before you send" value the product promises:
    a predictable stablecoin-denominated cost instead of unpredictable native
    gas. Currently a static placeholder; swap for a live fee oracle later.
    """
    return PAYMASTER_FEE_USDC_BY_CHAIN.get(
        get_chain(chain).name, PAYMASTER_FEE_USDC_DEFAULT
    )
