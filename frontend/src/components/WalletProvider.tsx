/**
 * MVP WalletProvider — persists simulated wallet in localStorage.
 * TODO: Replace with real wallet adapter provider.
 */
import { useState, useEffect, ReactNode } from "react";
import { WalletContext } from "@/hooks/use-wallet";

const STORAGE_KEY = "colosseum_wallet";

function generateMockAddress(): string {
  const chars = "0123456789abcdef";
  let addr = "0x";
  for (let i = 0; i < 40; i++) addr += chars[Math.floor(Math.random() * 16)];
  return addr;
}

export function WalletProvider({ children }: { children: ReactNode }) {
  const [address, setAddress] = useState<string | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) setAddress(saved);
  }, []);

  const connect = () => {
    const addr = generateMockAddress();
    setAddress(addr);
    localStorage.setItem(STORAGE_KEY, addr);
  };

  const disconnect = () => {
    setAddress(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <WalletContext.Provider value={{ connected: !!address, address, connect, disconnect }}>
      {children}
    </WalletContext.Provider>
  );
}
