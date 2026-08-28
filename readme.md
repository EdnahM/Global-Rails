# 🌍 Global Rails: The Financial SDK for Autonomous AI Agents

[![PyPI version](https://img.shields.io/pypi/v/african-rails.svg)](https://pypi.org/project/african-rails/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![LangChain Compatible](https://img.shields.io/badge/LangChain-Compatible-green.svg)](https://python.langchain.com/)
[![CrewAI Compatible](https://img.shields.io/badge/CrewAI-Compatible-orange.svg)](https://crewai.com/)

**Global Rails** is a developer-first Python SDK designed to give autonomous AI agents native financial capabilities across the African continent. 

Traditional mobile money APIs (like Daraja) are built for human-in-the-loop workflows—requiring registered businesses, KRA PINs, and manual KYB. **African Rails bypasses this friction.** By sitting on top of Web3-to-fiat infrastructure (Kotani Pay, HoneyCoin, Swypt, Eversend), this SDK provides your LangChain or CrewAI agents with programmatic, machine-native financial execution—from on-chain token swaps to last-mile M-Pesa payouts.

## 🚀 Key Capabilities (The Skills Stack)

1. **Market Data Oracle:** Real-time fetching of local fiat-to-crypto exchange rates (KES/USDC, NGN/USDT).
2. **Native On-Chain Transactions:** Generate, sign, and broadcast transactions directly to blockchains via MPC wallets.
3. **Autonomous Token Swaps:** Programmatic DEX routing to swap tokens (e.g., USDT to USDC) on-chain based on optimal slippage.
4. **L402 Agentic Paywalls:** Native support for the HTTP 402 protocol, allowing agents to seamlessly pay other agents for data, inference, or API access per-request.
5. **The Statement Problem (Last-Mile Settlement):** Directly trigger a stablecoin payout to a local USSD mobile money wallet (M-Pesa, MTN Mobile Money) without requiring human intervention or corporate KYB.

---

## ⚙️ Installation

Install via pip:

```bash
pip install african-rails
