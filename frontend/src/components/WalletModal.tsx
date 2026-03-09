import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useWallet } from "@/hooks/use-wallet";
import { Wallet } from "lucide-react";

interface WalletModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConnected?: () => void;
}

export function WalletModal({ open, onOpenChange, onConnected }: WalletModalProps) {
  const { connect } = useWallet();

  const handleConnect = () => {
    connect();
    onOpenChange(false);
    onConnected?.();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Wallet className="h-5 w-5 text-cyan" />
            Connect Wallet
          </DialogTitle>
          <DialogDescription>
            Connect your wallet to access the Colosseum Arena.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3 pt-4">
          {/* TODO: Replace with real wallet options (Phantom, MetaMask, etc.) */}
          <Button variant="outline" className="w-full justify-start gap-3 h-14" onClick={handleConnect}>
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white text-xs font-bold">P</div>
            <div className="text-left">
              <div className="font-medium">Phantom</div>
              <div className="text-xs text-muted-foreground">Solana Wallet</div>
            </div>
          </Button>
          <Button variant="outline" className="w-full justify-start gap-3 h-14" onClick={handleConnect}>
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white text-xs font-bold">M</div>
            <div className="text-left">
              <div className="font-medium">MetaMask</div>
              <div className="text-xs text-muted-foreground">EVM Wallet</div>
            </div>
          </Button>
          <p className="text-xs text-muted-foreground text-center pt-2">
            {/* TODO: MVP simulated connect — no real chain interaction */}
            MVP: Simulated wallet connection
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
