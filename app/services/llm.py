import logging
from typing import List, Optional, AsyncGenerator, Dict, Any
from app.core.config import get_settings
from app.models.schemas import ChatMessage
from app.services.groq import get_groq_service
from app.services.gemini import get_gemini_service

logger = logging.getLogger("chatbot.llm")


class UnifiedLLMService:
    """
    Unified LLM router that dynamically dispatches chat requests to
    Groq (active default) or Gemini based on `LLM_PROVIDER` in .env.
    """

    def __init__(self):
        self.settings = get_settings()

    def generate_reply(
        self,
        message: str,
        history: List[ChatMessage],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Dispatches to active LLM provider (Groq or Gemini).
        """
        provider = self.settings.llm_provider.lower().strip()

        if provider == "groq":
            try:
                groq_svc = get_groq_service()
                return groq_svc.generate_reply(message=message, history=history, user_id=user_id)
            except Exception as exc:
                logger.warning("Groq generation failed (%s). Attempting Gemini/fallback.", exc)
                gemini_svc = get_gemini_service()
                return gemini_svc.generate_reply(message=message, history=history, user_id=user_id)
        else:
            # Default to Gemini
            return get_gemini_service().generate_reply(
                message=message, history=history, user_id=user_id
            )

    async def generate_reply_stream(
        self,
        message: str,
        history: List[ChatMessage],
        user_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Dispatches streaming generation to active LLM provider.
        """
        provider = self.settings.llm_provider.lower().strip()

        if provider == "groq":
            try:
                groq_svc = get_groq_service()
                async for chunk in groq_svc.generate_reply_stream(
                    message=message, history=history, user_id=user_id
                ):
                    yield chunk
            except Exception as exc:
                logger.warning("Groq stream failed (%s). Falling back to Gemini/knowledge stream.", exc)
                gemini_svc = get_gemini_service()
                async for chunk in gemini_svc.generate_reply_stream(
                    message=message, history=history, user_id=user_id
                ):
                    yield chunk
        else:
            gemini_svc = get_gemini_service()
            async for chunk in gemini_svc.generate_reply_stream(
                message=message, history=history, user_id=user_id
            ):
                yield chunk


_unified_llm_instance: Optional[UnifiedLLMService] = None


def get_llm_service() -> UnifiedLLMService:
    global _unified_llm_instance
    if _unified_llm_instance is None:
        _unified_llm_instance = UnifiedLLMService()
    return _unified_llm_instance
