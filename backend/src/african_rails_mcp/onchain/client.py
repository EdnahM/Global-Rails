from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from .constants import CHAINS

_clients: dict[str, Web3] = {}


def get_web3(chain: str) -> Web3:
    if chain not in CHAINS:
        raise ValueError(f"Unknown chain '{chain}'. Supported: {list(CHAINS.keys())}")

    if chain not in _clients:
        cfg = CHAINS[chain]
        w3 = Web3(Web3.HTTPProvider(cfg["rpc_url"]))

        if cfg.get("is_poa"):
            w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        _clients[chain] = w3

    return _clients[chain]


def get_chain_config(chain: str) -> dict:
    if chain not in CHAINS:
        raise ValueError(f"Unknown chain '{chain}'. Supported: {list(CHAINS.keys())}")
    return CHAINS[chain]
