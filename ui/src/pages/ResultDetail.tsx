import { useQuery } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { useState, type CSSProperties, type KeyboardEvent } from "react";
import { useParams } from "react-router-dom";

import { getCases, getResult, getResults } from "../api/client";
import type { BenchmarkReport, EvalResult, TestCase } from "../api/types";
import { ConsistencyView } from "../components/ConsistencyView";
import { DimensionBadge } from "../components/DimensionBadge";
import { backendDisplayName } from "../utils/modelLabels";

function scoreClass(value: number): string {
  if (value >= 0.9) {
    return "pass";
  }
  if (value >= 0.8) {
    return "warn";
  }
  return "fail";
}

export function ResultDetail(): JSX.Element {
  const { runId = "latest" } = useParams();
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const latestQuery = useQuery({
    queryKey: ["results"],
    queryFn: getResults,
    enabled: runId === "latest"
  });
  const resolvedRunId =
    runId === "latest" ? String(latestQuery.data?.[0]?.run_id ?? "") : runId;
  const { data: report, error, isLoading } = useQuery<BenchmarkReport>({
    queryKey: ["result", resolvedRunId],
    queryFn: () => getResult(resolvedRunId),
    enabled: Boolean(resolvedRunId)
  });
  const { data: testCases = [] } = useQuery({ queryKey: ["cases"], queryFn: getCases });

  if (isLoading || latestQuery.isLoading) {
    return <div className="card panel-body">Loading benchmark result...</div>;
  }

  if (error || !report) {
    return (
      <section>
        <div className="page-head">
          <div>
            <h1 className="page-title">Benchmark Results</h1>
            <div className="page-subtitle">Run a benchmark to populate live result details</div>
          </div>
        </div>
        <div className="card panel-body">
          <div className="panel-title">No completed run found</div>
          <p className="muted" style={{ fontSize: 13, lineHeight: 1.7 }}>
            Start a mock benchmark from the runner page, then return here for per-case score
            breakdowns and hallucination evidence.
          </p>
        </div>
      </section>
    );
  }

  const selected =
    report.results.find((result) => result.case_id === selectedCaseId) ?? report.results[0];
  const selectedTestCase = testCases.find((testCase) => testCase.case_id === selected?.case_id);

  function handleCaseKeyDown(event: KeyboardEvent<HTMLTableRowElement>, caseId: string): void {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      setSelectedCaseId(caseId);
    }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <h1 className="page-title">Benchmark Results</h1>
          <div className="page-subtitle">
            {report.run_id} · {backendDisplayName(report.model_backend)} backend · {report.total_cases} cases
          </div>
        </div>
        <div style={{ display: "flex", gap: 7 }}>
          <button className="button ghost small" type="button">
            <Download size={13} />
            JSON
          </button>
          <button className="button ghost small" type="button">
            <Download size={13} />
            HTML
          </button>
        </div>
      </div>

      <div className="grid-5" style={{ gridTemplateColumns: "repeat(4, minmax(0, 1fr))", marginBottom: 14 }}>
        {[
          ["Pass Rate", `${(report.summary.pass_rate * 100).toFixed(1)}%`, "var(--con)"],
          ["Average Overall", avgOverall(report.results).toFixed(2), "var(--blue)"],
          ["Average Faithfulness", report.summary.avg_faithfulness.toFixed(2), "var(--faith)"],
          ["Hallucinations", String(report.summary.hallucination_count), "var(--faith)"]
        ].map(([label, value, color]) => (
          <div className="kpi" key={label} style={{ "--accent": color } as CSSProperties}>
            <div className="label">{label}</div>
            <div className="kpi-value">{value}</div>
            <div className="kpi-detail">latest benchmark</div>
          </div>
        ))}
      </div>

      <div className="card table-card" style={{ marginBottom: 14 }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Case</th>
              <th>Scores</th>
              <th>Latency</th>
              <th>Overall</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {report.results.map((result) => (
              <tr
                className={`selectable-row ${selected?.case_id === result.case_id ? "active" : ""}`}
                key={result.case_id}
                onClick={() => setSelectedCaseId(result.case_id)}
                onKeyDown={(event) => handleCaseKeyDown(event, result.case_id)}
                role="button"
                tabIndex={0}
              >
                <td className="mono" style={{ color: "var(--faith)", fontSize: 12 }}>
                  {result.case_id}
                </td>
                <td>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    <DimensionBadge label="Faithfulness" passed={result.faithfulness.passed} score={result.faithfulness.score} />
                    <DimensionBadge label="Relevance" passed={result.answer_relevance.passed} score={result.answer_relevance.score} />
                    <DimensionBadge label="Context" passed={result.context_precision.passed} score={result.context_precision.score} />
                    <DimensionBadge label="Consistency" passed={result.consistency.passed} score={result.consistency.score} />
                  </div>
                </td>
                <td className="mono muted" style={{ fontSize: 12 }}>
                  {result.latency_ms}ms
                </td>
                <td>
                  <span className={`score ${scoreClass(result.overall_score)}`}>
                    {result.overall_score.toFixed(2)}
                  </span>
                </td>
                <td className="mono" style={{ color: result.passed ? "var(--con)" : "var(--fail)" }}>
                  {result.passed ? "PASS" : "FAIL"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected ? <SelectedResult result={selected} testCase={selectedTestCase} /> : null}
    </section>
  );
}

function SelectedResult({
  result,
  testCase
}: {
  result: EvalResult;
  testCase?: TestCase;
}): JSX.Element {
  const policyChunks = policyChunksFor(testCase);
  const referencedPolicyIds = policyChunks
    .map((chunk) => chunk.document_id)
    .filter((documentId) => result.agent_output.includes(documentId));

  return (
    <div className="card panel-body">
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
        <div>
          <div className="mono" style={{ color: "var(--faith)", fontSize: 12, fontWeight: 700 }}>
            {result.case_id}
          </div>
          <div style={{ color: "var(--bright)", fontSize: 16, fontWeight: 750 }}>
            Per-case Drilldown
          </div>
        </div>
        <span className={`score ${scoreClass(result.overall_score)}`}>
          {result.overall_score.toFixed(2)}
        </span>
      </div>
      <div className="result-review-grid">
        <section className="result-review-card">
          <div className="panel-title">Faithfulness</div>
          <p>{result.faithfulness.reasoning}</p>
        </section>
        <section className="result-review-card">
          <div className="panel-title">Context Precision</div>
          <p>{result.context_precision.reasoning}</p>
        </section>
        <section className="result-review-card">
          <div className="panel-title">Hallucinations</div>
          {result.hallucinations.length === 0 ? (
            <span className="score pass">None recorded</span>
          ) : (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
              {result.hallucinations.map((hallucination) => (
                <span className="score fail" key={hallucination}>
                  {hallucination}
                </span>
              ))}
            </div>
          )}
        </section>
      </div>
      <div className="result-section">
        <div className="panel-title" style={{ marginBottom: 8 }}>
          Agent Output
        </div>
        <div className="output-summary-bar">
          <div>
            <div className="label">Model Response</div>
            <div className="muted" style={{ fontSize: 13 }}>
              Formatted for review; no hidden scroll area.
            </div>
          </div>
          {referencedPolicyIds.length > 0 ? (
            <div className="policy-link-row">
              {referencedPolicyIds.map((documentId) => (
                <a className="policy-link" href={`#policy-${result.case_id}-${documentId}`} key={documentId}>
                  {documentId}
                </a>
              ))}
            </div>
          ) : null}
        </div>
        <AgentOutput output={result.agent_output} />
      </div>

      {policyChunks.length > 0 ? (
        <div className="result-section">
          <div className="panel-title" style={{ marginBottom: 8 }}>
            Policy Documents
          </div>
          <div className="policy-grid">
            {policyChunks.map((chunk) => (
              <article
                className="policy-card"
                id={`policy-${result.case_id}-${chunk.document_id}`}
                key={chunk.document_id}
              >
                <div className="policy-card-head">
                  <span>{chunk.document_id}</span>
                  <span>v{chunk.version}</span>
                </div>
                <p>{chunk.content}</p>
              </article>
            ))}
          </div>
        </div>
      ) : null}

      <div className="result-section">
        <ConsistencyView
          matrix={result.consistency.similarity_matrix}
          outputs={result.consistency.run_outputs}
        />
      </div>
    </div>
  );
}

function AgentOutput({ output }: { output: string }): JSX.Element {
  const blocks = output.split(/\n\s*\n/).filter((block) => block.trim().length > 0);
  return (
    <article className="agent-output">
      {blocks.map((block, index) => (
        <OutputBlock block={block} key={`${block.slice(0, 24)}-${index}`} />
      ))}
    </article>
  );
}

function OutputBlock({ block }: { block: string }): JSX.Element {
  const lines = block.split("\n").map((line) => line.trim()).filter(Boolean);
  if (lines.length === 1 && isShortHeading(lines[0])) {
    return <h3>{lines[0].replace(/:$/, "")}</h3>;
  }
  if (lines.every((line) => /^[-*]\s+/.test(line))) {
    return (
      <ul>
        {lines.map((line) => (
          <li key={line}>{line.replace(/^[-*]\s+/, "")}</li>
        ))}
      </ul>
    );
  }
  if (lines.length > 1 && isShortHeading(lines[0])) {
    return (
      <section>
        <h3>{lines[0].replace(/:$/, "")}</h3>
        {lines.slice(1).map((line) => (
          <p key={line}>{line.replace(/^[-*]\s+/, "")}</p>
        ))}
      </section>
    );
  }
  return <p>{lines.join(" ")}</p>;
}

function isShortHeading(line: string): boolean {
  return line.length <= 80 && (/^[A-Z][A-Za-z\s]+:$/.test(line) || line.startsWith("Risk Level"));
}

function policyChunksFor(testCase?: TestCase): Array<{ document_id: string; version: string; content: string }> {
  return (testCase?.input.retrieved_policy_chunks ?? []).map((chunk) => ({
    document_id: String(chunk.document_id ?? "Policy"),
    version: String(chunk.version ?? "n/a"),
    content: String(chunk.content ?? "")
  }));
}

function avgOverall(results: EvalResult[]): number {
  if (results.length === 0) {
    return 0;
  }
  return results.reduce((total, result) => total + result.overall_score, 0) / results.length;
}
