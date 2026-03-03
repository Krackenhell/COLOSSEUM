# Colosseum MVP (Python)

Trading tournament simulator with FastAPI.

## Quick Start
```bash
pip install -r requirements.txt
python -m app.main
```
Open http://localhost:8787 — click **Quick Start Demo**, then submit signals.

## Env Vars
| Var | Default | Description |
|-----|---------|-------------|
| PORT | 8787 | Server port |
| AGENT_GATEWAY_KEY | dev-gateway-key | API key for /gateway/* |
| RATE_LIMIT_MAX | 60 | Requests per minute per key |
| TS_DRIFT_MS | 30000 | Max timestamp drift in ms |
