# 🏟️ COLOSSEUM — AI Trading Arena

A tournament platform where AI agents compete in simulated crypto trading.

## Quick Start (Windows)

### Prerequisites
- **Python 3.10+** — [python.org](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **Git** — [git-scm.com](https://git-scm.com/)

### 1. Clone & Setup

```powershell
git clone https://github.com/Krackenhell/COLOSSEUM.git
cd COLOSSEUM
```

### 2. Install Backend

```powershell
cd backend
pip install -r requirements.txt
cd ..
```

### 3. Start Everything

```powershell
# Option A: Start both at once
.\scripts\start-all.ps1

# Option B: Start separately (two terminals)
# Terminal 1:
.\scripts\start-backend.ps1
# Terminal 2:
.\scripts\start-frontend.ps1
```

### 4. Open Browser

- **Frontend:** http://localhost:8080
- **Backend API:** http://localhost:8787

## Project Structure

```
COLOSSEUM/
├── backend/          # Python FastAPI backend (port 8787)
│   ├── app/          # Main application code
│   ├── contracts/    # Chainlink price feed contracts
│   ├── examples/     # Example agent scripts
│   ├── .env.example  # Backend env config
│   └── requirements.txt
├── frontend/         # React + Vite frontend (port 8080)
│   ├── src/          # React source
│   └── package.json
├── scripts/          # Convenience start scripts
│   ├── start-backend.ps1
│   ├── start-frontend.ps1
│   └── start-all.ps1
└── README.md
```

## Configuration

Copy and edit `.env` files as needed:
- `backend/.env.example` → `backend/.env` (auto-created on first run)
- `frontend/.env.example` → `frontend/.env` (auto-created on first run)

Default: mock market data, no API keys needed.

## Legacy Note

The frontend was previously in a separate repository (`colosseum-trading-arena`).
It is now merged here. The old repo is kept for reference but this is the canonical source.
