/**
 * Converts provider model IDs into names that are understandable in UI docs.
 */
export function modelDisplayName(model: string | null | undefined): string {
  const value = model ?? "";
  const normalized = value.toLowerCase();
  if (normalized.startsWith("qwen2.5:7b")) return "Qwen 2.5 7B";
  if (normalized.startsWith("qwen")) return "Qwen";
  if (normalized.startsWith("llama3.2")) return "Llama 3.2";
  if (normalized.startsWith("llama3.1")) return "Llama 3.1";
  if (normalized.startsWith("llama3")) return "Llama 3";
  if (normalized.startsWith("mistral-nemo:12b")) return "Mistral Nemo 12B";
  if (normalized.startsWith("mistral")) return "Mistral";
  if (normalized.startsWith("phi3.5")) return "Phi 3.5";
  if (normalized === "mock-judge") return "Mock Judge";
  if (normalized === "mock-sut") return "Mock System";
  if (normalized === "banking-platform") return "Banking Platform";
  return value || "Not set";
}

/**
 * Converts backend identifiers into labels for dashboards and tables.
 */
export function backendDisplayName(backend: string | null | undefined): string {
  if (backend === "mock") return "Mock";
  if (backend === "ollama") return "Ollama";
  if (backend === "api") return "API";
  if (backend === "platform") return "Banking Platform";
  return backend || "Not set";
}

/**
 * Converts API/data identifiers into readable labels without changing the data.
 */
export function readableLabel(value: string | null | undefined): string {
  if (!value) {
    return "Not set";
  }
  return value
    .replace(/[_-]+/g, " ")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}
