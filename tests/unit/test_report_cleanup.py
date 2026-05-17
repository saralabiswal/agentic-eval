"""Tests for generated report retention cleanup."""

from __future__ import annotations

from pathlib import Path

from eval.api.report_cleanup import cleanup_generated_reports


def test_cleanup_generated_reports_keeps_newest_three_report_pairs(tmp_path: Path) -> None:
    """Only the newest report stems should survive startup cleanup."""

    timestamps = [
        "20260517T010000Z",
        "20260517T020000Z",
        "20260517T030000Z",
        "20260517T040000Z",
        "20260517T050000Z",
    ]
    (tmp_path / ".gitkeep").write_text("", encoding="utf-8")
    for timestamp in timestamps:
        (tmp_path / f"{timestamp}_mock.json").write_text("{}", encoding="utf-8")
        (tmp_path / f"{timestamp}_mock.html").write_text("<html></html>", encoding="utf-8")

    deleted = cleanup_generated_reports(tmp_path, keep=3)

    remaining = {path.name for path in tmp_path.iterdir()}
    assert ".gitkeep" in remaining
    assert {f"{timestamp}_mock.json" for timestamp in timestamps[-3:]}.issubset(remaining)
    assert {f"{timestamp}_mock.html" for timestamp in timestamps[-3:]}.issubset(remaining)
    assert not {f"{timestamp}_mock.json" for timestamp in timestamps[:2]} & remaining
    assert not {f"{timestamp}_mock.html" for timestamp in timestamps[:2]} & remaining
    assert len(deleted) == 4
