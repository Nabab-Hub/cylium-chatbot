import json
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    ChatSession,
    ChatSessionSummary,
)
from app.api.deps import get_current_user_id
from app.services.session_manager import get_session_manager
from app.services.llm import get_llm_service
from app.utils.helpers import current_timestamp_ms, generate_message_id, match_suggested_actions

logger = logging.getLogger("chatbot.routes.chat")

chat_router = APIRouter(prefix="/api/v1/chat", tags=["AI Chatbot"])


@chat_router.post(
    "",
    response_model=ChatResponse,
    summary="Submit user chat message",
    description=(
        "Submits a user prompt to the RAG Chatbot (Groq / Gemini). "
        "For logged-in users, conversation history is preserved in Firebase Firestore. "
        "For guest users, session state is preserved in-memory only."
    ),
)
async def chat_endpoint(
    req: ChatRequest,
    auth_user_id: Optional[str] = Depends(get_current_user_id),
):
    # Resolve user ID priority: explicit request body or Bearer/Header auth
    user_id = req.user_id or auth_user_id
    is_authenticated = bool(user_id)

    session_mgr = get_session_manager()
    llm_svc = get_llm_service()

    # 1. Retrieve or create session
    session = session_mgr.get_or_create_session(
        session_id=req.session_id,
        user_id=user_id,
        initial_message=req.message,
    )

    # 2. Extract conversation history for LLM
    history = session_mgr.get_conversation_history(session) if req.include_history else []

    # 3. Save incoming user message to session
    user_msg = ChatMessage(
        id=generate_message_id(),
        role="user",
        content=req.message,
        timestamp=current_timestamp_ms(),
    )
    session_mgr.save_message(session, user_msg)

    # 4. Handle Server-Sent Events (SSE) Streaming
    if req.stream:
        async def event_generator():
            accumulated_chunks: List[str] = []
            try:
                async for chunk in llm_svc.generate_reply_stream(
                    message=req.message,
                    history=history,
                    user_id=user_id,
                ):
                    accumulated_chunks.append(chunk)
                    yield f"data: {json.dumps({'text': chunk, 'session_id': session.session_id})}\n\n"

                # Once streaming finishes, save complete assistant response
                full_reply = "".join(accumulated_chunks)
                actions = match_suggested_actions(req.message, full_reply)
                assistant_msg = ChatMessage(
                    id=generate_message_id(),
                    role="model",
                    content=full_reply,
                    timestamp=current_timestamp_ms(),
                    actions=actions,
                )
                session_mgr.save_message(session, assistant_msg)

                # Send completion metadata event
                completion_payload = {
                    "done": True,
                    "session_id": session.session_id,
                    "actions": [a.model_dump() for a in actions],
                    "timestamp": current_timestamp_ms(),
                }
                yield f"data: {json.dumps(completion_payload)}\n\n"

            except Exception as exc:
                logger.error("Error in streaming response: %s", exc)
                error_payload = {"error": str(exc), "session_id": session.session_id}
                yield f"data: {json.dumps(error_payload)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # 5. Handle Standard Synchronous Response
    try:
        llm_result = llm_svc.generate_reply(
            message=req.message,
            history=history,
            user_id=user_id,
        )

        reply_text = llm_result["text"]
        actions = llm_result["actions"]

        # Persist assistant message
        assistant_msg = ChatMessage(
            id=generate_message_id(),
            role="model",
            content=reply_text,
            timestamp=current_timestamp_ms(),
            actions=actions,
        )
        session_mgr.save_message(session, assistant_msg)

        return ChatResponse(
            success=True,
            session_id=session.session_id,
            response=reply_text,
            user_id=user_id,
            is_authenticated=is_authenticated,
            actions=actions,
            timestamp=current_timestamp_ms(),
        )

    except Exception as exc:
        logger.error("Failed to generate chat reply: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "generation_failed",
                "message": f"Failed to generate response from Gemini: {str(exc)}",
            },
        )


@chat_router.get(
    "/sessions",
    response_model=List[ChatSessionSummary],
    summary="List user chat sessions",
    description="Retrieves a list of previous chat sessions for an authenticated user.",
)
async def list_sessions_endpoint(
    user_id: Optional[str] = None,
    auth_user_id: Optional[str] = Depends(get_current_user_id),
):
    target_user_id = user_id or auth_user_id
    if not target_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view stored chat sessions.",
        )

    session_mgr = get_session_manager()
    return session_mgr.list_user_sessions(target_user_id)


@chat_router.get(
    "/sessions/{session_id}",
    response_model=ChatSession,
    summary="Get chat session details",
    description="Loads a specific chat session with its full message history.",
)
async def get_session_endpoint(
    session_id: str,
    user_id: Optional[str] = None,
    auth_user_id: Optional[str] = Depends(get_current_user_id),
):
    target_user_id = user_id or auth_user_id
    session_mgr = get_session_manager()
    session = session_mgr.get_or_create_session(
        session_id=session_id,
        user_id=target_user_id,
    )

    if not session.messages and target_user_id:
        # Check if session really existed
        existing = session_mgr.get_or_create_session(session_id, target_user_id)
        if not existing.messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session `{session_id}` not found.",
            )

    return session


@chat_router.delete(
    "/sessions/{session_id}",
    summary="Delete a chat session",
    description="Deletes a chat session and all associated messages.",
)
async def delete_session_endpoint(
    session_id: str,
    user_id: Optional[str] = None,
    auth_user_id: Optional[str] = Depends(get_current_user_id),
):
    target_user_id = user_id or auth_user_id
    session_mgr = get_session_manager()
    deleted = session_mgr.delete_session(session_id, target_user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not delete session `{session_id}`.",
        )
    return {"success": True, "message": f"Session `{session_id}` deleted successfully."}
