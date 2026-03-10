// src/components/WalletProvider.tsx
// EVM wallet provider — works with any EIP-1193 wallet (MetaMask, Rabby, etc.)
// Automatically switches to Avalanche Fuji Testnet on connect.
// Persists address in localStorage; respects explicit disconnect.

import { useState, useEffect, useCallback, useRef, ReactNode } from "react";
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
const DISCONNECTED_KEY = "colosseum_disconnected";

// ──────────────────────────────────────────────────────────────
export function WalletProvider({ children }: { children: ReactNode }) {
  const [address, setAddress] = useState<string | null>(null);
  const [chainId, setChainId] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track whether user explicitly disconnected — prevents silent re-attach
  const userDisconnectedRef = useRef(
    localStorage.getItem(DISCONNECTED_KEY) === "1"
  );

  // ── Restore persisted address on mount (only if user did NOT disconnect) ──
  useEffect(() => {
    if (userDisconnectedRef.current) return; // respect explicit disconnect

    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && window.ethereum) {
      window.ethereum
        .request<string[]>({ method: "eth_accounts" })
        .then((accounts) => {
          if (accounts && accounts.length > 0) {
            setAddress(accounts[0]);
            window.ethereum!
              .request<string>({ method: "eth_chainId" })
              .then((cid) => setChainId(parseInt(cid, 16).toString()))
              .catch(() => {});
          } else {
            localStorage.removeItem(STORAGE_KEY);
          }
        })
        .catch(() => localStorage.removeItem(STORAGE_KEY));
    }
  }, []);

  // ── Subscribe to provider events ──
  useEffect(() => {
    if (!window.ethereum) return;

    const onAccountsChanged = (accounts: string[]) => {
      // If user explicitly disconnected via app, ignore provider events
      if (userDisconnectedRef.current) return;

      if (accounts.length === 0) {
        // Wallet revoked all accounts
        setAddress(null);
        setChainId(null);
        localStorage.removeItem(STORAGE_KEY);
      } else {
        setAddress(accounts[0]);
        localStorage.setItem(STORAGE_KEY, accounts[0]);
      }
    };

    const onChainChanged = (cid: string) => {
      if (userDisconnectedRef.current) return;
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

    if (!window.ethereum) {
      setError("No EVM wallet found. Install MetaMask or Rabby.");
      return;
    }

    // Clear disconnect flag — user is explicitly connecting
    userDisconnectedRef.current = false;
    localStorage.removeItem(DISCONNECTED_KEY);

    setIsConnecting(true);
    try {
      // 1. Force explicit permission flow when wallet supports it
      try {
        await window.ethereum.request({
          method: "wallet_requestPermissions",
          params: [{ eth_accounts: {} }],
        });
      } catch {
        // Not all wallets implement this method — fallback to eth_requestAccounts below
      }

      // 2. Request accounts (explicit user action path)
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
      if ((err as { code?: number }).code !== 4001) {
        setError(msg);
      }
    } finally {
      setIsConnecting(false);
    }
  }, []);

  // ── Disconnect ──
  const disconnect = useCallback(async () => {
    setAddress(null);
    setChainId(null);
    setError(null);
    localStorage.removeItem(STORAGE_KEY);
    // Mark explicit disconnect — prevents auto-restore on refresh & stale events
    localStorage.setItem(DISCONNECTED_KEY, "1");
    userDisconnectedRef.current = true;

    // Best-effort wallet permission revoke (if supported)
    if (window.ethereum) {
      try {
        await window.ethereum.request({
          method: "wallet_revokePermissions",
          params: [{ eth_accounts: {} }],
        });
      } catch {
        // Some wallets do not support revokePermissions
      }
    }
  }, []);

  const isWrongNetwork = chainId !== null && chainId !== FUJI_CHAIN_ID;

  return (
    <WalletContext.Provider
      value={{
        connected: !!address,
        address,
        chainId,
        isAdmin: false,
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
