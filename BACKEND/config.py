"""
BACKEND/config.py
Centralised configuration via Pydantic Settings (reads from .env)
"""
from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_name:    str = "ProofSAR AI"
    app_version: str = "1.0.0"
    app_env:     str = "development"
    app_host:    str = "0.0.0.0"
    app_port:    int = 8000

    # JWT
    jwt_secret:       str = "proofsar_super_secret_jwt_key_change_in_production_2026"
    jwt_algorithm:    str = "HS256"
    jwt_expiry_hours: int = 24

    # Email
    email_user: str = ""
    email_pass: str = ""

    # AI
    gemini_api_key: str = ""

    # URLs
    backend_url: str = "http://localhost:8000"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def allow_origins(self) -> list[str]:
        if self.is_production:
            return ["https://proofsar.streamlit.app"]
        return ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
