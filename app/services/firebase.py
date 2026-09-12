import os
import json
import logging
from typing import Optional, List, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore
from app.core.config import get_settings
from app.models.schemas import ChatMessage, ChatSession, ChatSessionSummary
from app.utils.helpers import current_timestamp_ms

logger = logging.getLogger("chatbot.firebase")

_firestore_client: Optional[firestore.Client] = None
_firebase_initialized: bool = False


def init_firebase() -> Optional[firestore.Client]:
    """
    Initializes Firebase Admin SDK and returns the Firestore client.
    Supports file path credentials, raw JSON string credentials, or project ID fallback.
    """
    global _firestore_client, _firebase_initialized

    if _firestore_client is not None:
        return _firestore_client

    settings = get_settings()

    # 1. Try raw JSON string credentials
    if settings.firebase_service_account_json:
        try:
            cert_dict = json.loads(settings.firebase_service_account_json)
            cred = credentials.Certificate(cert_dict)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            _firestore_client = firestore.client()
            logger.info("Firebase initialized successfully using inline service account JSON.")
            return _firestore_client
        except Exception as exc:
            logger.warning("Failed to initialize Firebase from inline JSON: %s", exc)

    # 2. Try file path credentials
    candidate_paths = [
        settings.firebase_credentials,
        os.getenv("FIREBASE_CREDENTIALS"),
        "cyliumos-firebase-adminsdk.json",
        os.path.join(os.path.dirname(__file__), "..", "..", "cyliumos-firebase-adminsdk.json"),
        os.path.join(os.getcwd(), "cyliumos-firebase-adminsdk.json"),
        "/etc/secrets/firebase-service-account.json",
        "firebase-service-account.json",
        "nude-checker-firebase-adminsdk.json",
        os.path.join(os.getcwd(), "firebase-service-account.json"),
        os.path.join(os.getcwd(), "..", "..", "firebase-service-account.json"),
        os.path.join(os.getcwd(), "..", "..", "cyliumos-firebase-adminsdk.json"),
    ]

    for path in candidate_paths:
        if path and os.path.exists(path):
            try:
                cred = credentials.Certificate(path)
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred)
                _firebase_initialized = True
                _firestore_client = firestore.client()
                logger.info("Firebase initialized successfully from certificate: %s", path)
                return _firestore_client
            except Exception as exc:
                logger.warning("Failed to initialize Firebase from certificate %s: %s", path, exc)

    # 3. Fallback: Only initialize with project ID if GOOGLE_APPLICATION_CREDENTIALS is set
    # to avoid 12-second metadata server network timeouts on local environments
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            project_id = settings.firebase_project_id
            if not firebase_admin._apps:
                firebase_admin.initialize_app(options={"projectId": project_id})
            _firebase_initialized = True
            _firestore_client = firestore.client()
            logger.info("Firebase initialized with project ID and ADC: %s", project_id)
            return _firestore_client
        except Exception as exc:
            logger.warning("Could not initialize Firebase client via ADC: %s", exc)

    logger.info(
        "No Firebase service account file provided. Operating in fast local RAG mode with cached knowledge."
    )
    _firebase_initialized = False
    return None


def get_firestore_client() -> Optional[firestore.Client]:
    """Retrieves the active Firestore client singleton."""
    return init_firebase()


def is_firebase_connected() -> bool:
    """Checks whether Firestore client is available."""
    try:
        db = get_firestore_client()
        return db is not None
    except Exception:
        return False


# ============================================================
# Platform Data Retrieval (RAG)
# ============================================================

def fetch_active_services() -> List[Dict[str, Any]]:
    """
    Fetches active services from the Firestore `services` collection.
    """
    db = get_firestore_client()
    if db is None:
        return []

    try:
        services_ref = db.collection("services").where("status", "==", "active").stream()
        results: List[Dict[str, Any]] = []
        for doc in services_ref:
            data = doc.to_dict() or {}
            data["id"] = doc.id
            results.append(data)
        return results
    except Exception as exc:
        logger.warning("Error fetching active services from Firestore: %s", exc)
        return []


def fetch_active_plans() -> List[Dict[str, Any]]:
    """
    Fetches active plans from the Firestore `plans` collection.
    """
    db = get_firestore_client()
    if db is None:
        return []

    try:
        plans_ref = db.collection("plans").where("isActive", "==", True).stream()
        results: List[Dict[str, Any]] = []
        for doc in plans_ref:
            data = doc.to_dict() or {}
            data["id"] = doc.id
            results.append(data)
        return results
    except Exception as exc:
        logger.warning("Error fetching active plans from Firestore: %s", exc)
        return []


def fetch_user_context(user_id: str) -> Dict[str, Any]:
    """
    Fetches real-time profile, subscriptions, API keys, and usage statistics
    for a logged-in user from Firestore.
    """
    db = get_firestore_client()
    if db is None or not user_id:
        return {}

    user_info: Dict[str, Any] = {"userId": user_id}

    try:
        # 1. User profile
        user_doc = db.collection("users").document(user_id).get()
        if user_doc.exists:
            data = user_doc.to_dict() or {}
            user_info["displayName"] = data.get("displayName", "")
            user_info["email"] = data.get("email", "")
            user_info["role"] = data.get("role", "user")

        # 2. Subscriptions
        subs_ref = db.collection("subscriptions").where("userId", "==", user_id).stream()
        subscriptions: List[Dict[str, Any]] = []
        for s in subs_ref:
            s_data = s.to_dict() or {}
            subscriptions.append({
                "serviceId": s_data.get("serviceId", "all"),
                "planId": s_data.get("planId", ""),
                "status": s_data.get("status", "active"),
                "currentPeriodEnd": s_data.get("currentPeriodEnd", 0),
            })
        user_info["subscriptions"] = subscriptions

        # 3. API Keys (safe summary: no plaintext keys exposed)
        keys_ref = db.collection("apiKeys").where("userId", "==", user_id).stream()
        keys: List[Dict[str, Any]] = []
        for k in keys_ref:
            k_data = k.to_dict() or {}
            keys.append({
                "keyPrefix": k_data.get("keyPrefix", ""),
                "environment": k_data.get("environment", "production"),
                "status": k_data.get("status", "active"),
                "monthlyLimit": k_data.get("monthlyLimit", 0),
                "requestCount": k_data.get("requestCount", 0),
            })
        user_info["apiKeys"] = keys

        # 4. Usage counters
        counters_ref = db.collection("usageCounters").where("userId", "==", user_id).stream()
        counters: List[Dict[str, Any]] = []
        for c in counters_ref:
            c_data = c.to_dict() or {}
            counters.append({
                "serviceId": c_data.get("serviceId", ""),
                "requestCount": c_data.get("requestCount", 0),
                "monthlyLimit": c_data.get("monthlyLimit", 0),
            })
        user_info["usageCounters"] = counters

    except Exception as exc:
        logger.warning("Error fetching user account context for user %s: %s", user_id, exc)

    return user_info


# ============================================================
# Chat Session & Message Persistence (FOR LOGGED-IN USERS ONLY)
# ============================================================

def save_chat_session(session: ChatSession) -> bool:
    """
    Saves or updates a chat session in Firestore under `chatSessions`.
    CRITICAL: Only called for logged-in users!
    """
    db = get_firestore_client()
    if db is None or not session.user_id:
        return False

    try:
        session_ref = db.collection("chatSessions").document(session.session_id)
        session_ref.set({
            "sessionId": session.session_id,
            "userId": session.user_id,
            "title": session.title,
            "messageCount": len(session.messages),
            "createdAt": session.created_at,
            "updatedAt": current_timestamp_ms(),
        }, merge=True)

        # Write messages to subcollection `messages`
        batch = db.batch()
        messages_coll = session_ref.collection("messages")
        for idx, msg in enumerate(session.messages):
            msg_doc_id = msg.id or f"msg_{idx:04d}"
            msg_ref = messages_coll.document(msg_doc_id)
            actions_dicts = [a.model_dump() for a in msg.actions] if msg.actions else []
            batch.set(msg_ref, {
                "id": msg_doc_id,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "actions": actions_dicts,
                "metadata": msg.metadata or {},
            }, merge=True)

        batch.commit()
        return True
    except Exception as exc:
        logger.error("Error saving chat session to Firestore: %s", exc)
        return False


def load_chat_session(session_id: str, user_id: str) -> Optional[ChatSession]:
    """
    Loads a chat session and its full message history from Firestore.
    Ensures user ownership.
    """
    db = get_firestore_client()
    if db is None or not user_id:
        return None

    try:
        session_ref = db.collection("chatSessions").document(session_id)
        doc = session_ref.get()
        if not doc.exists:
            return None

        data = doc.to_dict() or {}
        # Security check: verify session belongs to user
        if data.get("userId") != user_id:
            logger.warning("Unauthorized attempt to access session %s by user %s", session_id, user_id)
            return None

        # Fetch messages in chronological order
        msgs_stream = session_ref.collection("messages").order_by("timestamp").stream()
        messages: List[ChatMessage] = []
        for m in msgs_stream:
            m_data = m.to_dict() or {}
            messages.append(ChatMessage(
                id=m_data.get("id"),
                role=m_data.get("role", "user"),
                content=m_data.get("content", ""),
                timestamp=m_data.get("timestamp", current_timestamp_ms()),
                actions=m_data.get("actions"),
                metadata=m_data.get("metadata"),
            ))

        return ChatSession(
            session_id=session_id,
            user_id=user_id,
            title=data.get("title", "Conversation"),
            messages=messages,
            created_at=data.get("createdAt", current_timestamp_ms()),
            updated_at=data.get("updatedAt", current_timestamp_ms()),
        )
    except Exception as exc:
        logger.error("Error loading chat session from Firestore: %s", exc)
        return None


def list_user_sessions(user_id: str, limit: int = 20) -> List[ChatSessionSummary]:
    """
    Lists recent chat sessions for a logged-in user.
    """
    db = get_firestore_client()
    if db is None or not user_id:
        return []

    try:
        sessions_query = (
            db.collection("chatSessions")
            .where("userId", "==", user_id)
            .order_by("updatedAt", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        results: List[ChatSessionSummary] = []
        for s in sessions_query:
            s_data = s.to_dict() or {}
            results.append(ChatSessionSummary(
                session_id=s_data.get("sessionId", s.id),
                user_id=user_id,
                title=s_data.get("title", "Conversation"),
                message_count=s_data.get("messageCount", 0),
                created_at=s_data.get("createdAt", 0),
                updated_at=s_data.get("updatedAt", 0),
            ))
        return results
    except Exception as exc:
        logger.warning("Error listing user chat sessions: %s", exc)
        return []


def delete_user_session(session_id: str, user_id: str) -> bool:
    """
    Deletes a user's chat session and all its messages.
    """
    db = get_firestore_client()
    if db is None or not user_id:
        return False

    try:
        session_ref = db.collection("chatSessions").document(session_id)
        doc = session_ref.get()
        if not doc.exists or doc.to_dict().get("userId") != user_id:
            return False

        # Delete subcollection messages
        for m in session_ref.collection("messages").stream():
            m.reference.delete()

        session_ref.delete()
        return True
    except Exception as exc:
        logger.error("Error deleting session %s: %s", session_id, exc)
        return False
