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
  if (normalized === "mock-sut") return "Mock SUT";
  return value || "Not set";
}
