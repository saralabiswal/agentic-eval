"""Integration tests for runner implementations."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from eval.core.config import settings
from eval.core.exceptions import RunnerError
from eval.core.schemas import TestCase as EvalTestCase
from eval.core.schemas import TestCaseExpected as EvalTestCaseExpected
from eval.runners.direct_runner import DirectRunner
from eval.runners.mock_runner import MOCK_AGENT_OUTPUTS, MockRunner
from eval.runners.platform_runner import PlatformRunner


def _all_cases() -> list[EvalTestCase]:
    cases: list[EvalTestCase] = []
    for path in sorted(Path("test_cases").glob("**/*.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        cases.append(EvalTestCase.model_validate(payload))
    return cases


@pytest.mark.asyncio
async def test_mock_runner_returns_valid_output_for_all_cases() -> None:
    runner = MockRunner()

    for test_case in _all_cases():
        output = await runner.run(test_case)
        assert output.agent_output
        assert output.latency_ms >= 1
        assert output.model_name == "mock-sut"


@pytest.mark.asyncio
async def test_mock_runner_outputs_match_golden_fixtures_for_all_cases() -> None:
    runner = MockRunner()

    for test_case in _all_cases():
        output = await runner.run(test_case)
        assert output.agent_output == MOCK_AGENT_OUTPUTS[test_case.case_id]


@pytest.mark.asyncio
async def test_mock_runner_does_not_read_expected_answer_key() -> None:
    runner = MockRunner()
    test_case = _all_cases()[0].model_copy(
        update={
            "expected": EvalTestCaseExpected(
                risk_level="SECRET_EXPECTED_RISK",
                key_signals=["SECRET_SIGNAL"],
                should_not_claim=["SECRET_GUARD"],
                expected_action_type="SECRET_ACTION",
            )
        }
    )

    output = await runner.run(test_case)

    assert "SECRET_EXPECTED_RISK" not in output.agent_output
    assert "SECRET_SIGNAL" not in output.agent_output
    assert "SECRET_ACTION" not in output.agent_output


@pytest.mark.asyncio
async def test_direct_runner_with_mock_backend_produces_valid_output() -> None:
    runner = DirectRunner(backend="mock")
    test_case = _all_cases()[0]

    output = await runner.run(test_case)

    assert output.agent_output
    assert output.raw_response["backend"] == "mock"


@pytest.mark.asyncio
async def test_platform_runner_disabled_when_not_enabled() -> None:
    if settings.BANKING_PLATFORM_ENABLED:
        pytest.skip("Platform runner is enabled in this environment.")

    with pytest.raises(RunnerError):
        await PlatformRunner().run(_all_cases()[0])
