import { modelDisplayName } from "../utils/modelLabels";

type LiveEvalLogProps = {
  events: string[];
};

type ParsedLogEvent = {
  name: string;
  text: string;
  tone: "info" | "running" | "success" | "fail";
  time: string;
};

export function LiveEvalLog({ events }: LiveEvalLogProps): JSX.Element {
  const newestFirst = [...events].reverse();

  return (
    <div className="log-box">
      {events.length === 0 ? (
        <div className="tiny" style={{ padding: "40px 0", textAlign: "center" }}>
          Configure and click Run Benchmark.
        </div>
      ) : null}
      {newestFirst.map((event, index) => {
        const parsed = parseLogEvent(event);
        return (
        <div className="log-line" key={`${event}-${index}`}>
          <span className="log-time">{parsed.time}</span>
          <span
            className="log-tag"
            style={{
              background: parsed.tone === "success"
                ? "rgba(16,185,129,.12)"
                : parsed.tone === "fail"
                  ? "rgba(255,71,87,.12)"
                  : parsed.tone === "running"
                    ? "rgba(251,191,36,.12)"
                    : "rgba(59,130,246,.12)",
              borderColor: parsed.tone === "success"
                ? "var(--con)"
                : parsed.tone === "fail"
                  ? "var(--fail)"
                  : parsed.tone === "running"
                    ? "var(--prec)"
                    : "var(--blue)",
              color: parsed.tone === "success"
                ? "var(--con)"
                : parsed.tone === "fail"
                  ? "var(--fail)"
                  : parsed.tone === "running"
                    ? "var(--prec)"
                    : "var(--blue)"
            }}
          >
            {labelFor(parsed.name)}
          </span>
          <span className="log-message">{parsed.text}</span>
        </div>
        );
      })}
    </div>
  );
}

function parseLogEvent(event: string): ParsedLogEvent {
  const [name, ...rawPayload] = event.split(" ");
  const payload = rawPayload.join(" ");
  const parsed = parsePayload(payload);
  const data = parsed.data ?? parsed;
  const timestamp = typeof parsed.timestamp === "string" ? new Date(parsed.timestamp) : new Date();

  // Each branch below maps one backend event into user-facing language for
  // generated UI documentation and for the live execution log.
  if (name === "benchmark_started") {
    return { name, text: `Started run ${String(parsed.run_id ?? "")}.`, time: timeLabel(timestamp), tone: "info" };
  }
  if (name === "case_started") {
    return {
      name,
      text: `Case ${String(data.case_id ?? "")} started: ${String(data.description ?? "")}`,
      time: timeLabel(timestamp),
      tone: "info"
    };
  }
  if (name === "sut_started") {
    return {
      name,
      text: `Calling ${String(data.backend ?? "SUT")} model ${String(data.model ?? "")} for ${String(data.case_id ?? "")}.`,
      time: timeLabel(timestamp),
      tone: "running"
    };
  }
  if (name === "sut_completed") {
    return {
      name,
      text: `SUT response received for ${String(data.case_id ?? "")} in ${String(data.latency_ms ?? "?")} ms.`,
      time: timeLabel(timestamp),
      tone: "success"
    };
  }
  if (name === "evaluation_started") {
    return {
      name,
      text: `Scoring ${String(data.case_id ?? "")} with ${modelDisplayName(String(data.judge_model ?? ""))}.`,
      time: timeLabel(timestamp),
      tone: "running"
    };
  }
  if (name === "case_completed") {
    return {
      name,
      text: `Case ${String(data.case_id ?? "")} completed with overall score ${formatScore(data.overall_score)}.`,
      time: timeLabel(timestamp),
      tone: data.passed === false ? "fail" : "success"
    };
  }
  if (name === "benchmark_progress") {
    return {
      name,
      text: `Still running after ${String(data.elapsed_seconds ?? "?")} seconds.`,
      time: timeLabel(timestamp),
      tone: "running"
    };
  }
  if (name === "benchmark_failed") {
    return {
      name,
      text: `Benchmark failed: ${String(data.message ?? "Unknown error")}`,
      time: timeLabel(timestamp),
      tone: "fail"
    };
  }
  if (name === "benchmark_done") {
    return {
      name,
      text: `Benchmark finished: ${String(data.passed ?? 0)} passed, ${String(data.failed ?? 0)} failed.`,
      time: timeLabel(timestamp),
      tone: "success"
    };
  }
  if (name === "stream_error") {
    return {
      name,
      text: String(parsed.message ?? payload),
      time: timeLabel(timestamp),
      tone: "fail"
    };
  }
  return { name, text: event, time: timeLabel(timestamp), tone: "info" };
}

function parsePayload(payload: string): Record<string, unknown> & { data?: Record<string, unknown> } {
  try {
    return JSON.parse(payload) as Record<string, unknown> & { data?: Record<string, unknown> };
  } catch {
    return {};
  }
}

function labelFor(name: string): string {
  if (name === "benchmark_done") return "DONE";
  if (name === "benchmark_failed" || name === "stream_error") return "FAIL";
  if (name === "benchmark_progress") return "RUN";
  if (name === "sut_started" || name === "sut_completed") return "SUT";
  if (name === "evaluation_started") return "JUDGE";
  if (name === "case_completed") return "CASE";
  return "RUN";
}

function formatScore(value: unknown): string {
  return typeof value === "number" ? value.toFixed(2) : "n/a";
}

function timeLabel(value: Date): string {
  return value.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
