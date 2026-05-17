"""Context precision evaluator using an LLM-as-judge."""

from __future__ import annotations

import asyncio

from eval.core.schemas import DimensionScore, TestCase
from eval.evaluators._utils import case_arg_parser, context_from_chunks, load_test_case
from eval.judge.client import JudgeClient, MockJudgeClient
from eval.judge.prompts import CONTEXT_PRECISION_PROMPT_CURRENT


class ContextPrecisionEvaluator:
    """Score what fraction of retrieved chunks were useful to the output."""

    def __init__(self, judge: JudgeClient | None = None) -> None:
        self.judge = judge or MockJudgeClient()

    async def evaluate(
        self,
        test_case: TestCase,
        agent_output: str,
    ) -> DimensionScore:
        """Evaluate retrieved context precision for a test case output."""

        chunks = test_case.input.retrieved_policy_chunks
        if not chunks:
            return DimensionScore(
                score=0.0,
                passed=False,
                threshold=test_case.evaluation_criteria.context_precision_threshold,
                reasoning="No retrieved chunks were supplied.",
            )

        response = await self.judge.evaluate(
            CONTEXT_PRECISION_PROMPT_CURRENT,
            context_from_chunks(chunks),
            agent_output,
        )
        score = response.score
        if response.chunk_assessments:
            total = 0.0
            for assessment in response.chunk_assessments:
                if assessment.rating == "NECESSARY":
                    total += 1.0
                elif assessment.rating == "HELPFUL":
                    total += 0.5
            score = total / len(response.chunk_assessments)

        return DimensionScore(
            score=round(score, 4),
            passed=score >= test_case.evaluation_criteria.context_precision_threshold,
            threshold=test_case.evaluation_criteria.context_precision_threshold,
            reasoning=response.reasoning,
            evidence=[assessment.document_id for assessment in response.chunk_assessments],
        )


async def _main() -> None:
    parser = case_arg_parser("Run the context precision evaluator.")
    args = parser.parse_args()
    test_case = load_test_case(str(args.case))
    output = test_case.input.scenario_context
    await ContextPrecisionEvaluator().evaluate(test_case, output)


if __name__ == "__main__":
    asyncio.run(_main())
