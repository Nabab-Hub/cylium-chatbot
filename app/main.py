import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.routes import health_router, chat_router
from app.services.firebase import init_firebase
from app.services.gemini import get_gemini_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("chatbot.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown events."""
    logger.info("Initializing CyliumOS AI Chatbot API...")

    settings = get_settings()

    # Pre-initialize Firebase and Gemini client
    try:
        init_firebase()
    except Exception as exc:
        logger.warning("Firebase initialization note: %s", exc)

    try:
        get_gemini_client()
    except Exception as exc:
        logger.warning("Gemini initialization note: %s", exc)

    logger.info(
        "CyliumOS AI Chatbot API started successfully on %s:%s (Model: %s)",
        settings.host,
        settings.port,
        settings.gemini_model,
    )
    yield
    logger.info("CyliumOS AI Chatbot API shutting down.")


# Application Factory
settings = get_settings()

app = FastAPI(
    title="CyliumOS AI Chatbot API",
    version="1.0.0",
    description=(
        "Enterprise-grade AI Chatbot microservice powered by Google Gemini text model "
        "and real-time Firebase Firestore RAG (Retrieval Augmented Generation)."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router)
app.include_router(chat_router)
