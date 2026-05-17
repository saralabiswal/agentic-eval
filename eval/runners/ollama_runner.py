"""Runner that calls Ollama directly for local inference."""

from __future__ import annotations

from time import perf_counter

import httpx

from eval.core.config import settings
from eval.core.exceptions import RunnerError
from eval.core.schemas import TestCase
from eval.runners.base_runner import RunnerOutput


class OllamaRunner:
    """Call a local Ollama model without requiring an API key."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float = 180.0,
    ) -> None:
        self.model = model or settings.SUT_MODEL
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.timeout_seconds = timeout_seconds

    async def run(self, test_case: TestCase) -> RunnerOutput:
        """Run the test case through Ollama."""

        prompt = self._prompt(test_case)
        start = perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                )
        except httpx.HTTPError as exc:
            raise RunnerError(f"Ollama runner could not reach {self.base_url}.") from exc
        latency_ms = max(1, int((perf_counter() - start) * 1000))
        if response.status_code >= 400:
            raise RunnerError(f"Ollama runner failed with status {response.status_code}")
        payload = response.json()
        return RunnerOutput(
            agent_output=str(payload.get("response", "")),
            latency_ms=latency_ms,
            model_name=self.model,
            raw_response={
                "backend": "ollama",
                "case_id": test_case.case_id,
                "model": self.model,
                "ollama": payload,
            },
        )

    def _prompt(self, test_case: TestCase) -> str:
        return (
            "You are a banking AI risk assessment agent. "
            "Use only the supplied customer profile and policy context. "
            "Do not invent customer attributes, tiers, tenure, discounts, or sentiment. "
            "Return a concise assessment with risk level, key signals, cited policy IDs, "
            "and recommended action. "
            f"Expected action categories may include: {test_case.expected.expected_action_type}. "
            f"Customer Profile: {test_case.input.customer_profile}. "
            f"Policy Context: {test_case.input.retrieved_policy_chunks}. "
            f"Task: {test_case.input.scenario_context}"
        )
