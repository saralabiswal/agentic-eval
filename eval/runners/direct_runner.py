"""Standalone direct runner that works without the banking platform."""

from __future__ import annotations

from eval.core.config import settings
from eval.core.exceptions import RunnerError
from eval.core.schemas import TestCase
from eval.runners.base_runner import RunnerOutput
from eval.runners.mock_runner import MockRunner


class DirectRunner:
    """Run evaluation directly from test case context using configured backend."""

    def __init__(self, backend: str | None = None) -> None:
        self.backend = backend or settings.SUT_BACKEND
        self._mock = MockRunner()

    async def run(self, test_case: TestCase) -> RunnerOutput:
        """Run a test case without requiring the banking platform."""

        if self.backend == "mock":
            return await self._mock.run(test_case)
        raise RunnerError(
            "DirectRunner only supports the mock fixture backend. "
            "Use OllamaRunner or ApiRunner for real non-mock SUT execution."
        )
