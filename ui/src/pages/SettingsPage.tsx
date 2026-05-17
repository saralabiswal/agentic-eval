import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import { getConfig, testConnection, updateRuntimeConfig } from "../api/client";
import type { JudgeBackend, ModelBackend, RuntimeConfig, SutBackend } from "../api/types";

type ConfigRole = "judge" | "sut";

const judgeBackendOptions: ModelBackend[] = ["mock", "ollama", "api"];
const sutBackendOptions: ModelBackend[] = ["mock", "ollama", "api", "platform"];

export function SettingsPage(): JSX.Element {
  const queryClient = useQueryClient();
  const { data: config } = useQuery({ queryKey: ["config"], queryFn: getConfig });
  const [judgeBackend, setJudgeBackend] = useState<ModelBackend>("mock");
  const [judgeModel, setJudgeModel] = useState("mock-judge");
  const [sutBackend, setSutBackend] = useState<ModelBackend>("mock");
  const [sutModel, setSutModel] = useState("mock-sut");
  const testMutation = useMutation({ mutationFn: testConnection });
  const saveMutation = useMutation({
    mutationFn: updateRuntimeConfig,
    onSuccess: (updated) => {
      queryClient.setQueryData(["config"], updated);
    }
  });

  useEffect(() => {
    if (!config) {
      return;
    }
    setJudgeBackend(config.eval_judge_backend);
    setJudgeModel(config.eval_judge_model);
    setSutBackend(config.sut_backend);
    setSutModel(config.sut_model);
  }, [config]);

  const localPairStatus = useMemo(
    () => localPairMessage(judgeBackend, judgeModel, sutBackend, sutModel),
    [judgeBackend, judgeModel, sutBackend, sutModel]
  );

  return (
    <section>
      <div className="page-head">
        <div>
          <h1 className="page-title">Settings</h1>
          <div className="page-subtitle">Runtime configuration · loaded from FastAPI</div>
        </div>
      </div>

      <SettingsSection
        body={
          <BackendSelector
            backend={judgeBackend}
            config={config}
            model={judgeModel}
            onBackendChange={(backend) =>
              setDraftBackend("judge", backend, config, setJudgeBackend, setJudgeModel)
            }
            onModelChange={setJudgeModel}
            onSave={() =>
              saveMutation.mutate({
                eval_judge_backend: judgeBackend as JudgeBackend,
                eval_judge_model: effectiveModel("judge", judgeBackend, judgeModel)
              })
            }
            onTest={(apiKey) =>
              testMutation.mutate({
                target: "judge",
                backend: judgeBackend,
                model: judgeModel,
                api_key: apiKey || undefined
              })
            }
            role="judge"
            saveMessage={saveMutation.isPending ? "Saving..." : undefined}
            testMessage={testMutation.data?.target === "judge" ? testMutation.data.message : undefined}
          />
        }
        subtitle="Evaluates agent outputs. Should differ from the system under test to avoid self-evaluation bias."
        title="Judge Model"
      />
      <SettingsSection
        body={
          <BackendSelector
            backend={sutBackend}
            config={config}
            model={sutModel}
            onBackendChange={(backend) =>
              setDraftBackend("sut", backend, config, setSutBackend, setSutModel)
            }
            onModelChange={setSutModel}
            onSave={() =>
              saveMutation.mutate({
                sut_backend: sutBackend as SutBackend,
                sut_model: effectiveModel("sut", sutBackend, sutModel)
              })
            }
            onTest={(apiKey) =>
              testMutation.mutate({
                target: "sut",
                backend: sutBackend,
                model: sutModel,
                api_key: apiKey || undefined
              })
            }
            role="sut"
            options={sutBackendOptions}
            saveMessage={saveMutation.isPending ? "Saving..." : undefined}
            testMessage={testMutation.data?.target === "sut" ? testMutation.data.message : undefined}
          />
        }
        subtitle="The model being evaluated. It should differ from the judge."
        title="System Under Test"
      />
      {localPairStatus ? <StatusBox tone={localPairStatus.tone} text={localPairStatus.text} /> : null}
      <SettingsSection
        body={<Thresholds thresholds={config?.thresholds ?? {}} />}
        subtitle="Applied on the next benchmark run."
        title="Evaluation Thresholds"
      />
      <SettingsSection
        body={
          <div>
            <div className="field-label">Platform Runner</div>
            <div className="segmented" style={{ marginBottom: 10 }}>
              <button
                className={`segment ${config?.banking_platform_enabled ? "active" : ""}`}
                type="button"
              >
                {config?.banking_platform_enabled ? "Enabled" : "Disabled"}
              </button>
              <button
                className="segment"
                onClick={() => testMutation.mutate({ target: "platform", backend: "platform" })}
                type="button"
              >
                Test Connection
              </button>
            </div>
            <div className="field-label">Platform URL</div>
            <input className="field" readOnly value={config?.banking_platform_url ?? ""} />
            <div className="kpi-detail" style={{ marginTop: 8 }}>
              {testMutation.data?.target === "platform"
                ? testMutation.data.message
                : "Disabled by default. Enable it in .env before using the Banking Platform preset."}
            </div>
          </div>
        }
        subtitle="Connect to banking-agentic-ai-platform for real multi-layer evaluation."
        title="Banking Platform Integration"
      />
    </section>
  );
}

function SettingsSection({
  body,
  subtitle,
  title
}: {
  body: JSX.Element;
  subtitle: string;
  title: string;
}): JSX.Element {
  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <div className="panel-head">
        <div>
          <div className="panel-title">{title}</div>
          <div className="tiny">{subtitle}</div>
        </div>
      </div>
      <div className="panel-body">{body}</div>
    </div>
  );
}

function BackendSelector({
  backend,
  config,
  model,
  onBackendChange,
  onModelChange,
  onSave,
  onTest,
  options = judgeBackendOptions,
  role,
  saveMessage,
  testMessage
}: {
  backend: ModelBackend;
  config?: RuntimeConfig;
  model: string;
  onBackendChange: (backend: ModelBackend) => void;
  onModelChange: (value: string) => void;
  onSave: () => void;
  onTest: (apiKey: string) => void;
  options?: ModelBackend[];
  role: ConfigRole;
  saveMessage?: string;
  testMessage?: string;
}): JSX.Element {
  const [apiKeyMode, setApiKeyMode] = useState(config?.has_openai_api_key ? "configured" : "temporary");
  const [apiKey, setApiKey] = useState("");
  const modelOptions = modelsFor(role, backend, config);

  useEffect(() => {
    setApiKeyMode(config?.has_openai_api_key ? "configured" : "temporary");
  }, [config?.has_openai_api_key]);

  return (
    <>
      <div className="field-label">Backend Type</div>
      <div className="segmented" style={{ marginBottom: 10 }}>
        {options.map((option) => (
          <button
            className={`segment ${backend === option ? "active" : ""}`}
            key={option}
            onClick={() => onBackendChange(option)}
            type="button"
          >
            {backend === option ? "● " : ""}
            {option.charAt(0).toUpperCase() + option.slice(1)}
          </button>
        ))}
      </div>

      {backend === "mock" || backend === "platform" ? (
        <div style={{ marginBottom: 10 }}>
          <div className="field-label">{backend === "platform" ? "Platform Adapter" : "Fixture Model"}</div>
          <input className="field" readOnly value={effectiveModel(role, backend, model)} />
        </div>
      ) : (
        <div style={{ display: "grid", gap: 8, gridTemplateColumns: backend === "api" ? "1fr 1fr" : "1fr", marginBottom: 10 }}>
          <div>
            <div className="field-label">{backend === "ollama" ? "Ollama Model" : "OpenAI Model"}</div>
            <select
              className="field"
              onChange={(event) => onModelChange(event.target.value)}
              value={model}
            >
              {[...new Set([model, ...modelOptions])].map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
          {backend === "api" ? (
            <div>
              <div className="field-label">OpenAI API Key</div>
              <select
                className="field"
                onChange={(event) => setApiKeyMode(event.target.value)}
                value={apiKeyMode}
              >
                <option disabled={!config?.has_openai_api_key} value="configured">
                  {config?.has_openai_api_key ? "Configured server key" : "No configured server key"}
                </option>
                <option value="temporary">Temporary test key</option>
              </select>
            </div>
          ) : null}
        </div>
      )}

      {backend === "api" && apiKeyMode === "temporary" ? (
        <div style={{ marginBottom: 10 }}>
          <div className="field-label">Temporary Key Value</div>
          <input
            className="field"
            onChange={(event) => setApiKey(event.target.value)}
            placeholder="sk-... (never echoed back)"
            type="password"
            value={apiKey}
          />
        </div>
      ) : null}

      <div className="segmented" style={{ marginBottom: 10 }}>
        <button className="segment" onClick={() => onTest(apiKeyMode === "temporary" ? apiKey : "")} type="button">
          Test {backend}
        </button>
        <button className="segment active" onClick={onSave} type="button">
          Save {role === "judge" ? "Judge" : "System"}
        </button>
      </div>
      <StatusBox
        tone={backend === "mock" ? "success" : "neutral"}
        text={testMessage ?? saveMessage ?? "Effective configuration is loaded from the API."}
      />
    </>
  );
}

function Thresholds({ thresholds }: { thresholds: Record<string, number> }): JSX.Element {
  const rows = [
    ["Faithfulness", "var(--faith)", thresholds.faithfulness ?? 0.85],
    ["Answer Relevance", "var(--rel)", thresholds.answer_relevance ?? 0.8],
    ["Context Precision", "var(--prec)", thresholds.context_precision ?? 0.7],
    ["Consistency", "var(--con)", thresholds.consistency ?? 0.9]
  ];
  return (
    <>
      {rows.map(([label, color, value]) => (
        <div key={String(label)} style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
            <span style={{ color: String(color), fontSize: 13, fontWeight: 600 }}>{label}</span>
            <span className="mono" style={{ color: String(color), fontSize: 12, fontWeight: 700 }}>
              {Number(value).toFixed(2)}
            </span>
          </div>
          <div className="bar-track" style={{ width: "100%" }}>
            <div className="bar-fill" style={{ background: String(color), width: `${Number(value) * 100}%` }} />
          </div>
        </div>
      ))}
      <div className="field-label">Consistency Runs</div>
      <span className="score warn">{thresholds.consistency_runs ?? 5}</span>
    </>
  );
}

function StatusBox({ text, tone }: { text: string; tone: "neutral" | "success" | "warn" }): JSX.Element {
  const palette = {
    neutral: ["var(--surface)", "var(--border)", "var(--mid)"],
    success: ["rgba(16,185,129,.06)", "rgba(16,185,129,.2)", "var(--con)"],
    warn: ["rgba(251,191,36,.08)", "rgba(251,191,36,.26)", "var(--warn)"]
  }[tone];
  return (
    <div
      className="card"
      style={{
        background: palette[0],
        borderColor: palette[1],
        color: palette[2],
        fontFamily: "var(--mono)",
        fontSize: 12,
        marginBottom: 12,
        padding: "8px 11px"
      }}
    >
      {text}
    </div>
  );
}

function modelsFor(role: ConfigRole, backend: ModelBackend, config?: RuntimeConfig): string[] {
  if (backend === "platform") {
    return ["banking-platform"];
  }
  if (backend === "api") {
    return config?.openai_model_options ?? ["gpt-4o", "gpt-4o-mini"];
  }
  if (backend === "ollama") {
    return role === "judge"
      ? config?.ollama_judge_model_options ?? ["qwen2.5:7b", "mistral-nemo:12b", "llama3.2"]
      : config?.ollama_sut_model_options ?? ["llama3.2", "mistral", "phi3.5"];
  }
  return [effectiveModel(role, backend, "")];
}

function effectiveModel(role: ConfigRole, backend: ModelBackend, model: string): string {
  if (backend === "mock") {
    return role === "judge" ? "mock-judge" : "mock-sut";
  }
  if (backend === "platform") {
    return "banking-platform";
  }
  return model;
}

function setDraftBackend(
  role: ConfigRole,
  backend: ModelBackend,
  config: RuntimeConfig | undefined,
  setBackend: (backend: ModelBackend) => void,
  setModel: (model: string) => void
): void {
  setBackend(backend);
  setModel(modelsFor(role, backend, config)[0]);
}

function localPairMessage(
  judgeBackend: ModelBackend,
  judgeModel: string,
  systemBackend: ModelBackend,
  systemModel: string
): { text: string; tone: "neutral" | "success" | "warn" } | null {
  if (judgeBackend !== "ollama" || systemBackend !== "ollama") {
    return null;
  }
  if (judgeModel === systemModel) {
    return {
      text: "Judge and system use the same Ollama model. Choose different models for serious evaluation.",
      tone: "warn"
    };
  }
  return {
    text: "Local-only Ollama evaluation selected. Useful for development; lower confidence than a stronger external judge.",
    tone: "neutral"
  };
}
