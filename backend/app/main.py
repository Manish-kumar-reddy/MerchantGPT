import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

import app.models  # noqa: F401
from app.api.routes import analytics, auth, campaigns, chat
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine, SessionLocal
from scripts.seed import seed

settings = get_settings()
logger = logging.getLogger("merchantgpt")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enable pgvector if possible
    async with engine.connect() as conn:
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.commit()
        except DBAPIError:
            logger.warning(
                "Could not create pgvector extension. Assuming it already exists."
            )

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    db = SessionLocal()
    try:
        seed(db)
        db.commit()
    finally:
        db.close()


    yield

    await engine.dispose()


app = FastAPI(
    title="MerchantGPT API",
    description="Autonomous AI growth manager for e-commerce merchants.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}


app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(analytics.router, prefix=settings.api_v1_prefix)
app.include_router(chat.router, prefix=settings.api_v1_prefix)
app.include_router(campaigns.router, prefix=settings.api_v1_prefix)