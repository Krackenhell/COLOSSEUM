// src/types/ethereum.d.ts
// TypeScript declarations for window.ethereum (MetaMask injected provider)

interface EthereumRequestArguments {
  method: string;
  params?: unknown[];
}

interface EthereumEvent {
  connect: { chainId: string };
  disconnect: Error;
  accountsChanged: string[];
  chainChanged: string;
}

type EthereumEventKey = keyof EthereumEvent;

interface Ethereum {
  isMetaMask?: boolean;
  isRabby?: boolean;
  request<T = unknown>(args: EthereumRequestArguments): Promise<T>;
  on<K extends EthereumEventKey>(event: K, handler: (data: EthereumEvent[K]) => void): void;
  removeListener<K extends EthereumEventKey>(event: K, handler: (data: EthereumEvent[K]) => void): void;
}

declare global {
  interface Window {
    ethereum?: Ethereum;
  }
}

export {};
