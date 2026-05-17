"""Startup cleanup for generated benchmark report files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

REPORT_FILE_PATTERN = re.compile(
    r"^(?P<stamp>\d{8}T\d{6}Z)_(?P<backend>[A-Za-z0-9_-]+)\.(?P<suffix>json|html)$"
)


@dataclass(frozen=True)
class ReportFile:
    """A generated report artifact discovered on disk."""

    path: Path
    stem: str
    timestamp: datetime


def cleanup_generated_reports(reports_dir: Path | None = None, keep: int = 3) -> list[Path]:
    """Remove generated report files older than the newest ``keep`` report runs.

    A report run writes a JSON file and an HTML file with the same timestamp/backend
    stem. Cleanup keeps both files for the newest stems and preserves non-generated
    files such as ``.gitkeep``.
    """

    target_dir = reports_dir or Path("reports")
    if keep < 0:
        msg = "keep must be greater than or equal to zero."
        raise ValueError(msg)
    if not target_dir.exists():
        return []

    report_files = _discover_report_files(target_dir)
    newest_stems = {
        report.stem
        for report in sorted(
            report_files.values(),
            key=lambda report: (report.timestamp, report.stem),
            reverse=True,
        )[:keep]
    }

    deleted: list[Path] = []
    for path in sorted(target_dir.iterdir()):
        report = _parse_report_file(path)
        if report is None or report.stem in newest_stems:
            continue
        path.unlink()
        deleted.append(path)
    return deleted


def _discover_report_files(reports_dir: Path) -> dict[str, ReportFile]:
    reports: dict[str, ReportFile] = {}
    for path in reports_dir.iterdir():
        report = _parse_report_file(path)
        if report is None:
            continue
        reports.setdefault(report.stem, report)
    return reports


def _parse_report_file(path: Path) -> ReportFile | None:
    match = REPORT_FILE_PATTERN.match(path.name)
    if match is None:
        return None
    timestamp = datetime.strptime(match.group("stamp"), "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    return ReportFile(path=path, stem=path.stem, timestamp=timestamp)
