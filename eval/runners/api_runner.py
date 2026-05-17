"""Runner that calls a cloud LLM through LiteLLM."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from eval.core.config import settings
from eval.core.exceptions import RunnerError
from eval.core.schemas import TestCase
from eval.runners.base_runner import RunnerOutput


class ApiRunner:
    """Call a configured API LLM through LiteLLM."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.SUT_MODEL

    async def run(self, test_case: TestCase) -> RunnerOutput:
        """Run the test case through LiteLLM."""

        try:
            from litellm import acompletion
        except ImportError as exc:  # pragma: no cover
            raise RunnerError("LiteLLM is not installed.") from exc

        start = perf_counter()
        try:
            response: Any = await acompletion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a banking AI risk assessment agent.",
                    },
                    {"role": "user", "content": self._prompt(test_case)},
                ],
                temperature=0,
            )
        except Exception as exc:
            raise RunnerError("API runner failed to produce a response.") from exc
        latency_ms = max(1, int((perf_counter() - start) * 1000))
        content = response.choices[0].message.content
        if content is None:
            raise RunnerError("API runner returned empty content.")
        return RunnerOutput(
            agent_output=str(content),
            latency_ms=latency_ms,
            model_name=self.model,
            raw_response={"model": self.model, "case_id": test_case.case_id},
        )

    def _prompt(self, test_case: TestCase) -> str:
        return (
            f"Customer Profile: {test_case.input.customer_profile}\n"
            f"Policy Context: {test_case.input.retrieved_policy_chunks}\n"
            f"Task: {test_case.input.scenario_context}"
        )
