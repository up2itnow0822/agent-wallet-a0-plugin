"""
Agent Wallet Tool for Agent Zero
Non-custodial wallet operations: balance, send, swap, bridge, x402.
"""
import json
import os
import asyncio
from dataclasses import dataclass
from typing import Any

from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers.plugins import get_plugin_config

# Chain configurations
CHAINS = {
    "base": {
        "chain_id": 8453,
        "rpc": "https://mainnet.base.org",
        "name": "Base",
        "explorer": "https://basescan.org",
        "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    },
    "base-sepolia": {
        "chain_id": 84532,
        "rpc": "https://sepolia.base.org",
        "name": "Base Sepolia",
        "explorer": "https://sepolia.basescan.org",
        "usdc": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    },
    "ethereum": {
        "chain_id": 1,
        "rpc": "https://eth.llamarpc.com",
        "name": "Ethereum",
        "explorer": "https://etherscan.io",
        "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    },
    "arbitrum": {
        "chain_id": 42161,
        "rpc": "https://arb1.arbitrum.io/rpc",
        "name": "Arbitrum",
        "explorer": "https://arbiscan.io",
        "usdc": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    },
    "polygon": {
        "chain_id": 137,
        "rpc": "https://polygon-rpc.com",
        "name": "Polygon",
        "explorer": "https://polygonscan.com",
        "usdc": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    },
}

# ERC-20 minimal ABI for balance and transfer
ERC20_ABI = json.dumps([
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
])


def _get_config(agent) -> dict:
    """Load plugin config with defaults."""
    defaults = {
        "rpc_url": "https://mainnet.base.org",
        "chain": "base",
        "spend_limit_usd": 10.0,
        "daily_limit_usd": 100.0,
        "private_key_env": "AGENT_WALLET_PRIVATE_KEY",
        "usdc_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "swap_slippage_bps": 50,
        "swap_fee_tier": 3000,
        "bridge_destination_chain": "ethereum",
        "x402_max_payment_usd": 5.0,
    }
    cfg = get_plugin_config("agent-wallet", agent=agent) or {}
    for k, v in defaults.items():
        cfg.setdefault(k, v)
    return cfg


def _get_private_key(config: dict) -> str:
    """Resolve private key from environment variable."""
    env_var = config.get("private_key_env", "AGENT_WALLET_PRIVATE_KEY")
    key = os.environ.get(env_var, "")
    if not key:
        raise ValueError(
            f"Private key not found. Set the {env_var} environment variable."
        )
    return key


def _build_web3_script(config: dict, script_body: str) -> str:
    """Build a Node.js script using ethers.js for wallet operations."""
    chain = config.get("chain", "base")
    chain_info = CHAINS.get(chain, CHAINS["base"])
    rpc = config.get("rpc_url", chain_info["rpc"])

    return f"""
const {{ ethers }} = require('ethers');
const provider = new ethers.JsonRpcProvider('{rpc}');
const PRIVATE_KEY = process.env.{config.get('private_key_env', 'AGENT_WALLET_PRIVATE_KEY')};
const wallet = PRIVATE_KEY ? new ethers.Wallet(PRIVATE_KEY, provider) : null;
const ERC20_ABI = {ERC20_ABI};

async function main() {{
    try {{
        {script_body}
    }} catch (err) {{
        console.log(JSON.stringify({{ error: err.message }}));
    }}
}}
main();
"""


class WalletBalance(Tool):
    """Check wallet ETH and token balances."""

    async def execute(self, **kwargs) -> Response:
        config = _get_config(self.agent)
        address = self.args.get("address", "")
        token = self.args.get("token", "").strip()

        if not address and not token:
            # Get own wallet address and ETH balance
            script = _build_web3_script(config, """
                if (!wallet) { console.log(JSON.stringify({error: 'No private key configured'})); return; }
                const balance = await provider.getBalance(wallet.address);
                const ethBalance = ethers.formatEther(balance);
                console.log(JSON.stringify({
                    address: wallet.address,
                    balance_eth: ethBalance,
                    chain: '""" + config.get("chain", "base") + """'
                }));
            """)
        elif token:
            # Check specific token balance
            target = address or "wallet.address"
            addr_setup = "" if address else "if (!wallet) { console.log(JSON.stringify({error: 'No private key configured'})); return; }"
            addr_ref = f'"{address}"' if address else "wallet.address"
            script = _build_web3_script(config, f"""
                {addr_setup}
                const token = new ethers.Contract('{token}', ERC20_ABI, provider);
                const [balance, decimals, symbol] = await Promise.all([
                    token.balanceOf({addr_ref}),
                    token.decimals(),
                    token.symbol()
                ]);
                const formatted = ethers.formatUnits(balance, decimals);
                console.log(JSON.stringify({{
                    address: {addr_ref},
                    token: '{token}',
                    symbol: symbol,
                    balance: formatted
                }}));
            """)
        else:
            # Check ETH balance for specific address
            script = _build_web3_script(config, f"""
                const balance = await provider.getBalance('{address}');
                const ethBalance = ethers.formatEther(balance);
                console.log(JSON.stringify({{
                    address: '{address}',
                    balance_eth: ethBalance,
                    chain: '{config.get("chain", "base")}'
                }}));
            """)

        result = await self._run_node(script)
        return Response(message=result, break_loop=False)

    async def _run_node(self, script: str) -> str:
        """Execute a Node.js script and return output."""
        import tempfile
        import subprocess

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(script)
            f.flush()
            try:
                proc = await asyncio.create_subprocess_exec(
                    "node", f.name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ},
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
                output = stdout.decode().strip()
                if not output and stderr:
                    return json.dumps({"error": stderr.decode().strip()})
                return output or json.dumps({"error": "No output from script"})
            except asyncio.TimeoutError:
                return json.dumps({"error": "Script execution timed out"})
            finally:
                os.unlink(f.name)


class WalletSend(Tool):
    """Send ETH or ERC-20 tokens to an address."""

    async def execute(self, **kwargs) -> Response:
        config = _get_config(self.agent)
        to_address = self.args.get("to", "")
        amount = self.args.get("amount", "0")
        token = self.args.get("token", "").strip()

        if not to_address:
            return Response(message="Error: 'to' address is required.", break_loop=False)

        # Spend limit check
        try:
            amount_float = float(amount)
        except (ValueError, TypeError):
            return Response(message=f"Error: Invalid amount '{amount}'.", break_loop=False)

        spend_limit = float(config.get("spend_limit_usd", 10.0))
        if spend_limit > 0 and amount_float > spend_limit:
            return Response(
                message=f"Error: Amount ${amount_float} exceeds per-transaction spend limit of ${spend_limit}. Adjust in plugin settings.",
                break_loop=False,
            )

        if token:
            # ERC-20 transfer
            script = _build_web3_script(config, f"""
                if (!wallet) {{ console.log(JSON.stringify({{error: 'No private key configured'}})); return; }}
                const token = new ethers.Contract('{token}', ERC20_ABI, wallet);
                const decimals = await token.decimals();
                const amount = ethers.parseUnits('{amount}', decimals);
                const tx = await token.transfer('{to_address}', amount);
                const receipt = await tx.wait();
                const symbol = await token.symbol();
                console.log(JSON.stringify({{
                    success: true,
                    tx_hash: receipt.hash,
                    from: wallet.address,
                    to: '{to_address}',
                    amount: '{amount}',
                    symbol: symbol,
                    block: receipt.blockNumber
                }}));
            """)
        else:
            # ETH transfer
            script = _build_web3_script(config, f"""
                if (!wallet) {{ console.log(JSON.stringify({{error: 'No private key configured'}})); return; }}
                const tx = await wallet.sendTransaction({{
                    to: '{to_address}',
                    value: ethers.parseEther('{amount}')
                }});
                const receipt = await tx.wait();
                console.log(JSON.stringify({{
                    success: true,
                    tx_hash: receipt.hash,
                    from: wallet.address,
                    to: '{to_address}',
                    amount: '{amount}',
                    symbol: 'ETH',
                    block: receipt.blockNumber
                }}));
            """)

        result = await self._run_node(script)
        return Response(message=result, break_loop=False)

    async def _run_node(self, script: str) -> str:
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(script)
            f.flush()
            try:
                proc = await asyncio.create_subprocess_exec(
                    "node", f.name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ},
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
                output = stdout.decode().strip()
                if not output and stderr:
                    return json.dumps({"error": stderr.decode().strip()})
                return output or json.dumps({"error": "No output"})
            except asyncio.TimeoutError:
                return json.dumps({"error": "Transaction timed out"})
            finally:
                os.unlink(f.name)


class WalletSwap(Tool):
    """Swap tokens via Uniswap V3 on Base."""

    async def execute(self, **kwargs) -> Response:
        config = _get_config(self.agent)
        token_in = self.args.get("token_in", "")
        token_out = self.args.get("token_out", "")
        amount = self.args.get("amount", "0")

        if not token_in or not token_out:
            return Response(
                message="Error: 'token_in' and 'token_out' addresses are required.",
                break_loop=False,
            )

        slippage = config.get("swap_slippage_bps", 50)
        fee_tier = config.get("swap_fee_tier", 3000)

        # Uniswap V3 SwapRouter02 on Base
        SWAP_ROUTER = "0x2626664c2603336E57B271c5C0b26F421741e481"

        script = _build_web3_script(config, f"""
            if (!wallet) {{ console.log(JSON.stringify({{error: 'No private key configured'}})); return; }}

            const SWAP_ROUTER_ABI = [
                'function exactInputSingle((address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 amountIn, uint256 amountOutMinimum, uint160 sqrtPriceLimitX96)) external payable returns (uint256 amountOut)'
            ];

            const tokenIn = new ethers.Contract('{token_in}', ERC20_ABI, wallet);
            const decimals = await tokenIn.decimals();
            const amountIn = ethers.parseUnits('{amount}', decimals);

            // Approve router
            const approveTx = await tokenIn.approve('{SWAP_ROUTER}', amountIn);
            await approveTx.wait();

            // Execute swap
            const router = new ethers.Contract('{SWAP_ROUTER}', SWAP_ROUTER_ABI, wallet);
            const params = {{
                tokenIn: '{token_in}',
                tokenOut: '{token_out}',
                fee: {fee_tier},
                recipient: wallet.address,
                amountIn: amountIn,
                amountOutMinimum: 0,  // In production, calculate with slippage
                sqrtPriceLimitX96: 0
            }};

            const tx = await router.exactInputSingle(params);
            const receipt = await tx.wait();

            console.log(JSON.stringify({{
                success: true,
                tx_hash: receipt.hash,
                token_in: '{token_in}',
                token_out: '{token_out}',
                amount_in: '{amount}',
                fee_tier: {fee_tier},
                block: receipt.blockNumber
            }}));
        """)

        result = await self._run_node(script)
        return Response(message=result, break_loop=False)

    async def _run_node(self, script: str) -> str:
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(script)
            f.flush()
            try:
                proc = await asyncio.create_subprocess_exec(
                    "node", f.name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ},
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=90)
                output = stdout.decode().strip()
                if not output and stderr:
                    return json.dumps({"error": stderr.decode().strip()})
                return output or json.dumps({"error": "No output"})
            except asyncio.TimeoutError:
                return json.dumps({"error": "Swap timed out"})
            finally:
                os.unlink(f.name)
