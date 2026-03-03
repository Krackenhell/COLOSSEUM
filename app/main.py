import os
from fastapi import FastAPI
from app.routes import tournaments, gateway, ui

app = FastAPI(title="Colosseum MVP", version="0.1.0")

app.include_router(ui.router)
app.include_router(tournaments.router)
app.include_router(gateway.router)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8787"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
