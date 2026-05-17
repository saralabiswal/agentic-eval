"""Runtime configuration overlay for local API-driven settings."""

from __future__ import annotations

from threading import Lock
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from eval.core.config import settings

JudgeBackend = Literal["mock", "ollama", "api"]
SutBackend = Literal["mock", "ollama", "api", "platform"]

OPENAI_MODEL_OPTIONS = ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"]
OLLAMA_JUDGE_MODEL_OPTIONS = ["qwen2.5:7b", "mistral-nemo:12b", "llama3.2"]
OLLAMA_SUT_MODEL_OPTIONS = ["llama3.2", "mistral", "phi3.5"]


class RuntimeConfig(BaseModel):
    """Effective non-secret model backend configuration for this process."""

    eval_judge_backend: JudgeBackend = settings.EVAL_JUDGE_BACKEND
    eval_judge_model: str = settings.EVAL_JUDGE_MODEL
    sut_backend: SutBackend = settings.SUT_BACKEND
    sut_model: str = settings.SUT_MODEL

    @model_validator(mode="after")
    def validate_models(self) -> RuntimeConfig:
        """Validate backend/model combinations that must be strict."""

        if self.eval_judge_backend == "api" and self.eval_judge_model not in OPENAI_MODEL_OPTIONS:
            msg = f"API judge model must be one of: {', '.join(OPENAI_MODEL_OPTIONS)}."
            raise ValueError(msg)
        if self.sut_backend == "api" and self.sut_model not in OPENAI_MODEL_OPTIONS:
            msg = f"API SUT model must be one of: {', '.join(OPENAI_MODEL_OPTIONS)}."
            raise ValueError(msg)
        if (
            self.eval_judge_backend == "ollama"
            and self.eval_judge_model not in OLLAMA_JUDGE_MODEL_OPTIONS
        ):
            msg = f"Ollama judge model must be one of: {', '.join(OLLAMA_JUDGE_MODEL_OPTIONS)}."
            raise ValueError(msg)
        if self.sut_backend == "ollama" and self.sut_model not in OLLAMA_SUT_MODEL_OPTIONS:
            msg = f"Ollama SUT model must be one of: {', '.join(OLLAMA_SUT_MODEL_OPTIONS)}."
            raise ValueError(msg)
        return self


class RuntimeConfigUpdate(BaseModel):
    """Partial runtime configuration update from the Settings UI."""

    eval_judge_backend: JudgeBackend | None = None
    eval_judge_model: str | None = Field(default=None, min_length=1)
    sut_backend: SutBackend | None = None
    sut_model: str | None = Field(default=None, min_length=1)


class RuntimeConfigStore:
    """Thread-safe in-memory runtime config store."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._config = RuntimeConfig()

    def get(self) -> RuntimeConfig:
        """Return the current runtime config."""

        with self._lock:
            return self._config.model_copy()

    def update(self, update: RuntimeConfigUpdate) -> RuntimeConfig:
        """Apply a partial update and return the effective config."""

        with self._lock:
            next_config = self._config.model_copy(update=update.model_dump(exclude_none=True))
            self._config = RuntimeConfig.model_validate(next_config.model_dump())
            return self._config.model_copy()

    def reset(self) -> RuntimeConfig:
        """Reset runtime config to environment-backed defaults."""

        with self._lock:
            self._config = RuntimeConfig()
            return self._config.model_copy()


runtime_config = RuntimeConfigStore()
