from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.core.config import get_settings
from app.utils.helpers import current_timestamp_ms
from app.services.firebase import is_firebase_connected
from app.services.gemini import get_gemini_client
from app.services.groq import get_groq_client

health_router = APIRouter(tags=["Health & Service Info"])


@health_router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service availability, active LLM status (Groq / Gemini), and Firebase state.",
)
async def health_check():
    settings = get_settings()
    provider = settings.llm_provider.lower().strip()
    if provider == "groq":
        llm_ready = get_groq_client() is not None
    else:
        llm_ready = get_gemini_client() is not None

    return HealthResponse(
        status="healthy",
        service="cyliumos-chatbot-api",
        version="1.0.0",
        llm_provider=settings.llm_provider,
        model=settings.active_model_name,
        llm_ready=llm_ready,
        firebase_connected=is_firebase_connected(),
        timestamp=current_timestamp_ms(),
    )


@health_router.get(
    "/",
    summary="Root Service Info",
    description="Returns introductory information and documentation links.",
)
async def service_info():
    settings = get_settings()
    return {
        "service": "CyliumOS AI Chatbot API",
        "description": "Cylium 3.0 conversational AI service with real-time Firebase RAG integration.",
        "llm_provider": "Cylium Engine",
        "model": "cylium-3.0",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "health_url": "/health",
        "chat_endpoint": "/api/v1/chat",
    }
