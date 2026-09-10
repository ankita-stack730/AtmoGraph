import { Link, useRouterState } from "@tanstack/react-router";
import {
  Activity,
  Boxes,
  BrainCircuit,
  LayoutDashboard,
  Network,
  Radar,
  Search,
  ServerCog,
  Waves,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { API_BASE_URL } from "@/api/client";
import { useHealth } from "./useHealth";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/network", label: "Network", icon: Network },
  { to: "/disruptions", label: "Disruptions", icon: Waves },
  { to: "/predictions", label: "Predictions", icon: BrainCircuit },
  { to: "/entities", label: "Entities", icon: Boxes },
  { to: "/system", label: "System Status", icon: ServerCog },
] as const;

function Dot({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
      <span
        className={cn(
          "size-2 rounded-full",
          ok ? "bg-risk-low shadow-[0_0_8px_currentColor]" : "bg-risk-high",
        )}
      />
      {label}
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { data } = useHealth();
  const live = data?.source === "live";
  const [query, setQuery] = useState("");

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar md:flex">
        <div className="flex items-center gap-2.5 border-b border-sidebar-border px-5 py-4">
          <Radar className="size-5 text-primary" />
          <div>
            <div className="font-mono text-sm font-semibold tracking-tight">ATMOgraph</div>
            <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Ripple Intelligence
            </div>
          </div>
        </div>

        <nav className="flex-1 space-y-0.5 p-3">
          {NAV.map((item) => {
            const active = item.to === "/" ? pathname === "/" : pathname.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                  active
                    ? "bg-primary/10 text-primary ring-1 ring-primary/25"
                    : "text-muted-foreground hover:bg-sidebar-accent hover:text-foreground",
                )}
              >
                <item.icon className="size-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="space-y-2 border-t border-sidebar-border px-5 py-4">
          <Dot ok={live} label="API" />
          <Dot ok={live && data?.data.neo4j !== "offline"} label="Neo4j" />
          <Dot ok label="Env" />
          <div className="truncate pt-1 font-mono text-[10px] text-muted-foreground/70">
            {API_BASE_URL}
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex items-center gap-4 border-b border-border bg-background/85 px-4 py-3 backdrop-blur md:px-6">
          <div className="relative w-full max-w-md">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search nodes, entities, routes…"
              className="w-full rounded-md border border-border bg-card py-2 pl-9 pr-3 font-mono text-xs text-foreground outline-none placeholder:text-muted-foreground focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
            />
            {query.trim() && (
              <Link
                to="/entities"
                search={{ q: query.trim() }}
                onClick={() => setQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded border border-primary/40 bg-primary/10 px-2 py-0.5 font-mono text-[10px] uppercase text-primary"
              >
                Go
              </Link>
            )}
          </div>

          <div className="ml-auto flex items-center gap-3">
            <ConnectionBadge live={live} />
            <Activity className="size-4 text-primary/70" />
          </div>
        </header>

        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}

export function ConnectionBadge({ live }: { live: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 font-mono text-[10px] uppercase tracking-widest",
        live
          ? "border-risk-low/40 bg-risk-low/10 text-risk-low"
          : "border-primary/40 bg-primary/10 text-primary",
      )}
    >
      <span className="size-1.5 rounded-full bg-current" />
      {live ? "Live FastAPI" : "Demo / Baseline Mode"}
    </span>
  );
}
