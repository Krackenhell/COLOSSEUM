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
import { BackendStatus } from "./components/BackendStatus";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 10000),
      refetchOnWindowFocus: false,
      // Don't throw on error — let components handle gracefully
      throwOnError: false,
    },
  },
});

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <WalletProvider>
        <BackendStatus />
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
