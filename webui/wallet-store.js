import { createStore } from "/js/AlpineStore.js";

export const store = createStore("walletStore", {
    address: null,
    balanceEth: "0",
    balanceUsdc: "0",
    chain: "base",
    loading: false,
    error: null,
    recentTxs: [],

    init() {
        this.chain = "base";
    },

    async onOpen() {
        this.loading = true;
        this.error = null;
        try {
            const res = await fetch("/plugin/agent-wallet/api/status");
            if (res.ok) {
                const data = await res.json();
                this.address = data.address;
                this.balanceEth = data.balance_eth || "0";
                this.balanceUsdc = data.balance_usdc || "0";
                this.chain = data.chain || "base";
                this.recentTxs = data.recent_txs || [];
            } else {
                this.error = "Failed to load wallet status";
            }
        } catch (e) {
            this.error = e.message;
        }
        this.loading = false;
    },

    cleanup() {
        this.address = null;
        this.balanceEth = "0";
        this.balanceUsdc = "0";
        this.error = null;
        this.recentTxs = [];
    },

    get shortAddress() {
        if (!this.address) return "Not connected";
        return this.address.slice(0, 6) + "..." + this.address.slice(-4);
    },

    get explorerUrl() {
        const explorers = {
            base: "https://basescan.org/address/",
            "base-sepolia": "https://sepolia.basescan.org/address/",
            ethereum: "https://etherscan.io/address/",
            arbitrum: "https://arbiscan.io/address/",
            polygon: "https://polygonscan.com/address/",
        };
        return (explorers[this.chain] || explorers.base) + (this.address || "");
    },
});
