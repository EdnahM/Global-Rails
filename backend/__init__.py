from backend.fetch_price.tool import fetch_price_tool
from backend.transfer.tool import transfer_tool
from backend.swap.tool import swap_tool
from backend.x402.tool import x402_tool

TOOLKIT = [
    fetch_price_tool,
    transfer_tool,
    swap_tool,
    x402_tool,
]
