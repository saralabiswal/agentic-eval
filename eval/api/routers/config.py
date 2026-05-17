"""Configuration inspection and connection test API routes."""

from __future__ import annotations

from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from eval.core.config import settings
from eval.core.runtime_config import (
    OLLAMA_JUDGE_MODEL_OPTIONS,
    OLLAMA_SUT_MODEL_OPTIONS,
    OPENAI_MODEL_OPTIONS,
    JudgeBackend,
    RuntimeConfigUpdate,
    SutBackend,
    runtime_config,
)

router = APIRouter(prefix="/config", tags=["config"])


class ConfigResponse(BaseModel):
    """Non-secret effective runtime configuration."""

    eval_judge_backend: JudgeBackend
    eval_judge_model: str
    sut_backend: SutBackend
    sut_model: str
    ollama_base_url: str
    banking_platform_enabled: bool
    banking_platform_url: str
    thresholds: dict[str, float | int]
    has_openai_api_key: bool
    openai_model_options: list[str]
    ollama_judge_model_options: list[str]
    ollama_sut_model_options: list[str]


class ConnectionTestRequest(BaseModel):
    """Connection test request that never echoes secrets."""

    target: Literal["judge", "sut", "ollama", "api", "platform"]
    backend: Literal["mock", "ollama", "api", "platform"] = "mock"
    model: str | None = None
    api_key: str | None = Field(default=None, repr=False)


class ConnectionTestResponse(BaseModel):
    """Safe connection test response."""

    ok: bool
    target: str
    backend: str
    message: str


@router.get("")
async def get_config() -> ConfigResponse:
    """Return effective runtime config without secret values."""

    effective = runtime_config.get()
    return ConfigResponse(
        eval_judge_backend=effective.eval_judge_backend,
        eval_judge_model=effective.eval_judge_model,
        sut_backend=effective.sut_backend,
        sut_model=effective.sut_model,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        banking_platform_enabled=settings.BANKING_PLATFORM_ENABLED,
        banking_platform_url=settings.BANKING_PLATFORM_URL,
        thresholds={
            "faithfulness": settings.FAITHFULNESS_THRESHOLD,
            "answer_relevance": settings.ANSWER_RELEVANCE_THRESHOLD,
            "context_precision": settings.CONTEXT_PRECISION_THRESHOLD,
            "consistency": settings.CONSISTENCY_THRESHOLD,
            "consistency_runs": settings.CONSISTENCY_RUNS,
        },
        has_openai_api_key=settings.OPENAI_API_KEY is not None,
        openai_model_options=OPENAI_MODEL_OPTIONS,
        ollama_judge_model_options=OLLAMA_JUDGE_MODEL_OPTIONS,
        ollama_sut_model_options=OLLAMA_SUT_MODEL_OPTIONS,
    )


@router.post("/runtime")
async def update_runtime_config(update: RuntimeConfigUpdate) -> ConfigResponse:
    """Update non-secret runtime model selection for this API process."""

    try:
        runtime_config.update(update)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await get_config()


@router.post("/test-connection")
async def test_connection(request: ConnectionTestRequest) -> ConnectionTestResponse:
    """Test backend reachability without exposing secrets."""

    if request.backend == "mock":
        return ConnectionTestResponse(
            ok=True,
            target=request.target,
            backend=request.backend,
            message="Mock backend is local and deterministic.",
        )
    if request.backend == "ollama":
        return await _test_http_endpoint(
            target=request.target,
            backend=request.backend,
            url=settings.OLLAMA_BASE_URL,
            success_message="Ollama endpoint is reachable.",
            failure_message="Ollama is not reachable. Start docker compose and pull the model.",
        )
    if request.backend == "platform":
        return await _test_http_endpoint(
            target=request.target,
            backend=request.backend,
            url=settings.BANKING_PLATFORM_URL,
            success_message="Banking platform endpoint is reachable.",
            failure_message="Banking platform is not reachable.",
        )
    has_key = bool(request.api_key or settings.OPENAI_API_KEY is not None)
    model = request.model or runtime_config.get().eval_judge_model
    return ConnectionTestResponse(
        ok=has_key,
        target=request.target,
        backend=request.backend,
        message=(
            f"OpenAI API key is configured for {model}. Secret value was not returned."
            if has_key
            else f"No OpenAI API key configured for {model}."
        ),
    )


async def _test_http_endpoint(
    target: str,
    backend: str,
    url: str,
    success_message: str,
    failure_message: str,
) -> ConnectionTestResponse:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url)
        ok = response.status_code < 500
    except httpx.HTTPError:
        ok = False
    return ConnectionTestResponse(
        ok=ok,
        target=target,
        backend=backend,
        message=success_message if ok else failure_message,
    )
