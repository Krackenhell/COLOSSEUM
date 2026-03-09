// src/components/WalletProvider.tsx
// Real MetaMask EVM wallet provider.
// Automatically switches to Avalanche Fuji Testnet on connect.
// Persists address in localStorage to survive page refresh.

import { useState, useEffect, useCallback, ReactNode } from "react";
import { WalletContext } from "@/hooks/use-wallet";
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
            localStorage.removeItem(STORAGE_KEY);
          }
        })
        .catch(() => localStorage.removeItem(STORAGE_KEY));
    }
  }, []);

  // ── Subscribe to MetaMask events ──
  useEffect(() => {
    if (!window.ethereum) return;

    const onAccountsChanged = (accounts: string[]) => {
      if (accounts.length === 0) {
        // User disconnected all accounts in MetaMask
        setAddress(null);
        setChainId(null);
        localStorage.removeItem(STORAGE_KEY);
      } else {
        setAddress(accounts[0]);
        localStorage.setItem(STORAGE_KEY, accounts[0]);
      }
    };

    const onChainChanged = (cid: string) => {
      setChainId(parseInt(cid, 16).toString());
    };

    window.ethereum.on("accountsChanged", onAccountsChanged);
    window.ethereum.on("chainChanged", onChainChanged);

    return () => {
      window.ethereum!.removeListener("accountsChanged", onAccountsChanged);
      window.ethereum!.removeListener("chainChanged", onChainChanged);
    };
  }, []);

  // ── Switch / add Fuji network ──
  const switchToFuji = async () => {
    if (!window.ethereum) return;
    try {
      await window.ethereum.request({
        method: "wallet_switchEthereumChain",
        params: [{ chainId: FUJI_CHAIN_ID_HEX }],
      });
    } catch (switchErr: unknown) {
      // 4902 = chain not added yet in MetaMask
      const err = switchErr as { code?: number };
      if (err.code === 4902) {
        await window.ethereum.request({
          method: "wallet_addEthereumChain",
          params: [FUJI_NETWORK],
        });
      } else {
        throw switchErr;
      }
    }
  };

  // ── Connect ──
  const connect = useCallback(async () => {
    setError(null);

    if (!window.ethereum || !window.ethereum.isMetaMask) {
      const msg = "MetaMask not found. Install it from metamask.io";
      setError(msg);
      return;
    }

    setIsConnecting(true);
    try {
      // 1. Request accounts → triggers MetaMask popup
      const accounts = await window.ethereum.request<string[]>({
        method: "eth_requestAccounts",
      });
      if (!accounts || accounts.length === 0) throw new Error("No accounts returned");

      // 2. Switch to Fuji testnet automatically
      await switchToFuji();

      // 3. Get confirmed chainId after switch
      const cid = await window.ethereum.request<string>({ method: "eth_chainId" });
      setChainId(parseInt(cid, 16).toString());

      // 4. Save address
      setAddress(accounts[0]);
      localStorage.setItem(STORAGE_KEY, accounts[0]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Connection failed";
      // 4001 = user rejected the request — not an error to show
      if ((err as { code?: number }).code !== 4001) {
        setError(msg);
      }
    } finally {
      setIsConnecting(false);
    }
  }, []);

  // ── Disconnect ──
  const disconnect = useCallback(() => {
    setAddress(null);
    setChainId(null);
    setError(null);
    localStorage.removeItem(STORAGE_KEY);
    // Note: MetaMask has no programmatic disconnect — we only clear local state.
    // User must disconnect in MetaMask extension if desired.
  }, []);

  const isWrongNetwork = chainId !== null && chainId !== FUJI_CHAIN_ID;

  return (
    <WalletContext.Provider
      value={{
        connected: !!address,
        address,
        chainId,
        false,
        isConnecting,
        error: isWrongNetwork
          ? `Wrong network. Please switch to Avalanche Fuji Testnet.`
          : error,
        connect,
        disconnect,
      }}
    >
      {children}
    </WalletContext.Provider>
  );
}
