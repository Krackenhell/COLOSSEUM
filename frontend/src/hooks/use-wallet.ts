// src/hooks/use-wallet.ts
// WalletContext type + useWallet hook.
// isAdmin is derived from whitelist check in WalletProvider.

import { createContext, useContext } from "react";

export interface WalletContextType {
  /** Is wallet connected? */
  connected: boolean;
  /** Connected wallet address (checksummed), or null */
  address: string | null;
  /** Current chainId as decimal string, e.g. "43113" */
  chainId: string | null;
  /** True if address is in ADMIN_WHITELIST */
  isAdmin: boolean;
  /** Is connection in progress? */
  isConnecting: boolean;
  /** Last connection error message */
  error: string | null;
  /** Connect wallet → switches to Fuji testnet automatically */
  connect: () => Promise<void>;
  /** Disconnect (clears state + best-effort permission revoke) */
  disconnect: () => Promise<void>;
}

export const WalletContext = createContext<WalletContextType>({
  connected: false,
  address: null,
  chainId: null,
  isAdmin: false,
  isConnecting: false,
  error: null,
  connect: async () => {},
  disconnect: async () => {},
});

export function useWallet(): WalletContextType {
  return useContext(WalletContext);
}
