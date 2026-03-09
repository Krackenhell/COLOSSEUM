import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { WalletProvider } from "@/components/WalletProvider";
import Landing from "./pages/Landing";
import UserPanel from "./pages/UserPanel";
import AgentPanel from "./pages/AgentPanel";
import Leaderboard from "./pages/Leaderboard";
import History from "./pages/History";
import AdminPanel from "./pages/AdminPanel";
import Onboarding from "./pages/Onboarding";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <WalletProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/app/user" element={<UserPanel />} />
            <Route path="/app/agent" element={<AgentPanel />} />
            <Route path="/app/leaderboard" element={<Leaderboard />} />
            <Route path="/app/history" element={<History />} />
            <Route path="/app/admin" element={<AdminPanel />} />
            <Route path="/app/onboarding" element={<Onboarding />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </WalletProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
