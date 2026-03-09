
import os
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routes import tournaments, gateway, ui, agent_api, test_agent_routes

app = FastAPI(title="Colosseum MVP", version="0.3.0")

# CORS: allow frontend dev server and any localhost origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    print(f"ERROR on {request.method} {request.url}:\n{tb}")
    return JSONResponse(status_code=500, content={"error": str(exc), "detail": tb})


app.include_router(ui.router)
app.include_router(tournaments.router)
app.include_router(gateway.router)
app.include_router(agent_api.router)
app.include_router(test_agent_routes.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/market-status")
def market_status():
    from app.services.market_data import get_market_status, MARKET_SOURCE
    try:
        return get_market_status()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"market-status error: {e}")
        return {"marketSource": MARKET_SOURCE, "status": "degraded",
                "error": str(e)[:200], "symbols": {}}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8787"))
    # Stable mode by default: reload is OFF to prevent random restarts while files change.
    reload_enabled = os.environ.get("COLOSSEUM_RELOAD", "0") == "1"
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=reload_enabled)
