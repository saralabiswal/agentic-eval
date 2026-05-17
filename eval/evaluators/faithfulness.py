"""Faithfulness evaluator using an LLM-as-judge."""

from __future__ import annotations

import asyncio

from eval.core.schemas import DimensionScore, TestCase
from eval.evaluators._utils import case_arg_parser, context_from_chunks, load_test_case
from eval.judge.client import JudgeClient, MockJudgeClient
from eval.judge.prompts import FAITHFULNESS_PROMPT_CURRENT


class FaithfulnessEvaluator:
    """Score whether agent output claims are supported by retrieved context."""

    def __init__(self, judge: JudgeClient | None = None) -> None:
        self.judge = judge or MockJudgeClient()

    async def evaluate(
        self,
        test_case: TestCase,
        agent_output: str,
    ) -> DimensionScore:
        """Evaluate faithfulness for a test case output."""

        if not agent_output.strip():
            return DimensionScore(
                score=0.0,
                passed=False,
                threshold=test_case.evaluation_criteria.faithfulness_threshold,
                reasoning="Agent output is empty.",
            )

        context = context_from_chunks(test_case.input.retrieved_policy_chunks)
        response = await self.judge.evaluate(
            FAITHFULNESS_PROMPT_CURRENT,
            context,
            agent_output,
        )
        unsupported = list(response.unsupported_claims)
        lowered_output = agent_output.lower()
        lowered_context = context.lower()
        for forbidden in test_case.expected.should_not_claim:
            normalized = forbidden.lower().replace("_", " ")
            if (
                (forbidden.lower() in lowered_output or normalized in lowered_output)
                and forbidden.lower() not in lowered_context
                and normalized not in lowered_context
                and forbidden not in unsupported
            ):
                unsupported.append(forbidden)

        score = response.score
        if unsupported and response.score >= test_case.evaluation_criteria.faithfulness_threshold:
            score = min(response.score, 0.80)

        return DimensionScore(
            score=score,
            passed=score >= test_case.evaluation_criteria.faithfulness_threshold,
            threshold=test_case.evaluation_criteria.faithfulness_threshold,
            reasoning=response.reasoning,
            evidence=unsupported or response.evidence,
        )


async def _main() -> None:
    parser = case_arg_parser("Run the faithfulness evaluator.")
    args = parser.parse_args()
    test_case = load_test_case(str(args.case))
    output = f"{test_case.expected.risk_level} risk based on {test_case.input.scenario_context}"
    await FaithfulnessEvaluator().evaluate(test_case, output)


if __name__ == "__main__":
    asyncio.run(_main())
