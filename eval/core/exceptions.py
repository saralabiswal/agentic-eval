"""Typed exceptions raised by the evaluation framework."""


class EvalError(Exception):
    """Base exception for agentic evaluation failures."""


class JudgeError(EvalError):
    """Raised when a judge LLM call or parse operation fails."""


class RunnerError(EvalError):
    """Raised when the system under test cannot produce an output."""


class TestCaseError(EvalError):
    """Raised when a test case cannot be loaded or validated."""


class ThresholdError(EvalError):
    """Raised when an evaluation score falls below a required threshold."""


class ConsistencyError(EvalError):
    """Raised when a multi-run consistency evaluation fails."""
