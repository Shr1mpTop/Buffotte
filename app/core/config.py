import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


load_dotenv()


def _csv_env(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    cors_origins: list[str] = field(default_factory=lambda: _csv_env(
        "CORS_ORIGINS",
        [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "https://buffotte.hezhili.online",
        ],
    ))
    bufftracker_url: str = os.getenv("BUFFTRACKER_URL", "http://host.docker.internal:8001")


settings = Settings()
