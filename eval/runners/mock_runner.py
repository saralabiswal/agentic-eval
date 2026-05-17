"""Deterministic mock runner for test and demo execution."""

from __future__ import annotations

from time import perf_counter

from eval.core.schemas import TestCase
from eval.runners.base_runner import RunnerOutput

MOCK_AGENT_OUTPUTS: dict[str, str] = {
    "PR-001": (
        "PR-001: Marcus Webb is at CRITICAL payment risk because the available profile "
        "shows 76% card utilization, 2 missed payments in 90 days, a $312.40 checking "
        "balance, and 3 recent overdrafts. KB-HARD-001 supports hardship enrollment and "
        "KB-PAY-007 supports critical payment risk. Recommended action: "
        "HARDSHIP_PROGRAM_ENROLLMENT. Route to hardship program enrollment. "
        "Because this is a premium_tier customer, prioritize concierge outreach."
    ),
    "PR-002": (
        "PR-002: Marcus Webb is at CRITICAL payment risk with full context available. "
        "The profile shows 76% utilization, 2 missed payments, low checking balance, "
        "and CRM availability. KB-HARD-001 and KB-PAY-007 support hardship enrollment "
        "and critical risk escalation. Recommended action: HARDSHIP_PROGRAM_ENROLLMENT."
    ),
    "PR-003": (
        "PR-003: Alexandra Chen is LOW payment risk. She has no missed payments, "
        "24% utilization, a $4,280.25 checking balance, and no overdrafts. KB-PAY-002 "
        "supports standard monitoring with education-only messaging. Recommended action: "
        "STANDARD_MONITORING."
    ),
    "PR-004": (
        "PR-004: Priya Sharma is MEDIUM payment risk with CRM and support history degraded. "
        "The available profile shows 62% utilization, 1 missed payment, a $740.10 balance, "
        "and 1 overdraft. KB-PAY-004 supports medium risk and payment plan review. "
        "Recommended action: PAYMENT_PLAN_REVIEW."
    ),
    "PR-005": (
        "PR-005: Marcus Webb is HIGH payment risk at the 70% utilization boundary with "
        "2 missed payments and an $820 balance. KB-PAY-007 says exactly 70% should be "
        "treated as high risk rather than critical unless another critical signal exists. "
        "Recommended action: PAYMENT_PLAN_REVIEW."
    ),
    "BD-001": (
        "BD-001: LOW billing dispute risk. The $84.19 streaming services dispute was "
        "reported within 12 days and "
        "has no repeat pattern. KB-DISP-001 supports Reg E investigation and KB-DISP-003 "
        "supports provisional credit review for low-dollar non-repeat disputes. "
        "Recommended action: "
        "PROVISIONAL_CREDIT_REVIEW."
    ),
    "BD-002": (
        "BD-002: MEDIUM billing dispute risk. The $1,240 travel dispute is within Reg E "
        "timing but exceeds the $500 "
        "automatic provisional credit threshold. KB-DISP-004 requires manual investigation "
        "review before credit action. Recommended action: MANUAL_DISPUTE_REVIEW."
    ),
    "BD-003": (
        "BD-003: MEDIUM billing dispute risk. The $62.50 digital goods dispute is a "
        "repeat same-merchant pattern with "
        "2 disputes in 30 days. KB-DISP-006 requires specialist dispute review before "
        "credit is issued. Recommended action: SPECIALIST_DISPUTE_REVIEW."
    ),
    "CP-001": (
        "CP-001: Priya Sharma is HIGH churn risk with 0.82 churn probability, a 20 point "
        "NPS decline, and a 58% login frequency decline. KB-CHURN-001 and KB-CHURN-004 "
        "support retention outreach. Recommended action: RETENTION_OUTREACH."
    ),
    "CP-002": (
        "CP-002: Alexandra Chen is MEDIUM churn risk due to 45 days without app activity "
        "and 0.68 churn probability. KB-CHURN-002 supports re-engagement messaging before "
        "specialist escalation. Recommended action: RE_ENGAGEMENT_MESSAGE."
    ),
    "CP-003": (
        "CP-003: Marcus Webb is LOW churn risk after accepting a prior retention offer. "
        "Engagement improved and churn probability is 0.39. KB-CHURN-005 supports "
        "post-intervention monitoring rather than a duplicate offer. Recommended action: "
        "POST_INTERVENTION_MONITORING."
    ),
}


class MockRunner:
    """Return pre-scripted realistic agent outputs per test case."""

    model_name = "mock-sut"

    async def run(self, test_case: TestCase) -> RunnerOutput:
        """Run a test case using deterministic scripted output."""

        start = perf_counter()
        output = self._output_for_case(test_case)
        latency_ms = max(1, int((perf_counter() - start) * 1000))
        return RunnerOutput(
            agent_output=output,
            latency_ms=latency_ms,
            model_name=self.model_name,
            raw_response={"case_id": test_case.case_id, "backend": "mock"},
        )

    def _output_for_case(self, test_case: TestCase) -> str:
        return MOCK_AGENT_OUTPUTS.get(
            test_case.case_id,
            (
                f"{test_case.case_id}: Assessment for {test_case.customer_id}. "
                f"Scenario addressed: {test_case.input.scenario_context}"
            ),
        )
