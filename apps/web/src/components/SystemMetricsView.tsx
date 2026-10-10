import { useEffect, useState } from "react";
import { searchApi } from "../lib/api";
import type { MetricsSummary } from "../types/domain";

const ENTITY_LABELS: Record<string, string> = {
  destination: "Destino",
  category: "Categoría",
  budget: "Presupuesto",
  travelers: "Viajeros",
  start_date: "Fecha inicio",
  duration: "Duración",
};

function percent(value: number | undefined): string {
  return `${((value ?? 0) * 100).toFixed(0)}%`;
}

function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: number;
  hint: string;
}) {
  return (
    <div>
      <div className="text-xl font-bold text-brand-600">{percent(value)}</div>
      <div className="mt-1 text-xs font-semibold text-slate-700">{label}</div>
      <div className="text-[11px] leading-tight text-slate-400">{hint}</div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-brand-600"
          style={{ width: percent(value) }}
        />
      </div>
    </div>
  );
}

export default function SystemMetricsView() {
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    searchApi
      .metricsSummary()
      .then((data) => {
        if (active) setSummary(data);
      })
      .catch((err: Error) => {
        if (active) setError(err.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-sm text-slate-500">Cargando métricas de evaluación…</p>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-sm text-red-600">{error ?? "Métricas no disponibles"}</p>
      </div>
    );
  }

  const { asistente, buscador, entidades, datos, agente } = summary;

  const modeLabel =
    agente.mode === "llm" ? "LLM (Tool Calling)" : "planner determinista (offline)";

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-base font-semibold text-slate-900">
          Evaluación del Sistema
        </h2>
        <span className="shrink-0 text-xs text-slate-400">
          {datos.total_fusion} paquetes
        </span>
      </div>
      <p className="mt-1 text-xs text-slate-500">
        Asistente, buscador y agente (ReAct + Tool Calling) sobre un dataset
        sintético de {datos.interacciones_sinteticas} interacciones · embeddings:{" "}
        {datos.ml_enabled ? "sentence-transformers" : "tf-idf + svd"}
      </p>

      <div className="mt-4 grid grid-cols-3 gap-3">
        <MetricCard
          label="Macro-F1 intenciones"
          value={asistente.macro_f1_intenciones}
          hint="Clasificación"
        />
        <MetricCard
          label="Tasa de éxito"
          value={asistente.booking_success_rate}
          hint="Reserva top-1"
        />
        <MetricCard label="nDCG@5" value={buscador.ndcg_at_5} hint="Relevancia" />
      </div>

      <h3 className="mt-5 text-sm font-semibold text-slate-700">
        Agente de IA
      </h3>
      <div className="mt-2 grid grid-cols-2 gap-3">
        <MetricCard
          label="Selección de herramienta"
          value={agente.tool_selection_accuracy}
          hint="Tool Selection Accuracy"
        />
        <MetricCard
          label="Tasa de éxito"
          value={agente.task_success_rate}
          hint="Task Success Rate"
        />
      </div>
      <p className="mt-2 text-[11px] text-slate-400">
        Herramientas: buscar · scraper · preparar reserva · modo: {modeLabel}
      </p>

      <div>
        <h3 className="mt-5 text-sm font-semibold text-slate-700">
          F1 exacto por entidad
        </h3>
        <ul className="mt-2 space-y-2">
          {Object.entries(entidades).map(([key, value]) => (
            <li key={key} className="flex items-center gap-3">
              <span className="w-24 shrink-0 text-xs text-slate-600">
                {ENTITY_LABELS[key] ?? key}
              </span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full rounded-full bg-cyan-500"
                  style={{ width: percent(value) }}
                />
              </div>
              <span className="w-10 text-right font-mono text-xs text-slate-600">
                {percent(value)}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}