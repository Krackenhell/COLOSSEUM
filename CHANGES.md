# Colosseum Hardening — Changes Report

## Changed Files
1. **app/store.py** — Added `archived_tournaments` dict, `user_agent_tournament` mapping
2. **app/types.py** — Added `TournamentStatus.archived`
3. **app/routes/tournaments.py** — Major: auto-archive, single-agent rule, registration-before-start, replay endpoint, debug endpoint, history endpoint
4. **app/routes/agent_api.py** — Single-agent enforcement in `/join`, registration-before-start, `/rotate-key` endpoint
5. **app/routes/ui.py** — Scroll-safe updates (no page jumping), replay/debug UI panels, history button, chart update-in-place

## Behavior Changes

### UI Performance (Requirement 3)
- `overflow-anchor: none` on body and scrollable containers
- AI log only auto-scrolls if user was already at bottom (`isNearBottom()` check)
- Studio panel preserves `window.scrollY` during DOM rebuild
- Equity chart updates data in-place (`chart.update('none')`) instead of destroy/recreate — eliminates reflow
- Chart animation disabled for smoother updates

### Single Agent Per User (Requirement 4)
- `store.user_agent_tournament` tracks agentId → tournamentId
- Registration blocked if agent already registered in another active tournament (409)
- Registration only allowed when `effective_status` is `scheduled` or `pending`
- During tournament: `/agent-api/v1/rotate-key` allows key rotation (recovery) without creating new agent

### One Active Tournament (Requirement 5)
- `_archive_active_tournaments()` called on every `POST /tournaments`
- All existing active tournaments get `status=archived` and move to `archived_tournaments`
- All data (agents, events, signals, equity snapshots) preserved in store — NOT deleted

### Replay & Debug (Requirement 6)
- `GET /tournaments/{tid}/replay` — Full timeline combining events + signal records, sorted by timestamp
- `GET /tournaments/{tid}/debug/{agent_id}` — Diagnostics: rank, PnL, drawdown, rejection analysis, worst equity drops
- `GET /tournaments/all-history` — Lists all tournaments (active + archived)
- UI: Replay & Debug panel with buttons

### Cleanup (Requirement 2)
- All `__pycache__` directories cleaned
- `.gitignore` already had `__pycache__/`

## Run / Test Steps
```bash
cd C:\Users\Administrator\.openclaw\workspace\colosseum-new-version\COLOSSEUM
python -m uvicorn app.main:app --host 0.0.0.0 --port 8787
```
1. Open http://localhost:8787
2. Create tournament → previous ones auto-archived
3. Register agent → only works before start, one per user
4. Start test AI → verify no page jumping
5. After trades, use Replay & Debug panel
6. API: `GET /tournaments/{tid}/replay`, `GET /tournaments/{tid}/debug/{agentId}`

## Known Caveats
- In-memory store: all data lost on restart (no persistence layer yet)
- `user_agent_tournament` mapping cleared on new tournament creation (by design: fresh registration cycle)
- Replay timeline can be large for long tournaments — no pagination yet
- Debug diagnostics are heuristic-based first pass, not ML-driven
- Archived tournaments still accessible via `/all-history` and replay, but not in main `/tournaments` list

---

## Chainlink Integration Recommendation

### Architecture (based on https://docs.chain.link/any-api/introduction)

**Goal:** Use Chainlink Any API to bring tournament results on-chain for verifiable, trustless competition.

**Recommended Architecture:**

```
Colosseum Server (off-chain)
    ├── Tournament Engine (existing)
    ├── Results API endpoint (new: GET /tournaments/{tid}/results-hash)
    │   └── Returns: deterministic hash of final leaderboard + all trades
    │
    ▼
Chainlink Node (Any API)
    ├── External Adapter or Direct HTTP GET
    ├── Reads /results-hash endpoint
    ├── Delivers result on-chain
    │
    ▼
Smart Contract (Solidity)
    ├── ColosseumOracle.sol
    ├── requestTournamentResult(tid) → Chainlink request
    ├── fulfill(requestId, resultsHash, winnerId, winnerPnl)
    ├── Prize distribution based on verified results
    └── Historical results stored on-chain (immutable audit)
```

**Implementation Steps:**
1. **Add `/tournaments/{tid}/results-hash` endpoint** — returns keccak256 of canonical JSON (sorted leaderboard + trade hashes)
2. **Deploy ColosseumOracle.sol** — inherits ChainlinkClient, stores tournament results
3. **Configure Chainlink Job** — HTTP GET → JSON parse → ETH transaction
4. **Prize Pool Contract** — accepts deposits, distributes based on oracle-verified winner
5. **Verification UI** — show on-chain proof link for each tournament result

**Key Decisions:**
- Use **Chainlink Any API** (not Data Feeds/VRF) since we need custom off-chain data
- Results hash approach = minimal gas, full verifiability
- Store only hash + winner on-chain; full data stays off-chain (cost efficiency)
- LINK token needed for oracle requests (~0.1-0.25 LINK per request on most networks)

**Next Steps:**
1. Implement results-hash endpoint (1-2 hours)
2. Write & test ColosseumOracle.sol (half day)
3. Set up Chainlink node or use existing operator (depends on network choice)
4. Integration test on Sepolia testnet
5. Add prize pool contract
