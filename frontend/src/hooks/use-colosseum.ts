/**
 * React Query hooks for Colosseum backend.
 * Polls automatically where appropriate.
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "@/lib/api";

// ─── Health ───
export function useHealth() {
  return useQuery({ queryKey: ["health"], queryFn: api.getHealth, refetchInterval: 10_000 });
}

// ─── Tournaments ───
export function useTournaments() {
  return useQuery({ queryKey: ["tournaments"], queryFn: api.listTournaments, refetchInterval: 5_000 });
}

export function useAllTournaments() {
  return useQuery({ queryKey: ["tournaments-all"], queryFn: api.listAllTournaments });
}

export function useTournamentTimer(tid: string | undefined) {
  return useQuery({
    queryKey: ["timer", tid],
    queryFn: () => api.getTournamentTimer(tid!),
    enabled: !!tid,
    refetchInterval: 2_000,
  });
}

export function useLeaderboard(tid: string | undefined) {
  return useQuery({
    queryKey: ["leaderboard", tid],
    queryFn: () => api.getTournamentLeaderboard(tid!),
    enabled: !!tid,
    refetchInterval: 5_000,
  });
}

export function useEvents(tid: string | undefined) {
  return useQuery({
    queryKey: ["events", tid],
    queryFn: () => api.getTournamentEvents(tid!),
    enabled: !!tid,
    refetchInterval: 5_000,
  });
}

export function useAgentsStudio(tid: string | undefined) {
  return useQuery({
    queryKey: ["agents-studio", tid],
    queryFn: () => api.getAgentsStudio(tid!),
    enabled: !!tid,
    refetchInterval: 5_000,
  });
}

export function useEquityChart(tid: string | undefined) {
  return useQuery({
    queryKey: ["equity-chart", tid],
    queryFn: () => api.getEquityChart(tid!),
    enabled: !!tid,
    refetchInterval: 15_000,
  });
}

export function useTournamentAgents(tid: string | undefined) {
  return useQuery({
    queryKey: ["tournament-agents", tid],
    queryFn: () => api.getTournamentAgents(tid!),
    enabled: !!tid,
    refetchInterval: 5_000,
  });
}

// ─── Market ───
export function useMarketStatus() {
  return useQuery({
    queryKey: ["market-status"],
    queryFn: api.getMarketStatus,
    refetchInterval: 5_000,
  });
}

// ─── Test Agent (admin) ───
export function useTestAgents() {
  return useQuery({ queryKey: ["test-agents"], queryFn: api.listTestAgents, refetchInterval: 5_000 });
}

export function useTestAgentStatus(agentId: string | undefined) {
  return useQuery({
    queryKey: ["test-agent-status", agentId],
    queryFn: () => api.getTestAgentStatus(agentId!),
    enabled: !!agentId,
    refetchInterval: 3_000,
  });
}

// ─── Mutations ───
export function useCreateTournament() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.createTournament,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["tournaments"] }); },
  });
}

export function useSetTournamentStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ tid, status }: { tid: string; status: string }) =>
      api.setTournamentStatus(tid, status),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["tournaments"] }); },
  });
}

export function useRegisterAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ tid, agentId, name }: { tid: string; agentId: string; name?: string }) =>
      api.registerAgent(tid, agentId, name),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["tournament-agents"] }); },
  });
}

export function useStartTestAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.startTestAgent,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["test-agents"] });
      qc.invalidateQueries({ queryKey: ["leaderboard"] });
      qc.invalidateQueries({ queryKey: ["agents-studio"] });
      qc.invalidateQueries({ queryKey: ["tournament-agents"] });
    },
  });
}

export function useStopTestAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.stopTestAgent,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["test-agents"] }); },
  });
}
