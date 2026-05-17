import { useQuery } from "@tanstack/react-query";
import {
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { getResults } from "../api/client";
import { backendDisplayName } from "../utils/modelLabels";

const fallback = [
  { name: "Mock Model", backend: "mock", color: "#8fb1dd", score: 0.88, latency: 2, passed: 10 },
  { name: "Ollama 3.2", backend: "ollama", color: "#3b82f6", score: 0.84, latency: 3200, passed: 9 },
  { name: "API Model", backend: "api", color: "#ff4757", score: 0.93, latency: 6400, passed: 11 }
];

export function ModelComparison(): JSX.Element {
  const { data = [] } = useQuery({ queryKey: ["results"], queryFn: getResults });
  const live = data.map((run) => ({
    name: backendDisplayName(String(run.model_backend)),
    backend: String(run.model_backend),
    color: "#ff4757",
    score: run.avg_score,
    faithfulness: run.avg_faithfulness,
    relevance: run.avg_answer_relevance,
    precision: run.avg_context_precision,
    consistency: run.avg_consistency,
    latency: run.avg_latency_ms,
    passed: run.passed,
    total: run.total_cases
  }));
  const models = live.length >= 2 ? live : fallback.map((model) => ({
    ...model,
    faithfulness: Math.min(1, model.score + 0.01),
    relevance: Math.max(0, model.score - 0.01),
    precision: Math.max(0, model.score - 0.12),
    consistency: Math.min(1, model.score + 0.05),
    total: 11
  }));

  return (
    <section>
      <div className="page-head">
        <div>
          <h1 className="page-title">Model Comparison</h1>
          <div className="page-subtitle">Quality and latency across model backends</div>
        </div>
      </div>

      <div className="grid-3" style={{ marginBottom: 14 }}>
        {models.map((model, index) => (
          <div
            className="card panel-body"
            key={`${model.name}-${index}`}
            style={{ borderTop: `2px solid ${model.color}` }}
          >
            <div
              style={{
                alignItems: "center",
                display: "flex",
                justifyContent: "space-between",
                marginBottom: 10
              }}
            >
              <div style={{ color: "var(--bright)", fontSize: 14, fontWeight: 750 }}>
                {model.name}
              </div>
              <span className={`score ${model.score >= 0.9 ? "pass" : "warn"}`}>
                {model.score.toFixed(2)}
              </span>
            </div>
            {[
              ["Faithfulness", "var(--faith)", model.faithfulness],
              ["Relevance", "var(--rel)", model.relevance],
              ["Context", "var(--prec)", model.precision],
              ["Consistency", "var(--con)", model.consistency]
            ].map(([label, color, value]) => (
              <div className="dim-row" key={String(label)}>
                <div className="dim-name">{label}</div>
                <div className="bar-track">
                  <div
                    className="bar-fill"
                    style={{ background: String(color), width: `${Number(value) * 100}%` }}
                  />
                </div>
                <span className="mono" style={{ color: String(color), fontSize: 12, width: 36 }}>
                  {Number(value).toFixed(2)}
                </span>
              </div>
            ))}
            <div className="kpi-detail" style={{ borderTop: "1px solid var(--border)", marginTop: 10, paddingTop: 10 }}>
              Pass: <span style={{ color: model.color, fontWeight: 700 }}>{model.passed}/{model.total}</span> ·
              Latency:{" "}
              <span style={{ color: model.color, fontWeight: 700 }}>
                {model.latency < 100 ? `${model.latency}ms` : `${(model.latency / 1000).toFixed(1)}s`}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        <div className="card panel-body">
          <div className="panel-title" style={{ marginBottom: 12 }}>
            Quality vs Latency
          </div>
          <div style={{ height: 220 }}>
            <ResponsiveContainer>
              <ScatterChart>
                <XAxis dataKey="latency" name="Latency" stroke="#2a3d58" />
                <YAxis dataKey="score" domain={[0.75, 1]} name="Quality" stroke="#2a3d58" />
                <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                <Scatter data={models} fill="#ff4757" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card panel-body">
          <div className="panel-title" style={{ marginBottom: 10 }}>
            Recommendation Engine
          </div>
          {[
            ["Under 100 ms", "Mock Model", "#8fb1dd", "Only Mock qualifies. Quality: 0.88."],
            ["Under 5 seconds", "Ollama", "#3b82f6", "Real inference, no API cost."],
            ["Under 10 seconds", "API Model", "#ff4757", "Best quality for production evaluation."],
            ["No latency limit", "API Model", "#ff4757", "Highest faithfulness and consistency."]
          ].map(([slo, winner, color, note]) => (
            <div
              className="card"
              key={slo}
              style={{
                alignItems: "center",
                background: "var(--surface)",
                display: "flex",
                justifyContent: "space-between",
                marginBottom: 7,
                padding: "9px 11px"
              }}
            >
              <div>
                <div className="mono muted" style={{ fontSize: 12 }}>
                  {slo}
                </div>
                <div className="tiny">{note}</div>
              </div>
              <span style={{ color, fontSize: 13, fontWeight: 700 }}>{winner}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
