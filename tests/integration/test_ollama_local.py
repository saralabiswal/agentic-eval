"""Optional local Ollama integration checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest

from eval.benchmark import BenchmarkEngine
from eval.core.config import settings
from eval.core.runtime_config import RuntimeConfigUpdate, runtime_config

REQUIRED_MODELS = {"llama3.2", "qwen2.5:7b"}


async def _available_models() -> set[str]:
    async with httpx.AsyncClient(timeout=1.0) as client:
        try:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
        except httpx.HTTPError:
            pytest.skip("Ollama is not reachable. Run: make docker-up")
    if response.status_code >= 400:
        pytest.skip(f"Ollama /api/tags returned status {response.status_code}.")
    payload = response.json()
    models = payload.get("models", [])
    return {_model_name(model) for model in models if isinstance(model, dict)}


def _model_name(model: dict[str, Any]) -> str:
    return str(model.get("name", "")).split(":latest", 1)[0]


@pytest.mark.asyncio
async def test_local_two_model_ollama_smoke(tmp_path: Path) -> None:
    models = await _available_models()
    missing = sorted(REQUIRED_MODELS - models)
    if missing:
        pytest.skip(
            "Missing Ollama models: "
            + ", ".join(missing)
            + ". Run: ollama pull llama3.2 && ollama pull qwen2.5:7b"
        )

    runtime_config.update(
        RuntimeConfigUpdate(
            eval_judge_backend="ollama",
            eval_judge_model="qwen2.5:7b",
            sut_backend="ollama",
            sut_model="llama3.2",
        )
    )
    try:
        report = await BenchmarkEngine(reports_dir=tmp_path).run(cases=["PR-003"])
    finally:
        runtime_config.reset()

    assert report.model_backend == "ollama"
    assert report.total_cases == 1
