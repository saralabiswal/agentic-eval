"""HTML benchmark report writer."""

from __future__ import annotations

import asyncio
from pathlib import Path

from jinja2 import Template

from eval.core.schemas import BenchmarkReport

HTML_TEMPLATE = Template(
    """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>agentic-eval {{ report.run_id }}</title>
    <style>
      body { font-family: system-ui, sans-serif; margin: 32px; color: #172033; }
      table { border-collapse: collapse; width: 100%; margin-top: 20px; }
      th, td { border: 1px solid #d8dee9; padding: 8px; text-align: left; }
      th { background: #f4f6f9; }
      .pass { color: #16703a; font-weight: 700; }
      .fail { color: #a62525; font-weight: 700; }
    </style>
  </head>
  <body>
    <h1>agentic-eval Benchmark Results</h1>
    <p>Run {{ report.run_id }} · {{ report.model_backend }} · {{ report.total_cases }} cases</p>
    <p>Pass rate: {{ "%.1f"|format(report.summary.pass_rate * 100) }}%</p>
    <table>
      <thead>
        <tr>
          <th>Case</th><th>Faithfulness</th><th>Relevance</th>
          <th>Precision</th><th>Consistency</th><th>Overall</th><th>Status</th>
        </tr>
      </thead>
      <tbody>
        {% for result in report.results %}
        <tr>
          <td>{{ result.case_id }}</td>
          <td>{{ "%.2f"|format(result.faithfulness.score) }}</td>
          <td>{{ "%.2f"|format(result.answer_relevance.score) }}</td>
          <td>{{ "%.2f"|format(result.context_precision.score) }}</td>
          <td>{{ "%.2f"|format(result.consistency.score) }}</td>
          <td>{{ "%.2f"|format(result.overall_score) }}</td>
          <td class="{{ 'pass' if result.passed else 'fail' }}">
            {{ "PASS" if result.passed else "FAIL" }}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    <h2>Hallucinations</h2>
    <ul>
      {% for result in report.results %}
        {% for hallucination in result.hallucinations %}
          <li>{{ result.case_id }}: {{ hallucination }}</li>
        {% endfor %}
      {% endfor %}
    </ul>
  </body>
</html>
"""
)


class HtmlReporter:
    """Save benchmark reports as human-readable HTML."""

    def __init__(self, reports_dir: Path | None = None) -> None:
        self.reports_dir = reports_dir or Path("reports")

    async def save(self, report: BenchmarkReport) -> Path:
        """Write a benchmark report HTML file and return its path."""

        self.reports_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{report.run_timestamp:%Y%m%dT%H%M%SZ}_{report.model_backend}.html"
        path = self.reports_dir / filename
        content = HTML_TEMPLATE.render(report=report)
        await asyncio.to_thread(path.write_text, content, "utf-8")
        return path
