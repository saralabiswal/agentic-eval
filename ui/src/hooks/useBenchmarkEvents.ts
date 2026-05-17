import { useEffect, useState } from "react";

export function useBenchmarkEvents(runId: string | null): string[] {
  const [events, setEvents] = useState<string[]>([]);

  useEffect(() => {
    if (!runId) {
      setEvents([]);
      return undefined;
    }
    setEvents([`benchmark_started {"run_id":"${runId}","timestamp":"${new Date().toISOString()}"}`]);
    const source = new EventSource(`/api/benchmark/events/${runId}`);

    // Keep the raw event name with the payload so the log renderer can turn
    // backend lifecycle events into documentation-friendly status messages.
    const appendEvent = (eventName: string) => (message: MessageEvent<string>) => {
      setEvents((current) => [...current, `${eventName} ${message.data}`]);
    };

    source.addEventListener("case_started", appendEvent("case_started"));
    source.addEventListener("sut_started", appendEvent("sut_started"));
    source.addEventListener("sut_completed", appendEvent("sut_completed"));
    source.addEventListener("evaluation_started", appendEvent("evaluation_started"));
    source.addEventListener("case_completed", appendEvent("case_completed"));
    source.addEventListener("benchmark_progress", appendEvent("benchmark_progress"));
    source.addEventListener("benchmark_failed", (message) => {
      appendEvent("benchmark_failed")(message);
      source.close();
    });
    source.addEventListener("benchmark_done", (message) => {
      appendEvent("benchmark_done")(message);
      source.close();
    });
    source.onerror = () => {
      setEvents((current) => [
        ...current,
        `stream_error {"timestamp":"${new Date().toISOString()}","message":"The live benchmark stream disconnected."}`
      ]);
      source.close();
    };
    return () => source.close();
  }, [runId]);

  return events;
}
