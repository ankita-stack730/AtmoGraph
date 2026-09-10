import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => api.health(),
    retry: false,
    refetchInterval: 20000,
    staleTime: 10000,
  });
}

export function useGraph() {
  return useQuery({
    queryKey: ["graph"],
    queryFn: () => api.graph(),
    retry: false,
    staleTime: 60000,
  });
}
