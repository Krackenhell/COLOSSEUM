import {
  Dialog, DialogContent, DialogHeader,
  DialogTitle, DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useWallet } from "@/hooks/use-wallet";
import { Wallet, Loader2, AlertCircle, ExternalLink } from "lucide-react";

interface WalletModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConnected?: () => void;
}

// MetaMask logo as inline SVG (no external asset needed)
function MetaMaskIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 35 33" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M32.958 1L19.43 10.88l2.52-5.958L32.958 1z" fill="#E17726" stroke="#E17726" strokeWidth=".25"/>
      <path d="M2.042 1l13.41 9.97-2.4-6.048L2.042 1z" fill="#E27625" stroke="#E27625" strokeWidth=".25"/>
      <path d="M28.17 23.53l-3.6 5.51 7.7 2.12 2.21-7.49-6.31-.14z" fill="#E27625" stroke="#E27625" strokeWidth=".25"/>
      <path d="M.54 23.67l2.2 7.49 7.69-2.12-3.59-5.51-6.3.14z" fill="#E27625" stroke="#E27625" strokeWidth=".25"/>
    </svg>
  );
}

export function WalletModal({ open, onOpenChange, onConnected }: WalletModalProps) {
  const { connect, isConnecting, error } = useWallet();

  const handleConnect = async () => {
    await connect();
    // Check if connected successfully after attempt
    const saved = localStorage.getItem("colosseum_wallet");
    if (saved) {
      onOpenChange(false);
      onConnected?.();
    }
  };

  const hasMetaMask = typeof window !== "undefined" && !!window.ethereum?.isMetaMask;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Wallet className="h-5 w-5 text-cyan" />
            Connect Wallet
          </DialogTitle>
          <DialogDescription>
            Connect
