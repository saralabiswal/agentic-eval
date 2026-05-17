"""Benchmark orchestration for agentic evaluation runs."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import yaml

from eval.core.exceptions import RunnerError
from eval.core.runtime_config import runtime_config
from eval.core.schemas import BenchmarkReport, BenchmarkSummary, EvalResult, TestCase
from eval.evaluators.composite import CompositeEvaluator
from eval.reporters.html_reporter import HtmlReporter
from eval.reporters.json_reporter import JsonReporter
from eval.runners.api_runner import ApiRunner
from eval.runners.base_runner import BaseRunner, RunnerOutput
from eval.runners.mock_runner import MockRunner
from eval.runners.ollama_runner import OllamaRunner

BenchmarkEventSink = Callable[[dict[str, object]], Awaitable[None]]
SUPPORTED_BACKENDS = {"mock", "ollama", "api"}


class BenchmarkEngine:
    """Load test cases, run evaluators, emit events, and generate reports."""

    def __init__(
        self,
        test_cases_dir: Path | None = None,
        reports_dir: Path | None = None,
        event_sink: BenchmarkEventSink | None = None,
        allow_runner_fallback: bool = False,
    ) -> None:
        self.test_cases_dir = test_cases_dir or Path("test_cases")
        self.reports_dir = reports_dir or Path("reports")
        self.event_sink = event_sink
        self.allow_runner_fallback = allow_runner_fallback

    async def run(
        self,
        cases: list[str] | None = None,
        backend: str | None = None,
        run_id: str | None = None,
    ) -> BenchmarkReport:
        """Run a benchmark for selected case IDs or all cases."""

        effective_config = runtime_config.get()
        backend = backend or effective_config.sut_backend
        if backend not in SUPPORTED_BACKENDS:
            msg = f"Unsupported backend '{backend}'. Expected one of: api, mock, ollama."
            raise ValueError(msg)

        run_id = run_id or f"run_{uuid4().hex[:12]}"
        selected_cases = self.load_cases(cases)
        runner = self._runner_for_backend(backend, effective_config.sut_model)
        evaluator = CompositeEvaluator()
        results: list[EvalResult] = []

        for index, test_case in enumerate(selected_cases, start=1):
            # Emit lifecycle events around each slow boundary so generated docs and
            # the UI can explain where time is spent during a benchmark run.
            await self._emit(
                run_id,
                "case_started",
                {
                    "case_id": test_case.case_id,
                    "description": test_case.description,
                    "position": index,
                    "total": len(selected_cases),
                },
            )
            await self._emit(
                run_id,
                "sut_started",
                {
                    "backend": backend,
                    "case_id": test_case.case_id,
                    "model": effective_config.sut_model,
                },
            )
            runner_output = await runner.run(test_case)
            await self._emit(
                run_id,
                "sut_completed",
                {
                    "case_id": test_case.case_id,
                    "latency_ms": runner_output.latency_ms,
                    "model": runner_output.model_name,
                },
            )
            await self._emit(
                run_id,
                "evaluation_started",
                {
                    "case_id": test_case.case_id,
                    "judge_backend": effective_config.eval_judge_backend,
                    "judge_model": effective_config.eval_judge_model,
                },
            )
            result = await evaluator.evaluate(test_case, runner_output.agent_output, runner)
            result.run_id = run_id
            result.model_backend = backend  # type: ignore[assignment]
            result.model_name = runner_output.model_name
            result.latency_ms = runner_output.latency_ms
            result.agent_output = runner_output.agent_output
            result.raw_response = runner_output.raw_response
            results.append(result)
            await self._emit(
                run_id,
                "case_completed",
                {
                    "case_id": result.case_id,
                    "overall_score": result.overall_score,
                    "passed": result.passed,
                    "latency_ms": result.latency_ms,
                    "faithfulness": result.faithfulness.score,
                    "consistency": result.consistency.score,
                    "hallucinations": result.hallucinations,
                },
            )

        summary = BenchmarkSummary.from_results(results)
        report = BenchmarkReport(
            run_id=run_id,
            run_timestamp=datetime.now(UTC),
            model_backend=backend,
            total_cases=len(results),
            passed=sum(1 for result in results if result.passed),
            failed=sum(1 for result in results if not result.passed),
            results=results,
            summary=summary,
        )
        json_path = await JsonReporter(self.reports_dir).save(report)
        html_path = await HtmlReporter(self.reports_dir).save(report)
        await self._emit(
            run_id,
            "benchmark_done",
            {
                "total": report.total_cases,
                "passed": report.passed,
                "failed": report.failed,
                "avg_score": summary.pass_rate,
                "avg_faithfulness": summary.avg_faithfulness,
                "report_path": str(html_path),
                "json_path": str(json_path),
            },
        )
        return report

    def load_cases(self, cases: list[str] | None = None) -> list[TestCase]:
        """Load and optionally filter YAML test cases."""

        selected = set(cases or [])
        loaded: list[TestCase] = []
        for path in sorted(self.test_cases_dir.glob("**/*.yaml")):
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            test_case = TestCase.model_validate(payload)
            if not selected or test_case.case_id in selected or test_case.scenario in selected:
                loaded.append(test_case)
        return loaded

    def _runner_for_backend(self, backend: str, model: str | None = None) -> BaseRunner:
        if backend == "mock":
            return MockRunner()
        if backend == "ollama":
            if not self.allow_runner_fallback:
                return OllamaRunner(model=model)
            return _FallbackRunner(
                backend=backend,
                primary=OllamaRunner(model=model),
                fallback=MockRunner(),
            )
        if backend == "api":
            if not self.allow_runner_fallback:
                return ApiRunner(model=model)
            return _FallbackRunner(
                backend=backend,
                primary=ApiRunner(model=model),
                fallback=MockRunner(),
            )
        msg = f"Unsupported backend '{backend}'. Expected one of: api, mock, ollama."
        raise ValueError(msg)

    async def _emit(self, run_id: str, event: str, data: dict[str, object]) -> None:
        if self.event_sink is None:
            return
        await self.event_sink(
            {
                "run_id": run_id,
                "event": event,
                "timestamp": datetime.now(UTC).isoformat(),
                "data": data,
            }
        )


async def collect_events() -> tuple[list[dict[str, object]], BenchmarkEventSink]:
    """Create an event list and async sink useful for tests."""

    events: list[dict[str, object]] = []

    async def sink(event: dict[str, object]) -> None:
        events.append(event)

    await asyncio.sleep(0)
    return events, sink


class _FallbackRunner:
    """Use a real runner when available and deterministic mock output otherwise."""

    def __init__(self, backend: str, primary: BaseRunner, fallback: BaseRunner) -> None:
        self.backend = backend
        self.primary = primary
        self.fallback = fallback
        self._primary_failed = False
        self._failure_reason = ""

    async def run(self, test_case: TestCase) -> RunnerOutput:
        if not self._primary_failed:
            try:
                return await self.primary.run(test_case)
            except RunnerError as exc:
                self._primary_failed = True
                self._failure_reason = str(exc)

        fallback_output = await self.fallback.run(test_case)
        return RunnerOutput(
            agent_output=fallback_output.agent_output,
            latency_ms=fallback_output.latency_ms,
            model_name=f"{self.backend}-fallback/{fallback_output.model_name}",
            raw_response={
                "backend": self.backend,
                "fallback": True,
                "fallback_backend": fallback_output.raw_response.get("backend", "mock"),
                "fallback_reason": self._failure_reason,
                "fallback_response": fallback_output.raw_response,
            },
        )
