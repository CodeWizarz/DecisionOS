from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog
import os

from decisionos.core.config import settings
from decisionos.core.logging import configure_logging, logging_middleware
from decisionos.api import v1

# Configure logging for the main process
configure_logging()
logger = structlog.get_logger()
# Middleware addition handled in create_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events: startup and shutdown logic.
    
    Why:
    - Better than on_event("startup") deprecated methods.
    - Central place for connection pooling initialization if needed.
    """
    logger.info("startup", app=settings.APP_NAME, env=settings.ENV)
    
    # Validation check: Ensure DB connection is possible here if strictly required
    # or rely on connection pool lazy init
    
    yield
    
    logger.info("shutdown")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="Production AI Decision Intelligence System",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.ENV != "production" else None,
        redoc_url="/redoc" if settings.ENV != "production" else None,
    )

    # Mount Static Files for Demo UI
    # We use a relative path from this file to static directory
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    if os.path.exists(static_dir):
        app.mount("/demo", StaticFiles(directory=static_dir, html=True), name="demo")
    
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/demo")

    # Middleware
    app.middleware("http")(logging_middleware)

    # Security: Restrict CORS in production
    if settings.ENV == "development":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Health Check
    @app.get("/health", tags=["System"])
    async def health_check():
        return {"status": "ok", "version": "0.1.0"}

    # Include API Routers
    app.include_router(v1.router, prefix="/api/v1")
    app.include_router(v1.demo.router, prefix="/api/v1/demo", tags=["Demo"])

    return app

app = create_app()
