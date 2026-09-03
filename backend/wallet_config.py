"""Wallet configuration for real on-chain swap execution, read from
environment variables only - never hardcoded.

Set these on Render's dashboard (Settings -> Environment):
  WALLET_PRIVATE_KEY   the signing key for the swap-executing wallet
  WALLET_ADDRESS       that wallet's address (must match the private key)

If either is unset, swap/client.py falls back to the simulated path for
every chain, including avalanche-fuji - see its own module docstring.
"""
import os

PRIVATE_KEY = os.environ.get("WALLET_PRIVATE_KEY", "")
WALLET_ADDRESS = os.environ.get("WALLET_ADDRESS", "")
