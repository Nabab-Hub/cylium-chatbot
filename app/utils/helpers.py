import hashlib
import time
import uuid
import re
from typing import List
from app.models.schemas import ActionItem


def hash_api_key(api_key: str) -> str:
    """Computes SHA-256 hex digest of an API key."""
    return hashlib.sha256(api_key.strip().encode("utf-8")).hexdigest()


def current_timestamp_ms() -> int:
    """Returns current system timestamp in milliseconds."""
    return int(time.time() * 1000)



def generate_session_id() -> str:
    """Generates a unique session identifier."""
    return f"cs_{uuid.uuid4().hex[:16]}"


def generate_message_id() -> str:
    """Generates a unique message identifier."""
    return f"msg_{uuid.uuid4().hex[:16]}"


def summarize_session_title(first_message: str) -> str:
    """
    Creates a concise session title from the user's first query.
    """
    cleaned = re.sub(r"[^\w\s-]", "", first_message).strip()
    words = cleaned.split()
    if not words:
        return "New Conversation"
    if len(words) <= 6:
        return " ".join(words)
    return " ".join(words[:6]) + "..."


def match_suggested_actions(query: str, response_text: str) -> List[ActionItem]:
    """
    Dynamically infers and suggests the most relevant quick action buttons
    based on both the user's inquiry and the generated response content.
    """
    combined = f"{query} {response_text}".lower()
    actions: List[ActionItem] = []

    # Service exploration
    if any(k in combined for k in ["service", "nsfw", "enhancer", "moderation", "vision", "catalog"]):
        actions.append(ActionItem(label="Explore All Services", to="/services"))

    # Pricing & Subscription plans
    if any(k in combined for k in ["price", "pricing", "plan", "cost", "subscription", "upgrade", "billing", "free tier"]):
        actions.append(ActionItem(label="View Pricing & Plans", to="/pricing"))

    # Playground & Testing
    if any(k in combined for k in ["test", "try", "playground", "demo", "upload image", "sample"]):
        actions.append(ActionItem(label="Open Web Playground", to="/playground"))

    # Documentation & SDKs
    if any(k in combined for k in ["doc", "docs", "documentation", "api", "curl", "sdk", "python", "typescript", "integrate"]):
        actions.append(ActionItem(label="Developer Documentation", to="/docs"))

    # API Keys & Dashboard
    if any(k in combined for k in ["key", "api key", "dashboard", "token", "quota", "usage", "limit"]):
        actions.append(ActionItem(label="Manage API Keys", to="/dashboard"))

    # Refund policy
    if any(k in combined for k in ["refund", "money back", "cancel plan", "return"]):
        actions.append(ActionItem(label="Refund Policy", to="/refund-policy"))

    # Contact & Support
    if any(k in combined for k in ["support", "contact", "help", "email", "enterprise sales", "talk to human"]):
        actions.append(ActionItem(label="Contact Support", to="/contact"))

    # Default fallback if no specific keywords matched
    if not actions:
        actions = [
            ActionItem(label="Explore Services", to="/services"),
            ActionItem(label="Check Pricing", to="/pricing"),
            ActionItem(label="Read Docs", to="/docs"),
        ]

    # Limit to top 4 unique actions
    seen_destinations = set()
    unique_actions: List[ActionItem] = []
    for act in actions:
        dest = act.to or act.href or act.query
        if dest not in seen_destinations:
            seen_destinations.add(dest)
            unique_actions.append(act)
        if len(unique_actions) >= 4:
            break

    return unique_actions
