import { create } from "zustand";

type EvalState = {
  runId: string | null;
  setRunId: (runId: string | null) => void;
};

export const useEvalStore = create<EvalState>((set) => ({
  runId: null,
  setRunId: (runId) => set({ runId })
}));
