import { useState } from "react";
import type { NlpDebug } from "../types/domain";

const INTENT_LABELS: Record<string, string> = {
  saludo: "Saludo",
  despedida: "Despedida",
  buscar_paquetes: "Buscar paquetes",
  reservar_paquete: "Reservar paquete",
  presupuesto: "Presupuesto",
  recomendar: "Recomendar",
};

function intentLabel(intent: string): string {
  return INTENT_LABELS[intent] ?? intent;
}

function percent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

interface NlpInspectorProps {
  query: string;
  debug: NlpDebug | null;
  reply: string | null;
  loading: boolean;
  error: string | null;
}

export default function NlpInspector({
  query,
  debug,
  reply,
  loading,
  error,
}: NlpInspectorProps) {
  const [open, setOpen] = useState(true);

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950 shadow-lg">
      <div className="flex items-center justify-between border-b border-slate-800 px-3 py-2">
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
          <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
          <span className="ml-2 font-mono text-xs font-bold tracking-wider text-slate-300">
            NLP DEBUG ▼
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
          {query.trim() ? (
            <p className="text-slate-500">
              <span className="text-emerald-400">$</span> analizar{" "}
              <span className="text-slate-300">"{query.trim()}"</span>
            </p>
          ) : (
            <p className="text-slate-600">esperando mensaje para analizar…</p>
          )}

          {loading && (
            <p className="animate-pulse text-cyan-400">▌ejecutando pipeline NLP…</p>
          )}

          {error ? <p className="text-red-400">error: {error}</p> : null}

          {debug ? (
            <>
              <div className="space-y-1.5">
                <p>
                  <span className="text-cyan-400">intención</span>
                  <span className="text-slate-500"> → </span>
                  <span className="font-bold text-white">{intentLabel(debug.intent)}</span>
                  <span className="ml-2 text-slate-500">({debug.intent})</span>
                </p>
                <div className="flex items-center gap-2">
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-800">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-cyan-400"
                      style={{ width: percent(debug.confidence) }}
                    />
                  </div>
                  <span className="text-emerald-400">{percent(debug.confidence)}</span>
                </div>
                <p className="text-slate-500">modelo: {debug.model}</p>
              </div>

              <div>
                <p className="mb-1 text-cyan-400">entidades</p>
                <pre className="whitespace-pre-wrap rounded-md border border-slate-800 bg-black/40 p-2 text-emerald-300">
                  {JSON.stringify(debug.entities, null, 2)}
                </pre>
              </div>

              <div>
                <p className="mb-1 text-cyan-400">ranking de intenciones</p>
                <ul className="space-y-1.5">
                  {Object.entries(debug.scores).map(([key, value]) => (
                    <li key={key} className="flex items-center gap-2">
                      <span className="w-32 shrink-0 truncate text-slate-400">
                        {intentLabel(key)}
                      </span>
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full bg-cyan-400/70"
                          style={{ width: `${Math.round(value * 100)}%` }}
                        />
                      </div>
                      <span className="w-11 text-right text-slate-500">{percent(value)}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {reply ? (
                <div>
                  <p className="mb-1 text-cyan-400">respuesta</p>
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