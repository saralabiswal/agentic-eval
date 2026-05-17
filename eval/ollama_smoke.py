"""Local Ollama smoke check for no-key benchmark execution."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import httpx
from rich.console import Console

from eval.benchmark import BenchmarkEngine
from eval.core.config import settings
from eval.core.runtime_config import RuntimeConfigUpdate, runtime_config

REQUIRED_MODELS = {"llama3.2", "qwen2.5:7b"}


async def main() -> None:
    """Run the Ollama endpoint/model checks and one benchmark case."""

    console = Console()
    models = await _available_models()
    missing = sorted(model for model in REQUIRED_MODELS if model not in models)
    if missing:
        console.print(
            "[red]Missing Ollama models:[/red] "
            + ", ".join(missing)
            + "\nRun: ollama pull llama3.2 && ollama pull qwen2.5:7b"
        )
        raise SystemExit(1)

    runtime_config.update(
        RuntimeConfigUpdate(
            eval_judge_backend="ollama",
            eval_judge_model="qwen2.5:7b",
            sut_backend="ollama",
            sut_model="llama3.2",
        )
    )
    report = await BenchmarkEngine(reports_dir=Path("reports")).run(cases=["PR-003"])
    console.print(
        "[green]Ollama smoke passed[/green] "
        f"{report.results[0].case_id} backend={report.model_backend} "
        f"score={report.results[0].overall_score:.2f}"
    )


async def _available_models() -> set[str]:
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
        except httpx.HTTPError as exc:
            msg = (
                f"Ollama is not reachable at {settings.OLLAMA_BASE_URL}. "
                "Run: make docker-up"
            )
            raise SystemExit(msg) from exc
    if response.status_code >= 400:
        msg = f"Ollama returned status {response.status_code} from /api/tags."
        raise SystemExit(msg)
    payload = response.json()
    models = payload.get("models", [])
    return {_model_name(model) for model in models if isinstance(model, dict)}


def _model_name(model: dict[str, Any]) -> str:
    name = str(model.get("name", ""))
    return name.split(":latest", 1)[0]


if __name__ == "__main__":
    asyncio.run(main())
