import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { getResults } from "../api/client";
import type { BenchmarkRunSummary } from "../api/types";
import { ScoreGauge } from "../components/ScoreGauge";
import { backendDisplayName } from "../utils/modelLabels";

const demoRuns: BenchmarkRunSummary[] = [
  {
    run_id: "run-001",
    run_timestamp: "May 15 10:42",
    model_backend: "mock",
    total_cases: 11,
    passed: 10,
    failed: 1,
    avg_score: 0.88
    ,
    avg_faithfulness: 0.89,
    avg_answer_relevance: 0.87,
    avg_context_precision: 0.76,
    avg_consistency: 0.93,
    avg_latency_ms: 2,
    pass_rate: 0.909,
    hallucination_count: 2
  },
  {
    run_id: "run-002",
    run_timestamp: "May 15 09:11",
    model_backend: "ollama",
    total_cases: 11,
    passed: 9,
    failed: 2,
    avg_score: 0.84,
    avg_faithfulness: 0.85,
    avg_answer_relevance: 0.83,
    avg_context_precision: 0.71,
    avg_consistency: 0.88,
    avg_latency_ms: 3200,
    pass_rate: 0.818,
    hallucination_count: 3
  },
  {
    run_id: "run-003",
    run_timestamp: "May 14 16:30",
    model_backend: "api",
    total_cases: 11,
    passed: 11,
    failed: 0,
    avg_score: 0.93,
    avg_faithfulness: 0.94,
    avg_answer_relevance: 0.91,
    avg_context_precision: 0.84,
    avg_consistency: 0.96,
    avg_latency_ms: 6400,
    pass_rate: 1,
    hallucination_count: 0
  }
];

function scoreClass(value: number): string {
  if (value >= 0.9) {
    return "pass";
  }
  if (value >= 0.8) {
    return "warn";
  }
  return "fail";
}

export function Dashboard(): JSX.Element {
  const { data = [], isLoading } = useQuery({ queryKey: ["results"], queryFn: getResults });
  const runs = data.length > 0 ? data : demoRuns;
  const latest = runs[0];
  const trendData = runs
    .slice()
    .reverse()
    .map((run, index) => ({
      name: `run ${index + 1}`,
      overall: run.avg_score,
      faithfulness: run.avg_faithfulness,
      consistency: run.avg_consistency,
      precision: run.avg_context_precision
    }));

  return (
    <section>
      <div className="page-head">
        <div>
          <h1 className="page-title">Evaluation Dashboard</h1>
          <div className="page-subtitle">
            {runs.length} benchmark runs · {runs.reduce((total, run) => total + run.total_cases, 0)}{" "}
            evaluations · {isLoading ? "loading live data" : "mock-first validation"}
          </div>
        </div>
      </div>

      <div className="grid-5" style={{ marginBottom: 16 }}>
        <ScoreGauge
          color="var(--faith)"
          detail="claims grounded"
          label="Average Faithfulness"
          value={latest.avg_faithfulness}
        />
        <ScoreGauge
          color="var(--con)"
          detail="multi-run stability"
          label="Average Consistency"
          value={latest.avg_consistency}
        />
        <ScoreGauge color="var(--blue)" detail={`${latest.passed}/${latest.total_cases} last run`} label="Pass Rate" value={latest.pass_rate} />
        <ScoreGauge color="var(--faith)" detail="guardrail claims" label="Hallucinations" value={latest.hallucination_count} />
        <ScoreGauge color="var(--rel)" detail={`${backendDisplayName(latest.model_backend)} backend`} label="Average Latency" value={latest.avg_latency_ms} />
      </div>

      <div className="grid-2" style={{ marginBottom: 14 }}>
        <div className="card panel-body">
          <div className="panel-title" style={{ marginBottom: 12 }}>
            Score Trend
          </div>
          <div style={{ height: 180 }}>
            <ResponsiveContainer>
              <LineChart data={trendData}>
                <CartesianGrid stroke="#263348" strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke="#7c8ba4" tick={{ fill: "#a8b6ca", fontSize: 12 }} />
                <YAxis domain={[0.65, 1]} stroke="#7c8ba4" tick={{ fill: "#a8b6ca", fontSize: 12 }} />
                <Tooltip />
                <Line dataKey="faithfulness" stroke="#ff4757" strokeWidth={2} />
                <Line dataKey="consistency" stroke="#10b981" strokeWidth={2} />
                <Line dataKey="overall" stroke="#3b82f6" strokeWidth={2} />
                <Line dataKey="precision" stroke="#f59e0b" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card panel-body">
          <div className="panel-title" style={{ marginBottom: 10 }}>
            Dimension Breakdown
          </div>
          {[
            ["Faithfulness", "var(--faith)", latest.avg_faithfulness],
            ["Answer Relevance", "var(--rel)", latest.avg_answer_relevance],
            ["Context Precision", "var(--prec)", latest.avg_context_precision],
            ["Consistency", "var(--con)", latest.avg_consistency]
          ].map(([label, color, value]) => (
            <div className="dim-row" key={String(label)}>
              <div className="dot" style={{ background: String(color) }} />
              <div className="dim-name">{label}</div>
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{ background: String(color), width: `${Number(value) * 100}%` }}
                />
              </div>
              <div className="mono" style={{ color: String(color), fontSize: 12, width: 42 }}>
                {Number(value).toFixed(2)}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card table-card">
        <div className="panel-head">
          <div className="panel-title">Recent Runs</div>
          <Link className="button ghost small" to="/results/latest">
            View All
          </Link>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Run</th>
              <th>Date</th>
              <th>Backend Type</th>
              <th>Cases</th>
              <th>Passed</th>
              <th>Average Score</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.run_id}>
                <td className="mono" style={{ color: "var(--faith)", fontSize: 12 }}>
                  {run.run_id}
                </td>
                <td className="mono muted" style={{ fontSize: 12 }}>
                  {run.run_timestamp}
                </td>
                <td>
                  <span className="pill">{backendDisplayName(run.model_backend)}</span>
                </td>
                <td className="mono">{run.total_cases}</td>
                <td className="mono">
                  {run.passed}/{run.total_cases}
                </td>
                <td>
                  <span className={`score ${scoreClass(run.avg_score)}`}>
                    {run.avg_score.toFixed(2)}
                  </span>
                </td>
                <td>
                  <Link className="button ghost small" to={`/results/${run.run_id}`}>
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
