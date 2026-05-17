"""Application settings loaded from environment variables."""

from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for judges, runners, and the API server."""

    EVAL_JUDGE_BACKEND: Literal["mock", "ollama", "api"] = "mock"
    EVAL_JUDGE_MODEL: str = "gpt-4o"

    SUT_BACKEND: Literal["mock", "ollama", "api", "platform"] = "mock"
    SUT_MODEL: str = "llama3.2"

    OLLAMA_BASE_URL: str = "http://localhost:11434"

    OPENAI_API_KEY: SecretStr | None = None

    BANKING_PLATFORM_URL: str = "http://localhost:8000"
    BANKING_PLATFORM_ENABLED: bool = False

    CONSISTENCY_RUNS: int = 5
    FAITHFULNESS_THRESHOLD: float = 0.85
    ANSWER_RELEVANCE_THRESHOLD: float = 0.80
    CONTEXT_PRECISION_THRESHOLD: float = 0.70
    CONSISTENCY_THRESHOLD: float = 0.90

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
