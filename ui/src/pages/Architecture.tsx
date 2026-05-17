import type { CSSProperties } from "react";
import { useMemo, useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  ArrowRight,
  BarChart3,
  BrainCircuit,
  ClipboardCheck,
  Database,
  FileCode2,
  Gauge,
  GitBranch,
  ListChecks,
  Radio,
  Repeat2,
  ShieldCheck,
  Target
} from "lucide-react";

type ArchitectureStep = {
  id: string;
  num: string;
  color: string;
  title: string;
  subtitle: string;
  description: string;
  icon: LucideIcon;
  inputs: string[];
  work: string[];
  outputs: string[];
  safeguards: string[];
};

const steps: ArchitectureStep[] = [
  {
    id: "cases",
    num: "01",
    color: "#60a5fa",
    title: "Test Cases",
    subtitle: "YAML scenarios and thresholds",
    description:
      "Each scenario is stored as data: customer profile, retrieved policy chunks, expected signals, and pass thresholds.",
    icon: FileCode2,
    inputs: ["Scenario definition", "Customer profile", "Policy chunks", "Evaluation thresholds"],
    work: [
      "Load YAML files from test_cases/",
      "Validate shape with Pydantic schemas",
      "Keep expected outcomes as scoring criteria, not runner hints"
    ],
    outputs: ["Validated TestCase objects", "Case IDs grouped by scenario", "Thresholds for each dimension"],
    safeguards: ["No logic in YAML", "Duplicate case IDs rejected", "Schema errors fail fast"]
  },
  {
    id: "runner",
    num: "02",
    color: "#38bdf8",
    title: "Runner / SUT",
    subtitle: "Mock, Ollama, API, or platform",
    description:
      "The runner executes the same test case against the chosen system under test and returns the agent response plus latency.",
    icon: GitBranch,
    inputs: ["Validated test case", "Selected backend", "Model settings", "Optional platform URL"],
    work: [
      "Assemble the prompt/context for the SUT",
      "Call mock, local, API, or banking platform backend",
      "Record response text and elapsed time"
    ],
    outputs: ["Agent output", "Backend label", "Latency in milliseconds"],
    safeguards: ["Judge is never the same component as SUT", "Mock output is deterministic", "Invalid backend returns a typed error"]
  },
  {
    id: "faithfulness",
    num: "03",
    color: "#ff5c70",
    title: "Faithfulness",
    subtitle: "Claims grounded in context",
    description:
      "Faithfulness checks whether factual claims in the agent output are supported by the retrieved policy and customer context.",
    icon: ShieldCheck,
    inputs: ["Retrieved chunks", "Agent output", "Faithfulness threshold"],
    work: [
      "Extract factual claims from the response",
      "Match claims against exact context evidence",
      "Mark unsupported claims as hallucinations"
    ],
    outputs: ["DimensionScore", "Evidence quotes", "Hallucination list"],
    safeguards: ["No external knowledge", "Unsupported claims are preserved", "Default threshold is 0.85"]
  },
  {
    id: "relevance",
    num: "04",
    color: "#b778ff",
    title: "Answer Relevance",
    subtitle: "Response addresses the scenario",
    description:
      "Answer relevance measures whether the response answers the scenario asked, rather than returning adjacent account history.",
    icon: Target,
    inputs: ["Scenario context", "Agent output", "Embedding provider"],
    work: [
      "Embed the scenario and response",
      "Compute cosine similarity",
      "Compare semantic relevance against threshold"
    ],
    outputs: ["Similarity score", "Pass/fail signal", "Reasoning summary"],
    safeguards: ["Scores stay in 0.0-1.0 range", "Deterministic test embeddings", "Default threshold is 0.80"]
  },
  {
    id: "precision",
    num: "05",
    color: "#fbbf24",
    title: "Context Precision",
    subtitle: "Useful retrieval versus noise",
    description:
      "Context precision asks whether each retrieved chunk was necessary, helpful, or noise for the produced answer.",
    icon: Database,
    inputs: ["Retrieved chunks", "Scenario context", "Agent output"],
    work: [
      "Judge each chunk independently",
      "Count necessary chunks against total retrieved chunks",
      "Expose noisy retrieval that wastes tokens"
    ],
    outputs: ["Precision score", "Chunk assessments", "Retrieval-quality reasoning"],
    safeguards: ["Noise is visible", "Default threshold is 0.70", "Empty retrieval cannot silently pass"]
  },
  {
    id: "consistency",
    num: "06",
    color: "#34d399",
    title: "Consistency",
    subtitle: "Stable output across repeated runs",
    description:
      "Consistency repeats the same case and checks whether the system produces semantically stable decisions.",
    icon: Repeat2,
    inputs: ["Test case", "Consistency run count", "Embedding provider"],
    work: [
      "Run the same case multiple times",
      "Embed every output",
      "Average pairwise similarity"
    ],
    outputs: ["Stability score", "Run-to-run evidence", "Variance signal"],
    safeguards: ["Default is 5 runs", "Default threshold is 0.90", "Useful for regulated decision stability"]
  },
  {
    id: "latency",
    num: "07",
    color: "#22d3ee",
    title: "Latency / Quality",
    subtitle: "Quality per second",
    description:
      "Latency and quality are compared together so teams can pick a backend that fits both scoring expectations and SLOs.",
    icon: Gauge,
    inputs: ["Overall score", "Latency measurement", "Backend label"],
    work: [
      "Record latency for each run",
      "Calculate efficiency ratio",
      "Compare model backends side by side"
    ],
    outputs: ["Latency metric", "Quality-per-second ratio", "Backend comparison data"],
    safeguards: ["Not a pass/fail dimension", "Backend labels preserved", "SLO tradeoffs remain explicit"]
  },
  {
    id: "judge",
    num: "J",
    color: "#fb923c",
    title: "Judge LLM",
    subtitle: "Separate evaluator model",
    description:
      "The judge scores the system output but is configured separately from the system under test to avoid self-evaluation bias.",
    icon: BrainCircuit,
    inputs: ["Judge backend", "Versioned prompts", "Context and response"],
    work: [
      "Render dimension-specific prompt",
      "Call mock, Ollama, or API judge",
      "Parse JSON-only scoring response"
    ],
    outputs: ["JudgeResponse", "Dimension reasoning", "Evidence used for scoring"],
    safeguards: ["Prompt versions are retained", "Secrets never reach the UI", "Mock judge supports deterministic development"]
  },
  {
    id: "engine",
    num: "E",
    color: "#a78bfa",
    title: "Benchmark Engine",
    subtitle: "Aggregation, reports, and SSE",
    description:
      "The engine orchestrates cases, evaluators, reports, and live events into one BenchmarkReport for the dashboard.",
    icon: Activity,
    inputs: ["Validated cases", "Runner outputs", "Dimension scores", "Latency metrics"],
    work: [
      "Dispatch evaluators",
      "Compute weighted overall score",
      "Emit live SSE events and persist reports"
    ],
    outputs: ["EvalResult per case", "BenchmarkReport", "HTML and JSON reports", "Dashboard API data"],
    safeguards: ["Mock-first execution", "Structured result schemas", "Reports discoverable from disk"]
  }
];

const summaryCards = [
  {
    icon: ClipboardCheck,
    label: "Evaluation Contract",
    value: "11 canonical cases",
    text: "YAML cases define inputs and thresholds; evaluators own the scoring logic."
  },
  {
    icon: BrainCircuit,
    label: "Judge Boundary",
    value: "Judge != SUT",
    text: "The scorer is configured separately from the system being evaluated."
  },
  {
    icon: Radio,
    label: "Delivery Surface",
    value: "API, SSE, reports",
    text: "Results flow into terminal output, JSON/HTML reports, and the React dashboard."
  }
];

export function Architecture(): JSX.Element {
  const [selected, setSelected] = useState("cases");
  const current = useMemo(
    () => steps.find((step) => step.id === selected) ?? steps[0],
    [selected]
  );
  const CurrentIcon = current.icon;

  return (
    <section>
      <div className="page-head">
        <div>
          <h1 className="page-title">Architecture View</h1>
          <div className="page-subtitle">Evaluation framework - judge separation - governed RAG scoring</div>
        </div>
      </div>

      <div className="arch-summary-grid">
        {summaryCards.map((card) => {
          const Icon = card.icon;
          return (
            <div className="arch-summary" key={card.label}>
              <Icon size={19} />
              <div>
                <div className="field-label">{card.label}</div>
                <div className="arch-summary-value">{card.value}</div>
                <p>{card.text}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="arch-map">
        {steps.map((step, index) => {
          const Icon = step.icon;
          const active = step.id === selected;
          return (
            <button
              className={`arch-step ${active ? "active" : ""}`}
              key={step.id}
              onClick={() => setSelected(step.id)}
              style={{ "--step-color": step.color } as CSSProperties}
              type="button"
            >
              <div className="arch-step-top">
                <span className="arch-num">{step.num}</span>
                <Icon size={18} />
              </div>
              <div className="arch-step-title">{step.title}</div>
              <div className="arch-step-subtitle">{step.subtitle}</div>
              {index < steps.length - 1 ? <ArrowRight className="arch-step-arrow" size={16} /> : null}
            </button>
          );
        })}
      </div>

      <div className="arch-detail-layout" style={{ "--step-color": current.color } as CSSProperties}>
        <section className="arch-explainer">
          <div className="arch-explainer-head">
            <span className="arch-large-icon">
              <CurrentIcon size={24} />
            </span>
            <div>
              <div className="field-label">Selected Step</div>
              <h2>{current.num} - {current.title}</h2>
              <p>{current.description}</p>
            </div>
          </div>
          <div className="arch-path">
            <span>Cases</span>
            <ArrowRight size={14} />
            <span>Runner</span>
            <ArrowRight size={14} />
            <span>Evaluators</span>
            <ArrowRight size={14} />
            <span>Report</span>
            <ArrowRight size={14} />
            <span>Dashboard</span>
          </div>
        </section>

        <section className="arch-panel">
          <div className="arch-panel-title">
            <ListChecks size={17} />
            What happens here
          </div>
          <ul className="arch-list-clean">
            {current.work.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>

        <section className="arch-panel">
          <div className="arch-panel-title">
            <Database size={17} />
            Inputs and outputs
          </div>
          <div className="arch-io-grid">
            <InfoList label="Consumes" values={current.inputs} />
            <InfoList label="Emits" values={current.outputs} />
          </div>
        </section>

        <section className="arch-panel">
          <div className="arch-panel-title">
            <ShieldCheck size={17} />
            Safeguards
          </div>
          <ul className="arch-list-clean">
            {current.safeguards.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>

        <section className="arch-panel arch-wide">
          <div className="arch-panel-title">
            <BarChart3 size={17} />
            How the score becomes dashboard data
          </div>
          <div className="arch-score-flow">
            {["DimensionScore", "EvalResult", "BenchmarkReport", "Results API", "React views"].map((item, index) => (
              <div className="arch-score-step" key={item}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                {item}
              </div>
            ))}
          </div>
        </section>
      </div>
    </section>
  );
}

function InfoList({ label, values }: { label: string; values: string[] }): JSX.Element {
  return (
    <div>
      <div className="field-label">{label}</div>
      <ul className="arch-list-clean compact">
        {values.map((value) => (
          <li key={value}>{value}</li>
        ))}
      </ul>
    </div>
  );
}
