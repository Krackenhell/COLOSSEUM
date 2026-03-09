// src/components/WalletModal.tsx
// Wallet connect modal — MetaMask only (EVM / Avalanche Fuji).

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
            Connect your MetaMask wallet to access Colosseum Arena.
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

          {/* MetaMask button */}
          {hasMetaMask ? (
            <Button
              variant="outline"
              className="w-full justify-start gap-3 h-14"
              onClick={handleConnect}
              disabled={isConnecting}
            >
              <MetaMaskIcon />
              <div className="text-left flex-1">
                <div className="font-medium">MetaMask</div>
                <div className="text-xs text-muted-foreground">
                  Avalanche Fuji Testnet (EVM)
                </div>
              </div>
              {isConnecting && <Loader2 className="h-4 w-4 animate-spin ml-auto" />}
            </Button>
          ) : (
            /* MetaMask not installed */
            <div className="rounded-md border border-dashed p-4 text-center space-y-2">
              <p className="text-sm text-muted-foreground">
                MetaMask is not installed in your browser.
              </p>
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
          )}

          <p className="text-xs text-muted-foreground text-center pt-1">
            By connecting, you agree to the platform&apos;s terms of use.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
