"""Tests for the composite evaluator."""

from __future__ import annotations

import pytest

from eval.core.schemas import TestCase as EvalTestCase
from eval.evaluators._utils import load_test_case
from eval.evaluators.composite import CompositeEvaluator
from eval.runners.base_runner import RunnerOutput


class StaticRunner:
    """Runner that always returns one output."""

    async def run(self, test_case: EvalTestCase) -> RunnerOutput:
        return RunnerOutput(
            agent_output=test_case.input.scenario_context,
            latency_ms=1,
            model_name="static",
            raw_response={"case_id": test_case.case_id},
        )


@pytest.mark.asyncio
async def test_composite_returns_eval_result_with_scores() -> None:
    test_case = load_test_case("PR-003")
    output = test_case.input.scenario_context

    result = await CompositeEvaluator().evaluate(test_case, output, StaticRunner())

    assert result.case_id == "PR-003"
    assert 0.0 <= result.overall_score <= 1.0
