import os
from functools import lru_cache
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment and .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Active LLM Provider ('groq' or 'gemini')
    llm_provider: str = Field(default="groq", alias="LLM_PROVIDER")

    # Groq Configuration
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="qwen/qwen3.6-27b", alias="GROQ_MODEL")

    # Gemini Configuration
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    # Firebase Configuration
    firebase_project_id: str = Field(default="cyliumos", alias="FIREBASE_PROJECT_ID")
    firebase_credentials: Optional[str] = Field(default="cyliumos-firebase-adminsdk.json", alias="FIREBASE_CREDENTIALS")
    firebase_service_account_json: Optional[str] = Field(
        default=None, alias="FIREBASE_SERVICE_ACCOUNT_JSON"
    )

    # Server Settings
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8002, alias="PORT")
    debug: bool = Field(default=False, alias="DEBUG")
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")

    # Caching & Session Settings
    rag_cache_ttl_seconds: int = Field(default=120, alias="RAG_CACHE_TTL_SECONDS")
    anonymous_session_ttl_seconds: int = Field(
        default=3600, alias="ANONYMOUS_SESSION_TTL_SECONDS"
    )

    @property
    def resolved_groq_api_key(self) -> Optional[str]:
        return self.groq_api_key or os.getenv("GROQ_API_KEY")

    @property
    def active_model_name(self) -> str:
        if self.llm_provider.lower() == "groq":
            return self.groq_model
        return self.gemini_model

    @property
    def resolved_gemini_api_key(self) -> Optional[str]:
        """
        Returns GEMINI_API_KEY if present, else falls back to GOOGLE_API_KEY.
        """
        return (
            self.gemini_api_key
            or self.google_api_key
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Returns parsed list of CORS origins.
        """
        if not self.cors_origins or self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
