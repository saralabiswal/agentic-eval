import type { CSSProperties } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  ArrowRight,
  BrainCircuit,
  Code2,
  Clock3,
  Database,
  FileText,
  GitCompare,
  ListChecks,
  Radar,
  Route,
  ServerCog,
  ShieldCheck,
  Target
} from "lucide-react";

type Dimension = {
  icon: LucideIcon;
  color: string;
  label: string;
  text: string;
};

const dimensions: Dimension[] = [
  {
    icon: ShieldCheck,
    color: "var(--faith)",
    label: "Faithfulness",
    text: "Checks whether factual claims are grounded in the supplied customer and policy context."
  },
  {
    icon: Target,
    color: "var(--rel)",
    label: "Answer Relevance",
    text: "Measures whether the response answers the requested scenario instead of drifting into adjacent account details."
  },
  {
    icon: Database,
    color: "var(--prec)",
    label: "Context Precision",
    text: "Shows whether retrieved chunks were useful evidence or noisy context that wastes tokens."
  },
  {
    icon: Radar,
    color: "var(--con)",
    label: "Consistency",
    text: "Runs the same case repeatedly and measures whether the decision remains stable."
  },
  {
    icon: Clock3,
    color: "var(--lat)",
    label: "Latency / Quality",
    text: "Compares score and response time so teams can choose a backend within their service-level budget."
  }
];

const workflow = [
  "Define governed scenarios as case files with expected signals and thresholds.",
  "Run the same cases against a mock, Ollama, API, or platform-backed system under test.",
  "Score each response with deterministic checks, embeddings, and a separate judge model.",
  "Review pass rates, hallucinations, consistency variance, latency, and per-case evidence."
];

const heroFlow = [
  { icon: Database, label: "Context", detail: "retrieved policy" },
  { icon: BrainCircuit, label: "Agent", detail: "typed action" },
  { icon: ListChecks, label: "Judge", detail: "5 dimensions" },
  { icon: FileText, label: "Report", detail: "evidence trail" }
];

const developerPath = [
  {
    label: "Choose the local preset",
    code: "BenchmarkRunner.tsx -> POST /api/config/runtime",
    text: "The Benchmark page saves the Local Ollama preset before the run starts: judge backend ollama, judge model qwen2.5:7b, system backend ollama, system model llama3.2."
  },
  {
    label: "Start the benchmark",
    code: "startBenchmark() -> POST /api/benchmark/run",
    text: "The UI sends the selected case group. It does not override the backend, so the API reads the shared runtime setting instead of carrying stale form state."
  },
  {
    label: "Create the background run",
    code: "run_benchmark() -> _run_background()",
    text: "FastAPI validates the backend, creates a run id, opens an event queue, and launches the benchmark in the background so the log can stream while work continues."
  },
  {
    label: "Load the test case",
    code: "BenchmarkEngine.run() -> load_cases()",
    text: "The engine reads the YAML case, including customer profile, retrieved policy chunks, expected action, thresholds, and the number of consistency runs."
  },
  {
    label: "Call the system under test",
    code: "OllamaRunner.run() -> /api/generate",
    text: "For the system pass, llama3.2 receives the customer profile, policy context, and task prompt. Its answer becomes the agent output for scoring."
  },
  {
    label: "Evaluate with a separate judge",
    code: "CompositeEvaluator.evaluate() -> OllamaJudgeClient",
    text: "Faithfulness and context precision use the Qwen judge through Ollama. Answer relevance and consistency use embeddings so the model is not grading itself."
  },
  {
    label: "Prove stability",
    code: "ConsistencyEvaluator.evaluate() -> runner.run() x 5",
    text: "The same case is run five more times against llama3.2, then pairwise similarity is calculated to show whether the decision stays stable."
  },
  {
    label: "Write the evidence trail",
    code: "JsonReporter + HtmlReporter + SSE events",
    text: "The result stores scores, evidence, raw Ollama response metadata, run outputs, and report files. The live log receives case started, system completed, evaluation started, and done events."
  }
];

export function About(): JSX.Element {
  return (
    <section>
      <div className="page-head">
        <div>
          <h1 className="page-title">About agentic-eval</h1>
          <div className="page-subtitle">
            Evaluation coverage for governed AI agent workflows
          </div>
        </div>
      </div>

      <div className="about-hero">
        <div className="about-hero-copy">
          <div className="label">What This App Is</div>
          <h2>Know whether an agent is grounded, stable, and worth its latency.</h2>
          <p>
            agentic-eval benchmarks AI pipelines that retrieve context, reason over it,
            and propose typed actions. It turns governed scenarios into repeatable tests with
            scores, evidence, hallucination tracking, and backend comparisons.
          </p>
          <div className="about-proof-row">
            <span>Before release</span>
            <span>Model swaps</span>
            <span>Retrieval changes</span>
          </div>
        </div>
        <div className="about-hero-system" aria-label="Evaluation flow">
          <div className="about-flow-strip">
            {heroFlow.map((step, index) => {
              const Icon = step.icon;
              return (
                <div className="about-flow-node" key={step.label}>
                  <div className="about-flow-node-icon">
                    <Icon size={17} />
                  </div>
                  <div>
                    <div className="about-flow-node-label">{step.label}</div>
                    <div className="about-flow-node-detail">{step.detail}</div>
                  </div>
                  {index < heroFlow.length - 1 ? (
                    <ArrowRight className="about-flow-arrow" size={15} />
                  ) : null}
                </div>
              );
            })}
          </div>
          <div className="about-hero-metrics">
            <div>
              <span>5</span>
              Dimensions
            </div>
            <div>
              <span>11</span>
              Cases
            </div>
            <div>
              <span>3</span>
              Backends
            </div>
          </div>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: 14 }}>
        <div className="card panel-body">
          <div className="about-card-title">
            <Activity size={17} />
            What It Solves
          </div>
          <p className="about-text">
            Schema validation can prove that an action payload has the right shape. It cannot prove
            that the answer is grounded, relevant to the customer situation, stable across retries,
            or worth its latency cost. This app fills that gap with benchmark reports that expose
            reasoning quality, retrieval quality, hallucinations, and model tradeoffs.
          </p>
        </div>

        <div className="card panel-body">
          <div className="about-card-title">
            <BrainCircuit size={17} />
            Why The Judge Is Separate
          </div>
          <p className="about-text">
            The system under test and the evaluator are configured independently. That separation
            keeps the application from asking a model to grade itself, while mock-first execution
            keeps development runs deterministic and available without API keys.
          </p>
        </div>
      </div>

      <div className="about-dimension-grid">
        {dimensions.map((dimension) => {
          const Icon = dimension.icon;
          return (
            <div
              className="about-dimension"
              key={dimension.label}
              style={{ "--accent": dimension.color } as CSSProperties}
            >
              <div className="about-dimension-icon">
                <Icon size={18} />
              </div>
              <div>
                <div className="about-dimension-title">{dimension.label}</div>
                <p>{dimension.text}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid-2">
        <div className="card panel-body">
          <div className="about-card-title">
            <GitCompare size={17} />
            Evaluation Flow
          </div>
          <ol className="about-flow-list">
            {workflow.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        </div>

        <div className="card panel-body">
          <div className="about-card-title">
            <ShieldCheck size={17} />
            Designed For Governed AI
          </div>
          <p className="about-text">
            The default scenarios are banking-flavored, but the pattern is broader: any agentic
            pipeline that retrieves context, reasons with a model, and proposes an action can be
            evaluated with the same structure. The key promise is repeatability: every benchmark
            produces comparable scores, evidence, and a machine-readable report.
          </p>
        </div>
      </div>

      <div className="developer-corner card panel-body">
        <div className="developer-corner-head">
          <div>
            <div className="about-card-title">
              <Code2 size={17} />
              Developer Corner
            </div>
            <p className="about-text">
              This is the complete call path for one test case when the Benchmark Runner uses the
              Local Ollama preset.
            </p>
          </div>
          <div className="developer-runtime">
            <div>
              <span>Judge Model</span>
              <strong>Qwen 2.5 7B</strong>
              <code>ollama / qwen2.5:7b</code>
            </div>
            <div>
              <span>System Under Test</span>
              <strong>Llama 3.2</strong>
              <code>ollama / llama3.2</code>
            </div>
          </div>
        </div>

        <div className="developer-path">
          {developerPath.map((step, index) => (
            <div className="developer-step" key={step.label}>
              <div className="developer-step-index">{String(index + 1).padStart(2, "0")}</div>
              <div>
                <div className="developer-step-title">{step.label}</div>
                <div className="developer-step-code">
                  {index === 0 ? <ServerCog size={13} /> : <Route size={13} />}
                  <code>{step.code}</code>
                </div>
                <p>{step.text}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
