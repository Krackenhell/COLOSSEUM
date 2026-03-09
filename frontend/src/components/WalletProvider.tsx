import { useState, useEffect, useCallback, ReactNode } from "react";
import { WalletContext } from "@/hooks/use-wallet";
import { isWhitelisted } from "@/config/whitelist";
import "@/types/ethereum";

// ── Avalanche Fuji Testnet params ──────────────────────────────
const FUJI_CHAIN_ID = "43113";
const FUJI_CHAIN_ID_HEX = "0xA869";

const FUJI_NETWORK = {
  chainId: FUJI_CHAIN_ID_HEX,
  chainName: "Avalanche Fuji Testnet",
  nativeCurrency: { name: "AVAX", symbol: "AVAX", decimals: 18 },
  rpcUrls: ["https://api.avax-test.network/ext/bc/C/rpc"],
  blockExplorerUrls: ["https://testnet.snowtrace.io"],
};

const STORAGE_KEY = "colosseum_wallet";

// ──────────────────────────────────────────────────────────────
export function WalletProvider({ children }: { children: ReactNode }) {
  const [address, setAddress] = useState<string | null>(null);
  const [chainId, setChainId] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── Restore persisted address on mount ──
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && window.ethereum) {
      // Silently re-request accounts (no popup if already connected)
      window.ethereum
        .request<string[]>({ method: "eth_accounts" })
        .then((accounts) => {
          if (accounts && accounts.length > 0) {
            setAddress(accounts[0]);
            // Read current chainId
            window.ethereum!
              .request<string>({ method: "eth_chainId" })
              .then((cid) => setChainId(parseInt(cid, 16).toString()))
              .catch(() => {});
          } else {
            // Was connected before but MetaMask revoked — clean up
            localStorage.removeI
