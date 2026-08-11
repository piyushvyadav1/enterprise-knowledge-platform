from fastapi import FastAPI
from sqlalchemy import text

from fastapi.middleware.cors import CORSMiddleware

from app.database.database import Base, engine
from app.models import User

from app.api.v1.auth import (
    router as auth_router,
)

from app.api.v1.users import (
    router as users_router,
)

from app.api.v1.documents import (
    router as documents_router,
)

from app.api.v1.retrieval import (
    router as retrieval_router,
)

from app.api.v1.ask import (
    router as ask_router,
)


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(
    bind=engine
)


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Enterprise Knowledge Intelligence Platform",
    description=(
        "Backend API for the Enterprise "
        "Knowledge Intelligence Platform"
    ),
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        # Local development
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://172.23.152.154:5173",

        # Ngrok frontend
        "https://unevaporative-sherill-sturdily.ngrok-free.dev",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# =========================================================
# API ROUTES
# =========================================================

app.include_router(
    documents_router,
    prefix="/api/v1",
)


app.include_router(
    retrieval_router,
    prefix="/api/v1",
)


app.include_router(
    ask_router,
    prefix="/api/v1",
)


app.include_router(
    auth_router,
    prefix="/api/v1",
)


app.include_router(
    users_router,
    prefix="/api/v1",
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "application": (
            "Enterprise Knowledge "
            "Intelligence Platform"
        ),

        "version": "1.0.0",

        "status": "running",
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
    }


# =========================================================
# DATABASE HEALTH
# =========================================================

@app.get("/health/database")
def database_health():

    try:

        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as exc:

        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(exc),
        }