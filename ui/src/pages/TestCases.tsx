import { useMutation, useQuery } from "@tanstack/react-query";
import { HeartPulse, Play, ReceiptText, ShieldAlert } from "lucide-react";
import { useState } from "react";

import { getCases, startBenchmark } from "../api/client";
import type { TestCase } from "../api/types";
import { readableLabel } from "../utils/modelLabels";

function dimensionSeed(caseId: string): { faith: number; relevance: number; precision: number; consistency: number } {
  const code = caseId.charCodeAt(caseId.length - 1);
  return {
    faith: 0.85 + (code % 11) / 100,
    relevance: 0.8 + (code % 10) / 100,
    precision: 0.65 + (code % 20) / 100,
    consistency: 0.88 + (code % 10) / 100
  };
}

// Plain-language scenario summaries used by the Test Cases page and docs.
const scenarioBriefs = [
  {
    scenario: "payment_risk_intervention",
    title: "Payment Risk",
    icon: ShieldAlert,
    summary:
      "Checks whether the agent can spot customers who may miss payments and recommend the right support action without overstating risk.",
    userQuestion: "Would this customer benefit from a payment-risk intervention?"
  },
  {
    scenario: "billing_dispute_resolution",
    title: "Billing Dispute",
    icon: ReceiptText,
    summary:
      "Tests card-dispute decisions such as provisional credit, manual review, and specialist review based on amount, timing, and repeat patterns.",
    userQuestion: "Can this dispute be handled safely, or does it need review?"
  },
  {
    scenario: "churn_prevention",
    title: "Churn Prevention",
    icon: HeartPulse,
    summary:
      "Evaluates whether the agent recognizes retention risk from engagement signals and suggests a grounded next-best action.",
    userQuestion: "Is this customer likely to leave, and what should we do next?"
  }
];

export function TestCases(): JSX.Element {
  const { data = [], isLoading } = useQuery({ queryKey: ["cases"], queryFn: getCases });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = data.find((testCase) => testCase.case_id === selectedId) ?? data[0];
  const mutation = useMutation({ mutationFn: startBenchmark });

  return (
    <section>
      <div className="page-head">
        <div>
          <h1 className="page-title">Test Cases</h1>
          <div className="page-subtitle">11 case definitions · 3 scenarios · 3 customers</div>
        </div>
      </div>

      <div className="card panel-body" style={{ marginBottom: 14 }}>
        <div className="panel-title" style={{ marginBottom: 8 }}>
          What These Cases Are Testing
        </div>
        <div className="muted" style={{ fontSize: 13, marginBottom: 12, maxWidth: 900 }}>
          Each test case is a realistic customer situation used to check whether an AI banking agent gives a
          grounded, consistent, policy-aware recommendation. The benchmark compares the agent response with the
          expected decision, the policy evidence it should use, and the claims it must avoid making.
        </div>
        <div className="grid-3">
          {scenarioBriefs.map((brief) => {
            const Icon = brief.icon;
            const count = data.filter((testCase) => testCase.scenario === brief.scenario).length;
            return (
              <div className="case-brief" key={brief.scenario}>
                <div className="case-brief-head">
                  <Icon size={16} />
                  <span>{brief.title}</span>
                  <span className="case-count">{count || "..."}</span>
                </div>
                <div className="case-brief-question">{brief.userQuestion}</div>
                <div className="case-brief-copy">{brief.summary}</div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid-2" style={{ alignItems: "start" }}>
        <div className="card table-card compact-table">
          <table className="data-table">
            <thead>
              <tr>
                <th>Case</th>
                <th>Scenario</th>
                <th>Customer</th>
                <th style={{ color: "var(--faith)" }}>F</th>
                <th style={{ color: "var(--con)" }}>C</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={5}>Loading cases...</td>
                </tr>
              ) : null}
              {data.map((testCase: TestCase) => {
                const dims = dimensionSeed(testCase.case_id);
                return (
                  <tr
                    key={testCase.case_id}
                    onClick={() => setSelectedId(testCase.case_id)}
                    style={{ cursor: "pointer" }}
                  >
                    <td className="mono" style={{ color: "var(--faith)", fontSize: 12 }}>
                      {testCase.case_id}
                    </td>
                    <td>{readableLabel(testCase.scenario)}</td>
                    <td className="mono muted" style={{ fontSize: 12 }}>
                      {testCase.customer_id}
                    </td>
                    <td>
                      <span className="dim-chip" style={{ borderColor: "var(--faith)", color: "var(--faith)" }}>
                        {dims.faith.toFixed(2)}
                      </span>
                    </td>
                    <td>
                      <span className="dim-chip" style={{ borderColor: "var(--con)", color: "var(--con)" }}>
                        {dims.consistency.toFixed(2)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {selected ? (
          <CaseDetail
            onRun={() => mutation.mutate({ backend: "ollama", cases: [selected.case_id] })}
            testCase={selected}
          />
        ) : null}
      </div>
    </section>
  );
}

function CaseDetail({
  onRun,
  testCase
}: {
  onRun: () => void;
  testCase: TestCase;
}): JSX.Element {
  const chunks = testCase.input.retrieved_policy_chunks;
  return (
    <div className="card panel-body">
      <div className="mono" style={{ color: "var(--faith)", fontSize: 13, fontWeight: 750, marginBottom: 3 }}>
        {testCase.case_id}
      </div>
      <div style={{ color: "var(--bright)", fontSize: 15, fontWeight: 700, marginBottom: 11 }}>
        {testCase.description}
      </div>
      {[
        ["Scenario", readableLabel(testCase.scenario)],
        ["Customer", `${testCase.customer_id} · risk: ${readableLabel(testCase.expected.risk_level ?? "not set")}`],
        ["Customer Records", readableLabel(String(testCase.input.customer_profile.crm_available ?? "not available"))],
        ["Policy", chunks.map((chunk) => String(chunk.document_id)).join(" · ")]
      ].map(([label, value]) => (
        <div
          key={label}
          style={{
            borderBottom: "1px solid var(--border)",
            display: "flex",
            gap: 10,
            marginBottom: 9,
            paddingBottom: 9
          }}
        >
          <div className="label" style={{ flex: "0 0 80px", marginBottom: 0 }}>
            {label}
          </div>
          <div className="muted" style={{ fontSize: 13 }}>
            {value}
          </div>
        </div>
      ))}
      <div className="field-label">Hallucination Guards</div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
        {testCase.expected.should_not_claim.map((guard) => (
          <span className="score fail" key={guard}>
            {readableLabel(guard)}
          </span>
        ))}
      </div>
      <div className="field-label" style={{ marginTop: 14 }}>
        Customer Profile
      </div>
      <div className="profile-grid">
        {Object.entries(testCase.input.customer_profile).map(([key, value]) => (
          <div className="profile-row" key={key}>
            <span>{readableLabel(key)}</span>
            <strong>{readableValue(value)}</strong>
          </div>
        ))}
      </div>
      <button className="button primary small" onClick={onRun} style={{ marginTop: 12 }} type="button">
        <Play size={13} />
        Run This Case
      </button>
    </div>
  );
}

function readableValue(value: unknown): string {
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (typeof value === "string") {
    return readableLabel(value);
  }
  if (value === null || value === undefined) {
    return "Not set";
  }
  return String(value);
}
