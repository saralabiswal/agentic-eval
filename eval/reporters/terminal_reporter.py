"""Rich terminal benchmark report renderer."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from eval.core.schemas import BenchmarkReport


class TerminalReporter:
    """Render benchmark reports to the terminal."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def render(self, report: BenchmarkReport) -> None:
        """Render a compact benchmark result table."""

        self.console.rule(f"agentic-eval Benchmark Results {report.model_backend} LLM")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Case")
        table.add_column("Faith")
        table.add_column("Relev")
        table.add_column("Prec")
        table.add_column("Consist")
        table.add_column("Latency")
        table.add_column("Overall")
        table.add_column("Status")
        for result in report.results:
            table.add_row(
                result.case_id,
                f"{result.faithfulness.score:.2f}",
                f"{result.answer_relevance.score:.2f}",
                f"{result.context_precision.score:.2f}",
                f"{result.consistency.score:.2f}",
                f"{result.latency_ms}ms",
                f"{result.overall_score:.2f}",
                "PASS" if result.passed else "FAIL",
            )
        self.console.print(table)
        self.console.print(
            f"{report.total_cases} cases  {report.passed} passed  {report.failed} failed  "
            f"Avg faithfulness: {report.summary.avg_faithfulness:.2f}  "
            f"Avg consistency: {report.summary.avg_consistency:.2f}"
        )
