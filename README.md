# 💰 Agent Wallet — A0 Plugin

Non-custodial crypto wallet for Agent Zero. Give your agents the ability to send payments, check balances, swap tokens, bridge cross-chain, and pay for x402 resources — all without custodial risk.

## Features

| Capability | Description |
|-----------|-------------|
| **Check Balances** | ETH and any ERC-20 token on Base, Ethereum, Arbitrum, Polygon |
| **Send Payments** | Transfer ETH or tokens to any address with spend limits |
| **Token Swaps** | Uniswap V3 swaps with configurable slippage and fee tiers |
| **Cross-Chain Bridge** | CCTP (Circle) USDC bridging between supported chains |
| **x402 Payments** | Auto-pay for HTTP 402 resources (x402 protocol) |
| **Spend Limits** | Per-transaction and daily USD limits to keep agents safe |

## Quick Start

### 1. Install the Plugin

Copy this plugin to your Agent Zero installation:

```bash
# From the A0 Plugin Marketplace (coming soon)
# Or manually:
git clone https://github.com/up2itnow0822/agent-wallet-a0-plugin.git
cp -r agent-wallet-a0-plugin /path/to/agent-zero/usr/plugins/agent-wallet
```

### 2. Set Your Private Key

```bash
export AGENT_WALLET_PRIVATE_KEY="0x..."
```

> ⚠️ **Security**: Never paste your private key into config files. Always use environment variables. For production, use a dedicated agent wallet with limited funds.

### 3. Configure (Optional)

Open Agent Zero → Settings → Agent tab → Agent Wallet to configure:
- Chain selection (Base, Ethereum, Arbitrum, Polygon)
- Custom RPC endpoint
- Spend limits (per-transaction and daily)
- Swap slippage tolerance
- x402 payment limits

### 4. Use It

Your agent now has wallet tools available:

```
"Check my wallet balance"
"Send 5 USDC to 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18"
"Swap 100 USDC for WETH on Uniswap"
```

## Tools

| Tool | Arguments | Description |
|------|-----------|-------------|
| `wallet_balance` | `address?`, `token?` | Check ETH or token balance |
| `wallet_send` | `to`, `amount`, `token?` | Send ETH or ERC-20 tokens |
| `wallet_swap` | `token_in`, `token_out`, `amount` | Swap via Uniswap V3 |

## Supported Chains

| Chain | ID | Status |
|-------|----|--------|
| Base | 8453 | ✅ Full support |
| Base Sepolia | 84532 | ✅ Testnet |
| Ethereum | 1 | ✅ Full support |
| Arbitrum | 42161 | ✅ Full support |
| Polygon | 137 | ✅ Full support |

## Security Model

- **Non-custodial**: Private keys never leave your machine
- **Spend limits**: Configurable per-transaction and daily caps
- **Environment variables**: Keys loaded from env, never stored in config
- **Per-agent config**: Each agent profile can have its own wallet settings

## Requirements

- Node.js 18+ (for ethers.js wallet operations)
- `ethers` npm package: `npm install -g ethers`
- A funded wallet on your target chain

## Built By

[AI Agent Economy](https://github.com/up2itnow0822) — Building the infrastructure for autonomous AI agents.

- **Agent Wallet SDK**: [npm](https://www.npmjs.com/package/agentwallet-sdk)
- **ClawPay MCP**: [npm](https://www.npmjs.com/package/clawpay-mcp)
- **TaskBridge**: Agent marketplace

## License

MIT
