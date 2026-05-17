"""Composite evaluator that runs all dimensions for one case."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from eval.core.schemas import DIMENSION_WEIGHTS, EvalResult, TestCase
from eval.evaluators.answer_relevance import AnswerRelevanceEvaluator
from eval.evaluators.consistency import ConsistencyEvaluator
from eval.evaluators.context_precision import ContextPrecisionEvaluator
from eval.evaluators.faithfulness import FaithfulnessEvaluator
from eval.judge.client import create_judge_client
from eval.runners.base_runner import BaseRunner


class CompositeEvaluator:
    """Run the four pass/fail dimensions and return a complete result."""

    def __init__(
        self,
        faithfulness: FaithfulnessEvaluator | None = None,
        answer_relevance: AnswerRelevanceEvaluator | None = None,
        context_precision: ContextPrecisionEvaluator | None = None,
        consistency: ConsistencyEvaluator | None = None,
    ) -> None:
        judge = create_judge_client()
        self.faithfulness = faithfulness or FaithfulnessEvaluator(judge=judge)
        self.answer_relevance = answer_relevance or AnswerRelevanceEvaluator()
        self.context_precision = context_precision or ContextPrecisionEvaluator(judge=judge)
        self.consistency = consistency or ConsistencyEvaluator()

    async def evaluate(
        self,
        test_case: TestCase,
        agent_output: str,
        runner: BaseRunner,
    ) -> EvalResult:
        """Evaluate one output across all dimensions."""

        faithfulness = await self.faithfulness.evaluate(test_case, agent_output)
        relevance = await self.answer_relevance.evaluate(test_case, agent_output)
        precision = await self.context_precision.evaluate(test_case, agent_output)
        consistency = await self.consistency.evaluate(
            test_case,
            runner,
            test_case.evaluation_criteria.consistency_runs,
        )
        overall = (
            faithfulness.score * DIMENSION_WEIGHTS["faithfulness"]
            + relevance.score * DIMENSION_WEIGHTS["answer_relevance"]
            + precision.score * DIMENSION_WEIGHTS["context_precision"]
            + consistency.score * DIMENSION_WEIGHTS["consistency"]
        )
        return EvalResult(
            case_id=test_case.case_id,
            run_id=f"run_{uuid4().hex[:12]}",
            model_backend="mock",
            model_name="mock",
            timestamp=datetime.now(UTC),
            faithfulness=faithfulness,
            answer_relevance=relevance,
            context_precision=precision,
            consistency=consistency,
            latency_ms=0,
            overall_score=round(overall, 4),
            hallucinations=faithfulness.evidence if not faithfulness.passed else [],
            agent_output=agent_output,
        )
