export type ModelBackend = "mock" | "ollama" | "api";

export interface TestCaseInput {
  customer_profile: Record<string, unknown>;
  retrieved_policy_chunks: Array<Record<string, unknown>>;
  scenario_context: string;
}

export interface TestCaseExpected {
  risk_level: string | null;
  should_reference_policy: boolean;
  key_signals: string[];
  should_not_claim: string[];
  expected_action_type: string | null;
}

export interface EvaluationCriteria {
  faithfulness_threshold: number;
  answer_relevance_threshold: number;
  context_precision_threshold: number;
  consistency_threshold: number;
  consistency_runs: number;
  max_latency_ms: number;
}

export interface TestCase {
  case_id: string;
  scenario: string;
  customer_id: string;
  description: string;
  input: TestCaseInput;
  expected: TestCaseExpected;
  evaluation_criteria: EvaluationCriteria;
}

export interface DimensionScore {
  score: number;
  passed: boolean;
  threshold: number;
  reasoning: string;
  evidence: string[];
  run_outputs: string[];
  similarity_matrix: number[][];
}

export interface EvalResult {
  case_id: string;
  run_id: string;
  model_backend: ModelBackend;
  model_name: string;
  timestamp: string;
  faithfulness: DimensionScore;
  answer_relevance: DimensionScore;
  context_precision: DimensionScore;
  consistency: DimensionScore;
  latency_ms: number;
  overall_score: number;
  passed: boolean;
  hallucinations: string[];
  agent_output: string;
  raw_response: Record<string, unknown>;
}

export interface BenchmarkSummary {
  avg_faithfulness: number;
  avg_answer_relevance: number;
  avg_context_precision: number;
  avg_consistency: number;
  avg_latency_ms: number;
  pass_rate: number;
  worst_case: string;
  hallucination_count: number;
}

export interface BenchmarkReport {
  run_id: string;
  run_timestamp: string;
  model_backend: ModelBackend;
  total_cases: number;
  passed: number;
  failed: number;
  results: EvalResult[];
  summary: BenchmarkSummary;
}

export interface BenchmarkRunSummary {
  run_id: string;
  run_timestamp: string;
  model_backend: ModelBackend;
  total_cases: number;
  passed: number;
  failed: number;
  avg_score: number;
  avg_faithfulness: number;
  avg_answer_relevance: number;
  avg_context_precision: number;
  avg_consistency: number;
  avg_latency_ms: number;
  pass_rate: number;
  hallucination_count: number;
}

export interface RuntimeConfig {
  eval_judge_backend: ModelBackend;
  eval_judge_model: string;
  sut_backend: ModelBackend;
  sut_model: string;
  ollama_base_url: string;
  banking_platform_enabled: boolean;
  banking_platform_url: string;
  thresholds: Record<string, number>;
  has_openai_api_key: boolean;
  openai_model_options: string[];
  ollama_judge_model_options: string[];
  ollama_sut_model_options: string[];
}

export interface ConnectionTestResponse {
  ok: boolean;
  target: string;
  backend: string;
  message: string;
}
