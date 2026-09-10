import { useSyncExternalStore } from "react";
import type { DisruptionResponse } from "@/api/types";
import type { SourceMode } from "@/api/client";

export interface AtmoState {
  disruption: DisruptionResponse | null;
  disruptionText: string;
  disruptionSource: SourceMode | null;
  focusNodeId: string | null;
  analyzing: boolean;
}

let state: AtmoState = {
  disruption: null,
  disruptionText: "",
  disruptionSource: null,
  focusNodeId: null,
  analyzing: false,
};

const listeners = new Set<() => void>();

export function setAtmoState(patch: Partial<AtmoState>) {
  state = { ...state, ...patch };
  listeners.forEach((l) => l());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot() {
  return state;
}

export function useAtmoStore(): AtmoState {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
