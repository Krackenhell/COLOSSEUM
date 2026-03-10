// src/components/WalletModal.tsx
// Wallet connect modal — supports any EIP-1193 wallet (MetaMask, Rabby, etc.)

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

/** Detect which wallet is injected and return name + whether it exists */
function detectWallet(): { name: string; installed: boolean } {
  if (typeof window === "undefined" || !window.ethereum) {
    return { name: "Wallet", installed: false };
  }
  if (window.ethereum.isRabby) return { name: "Rabby", installed: true };
  if (window.ethereum.isMetaMask) return { name: "MetaMask", installed: true };
  return { name: "Browser Wallet", installed: true };
}

/** Generic wallet icon (no MetaMask-specific branding) */
function WalletIcon() {
  return (
    <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-cyan/20 to-cyan/5 border border-cyan/30">
      <Wallet className="h-4 w-4 text-cyan" />
    </div>
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

  const wallet = detectWallet();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Wallet className="h-5 w-5 text-cyan" />
            Connect Wallet
          </DialogTitle>
          <DialogDescription>
            Connect your EVM wallet to access Colosseum Arena.
            You will be switched to <strong>Avalanche Fuji Testnet</strong> automatically.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 pt-4">
          {/* Error banner */}
          {error && (
            <div className="flex items-start gap-2 rounded-md bg-destructive/10 border border-destructive/30 px-3 py-2 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Wallet button */}
          {wallet.installed ? (
            <Button
              variant="outline"
              className="w-full justify-start gap-3 h-14"
              onClick={handleConnect}
              disabled={isConnecting}
            >
              <WalletIcon />
              <div className="text-left flex-1">
                <div className="font-medium">{wallet.name}</div>
                <div className="text-xs text-muted-foreground">
                  Avalanche Fuji Testnet (EVM)
                </div>
              </div>
              {isConnecting && <Loader2 className="h-4 w-4 animate-spin ml-auto" />}
            </Button>
          ) : (
            /* No wallet installed */
            <div className="rounded-md border border-dashed p-4 text-center space-y-2">
              <p className="text-sm text-muted-foreground">
                No EVM wallet detected in your browser.
              </p>
              <div className="flex justify-center gap-3">
                <Button
                  variant="link"
                  size="sm"
                  className="gap-1"
                  onClick={() => window.open("https://rabby.io/", "_blank")}
                >
                  Install Rabby
                  <ExternalLink className="h-3 w-3" />
                </Button>
                <Button
                  variant="link"
                  size="sm"
                  className="gap-1"
                  onClick={() => window.open("https://metamask.io/download/", "_blank")}
                >
                  Install MetaMask
                  <ExternalLink className="h-3 w-3" />
                </Button>
              </div>
            </div>
          )}

          <p className="text-xs text-muted-foreground text-center pt-1">
            By connecting, you agree to the platform&apos;s terms of use.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
