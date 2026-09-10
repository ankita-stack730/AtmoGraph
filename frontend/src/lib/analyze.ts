import { api } from "@/api/client";
import { setAtmoState } from "./store";

export async function runDisruptionAnalysis(text: string) {
  const clean = text.trim();
  if (!clean) return null;
  setAtmoState({ analyzing: true, disruptionText: clean });
  const res = await api.disruptionAnalyze(clean);
  setAtmoState({
    analyzing: false,
    disruption: res.data,
    disruptionSource: res.source,
    focusNodeId: res.data.matched_source_nodes[0] ?? null,
  });
  return res;
}
