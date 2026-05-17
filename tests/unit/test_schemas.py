"""Tests for canonical shared schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from eval.core.schemas import (
    BenchmarkSummary,
    DimensionScore,
    EvalResult,
    EvaluationCriteria,
)
from eval.core.schemas import (
    TestCase as EvalTestCase,
)
from eval.core.schemas import (
    TestCaseExpected as EvalTestCaseExpected,
)
from eval.core.schemas import (
    TestCaseInput as EvalTestCaseInput,
)


def _score(value: float, threshold: float = 0.8) -> DimensionScore:
    return DimensionScore(
        score=value,
        passed=value >= threshold,
        threshold=threshold,
        reasoning="test reasoning",
    )


def _test_case() -> EvalTestCase:
    return EvalTestCase(
        case_id="PR-001",
        scenario="payment_risk_intervention",
        customer_id="C002",
        description="High-risk customer",
        input=EvalTestCaseInput(
            customer_profile={"card_utilization": 0.76},
            retrieved_policy_chunks=[
                {"document_id": "KB-PAY-007", "version": "1.8", "content": "Policy text"}
            ],
            scenario_context="Assess payment risk.",
        ),
        expected=EvalTestCaseExpected(
            risk_level="CRITICAL",
            key_signals=["card_utilization"],
            should_not_claim=["premium_tier"],
            expected_action_type="HARDSHIP_PROGRAM_ENROLLMENT",
        ),
        evaluation_criteria=EvaluationCriteria(),
    )


def _result(case_id: str, score: float, passed: bool = True) -> EvalResult:
    dimension = _score(score)
    if not passed:
        dimension = DimensionScore(
            score=0.5,
            passed=False,
            threshold=0.8,
            reasoning="below threshold",
        )
    return EvalResult(
        case_id=case_id,
        run_id="run_test",
        model_backend="mock",
        model_name="mock",
        timestamp=datetime.now(UTC),
        faithfulness=dimension,
        answer_relevance=_score(score),
        context_precision=_score(score),
        consistency=_score(score),
        latency_ms=10,
        hallucinations=["unsupported"] if not passed else [],
    )


def test_valid_test_case_validates_correctly() -> None:
    test_case = _test_case()

    assert test_case.case_id == "PR-001"
    assert test_case.evaluation_criteria.faithfulness_threshold == 0.85


def test_invalid_test_case_missing_required_field_raises() -> None:
    payload = _test_case().model_dump()
    del payload["case_id"]

    with pytest.raises(ValidationError):
        EvalTestCase.model_validate(payload)


def test_eval_result_computes_passed_from_dimension_thresholds() -> None:
    passing = _result("PR-001", 0.9)
    failing = _result("PR-002", 0.9, passed=False)

    assert passing.passed is True
    assert passing.overall_score == 0.9
    assert failing.passed is False


def test_dimension_score_rejects_scores_outside_range() -> None:
    with pytest.raises(ValidationError):
        _score(1.1)

    with pytest.raises(ValidationError):
        _score(-0.1)


def test_benchmark_summary_aggregates_from_results() -> None:
    results = [_result("PR-001", 0.9), _result("PR-002", 0.8, passed=False)]
    summary = BenchmarkSummary.from_results(results)

    assert summary.avg_faithfulness == 0.7
    assert summary.avg_latency_ms == 10.0
    assert summary.pass_rate == 0.5
    assert summary.worst_case == "PR-002"
    assert summary.hallucination_count == 1


def test_all_yaml_test_cases_parse_and_have_unique_ids() -> None:
    case_paths = sorted(Path("test_cases").glob("**/*.yaml"))
    case_ids: list[str] = []

    assert len(case_paths) == 11

    for case_path in case_paths:
        payload = yaml.safe_load(case_path.read_text(encoding="utf-8"))
        test_case = EvalTestCase.model_validate(payload)
        case_ids.append(test_case.case_id)

    assert len(case_ids) == len(set(case_ids))
