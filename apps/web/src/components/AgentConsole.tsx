import { useState } from "react";
import type { AgentStep, AgentTrace } from "../types/domain";

const TOOL_LABELS: Record<string, string> = {
  search_local_packages: "BUSCAR PAQUETES",
  trigger_async_scraper: "SCRAPER ASÍNCRONO",
  prepare_package_sync: "PREPARAR RESERVA",
};

function toolLabel(tool: string): string {
  return TOOL_LABELS[tool] ?? tool.toUpperCase();
}

function pretty(value: string | Record<string, unknown> | null | undefined): string {
  if (value == null) return "∅";
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function StepBlock({ step }: { step: AgentStep }) {
  return (
    <div className="space-y-1.5 border-l-2 border-slate-700 pl-2">
      <p>
        <span className="text-slate-500">paso {step.step}</span>
      </p>

      <div>
        <p className="text-amber-400">
          Piensa <span className="text-slate-600">→</span>
        </p>
        <p className="whitespace-pre-wrap text-slate-400">{step.thought}</p>
      </div>

      {step.tool ? (
        <>
          <div>
            <p className="text-cyan-400">
              Actúa <span className="text-slate-600">→</span>{" "}
              <span className="font-bold text-white">{toolLabel(step.tool)}</span>
            </p>
            {step.tool_params && Object.keys(step.tool_params).length > 0 ? (
              <pre className="whitespace-pre-wrap rounded-md border border-slate-800 bg-black/40 p-2 text-cyan-200/80">
                {pretty(step.tool_params as Record<string, unknown>)}
              </pre>
            ) : null}
          </div>
          <div>
            <p className="text-emerald-400">Resultado</p>
            <pre className="whitespace-pre-wrap rounded-md border border-slate-800 bg-black/40 p-2 text-emerald-300">
              {pretty(step.tool_output)}
            </pre>
          </div>
        </>
      ) : null}
    </div>
  );
}

interface AgentConsoleProps {
  query: string;
  trace: AgentTrace | null;
  reply: string | null;
  loading: boolean;
  error: string | null;
}

export default function AgentConsole({
  query,
  trace,
  reply,
  loading,
  error,
}: AgentConsoleProps) {
  const [open, setOpen] = useState(true);

  const modeLabel =
    trace?.mode === "llm" ? `LLM ocupa el rol ${trace.model}` : "planner determinista (offline)";

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950 shadow-lg">
      <div className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
          <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
          <span className="ml-2 font-mono text-xs font-bold tracking-wider text-slate-300">
            AGENTE DE IA — CONSOLA ReAct ▼
          </span>
        </div>
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          className="rounded border border-slate-700 px-2 py-0.5 font-mono text-[11px] text-slate-300 hover:bg-slate-800"
        >
          {open ? "colapsar" : "expandir"}
        </button>
      </div>

      {open && (
        <div className="space-y-3 p-3 font-mono text-xs">
          {trace ? (
            <p className="text-slate-500">
              <span className="text-fuchsia-400">modo</span>
              <span className="text-slate-500"> → </span>
              <span className="text-slate-300">{modeLabel}</span>
            </p>
          ) : null}

          {query.trim() ? (
            <p className="text-slate-500">
              <span className="text-fuchsia-400">$</span> razonar{" "}
              <span className="text-slate-300">"{query.trim()}"</span>
            </p>
          ) : (
            <p className="text-slate-600">esperando mensaje para razonar…</p>
          )}

          {loading && <p className="animate-pulse text-fuchsia-400">▌razonando con herramientas…</p>}

          {error ? <p className="text-red-400">error: {error}</p> : null}

          {trace ? (
            <>
              <div className="space-y-3">
                {trace.steps.length === 0 ? (
                  <p className="text-slate-500">sin herramientas ejecutadas (diálogo directo)</p>
                ) : (
                  trace.steps.map((step) => <StepBlock key={step.step} step={step} />)
                )}
              </div>

              {reply ? (
                <div>
                  <p className="mb-1 text-fuchsia-400">Responde</p>
                  <p className="whitespace-pre-wrap text-slate-400">{reply}</p>
                </div>
              ) : null}
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}