"""Base runner protocol for executing test cases."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel

from eval.core.schemas import TestCase


class RunnerOutput(BaseModel):
    """Raw output returned by a system-under-test runner."""

    agent_output: str
    latency_ms: int
    model_name: str
    raw_response: dict[str, Any]


class BaseRunner(Protocol):
    """Executes a test case and returns the raw agent output string."""

    async def run(self, test_case: TestCase) -> RunnerOutput:
        """Run a test case through the system under test."""

        ...
