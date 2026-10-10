import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AgentConsole from "../components/AgentConsole";
import NlpInspector from "../components/NlpInspector";
import ScrapePanel from "../components/ScrapePanel";
import SystemMetricsView from "../components/SystemMetricsView";
import { searchApi } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useSearchSession } from "../lib/searchSessionContext";

const SOURCE_LABELS: Record<string, string> = {
  catalogo: "Catálogo",
  sintetico: "Sintético",
  external: "Web",
};

const SOURCE_BADGE: Record<string, string> = {
  catalogo: "bg-slate-100 text-slate-600",
  sintetico: "bg-purple-100 text-purple-700",
  external: "bg-sky-100 text-sky-700",
};

export default function SearchPage() {
  const { getAccessToken } = useAuth();
  const {
    query,
    suggestions,
    results,
    searched,
    nlpDebug,
    nlpReply,
    analyzedQuery,
    agentTrace,
    agentReply,
    setQuery,
    setSuggestions,
    setResults,
    setSearched,
    setNlpDebug,
    setNlpReply,
    setAnalyzedQuery,
    setAgentTrace,
    setAgentReply,
  } = useSearchSession();

  const [nlpLoading, setNlpLoading] = useState(false);
  const [nlpError, setNlpError] = useState<string | null>(null);

  const handleSearch = useCallback(
    async (value: string) => {
      const token = getAccessToken();
      const [sugg, semantic] = await Promise.all([
        searchApi.search(value, token),
        searchApi.searchSemantic(value, 10, token),
      ]);
      setResults(semantic.packages);
      setSuggestions(sugg.suggestions);
      setSearched(true);
    },
    [getAccessToken, setResults, setSuggestions, setSearched],
  );

  const runChat = useCallback(
    async (value: string) => {
      setNlpLoading(true);
      setNlpError(null);
      try {
        const data = await searchApi.chat(value, getAccessToken());
        setNlpDebug(data.nlp_debug ?? null);
        setNlpReply(data.message);
        setAgentTrace(data.agent_trace ?? null);
        setAgentReply(data.message);
        setAnalyzedQuery(value);
      } catch (err) {
        setNlpError(err instanceof Error ? err.message : "Error al analizar el mensaje");
        setNlpDebug(null);
        setNlpReply(null);
        setAgentTrace(null);
        setAgentReply(null);
        setAnalyzedQuery("");
      } finally {
        setNlpLoading(false);
      }
    },
    [getAccessToken, setAgentReply, setAgentTrace, setAnalyzedQuery, setNlpDebug, setNlpReply],
  );

  useEffect(() => {
    if (!query.trim()) return;
    if (analyzedQuery === query && (nlpDebug || agentTrace)) return;
    const timer = setTimeout(() => {
      void runChat(query);
    }, 500);
    return () => clearTimeout(timer);
  }, [query, analyzedQuery, nlpDebug, agentTrace, runChat]);

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_400px]">
      <section>
        <h1 className="text-2xl font-semibold">Buscador avanzado</h1>

        <form
          className="mt-6 flex gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            void handleSearch(query);
            void runChat(query);
          }}
        >
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Ej: playa, aventura, fin de semana, Caribe..."
            className="flex-1 rounded-md border border-slate-300 px-4 py-2 focus:border-brand-500 focus:outline-none"
          />
          <button
            type="submit"
            className="rounded-md bg-brand-600 px-5 py-2 font-medium text-white hover:bg-brand-700"
          >
            Buscar
          </button>
        </form>

        {suggestions.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => {
                  setQuery(s);
                  void handleSearch(s);
                }}
                className="rounded-full bg-brand-100 px-3 py-1 text-sm text-brand-800 hover:bg-brand-200"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {searched && results.length === 0 && (
          <p className="mt-8 text-slate-500">
            No se encontraron resultados para "{query}".
          </p>
        )}

        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {results.map((pkg) => (
            <Link
              key={pkg.id}
              to={`/paquetes/${pkg.id}`}
              state={{ pkg }}
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="text-xs font-medium uppercase tracking-wide text-brand-600">
                  {pkg.destination}, {pkg.country}
                </div>
                <span
                  className={
                    "shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide " +
                    (SOURCE_BADGE[pkg.source] ?? "bg-slate-100 text-slate-600")
                  }
                >
                  {SOURCE_LABELS[pkg.source] ?? pkg.source}
                </span>
              </div>
              <h3 className="mt-1 text-lg font-semibold">{pkg.title}</h3>
              <p className="mt-2 text-sm text-slate-600 line-clamp-2">
                {pkg.description}
              </p>
              <div className="mt-3 text-sm font-semibold">
                {pkg.currency} {pkg.basePrice.toLocaleString("es-ES")} ·{" "}
                {pkg.durationDays} días
              </div>
            </Link>
          ))}
        </div>
      </section>

      <aside className="space-y-6">
        <AgentConsole
          query={query}
          trace={agentTrace}
          reply={agentReply}
          loading={nlpLoading}
          error={nlpError}
        />
        <NlpInspector
          query={query}
          debug={nlpDebug}
          reply={nlpReply}
          loading={nlpLoading}
          error={nlpError}
        />
        <ScrapePanel />
        <SystemMetricsView />
      </aside>
    </div>
  );
}