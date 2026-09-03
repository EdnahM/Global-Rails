ERC20_ABI = [
    {
        "name": "balanceOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "transfer",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
    },
    {
        "name": "approve",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
    },
    {
        "name": "allowance",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
        ],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "decimals",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint8"}],
    },
    {
        "name": "symbol",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "string"}],
    },
    {
        "name": "name",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "string"}],
    },
]

CHAINS: dict[str, dict] = {
    "ethereum": {
        "chain_id": 1,
        "rpc_url": "https://eth.llamarpc.com",
        "native_symbol": "ETH",
        "native_decimals": 18,
        "block_explorer": "https://etherscan.io",
        "is_poa": False,
        "tokens": {
            "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        },
    },
    "celo": {
        "chain_id": 42220,
        "rpc_url": "https://forno.celo.org",
        "native_symbol": "CELO",
        "native_decimals": 18,
        "block_explorer": "https://celoscan.io",
        "is_poa": True,
        "tokens": {
            "cUSD": "0x765DE816845861e75A25fCA122bb6898B8B1282a",
            "cEUR": "0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73",
            "cKES": "0x456a3D042C0DbD3db53D5489e98dFb038553B0d0",
            "USDC": "0xcebA9300f2b948710d2653dD7B07f33A8B32118C",
            "USDT": "0x617f3112bf5397D0467D315cC709EF968D9ba546",
            "cBRL": "0xe8537a3d056DA446677B9E9d6c5dB704EaAb4787",
        },
    },
    "celo-alfajores": {
        "chain_id": 44787,
        "rpc_url": "https://alfajores-forno.celo-testnet.org",
        "native_symbol": "CELO",
        "native_decimals": 18,
        "block_explorer": "https://alfajores.celoscan.io",
        "is_poa": True,
        "tokens": {
            "cUSD": "0x874069Fa1Eb16D44d622F2e0Ca25eeA172369bC1",
            "cEUR": "0x10c892A6EC43a53E45D0B916B4b7D383B1b78C0F",
            "cKES": "0x1E0433C1769271d5685e4d9F7D544F3f46E48914",
        },
    },
    "avalanche": {
        "chain_id": 43114,
        "rpc_url": "https://api.avax.network/ext/bc/C/rpc",
        "native_symbol": "AVAX",
        "native_decimals": 18,
        "block_explorer": "https://snowtrace.io",
        "is_poa": False,
        "tokens": {
            "USDC": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6C",
            "USDT": "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7",
            "WAVAX": "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7",
            "WETH": "0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB",
            "DAI": "0xd586E7F844cEa2F87f50152665BCbc2C279D8d70",
            "BTCb": "0x152b9d0FdC40C096757F570A51E494bd4b943E50",
        },
    },
    "avalanche-fuji": {
        "chain_id": 43113,
        "rpc_url": "https://api.avax-test.network/ext/bc/C/rpc",
        "native_symbol": "AVAX",
        "native_decimals": 18,
        "block_explorer": "https://testnet.snowtrace.io",
        "is_poa": False,
        "tokens": {
            # LFJ's own test USDC — NOT Circle's testnet USDC, which has no
            # liquidity pool against WAVAX on LFJ's router. Swaps against
            # the old address here would have failed silently for lack of
            # a route, not because anything was technically broken.
            "USDC": "0xB6076C93701D6a07266c31066B298AeC6dd65c2d",
            "WAVAX": "0xd00ae08403B9bbb9124bB305C09058E32C39A48c",
            "LINK": "0x0b9d5D9136855f6FEc3c0993feE6E9CE8a297846",
        },
    },
}

SUPPORTED_CHAINS = list(CHAINS.keys())
