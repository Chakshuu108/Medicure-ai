from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"

# asyncpg rejects sslmode / channel_binding in the URL query string
_ASYNC_STRIP_QUERY = frozenset({"sslmode", "channel_binding"})


def _clean_db_url(url: str, *, async_driver: bool) -> str:
    """Normalize Neon/Render connection strings for SQLAlchemy."""
    u = (url or "").strip().strip('"').strip("'")
    if not u:
        raise ValueError("DATABASE_URL is empty — set it in Render Environment variables")
    if u.startswith("postgres://"):
        u = "postgresql://" + u[len("postgres://") :]
    if async_driver:
        if u.startswith("postgresql://") and "+asyncpg" not in u:
            u = u.replace("postgresql://", "postgresql+asyncpg://", 1)
        parsed = urlparse(u)
        if parsed.query:
            kept = [(k, v) for k, v in parse_qsl(parsed.query) if k.lower() not in _ASYNC_STRIP_QUERY]
            u = urlunparse(parsed._replace(query=urlencode(kept)))
    else:
        u = u.replace("postgresql+asyncpg://", "postgresql://", 1)
    return u


def database_ssl_required(url: str) -> bool:
    """Neon and other cloud Postgres hosts need SSL for asyncpg."""
    host = (urlparse(url).hostname or "").lower()
    return host.endswith(".neon.tech") or "sslmode=require" in url.lower()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://medicure:medicure_secret@localhost:5432/medicure"
    database_url_sync: str = "postgresql://medicure:medicure_secret@localhost:5432/medicure"

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_async_url(cls, v: str) -> str:
        return _clean_db_url(v, async_driver=True)

    @field_validator("database_url_sync", mode="before")
    @classmethod
    def normalize_sync_url(cls, v: str) -> str:
        return _clean_db_url(v, async_driver=False)
    secret_key: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 1440
    algorithm: str = "HS256"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    frontend_url: str = "http://localhost:5173"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "MediCure AI"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:5173/auth/google/callback"
    max_chat_history: int = 20
    log_level: str = "INFO"
    # Proactive Health Guardian (background scans while patients are offline)
    guardian_proactive_enabled: bool = True
    guardian_scan_interval_hours: float = 24.0
    guardian_startup_delay_seconds: int = 60
    guardian_silence_alert_days: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    """Clear cached settings — call after .env changes."""
    get_settings.cache_clear()
    return get_settings()


def is_groq_configured() -> bool:
    key = get_settings().groq_api_key.strip()
    return bool(key) and key not in ("", "your_groq_api_key_here", "your-groq-api-key")
