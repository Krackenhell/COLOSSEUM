/**
 * MVP Wallet Context — simulated wallet connect.
 * TODO: Replace with real wallet adapter (e.g. @solana/wallet-adapter, wagmi, etc.)
 */
import { createContext, useContext } from "react";

export interface WalletState {
  connected: boolean;
  address: string | null;
  connect: () => void;
  disconnect: () => void;
}

export const WalletContext = createContext<WalletState>({
  connected: false,
  address: null,
  connect: () => {},
  disconnect: () => {},
});

export function useWallet() {
  return useContext(WalletContext);
}
