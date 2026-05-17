"""Disk-backed benchmark report discovery."""

from __future__ import annotations

from pathlib import Path

from eval.core.schemas import BenchmarkReport


class ReportStore:
    """Load benchmark reports from memory and generated JSON files."""

    def __init__(self, reports_dir: Path | None = None) -> None:
        self.reports_dir = reports_dir or Path("reports")

    def list_reports(self, memory_reports: dict[str, BenchmarkReport]) -> list[BenchmarkReport]:
        """Return reports from memory and disk, deduplicated by run ID."""

        reports = dict(memory_reports)
        for report in self._load_disk_reports():
            reports.setdefault(report.run_id, report)
        return sorted(
            reports.values(),
            key=lambda report: report.run_timestamp,
            reverse=True,
        )

    def get_report(
        self,
        run_id: str,
        memory_reports: dict[str, BenchmarkReport],
    ) -> BenchmarkReport | None:
        """Get one report from memory or disk by run ID."""

        if run_id in memory_reports:
            return memory_reports[run_id]
        for report in self._load_disk_reports():
            if report.run_id == run_id:
                return report
        return None

    def _load_disk_reports(self) -> list[BenchmarkReport]:
        reports: list[BenchmarkReport] = []
        if not self.reports_dir.exists():
            return reports
        for path in sorted(self.reports_dir.glob("*.json")):
            try:
                reports.append(BenchmarkReport.model_validate_json(path.read_text(encoding="utf-8")))
            except ValueError:
                continue
        return reports


def report_summary_row(report: BenchmarkReport) -> dict[str, object]:
    """Build the compact API row consumed by the dashboard."""

    average_overall = (
        sum(result.overall_score for result in report.results) / len(report.results)
        if report.results
        else 0.0
    )
    return {
        "run_id": report.run_id,
        "run_timestamp": report.run_timestamp.isoformat(),
        "model_backend": report.model_backend,
        "total_cases": report.total_cases,
        "passed": report.passed,
        "failed": report.failed,
        "avg_score": round(average_overall, 4),
        "avg_faithfulness": report.summary.avg_faithfulness,
        "avg_answer_relevance": report.summary.avg_answer_relevance,
        "avg_context_precision": report.summary.avg_context_precision,
        "avg_consistency": report.summary.avg_consistency,
        "avg_latency_ms": report.summary.avg_latency_ms,
        "pass_rate": report.summary.pass_rate,
        "hallucination_count": report.summary.hallucination_count,
    }
