from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.database import get_engine

app = FastAPI(title="SupportOps API", version="0.1.0")


@app.get("/api/health")
def health():
    return {"status": "ok", "environment": "synthetic sandbox"}


@app.get("/api/ready")
def ready():
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": "offline"})
    return {"status": "ready", "database": "connected"}


@app.get("/api/config")
def public_config():
    settings = get_settings()
    return {
        "model": settings.model_name,
        "max_tool_calls": settings.agent_max_tool_calls,
        "timeout_seconds": settings.agent_timeout_seconds,
        "agent_enabled": False,
        "mutations_enabled": False,
    }
