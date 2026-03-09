import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { Button } from "@/components/ui/button";
import { ControlPanelCard } from "@/components/arena/ControlPanelCard";
import { useWallet } from "@/hooks/use-wallet";
import { useToast } from "@/hooks/use-toast";
import { CreditCard, Settings, Key, CheckCircle, Copy, AlertTriangle, Loader2, Play, Square, RotateCcw, XCircle } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import * as api from "@/lib/api";

type Step = "payment" | "settings" | "apikey" | "done";

const BASE = import.meta.env.VITE_API_BASE_URL || "";

export default function Onboarding() {
  const { connected, address } = useWallet();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [step, setStep] = useState<Step>("payment");
  const [agentName, setAgentName] = useState("");
  const [agentId, setAgentId] = useState("");
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [allKeys, setAllKeys] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [paymentProcessing, setPaymentProcessing] = useState(false);
  const [existingAgent, setExistingAgent] = useState<any>(null);
  const [showKeyWarning, setShowKeyWarning] = useState(false);

  // Redirect if not connected
  useEffect(() => {
    if (!connected) navigate("/");
  }, [connected, navigate]);

  // Check if wallet already has agent
  useEffect(() => {
    if (!address) return;
    fetch(`${BASE}/agent-api/v1/wallet-agent/${address}`)
      .then(r => r.json())
      .then(data => {
        if (data.exists) {
          setExistingAgent(data);
          setAgentId(data.agentId);
          setAgentName(data.name);
          setStep("done");
        }
      })
      .catch(() => {});
  }, [address]);

  // Load keys when on apikey/done step
  useEffect(() => {
    if ((step === "apikey" || step === "done") && address) {
      loadKeys();
    }
  }, [step, address]);

  const loadKeys = async () => {
    try {
      const res = await fetch(`${BASE}/agent-api/v1/keys-by-wallet`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-api-key": "dev-gateway-key" },
        body: JSON.stringify({ wallet: address }),
      });
      const data = await res.json();
      setAllKeys(Array.isArray(data) ? data : []);
    } catch {}
  };

  /* ── Step A: Payment ── */
  const handlePayment = async () => {
    setPaymentProcessing(true);
    // TODO: Replace with real smart contract call
    // Placeholder: simulate payment delay
    await new Promise(r => setTimeout(r, 1500));
    // simulateSmartContractPayment(address, 0) — MVP discount $0
    setPaymentProcessing(false);
    toast({ title: "Payment Successful", description: "Participation card purchased (MVP: $0 discount applied)." });
    setStep("settings");
  };

  /* ── Step B: Agent Settings ── */
  const handleCreateAgent = async () => {
    if (!agentName.trim()) {
      toast({ title: "Name required", variant: "destructive" });
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${BASE}/agent-api/v1/register-wallet`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-api-key": "dev-gateway-key" },
        body: JSON.stringify({ wallet: address, name: agentName.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.error || "Registration failed");
      setAgentId(data.agentId);
      setApiKey(data.api_key);
      setShowKeyWarning(true);
      setStep("apikey");
    } catch (e: any) {
      toast({ title: "Error", description: e.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  /* ── API Key management ── */
  const handleCreateNewKey = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${BASE}/agent-api/v1/create-key`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-api-key": "dev-gateway-key" },
        body: JSON.stringify({ wallet: address }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");
      setApiKey(data.api_key);
      setShowKeyWarning(true);
      loadKeys();
    } catch (e: any) {
      toast({ title: "Error", description: e.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeKey = async (key: string) => {
    try {
      await fetch(`${BASE}/agent-api/v1/keys/${key}/revoke`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-api-key": "dev-gateway-key" },
      });
      toast({ title: "Key revoked" });
      loadKeys();
    } catch {}
  };

  const copyKey = () => {
    if (apiKey) {
      navigator.clipboard.writeText(apiKey);
      toast({ title: "Copied!", description: "API key copied to clipboard." });
    }
  };

  /* ── Test Agent ── */
  const [testAgentId, setTestAgentId] = useState<string | null>(null);
  const [testAgentRunning, setTestAgentRunning] = useState(false);
  const [testAgentLog, setTestAgentLog] = useState<string[]>([]);
  const [testAgentTrades, setTestAgentTrades] = useState(0);

  // Poll test agent status
  useEffect(() => {
    if (!testAgentId) return;
    const iv = setInterval(async () => {
      try {
        const s = await api.getTestAgentStatus(testAgentId);
        setTestAgentRunning(s.running);
        setTestAgentLog(s.log ?? []);
        setTestAgentTrades((s as any).trades ?? 0);
        if (!s.running) clearInterval(iv);
      } catch { /* ignore */ }
    }, 3000);
    return () => clearInterval(iv);
  }, [testAgentId]);

  const handleRunTestAgent = async () => {
    // Find active tournament
    try {
      const tournaments = await api.listTournaments();
      const active = tournaments?.[0];
      if (!active) {
        toast({ title: "No Tournament", description: "No active tournament found.", variant: "destructive" });
        return;
      }
      if (active.effectiveStatus === "finished" || active.effectiveStatus === "archived") {
        toast({ title: "Tournament Ended", description: "This tournament has already finished.", variant: "destructive" });
        return;
      }
      const result = await api.startTestAgent(active.id);
      setTestAgentId(result.agentId);
      setTestAgentRunning(true);
      toast({
        title: "Test Agent Started!",
        description: `Agent ${result.agentId} is ${active.effectiveStatus === "running" ? "trading now" : "waiting for tournament to start"}.`,
      });
    } catch (e: any) {
      toast({ title: "Failed", description: e.message, variant: "destructive" });
    }
  };

  const handleStopTestAgent = async () => {
    if (!testAgentId) return;
    try {
      await api.stopTestAgent(testAgentId);
      setTestAgentRunning(false);
      toast({ title: "Test Agent Stopped" });
    } catch (e: any) {
      toast({ title: "Stop failed", description: e.message, variant: "destructive" });
    }
  };

  const stepIndicator = (s: Step, label: string, icon: React.ReactNode) => {
    const steps: Step[] = ["payment", "settings", "apikey", "done"];
    const current = steps.indexOf(step);
    const target = steps.indexOf(s);
    const active = current >= target;
    return (
      <div className={`flex items-center gap-2 text-sm ${active ? "text-cyan" : "text-muted-foreground"}`}>
        {active ? <CheckCircle className="h-4 w-4" /> : icon}
        <span className={active ? "font-medium" : ""}>{label}</span>
      </div>
    );
  };

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-display font-bold">Agent Onboarding</h1>
          <p className="text-sm text-muted-foreground">Set up your trading agent in the arena</p>
        </div>

        {/* Progress */}
        <div className="flex items-center gap-6 p-4 bg-card border border-border rounded-lg">
          {stepIndicator("payment", "Purchase Card", <CreditCard className="h-4 w-4" />)}
          <div className="h-px flex-1 bg-border" />
          {stepIndicator("settings", "Agent Settings", <Settings className="h-4 w-4" />)}
          <div className="h-px flex-1 bg-border" />
          {stepIndicator("apikey", "API Key", <Key className="h-4 w-4" />)}
        </div>

        {/* Step: Payment */}
        {step === "payment" && (
          <ControlPanelCard title="Purchase Participation Card">
            <div className="space-y-4">
              <div className="p-4 bg-secondary/50 rounded-lg border border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Arena Participation Card</p>
                    <p className="text-sm text-muted-foreground">Season 1 Entry</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm line-through text-muted-foreground">$100.00</p>
                    <p className="text-lg font-bold text-cyan">$0.00</p>
                    <p className="text-xs text-accent">MVP Discount</p>
                  </div>
                </div>
              </div>

              {/* TODO: Smart contract call placeholder */}
              <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-xs text-yellow-200">
                <AlertTriangle className="h-3 w-3 inline mr-1" />
                MVP: Payment is simulated. Smart contract integration pending.
              </div>

              <Button variant="neon" className="w-full gap-2" onClick={handlePayment} disabled={paymentProcessing}>
                {paymentProcessing ? <Loader2 className="h-4 w-4 animate-spin" /> : <CreditCard className="h-4 w-4" />}
                {paymentProcessing ? "Processing..." : "Purchase Card — $0.00"}
              </Button>
            </div>
          </ControlPanelCard>
        )}

        {/* Step: Agent Settings */}
        {step === "settings" && (
          <ControlPanelCard title="Configure Your Agent">
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium block mb-1">Agent Name</label>
                <input
                  className="w-full bg-secondary border border-border rounded px-3 py-2 text-sm"
                  placeholder="e.g. AlphaTrader"
                  value={agentName}
                  onChange={(e) => setAgentName(e.target.value)}
                  maxLength={32}
                />
              </div>
              <div className="p-3 bg-secondary/30 rounded-lg text-xs text-muted-foreground">
                <p>Agent ID will be auto-generated.</p>
                <p>One agent per wallet address — choose wisely!</p>
              </div>
              <Button variant="neon" className="w-full gap-2" onClick={handleCreateAgent} disabled={loading}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
                Create Agent
              </Button>
            </div>
          </ControlPanelCard>
        )}

        {/* Step: API Key */}
        {(step === "apikey" || step === "done") && (
          <>
            <ControlPanelCard title="Your Agent">
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                  <div>
                    <p className="font-medium">{agentName}</p>
                    <p className="text-xs text-muted-foreground font-mono">{agentId}</p>
                  </div>
                  <CheckCircle className="h-5 w-5 text-cyan" />
                </div>

                {/* Test Agent */}
                {testAgentId && testAgentRunning ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 p-3 bg-cyan/10 border border-cyan/30 rounded-lg">
                      <Loader2 className="h-4 w-4 animate-spin text-cyan" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-cyan">Test Agent: {testAgentId}</p>
                        <p className="text-xs text-muted-foreground">{testAgentTrades} trades</p>
                      </div>
                      <Button variant="destructive" size="sm" className="gap-1" onClick={handleStopTestAgent}>
                        <Square className="h-3 w-3" /> Stop
                      </Button>
                    </div>
                    {testAgentLog.length > 0 && (
                      <div className="max-h-28 overflow-y-auto bg-secondary/50 rounded p-2 text-xs font-mono space-y-0.5">
                        {testAgentLog.slice(-6).map((line, i) => (
                          <div key={i} className="text-muted-foreground">{line}</div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <Button variant="outline" className="w-full gap-2" onClick={handleRunTestAgent}>
                    <Play className="h-4 w-4" />
                    Run Test Agent
                  </Button>
                )}
              </div>
            </ControlPanelCard>

            <ControlPanelCard title="API Keys">
              <div className="space-y-4">
                {/* Newly created key display */}
                {apiKey && showKeyWarning && (
                  <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg space-y-2">
                    <div className="flex items-center gap-2 text-red-400 text-sm font-medium">
                      <AlertTriangle className="h-4 w-4" />
                      Save this key now! It will NOT be shown again.
                    </div>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 bg-secondary p-2 rounded text-xs font-mono break-all">{apiKey}</code>
                      <Button size="sm" variant="outline" onClick={copyKey}>
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                    <Button size="sm" variant="ghost" className="text-xs" onClick={() => setShowKeyWarning(false)}>
                      I've saved it — dismiss
                    </Button>
                  </div>
                )}

                {/* Key list */}
                <div className="space-y-2">
                  {allKeys.map((k, i) => (
                    <div key={i} className="flex items-center justify-between p-2 bg-secondary/30 rounded text-xs">
                      <div>
                        <span className="font-mono">{k.api_key}</span>
                        <span className={`ml-2 ${k.is_active && !k.expired ? "text-cyan" : "text-crimson"}`}>
                          {k.is_active && !k.expired ? "Active" : k.expired ? "Expired" : "Revoked"}
                        </span>
                      </div>
                      {k.is_active && !k.expired && (
                        <Button size="sm" variant="ghost" className="h-6 text-xs text-crimson" onClick={() => handleRevokeKey(k.api_key_full)}>
                          <XCircle className="h-3 w-3 mr-1" /> Revoke
                        </Button>
                      )}
                    </div>
                  ))}
                </div>

                {/* Create new / rotate */}
                <Button variant="outline" className="w-full gap-2" onClick={handleCreateNewKey} disabled={loading}>
                  <RotateCcw className="h-4 w-4" />
                  Generate New API Key (rotates access)
                </Button>
              </div>
            </ControlPanelCard>

            <div className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={() => navigate("/app/user")}>
                Go to User Panel
              </Button>
            </div>
          </>
        )}
      </div>

      {/* Key warning dialog on first creation */}
      <Dialog open={showKeyWarning && step === "apikey" && !!apiKey} onOpenChange={() => {}}>
        <DialogContent className="sm:max-w-md" onPointerDownOutside={(e) => e.preventDefault()}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-400">
              <AlertTriangle className="h-5 w-5" />
              Save Your API Key
            </DialogTitle>
            <DialogDescription>
              This key is shown <strong>only once</strong>. Copy and store it securely. You will NOT be able to see it again.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 pt-2">
            <div className="flex items-center gap-2">
              <code className="flex-1 bg-secondary p-3 rounded text-xs font-mono break-all">{apiKey}</code>
              <Button size="sm" variant="outline" onClick={copyKey}>
                <Copy className="h-4 w-4" />
              </Button>
            </div>
            <Button variant="neon" className="w-full" onClick={() => { setShowKeyWarning(false); setStep("done"); }}>
              I've Saved My Key
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}
