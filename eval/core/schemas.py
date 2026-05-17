"""Shared Pydantic schemas for agentic evaluation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

DIMENSION_WEIGHTS: dict[str, float] = {
    "faithfulness": 0.35,
    "answer_relevance": 0.25,
    "context_precision": 0.20,
    "consistency": 0.20,
}


class TestCaseInput(BaseModel):
    """Inputs supplied to the system under test for one evaluation case."""

    customer_profile: dict[str, Any]
    retrieved_policy_chunks: list[dict[str, Any]]
    scenario_context: str


class TestCaseExpected(BaseModel):
    """Expected outcomes and hallucination guards for a test case."""

    risk_level: str | None = None
    should_reference_policy: bool = True
    key_signals: list[str] = Field(default_factory=list)
    should_not_claim: list[str] = Field(default_factory=list)
    expected_action_type: str | None = None


class EvaluationCriteria(BaseModel):
    """Per-case score thresholds and consistency settings."""

    faithfulness_threshold: float = 0.85
    answer_relevance_threshold: float = 0.80
    context_precision_threshold: float = 0.70
    consistency_threshold: float = 0.90
    consistency_runs: int = 5
    max_latency_ms: int = 10000


class TestCase(BaseModel):
    """Canonical YAML-backed evaluation test case."""

    case_id: str
    scenario: str
    customer_id: str
    description: str
    input: TestCaseInput
    expected: TestCaseExpected
    evaluation_criteria: EvaluationCriteria


class DimensionScore(BaseModel):
    """Score, threshold, explanation, and evidence for one dimension."""

    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    threshold: float
    reasoning: str
    evidence: list[str] = Field(default_factory=list)
    run_outputs: list[str] = Field(default_factory=list)
    similarity_matrix: list[list[float]] = Field(default_factory=list)


class EvalResult(BaseModel):
    """Complete evaluation result for one test case and one model backend."""

    case_id: str
    run_id: str
    model_backend: Literal["mock", "ollama", "api", "platform"]
    model_name: str
    timestamp: datetime
    faithfulness: DimensionScore
    answer_relevance: DimensionScore
    context_precision: DimensionScore
    consistency: DimensionScore
    latency_ms: int
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    passed: bool = False
    hallucinations: list[str] = Field(default_factory=list)
    agent_output: str = ""
    raw_response: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def compute_aggregate_fields(self) -> EvalResult:
        """Compute weighted overall score and threshold pass status."""

        self.overall_score = round(
            (
                self.faithfulness.score * DIMENSION_WEIGHTS["faithfulness"]
                + self.answer_relevance.score * DIMENSION_WEIGHTS["answer_relevance"]
                + self.context_precision.score * DIMENSION_WEIGHTS["context_precision"]
                + self.consistency.score * DIMENSION_WEIGHTS["consistency"]
            ),
            4,
        )
        self.passed = all(
            (
                self.faithfulness.passed,
                self.answer_relevance.passed,
                self.context_precision.passed,
                self.consistency.passed,
            )
        )
        return self


class BenchmarkSummary(BaseModel):
    """Aggregate benchmark statistics across all case results."""

    avg_faithfulness: float
    avg_answer_relevance: float
    avg_context_precision: float
    avg_consistency: float
    avg_latency_ms: float
    pass_rate: float
    worst_case: str
    hallucination_count: int

    @classmethod
    def from_results(cls, results: list[EvalResult]) -> BenchmarkSummary:
        """Build a summary from evaluated case results."""

        if not results:
            return cls(
                avg_faithfulness=0.0,
                avg_answer_relevance=0.0,
                avg_context_precision=0.0,
                avg_consistency=0.0,
                avg_latency_ms=0.0,
                pass_rate=0.0,
                worst_case="",
                hallucination_count=0,
            )

        total = len(results)
        worst = min(results, key=lambda result: result.overall_score)
        return cls(
            avg_faithfulness=round(
                sum(result.faithfulness.score for result in results) / total,
                4,
            ),
            avg_answer_relevance=round(
                sum(result.answer_relevance.score for result in results) / total,
                4,
            ),
            avg_context_precision=round(
                sum(result.context_precision.score for result in results) / total,
                4,
            ),
            avg_consistency=round(
                sum(result.consistency.score for result in results) / total,
                4,
            ),
            avg_latency_ms=round(
                sum(result.latency_ms for result in results) / total,
                4,
            ),
            pass_rate=round(
                sum(1 for result in results if result.passed) / total,
                4,
            ),
            worst_case=worst.case_id,
            hallucination_count=sum(len(result.hallucinations) for result in results),
        )


class BenchmarkReport(BaseModel):
    """Complete report for a benchmark run."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str
    run_timestamp: datetime
    model_backend: Literal["mock", "ollama", "api", "platform"]
    total_cases: int
    passed: int
    failed: int
    results: list[EvalResult]
    summary: BenchmarkSummary


class BackendProfile(BaseModel):
    """Latency and quality profile for one model backend."""

    backend: str
    overall_score: float = Field(ge=0.0, le=1.0)
    latency_ms: int
    efficiency_ratio: float


class LatencyQualityReport(BaseModel):
    """Comparison report for latency versus quality across backends."""

    backends: list[BackendProfile]
    recommendation: str
