"""Runner for the optional banking-agentic-ai-platform API."""

from __future__ import annotations

from time import perf_counter
from typing import Any

import httpx

from eval.core.config import settings
from eval.core.exceptions import RunnerError
from eval.core.schemas import TestCase
from eval.runners.base_runner import RunnerOutput


class PlatformRunner:
    """Call banking-agentic-ai-platform when explicitly enabled."""

    def __init__(self, base_url: str | None = None, timeout_seconds: float = 30.0) -> None:
        self.base_url = base_url or settings.BANKING_PLATFORM_URL
        self.timeout_seconds = timeout_seconds

    async def run(self, test_case: TestCase) -> RunnerOutput:
        """Run the test case through the external banking platform."""

        if not settings.BANKING_PLATFORM_ENABLED:
            raise RunnerError("Banking platform runner is disabled.")

        start = perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/pipeline/run",
                json={
                    "customer_id": test_case.customer_id,
                    "scenario": test_case.scenario,
                    "blueprint": test_case.scenario.upper(),
                },
            )
        latency_ms = max(1, int((perf_counter() - start) * 1000))
        if response.status_code >= 400:
            raise RunnerError(f"Platform runner failed with status {response.status_code}")
        payload: dict[str, Any] = response.json()
        output = payload.get("agent_output") or payload.get("response") or payload
        return RunnerOutput(
            agent_output=str(output),
            latency_ms=latency_ms,
            model_name="banking-platform",
            raw_response=payload,
        )
