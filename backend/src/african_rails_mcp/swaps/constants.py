UNISWAP_V3: dict[str, dict] = {
    "ethereum": {
        "swap_router_v2": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        "quoter_v2": "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
        "factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
    },
    "celo": {
        "swap_router_v2": "0x5615CDAb10dc425a742d643d949a7F474C01abc4",
        "quoter_v2": "0x82825d0554fA07f7FC52Ab63c961F330fdEFa8E8",
        "factory": "0xAfE208a311B21f13EF87E33A90049fC17A7acDEc",
    },
    "avalanche": {
        "swap_router_v2": "0xbb00FF08d01D300023C629444BAd1426de0551BaB",
        "quoter_v2": "0xbe0F5544EC67e9B3b2D979aaA43f18Fd87E6257F",
        "factory": "0x740b1c1de25031C31FF4fC9A62f554A55cdC1baD",
    },
}

# Uniswap V3 fee tiers in ascending order of liquidity typical preference
POOL_FEE_TIERS = [500, 3000, 100, 10000]  # 0.05%, 0.3%, 0.01%, 1%

# Mento Broker on Celo mainnet
MENTO_BROKER_ADDRESS = "0x777cD7E1f2c49EA8C20beEBAdaD73d2Df62B7a0"

# Celo stablecoin symbols routable through Mento
MENTO_STABLE_SYMBOLS = {"cUSD", "cEUR", "cKES", "cBRL", "CELO"}

QUOTER_V2_ABI = [
    {
        "name": "quoteExactInputSingle",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {
                "name": "params",
                "type": "tuple",
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
            }
        ],
        "outputs": [
            {"name": "amountOut", "type": "uint256"},
            {"name": "sqrtPriceX96After", "type": "uint160"},
            {"name": "initializedTicksCrossed", "type": "uint32"},
            {"name": "gasEstimate", "type": "uint256"},
        ],
    }
]

SWAP_ROUTER_ABI = [
    {
        "name": "exactInputSingle",
        "type": "function",
        "stateMutability": "payable",
        "inputs": [
            {
                "name": "params",
                "type": "tuple",
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "recipient", "type": "address"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMinimum", "type": "uint256"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
            }
        ],
        "outputs": [{"name": "amountOut", "type": "uint256"}],
    }
]

MENTO_BROKER_ABI = [
    {
        "name": "getAmountOut",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "exchangeProvider", "type": "address"},
            {"name": "exchangeId", "type": "bytes32"},
            {"name": "tokenIn", "type": "address"},
            {"name": "tokenOut", "type": "address"},
            {"name": "amountIn", "type": "uint256"},
        ],
        "outputs": [{"name": "amountOut", "type": "uint256"}],
    },
    {
        "name": "swapIn",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "exchangeProvider", "type": "address"},
            {"name": "exchangeId", "type": "bytes32"},
            {"name": "tokenIn", "type": "address"},
            {"name": "tokenOut", "type": "address"},
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
        ],
        "outputs": [{"name": "amountOut", "type": "uint256"}],
    },
    {
        "name": "getExchangeProviders",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "address[]"}],
    },
]

EXCHANGE_PROVIDER_ABI = [
    {
        "name": "getExchanges",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [
            {
                "name": "",
                "type": "tuple[]",
                "components": [
                    {"name": "exchangeId", "type": "bytes32"},
                    {"name": "assets", "type": "address[]"},
                ],
            }
        ],
    }
]
