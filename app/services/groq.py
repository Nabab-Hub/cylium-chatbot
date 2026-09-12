import re
import logging
from typing import List, Optional, AsyncGenerator, Dict, Any
from app.core.config import get_settings
from app.core.constants import SYSTEM_PROMPT
from app.models.schemas import ChatMessage
from app.utils.helpers import match_suggested_actions
from app.services.rag import get_rag_service

logger = logging.getLogger("chatbot.groq")

_groq_client = None


def get_groq_client():
    """
    Initializes and returns the Groq client singleton.
    """
    global _groq_client
    if _groq_client is not None:
        return _groq_client

    settings = get_settings()
    api_key = settings.resolved_groq_api_key

    if not api_key:
        logger.error("No Groq API key configured!")
        return None

    try:
        from groq import Groq
        _groq_client = Groq(api_key=api_key)
        logger.info("Initialized Groq client successfully.")
        return _groq_client
    except ImportError:
        logger.error("Package `groq` is not installed. Please run `pip install groq`.")
        return None
    except Exception as exc:
        logger.error("Failed to initialize Groq client: %s", exc)
        return None


def clean_think_tags(text: str) -> str:
    """
    Removes internal <think>...</think> reasoning blocks produced by Qwen models
    so the user receives crisp, direct, and formatted answers.
    """
    if not text:
        return ""
    if "</think>" in text:
        return text.split("</think>")[-1].strip()
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return cleaned


class GroqChatService:
    """
    Interacts with Groq API (e.g. qwen/qwen3.6-27b, llama-3.3-70b-versatile)
    for ultra-fast RAG-augmented generation.
    """

    def __init__(self):
        self.settings = get_settings()

    def _prepare_messages(
        self,
        message: str,
        history: List[ChatMessage],
        user_id: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Builds the messages array with system instruction, live RAG context, and prior turns.
        """
        rag_service = get_rag_service()
        rag_context = rag_service.build_rag_context(user_id=user_id)

        system_instruction = (
            f"{SYSTEM_PROMPT}\n\n"
            f"--- BEGIN CYLIUMOS KNOWLEDGE & LIVE PLATFORM CONTEXT ---\n"
            f"{rag_context}\n"
            f"--- END CYLIUMOS KNOWLEDGE & LIVE PLATFORM CONTEXT ---\n\n"
            f"Answer accurately based on the platform context above. "
            f"Provide direct answers without outputting internal thinking tags."
        )

        messages = [{"role": "system", "content": system_instruction}]

        for msg in history:
            role = "user" if msg.role == "user" else "assistant"
            messages.append({"role": role, "content": msg.content})

        messages.append({"role": "user", "content": message})
        return messages

    def generate_reply(
        self,
        message: str,
        history: List[ChatMessage],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates a synchronous completion reply using Groq.
        """
        client = get_groq_client()
        if client is None:
            raise RuntimeError("Groq client is not initialized. Please set GROQ_API_KEY.")

        messages = self._prepare_messages(message=message, history=history, user_id=user_id)
        model_name = self.settings.groq_model

        # Token limit set generous (2500) to ensure complete, fully-finished responses
        create_kwargs = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.6,
            "max_completion_tokens": 2500,
            "top_p": 0.95,
            "stream": False,
            "stop": None,
        }
        if "qwen" in model_name.lower():
            create_kwargs["reasoning_effort"] = "none"

        completion = client.chat.completions.create(**create_kwargs)

        raw_reply = completion.choices[0].message.content or ""
        reply_text = clean_think_tags(raw_reply)
        if not reply_text:
            reply_text = raw_reply.strip()

        actions = match_suggested_actions(query=message, response_text=reply_text)
        return {
            "text": reply_text,
            "actions": actions,
        }

    async def generate_reply_stream(
        self,
        message: str,
        history: List[ChatMessage],
        user_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generates a streaming reply (token by token) using Groq.
        """
        client = get_groq_client()
        if client is None:
            yield "Error: Groq client is not available. Please verify GROQ_API_KEY."
            return

        messages = self._prepare_messages(message=message, history=history, user_id=user_id)
        model_name = self.settings.groq_model

        try:
            stream_kwargs = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.6,
                "max_completion_tokens": 2500,
                "top_p": 0.95,
                "stream": True,
                "stop": None,
            }
            if "qwen" in model_name.lower():
                stream_kwargs["reasoning_effort"] = "none"

            completion = client.chat.completions.create(**stream_kwargs)

            in_think_block = False
            think_buffer = ""
            for chunk in completion:
                delta = chunk.choices[0].delta.content or ""
                if not delta:
                    continue

                if not in_think_block and "<think>" in delta:
                    in_think_block = True
                    think_buffer = delta
                    continue

                if in_think_block:
                    think_buffer += delta
                    if "</think>" in think_buffer:
                        after = think_buffer.split("</think>")[-1].lstrip()
                        in_think_block = False
                        think_buffer = ""
                        if after:
                            yield after
                    continue

                yield delta

        except Exception as exc:
            logger.error("Error in Groq streaming (%s): %s", model_name, exc)
            yield f"\n\n*(Error generating streaming response from Groq: {str(exc)})*"


# Singleton instance
_groq_service_instance: Optional[GroqChatService] = None


def get_groq_service() -> GroqChatService:
    global _groq_service_instance
    if _groq_service_instance is None:
        _groq_service_instance = GroqChatService()
    return _groq_service_instance
