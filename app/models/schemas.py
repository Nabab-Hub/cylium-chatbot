from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    """Suggested quick action or navigation link for the UI."""
    label: str = Field(..., description="Action button display label")
    to: Optional[str] = Field(None, description="Internal router route path, e.g. /services/nsfw-detection")
    href: Optional[str] = Field(None, description="External URL if applicable")
    query: Optional[str] = Field(None, description="Pre-filled prompt query to submit next")


class ChatMessage(BaseModel):
    """A single chat message in a conversation session."""
    id: Optional[str] = Field(None, description="Message unique ID")
    role: Literal["user", "model", "assistant", "system"] = Field(
        ..., description="Role of the message sender"
    )
    content: str = Field(..., description="Text content of the message")
    timestamp: int = Field(..., description="Timestamp in milliseconds")
    actions: Optional[List[ActionItem]] = Field(
        default=None, description="Interactive suggested actions accompanying the assistant message"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional contextual metadata"
    )


class ChatRequest(BaseModel):
    """Incoming user chat request."""
    message: str = Field(..., min_length=1, max_length=10000, description="User input message or question")
    session_id: Optional[str] = Field(
        None, description="Session ID. If omitted, a new session is created."
    )
    user_id: Optional[str] = Field(
        None, description="Logged in user ID. If provided, history is loaded and persisted in Firebase."
    )
    stream: bool = Field(
        default=False, description="Enable Server-Sent Events (SSE) streaming for real-time tokens."
    )
    include_history: bool = Field(
        default=True, description="Whether to include previous conversation turns as context."
    )


class ChatResponse(BaseModel):
    """Chatbot response message."""
    success: bool = Field(default=True)
    session_id: str = Field(..., description="Active session ID")
    response: str = Field(..., description="Assistant response text (Markdown supported)")
    user_id: Optional[str] = Field(None, description="User ID if authenticated")
    is_authenticated: bool = Field(
        default=False, description="True if user was recognized as logged-in and session stored in Firebase"
    )
    actions: Optional[List[ActionItem]] = Field(
        default_factory=list, description="Interactive quick action buttons for the frontend"
    )
    timestamp: int = Field(..., description="Response generation timestamp in milliseconds")


class ChatSessionSummary(BaseModel):
    """Summary of a chat session for listing past conversations."""
    session_id: str
    user_id: Optional[str] = None
    title: str
    message_count: int = 0
    created_at: int
    updated_at: int


class ChatSession(BaseModel):
    """Full chat session details with message history."""
    session_id: str
    user_id: Optional[str] = None
    title: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: int
    updated_at: int


class HealthResponse(BaseModel):
    """Service health and diagnostics response."""
    status: str
    service: str
    version: str
    llm_provider: str
    model: str
    llm_ready: bool
    firebase_connected: bool
    timestamp: int
