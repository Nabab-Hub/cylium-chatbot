import time
import logging
from typing import Optional, List, Dict, Tuple
from app.models.schemas import ChatMessage, ChatSession, ChatSessionSummary
from app.utils.helpers import (
    current_timestamp_ms,
    generate_session_id,
    summarize_session_title,
)
from app.services import firebase as fb_service
from app.core.config import get_settings

logger = logging.getLogger("chatbot.session_manager")


class SessionManager:
    """
    Hybrid Session Manager:
    1. Authenticated / Logged-in Users:
       - Every new session is tracked in Cloud Firestore (`chatSessions`).
       - Full message history is persisted to Cloud Firestore.
       - Restores previous session history across requests to provide continuous context.
    2. Anonymous / Non-Logged-in Users:
       - Session history is kept in memory ONLY for the duration of the conversation.
       - CRITICAL: Anonymous chat history is NEVER stored in Firebase.
       - Periodically sweeps expired sessions based on ANONYMOUS_SESSION_TTL_SECONDS.
    """

    def __init__(self):
        # Store for anonymous sessions: session_id -> (ChatSession, last_accessed_timestamp)
        self._anonymous_sessions: Dict[str, Tuple[ChatSession, float]] = {}
        self._last_cleanup: float = time.time()

    def _sweep_anonymous_cache(self) -> None:
        """Removes expired anonymous sessions to prevent memory bloat."""
        now = time.time()
        ttl = get_settings().anonymous_session_ttl_seconds
        # Run sweep at most once every 5 minutes
        if now - self._last_cleanup < 300:
            return

        self._last_cleanup = now
        expired_ids = [
            sid
            for sid, (_, last_seen) in self._anonymous_sessions.items()
            if now - last_seen > ttl
        ]
        for sid in expired_ids:
            self._anonymous_sessions.pop(sid, None)

        if expired_ids:
            logger.info("Swept %d expired anonymous chat sessions.", len(expired_ids))

    def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        initial_message: Optional[str] = None,
    ) -> ChatSession:
        """
        Retrieves an existing session or initializes a new one.
        """
        self._sweep_anonymous_cache()
        now_ms = current_timestamp_ms()

        # -------------------------------------------------------------
        # Case A: Authenticated / Logged-in User
        # -------------------------------------------------------------
        if user_id:
            if session_id:
                existing_session = fb_service.load_chat_session(session_id, user_id)
                if existing_session is not None:
                    return existing_session

            # Create new persistent session in Firebase
            new_id = session_id or generate_session_id()
            title = summarize_session_title(initial_message) if initial_message else "New Session"
            new_session = ChatSession(
                session_id=new_id,
                user_id=user_id,
                title=title,
                messages=[],
                created_at=now_ms,
                updated_at=now_ms,
            )
            # Store initial session metadata in Firebase
            fb_service.save_chat_session(new_session)
            return new_session

        # -------------------------------------------------------------
        # Case B: Anonymous / Non-Logged-in User (In-Memory ONLY)
        # -------------------------------------------------------------
        if session_id and session_id in self._anonymous_sessions:
            session, _ = self._anonymous_sessions[session_id]
            self._anonymous_sessions[session_id] = (session, time.time())
            return session

        new_id = session_id or generate_session_id()
        title = summarize_session_title(initial_message) if initial_message else "Guest Conversation"
        new_session = ChatSession(
            session_id=new_id,
            user_id=None,
            title=title,
            messages=[],
            created_at=now_ms,
            updated_at=now_ms,
        )
        self._anonymous_sessions[new_id] = (new_session, time.time())
        return new_session

    def save_message(
        self,
        session: ChatSession,
        message: ChatMessage,
    ) -> None:
        """
        Appends a message to the session and synchronizes state:
        - If logged-in user: writes update to Firebase.
        - If anonymous user: updates local in-memory session only.
        """
        session.messages.append(message)
        session.updated_at = current_timestamp_ms()

        if session.user_id:
            # Persist to Firebase for authenticated users
            fb_service.save_chat_session(session)
        else:
            # Keep in-memory for anonymous users
            self._anonymous_sessions[session.session_id] = (session, time.time())

    def get_conversation_history(
        self, session: ChatSession, max_turns: int = 12
    ) -> List[ChatMessage]:
        """
        Extracts recent conversation turns suitable for LLM context.
        """
        if not session.messages:
            return []
        # Return last N messages (e.g. 6 user + 6 assistant turns)
        return session.messages[-max_turns:]

    def list_user_sessions(self, user_id: str) -> List[ChatSessionSummary]:
        """Lists saved sessions for a logged-in user."""
        return fb_service.list_user_sessions(user_id)

    def delete_session(self, session_id: str, user_id: Optional[str]) -> bool:
        """Deletes a session."""
        if user_id:
            return fb_service.delete_user_session(session_id, user_id)
        if session_id in self._anonymous_sessions:
            self._anonymous_sessions.pop(session_id, None)
            return True
        return False


# Singleton instance
_session_manager_instance: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = SessionManager()
    return _session_manager_instance
