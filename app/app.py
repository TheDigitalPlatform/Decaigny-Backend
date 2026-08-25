from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.api import api_router
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(seed=True)
    yield


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    setup_logging()
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )
 
    # Optional debug print
    print("CORS Origins Allowed:", settings.cors_origins)
 
    # Temporary more permissive CORS Middleware for debugging
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins temporarily
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
 
    app.include_router(api_router, prefix=settings.API_V1_STR)
 
    return app
 
 