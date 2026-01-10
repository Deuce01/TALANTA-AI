"""
TALANTA AI Backend - Main Application Entry Point
The Neural Workforce Grid
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging

from app.config import settings
from app.database import init_databases, close_databases
from app.api import auth, chat, market, verify, admin
from app.core.pii_redaction import PIIRedactionMiddleware
from app.core.audit import AuditMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events"""
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📍 Environment: {settings.ENVIRONMENT}")
    
    try:
        await init_databases()
        logger.info("✓ All systems operational")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down gracefully...")
    await close_databases()
    logger.info("✓ Shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Sovereign Digital Infrastructure for Kenya's Workforce",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)


# ==================== Middleware ====================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PII Redaction Middleware (Data Sovereignty)
if settings.ENABLE_PII_REDACTION:
    app.add_middleware(PIIRedactionMiddleware)
    logger.info("✓ PII Redaction Middleware enabled")

# Audit Logging Middleware
if settings.ENABLE_AUDIT_LOGGING:
    app.add_middleware(AuditMiddleware)
    logger.info("✓ Audit Logging Middleware enabled")


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# ==================== Exception Handlers ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler for standardized error responses"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again later.",
            "detail": str(exc) if settings.DEBUG else None,
        }
    )


# ==================== Routes ====================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API health check"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "message": "Low Friction Entry, High Trust Output 🇰🇪"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check for all services"""
    from app.database import get_redis_client, Neo4jConnection, engine
    
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    try:
        # Check PostgreSQL
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        health_status["services"]["postgres"] = "ok"
    except Exception as e:
        health_status["services"]["postgres"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        # Check Neo4j
        driver = Neo4jConnection.get_driver()
        driver.verify_connectivity()
        health_status["services"]["neo4j"] = "ok"
    except Exception as e:
        health_status["services"]["neo4j"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        # Check Redis
        redis = await get_redis_client()
        await redis.ping()
        health_status["services"]["redis"] = "ok"
    except Exception as e:
        health_status["services"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


# Register API routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/chat", tags=["Conversational AI"])
app.include_router(market.router, prefix="/market", tags=["Market Intelligence"])
app.include_router(verify.router, prefix="/verify", tags=["Verification"])
app.include_router(admin.router, prefix="/admin", tags=["Administration"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
