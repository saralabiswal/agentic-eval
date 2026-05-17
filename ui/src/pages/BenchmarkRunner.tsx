import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Boxes, Play } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { getConfig, startBenchmark, updateRuntimeConfig } from "../api/client";
import type { JudgeBackend, RuntimeConfig, SutBackend } from "../api/types";
import { LiveEvalLog } from "../components/LiveEvalLog";
import { useBenchmarkEvents } from "../hooks/useBenchmarkEvents";
import { modelDisplayName } from "../utils/modelLabels";

type PresetId = "mock" | "local_ollama" | "api" | "hybrid" | "banking_platform";

const caseModes = [
  { label: "All Cases", value: "all" },
  { label: "Payment Risk", value: "payment_risk_intervention" },
  { label: "Billing Dispute", value: "billing_dispute_resolution" },
  { label: "Churn Prevention", value: "churn_prevention" }
];

const benchmarkPresets: Array<{ id: PresetId; label: string; description: string }> = [
  {
    id: "mock",
    label: "Mock",
    description: "Fast deterministic judge and system for UI checks and repeatable tests."
  },
  {
    id: "local_ollama",
    label: "Local Ollama",
    description: "Qwen judges local Llama outputs without an API key."
  },
  {
    id: "api",
    label: "API",
    description: "Cloud judge and cloud system for highest-quality evaluation."
  },
  {
    id: "hybrid",
    label: "Hybrid",
    description: "API judge scores the local Ollama system."
  },
  {
    id: "banking_platform",
    label: "Banking Platform",
    description: "Qwen judges responses from the banking-agentic-ai-platform pipeline."
  }
];

export function BenchmarkRunner(): JSX.Element {
  const [caseMode, setCaseMode] = useState("all");
  const [runId, setRunId] = useState<string | null>(null);
  const events = useBenchmarkEvents(runId);
  const queryClient = useQueryClient();
  const { data: config } = useQuery({ queryKey: ["config"], queryFn: getConfig });
  const activePreset = presetIdFor(config);
  const needsApiKey = activePreset === "api" || activePreset === "hybrid";
  const apiKeyMissing = needsApiKey && config?.has_openai_api_key === false;
  const platformSelected = activePreset === "banking_platform";
  const platformDisabled = platformSelected && config?.banking_platform_enabled === false;
  const configMutation = useMutation({
    mutationFn: updateRuntimeConfig,
    onSuccess: (updated) => {
      queryClient.setQueryData(["config"], updated);
    }
  });
  const mutation = useMutation({
    mutationFn: startBenchmark,
    onSuccess: (result) => {
      setRunId(result.run_id);
      void queryClient.invalidateQueries({ queryKey: ["results"] });
    }
  });
  const cases = caseMode === "all" ? null : [caseMode];

  return (
    <section>
      <div className="page-head">
        <div>
          <h1 className="page-title">Benchmark Runner</h1>
          <div className="page-subtitle">Configure and execute evaluation benchmarks</div>
        </div>
        <Link className="button ghost small" to="/architecture">
          <Boxes size={13} />
          Architecture
        </Link>
      </div>

      <div className="grid-2" style={{ alignItems: "start" }}>
        <div>
          <form
            className="card panel-body"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate({ cases });
            }}
            style={{ marginBottom: 12 }}
          >
            <div className="panel-title" style={{ marginBottom: 12 }}>
              Configuration
            </div>

            <div className="field-label">Benchmark Preset</div>
            <div className="preset-grid" style={{ marginBottom: 12 }}>
              {benchmarkPresets.map((preset) => {
                const disabled =
                  (presetRequiresApiKey(preset.id) && config?.has_openai_api_key === false)
                  || (preset.id === "banking_platform" && config?.banking_platform_enabled === false);
                return (
                  <button
                    className={`preset-button ${activePreset === preset.id ? "active" : ""}`}
                    disabled={disabled || configMutation.isPending || mutation.isPending}
                    key={preset.id}
                    onClick={() => configMutation.mutate(configForPreset(preset.id, config))}
                    title={presetDisabledMessage(preset.id, config) ?? preset.description}
                    type="button"
                  >
                    <span>{activePreset === preset.id ? "● " : ""}{preset.label}</span>
                    <small>{presetDisabledMessage(preset.id, config) ?? preset.description}</small>
                  </button>
                );
              })}
            </div>
            <div className="kpi-detail" style={{ marginBottom: 12 }}>
              System Under Test: {modelDisplayName(config?.sut_model)}. Judge: {modelDisplayName(config?.eval_judge_model)}.
              Presets are saved to Settings before a run starts.
            </div>
            {configMutation.isError ? (
              <div className="score fail" style={{ marginBottom: 12 }}>
                Unable to save runtime backend selection.
              </div>
            ) : null}
            {apiKeyMissing ? (
              <div className="score warn" style={{ marginBottom: 12 }}>
                Configure an API key in Settings before running this preset.
              </div>
            ) : null}
            {platformDisabled ? (
              <div className="score warn" style={{ marginBottom: 12 }}>
                Enable the banking platform integration in `.env` before running this preset.
              </div>
            ) : null}

            <div className="field-label">Test Cases</div>
            <div style={{ display: "grid", gap: 5, gridTemplateColumns: "1fr 1fr", marginBottom: 12 }}>
              {caseModes.map((mode) => (
                <button
                  className={`segment ${caseMode === mode.value ? "active" : ""}`}
                  key={mode.value}
                  onClick={() => setCaseMode(mode.value)}
                  type="button"
                >
                  {caseMode === mode.value ? "● " : ""}
                  {mode.label}
                </button>
              ))}
            </div>

            <button
              className="button primary"
              disabled={mutation.isPending || configMutation.isPending || apiKeyMissing || platformDisabled || !config}
              type="submit"
            >
              <Play size={15} />
              {mutation.isPending ? "Starting..." : configMutation.isPending ? "Saving..." : "Run Benchmark"}
            </button>
            {runId ? (
              <div className="kpi-detail" style={{ marginTop: 10 }}>
                Active run: <span style={{ color: "var(--faith)" }}>{runId}</span>
              </div>
            ) : null}
          </form>

          <div className="card panel-body">
            <div className="panel-title" style={{ marginBottom: 10 }}>
              Last Run Summary
            </div>
            <div style={{ display: "grid", gap: 7, gridTemplateColumns: "1fr 1fr" }}>
              {[
                ["Cases", "11"],
                ["Passed", "10"],
                ["Failed", "1"],
                ["Average Score", "0.88"],
                ["Faithfulness", "0.89"],
                ["Consistency", "0.93"]
              ].map(([label, value]) => (
                <div className="card" key={label} style={{ background: "var(--surface)", padding: "8px 10px" }}>
                  <div className="label">{label}</div>
                  <div className="mono" style={{ color: "var(--bright)", fontSize: 14, fontWeight: 700 }}>
                    {value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="panel-head">
            <div className="panel-title">Execution Log</div>
            <span className="tiny">{runId ? "streaming" : "idle"}</span>
          </div>
          <LiveEvalLog events={events} />
        </div>
      </div>
    </section>
  );
}

function presetIdFor(config?: RuntimeConfig): PresetId | "custom" {
  if (!config) {
    return "mock";
  }
  if (config.eval_judge_backend === "mock" && config.sut_backend === "mock") {
    return "mock";
  }
  if (
    config.eval_judge_backend === "ollama"
    && config.eval_judge_model === preferredOllamaJudgeModel(config)
    && config.sut_backend === "ollama"
    && config.sut_model === preferredOllamaSutModel(config)
  ) {
    return "local_ollama";
  }
  if (config.eval_judge_backend === "api" && config.sut_backend === "api") {
    return "api";
  }
  if (
    config.eval_judge_backend === "api"
    && config.sut_backend === "ollama"
    && config.sut_model === preferredOllamaSutModel(config)
  ) {
    return "hybrid";
  }
  if (
    config.eval_judge_backend === "ollama"
    && config.eval_judge_model === preferredOllamaJudgeModel(config)
    && config.sut_backend === "platform"
  ) {
    return "banking_platform";
  }
  return "custom";
}

function presetRequiresApiKey(preset: PresetId): boolean {
  return preset === "api" || preset === "hybrid";
}

function configForPreset(
  preset: PresetId,
  config?: RuntimeConfig
): {
  eval_judge_backend: JudgeBackend;
  eval_judge_model: string;
  sut_backend: SutBackend;
  sut_model: string;
} {
  if (preset === "mock") {
    return {
      eval_judge_backend: "mock",
      eval_judge_model: "mock-judge",
      sut_backend: "mock",
      sut_model: "mock-sut"
    };
  }
  if (preset === "local_ollama") {
    return {
      eval_judge_backend: "ollama",
      eval_judge_model: preferredOllamaJudgeModel(config),
      sut_backend: "ollama",
      sut_model: preferredOllamaSutModel(config)
    };
  }
  if (preset === "api") {
    return {
      eval_judge_backend: "api",
      eval_judge_model: preferredOpenAIModel(config),
      sut_backend: "api",
      sut_model: preferredOpenAIModel(config)
    };
  }
  if (preset === "banking_platform") {
    return {
      eval_judge_backend: "ollama",
      eval_judge_model: preferredOllamaJudgeModel(config),
      sut_backend: "platform",
      sut_model: "banking-platform"
    };
  }
  return {
    eval_judge_backend: "api",
    eval_judge_model: preferredOpenAIModel(config),
    sut_backend: "ollama",
    sut_model: preferredOllamaSutModel(config)
  };
}

function presetDisabledMessage(preset: PresetId, config?: RuntimeConfig): string | null {
  if (presetRequiresApiKey(preset) && config?.has_openai_api_key === false) {
    return "API key required";
  }
  if (preset === "banking_platform" && config?.banking_platform_enabled === false) {
    return "Enable banking platform integration in .env";
  }
  return null;
}

function preferredOllamaJudgeModel(config?: RuntimeConfig): string {
  return config?.ollama_judge_model_options[0] ?? "qwen2.5:7b";
}

function preferredOllamaSutModel(config?: RuntimeConfig): string {
  return config?.ollama_sut_model_options[0] ?? "llama3.2";
}

function preferredOpenAIModel(config?: RuntimeConfig): string {
  return config?.openai_model_options[0] ?? "gpt-4o";
}
