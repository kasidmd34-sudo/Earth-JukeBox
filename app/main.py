"""Main FastAPI Application Entrypoint for Earth Jukebox."""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from app.config import settings
from app.data.nasa_client import nasa_client
from app.reports.router import router as reports_router
from app.api import (
    routes_health,
    routes_modules,
    routes_observations,
    routes_predictions,
    routes_intelligence,
    routes_sonification,
    routes_evaluation,
    routes_location,
    routes_metadata,
    routes_media
)
from app.web import pages as web_pages
from app.api import routes_media
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("earth_jukebox")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=======================================================")
    logger.info("Earth Jukebox Engine Booting...")
    logger.info("Compliance: STRICT NASA DATA SOURCES ONLY")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"CORS Allowed Origins: {settings.cors_origins}")
    logger.info("=======================================================")
    yield
    logger.info("Closing NASA HTTP connection pools...")
    await nasa_client.close()
    logger.info("Earth Jukebox Engine Shut Down cleanly.")


app = FastAPI(
    title="Earth Jukebox API",
    description="NASA-Powered Environmental Intelligence, Prediction & Sonification Engine",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration - supports development origins and localhost testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.ENVIRONMENT != "development" else ["*"],
    allow_credentials=True if settings.ENVIRONMENT != "development" else False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "application": "Earth Jukebox",
            "message": exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "application": "Earth Jukebox",
            "message": "Validation error in request payload.",
            "errors": jsonable_encoder(exc.errors()),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled system exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "application": "Earth Jukebox",
            "message": "An internal error occurred while processing environmental intelligence.",
            "detail": str(exc) if settings.ENVIRONMENT == "development" else "Internal server error",
        },
    )


# Demo Page Endpoint: serves demo.html directly from project root if accessed via browser
@app.get("/demo", response_class=HTMLResponse, tags=["Demo"], include_in_schema=True)
@app.get("/demo.html", response_class=HTMLResponse, include_in_schema=False)
def get_demo_page():
    demo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo.html")
    if os.path.exists(demo_path):
        return FileResponse(demo_path, media_type="text/html")
    return HTMLResponse(
        "<h3>demo.html not yet generated. Please wait while the demonstration dashboard is created.</h3>",
        status_code=404,
    )


# Register All API Routers
app.include_router(routes_health.router)
app.include_router(routes_modules.router)
app.include_router(routes_observations.router)
app.include_router(routes_predictions.router)
app.include_router(routes_intelligence.router)
app.include_router(routes_sonification.router)
app.include_router(routes_evaluation.router)
app.include_router(routes_location.router)
app.include_router(routes_metadata.router)
app.include_router(reports_router)
app.include_router(routes_media.router)
app.include_router(web_pages.router)
app.include_router(routes_media.router)