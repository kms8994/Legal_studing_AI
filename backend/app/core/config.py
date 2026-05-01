import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv is not None:
    project_root = Path(__file__).resolve().parents[3]
    load_dotenv(project_root / ".env")


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    return value if value else None


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    app_name: str = os.getenv("APP_NAME", "Case AI Learning Service")
    backend_cors_origins: str = os.getenv(
        "BACKEND_CORS_ORIGINS",
        "http://localhost:3000",
    )

    supabase_url: str | None = _optional_env("SUPABASE_URL")
    supabase_anon_key: str | None = _optional_env("SUPABASE_ANON_KEY")
    supabase_service_role_key: str | None = _optional_env("SUPABASE_SERVICE_ROLE_KEY")

    gemini_api_key: str | None = _optional_env("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

    lawinfo_api_key: str | None = _optional_env("LAWINFO_API_KEY")
    lawinfo_base_url: str = os.getenv("LAWINFO_BASE_URL", "http://www.law.go.kr/DRF")

    vector_top_k: int = int(os.getenv("VECTOR_TOP_K", "5"))
    retrieval_score_threshold: float = float(
        os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.72"),
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
