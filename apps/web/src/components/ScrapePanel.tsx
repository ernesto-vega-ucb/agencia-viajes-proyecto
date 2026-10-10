import { useCallback, useEffect, useState } from "react";
import { searchApi } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { ScrapeRefreshResult, ScrapedPackage } from "../types/domain";

function formatPrice(price?: number | null, currency?: string | null): string {
  if (price == null) return "—";
  return `${currency ?? "EUR"} ${price.toLocaleString("es-ES")}`;
}

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString("es-ES", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ScrapePanel() {
  const { getAccessToken } = useAuth();
  const [open, setOpen] = useState(true);
  const [packages, setPackages] = useState<ScrapedPackage[]>([]);
  const [stats, setStats] = useState<ScrapeRefreshResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPackages = useCallback(async () => {
    try {
      setPackages(await searchApi.listScrapedPackages(getAccessToken()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar scrapeados");
    }
  }, [getAccessToken]);

  useEffect(() => {
    void loadPackages();
  }, [loadPackages]);

  const runRefresh = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await searchApi.refreshScrape(getAccessToken());
      setStats(result);
      await loadPackages();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al re-sincronizar");
    } finally {
      setBusy(false);
    }
  }, [getAccessToken, loadPackages]);

  return (
    <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <div className="flex items-center gap-2">
          <span
            className={
              "h-2 w-2 rounded-full " + (busy ? "animate-pulse bg-amber-400" : "bg-emerald-400")
            }
          />
          <h2 className="text-sm font-semibold text-slate-800">Scraping en vivo</h2>
          {packages.length > 0 && (
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
              {packages.length}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => void runRefresh()}
            disabled={busy}
            className="rounded-md bg-brand-600 px-3 py-1 text-xs font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {busy ? "Sincronizando…" : "Re-sincronizar"}
          </button>
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            aria-label={open ? "Colapsar panel" : "Expandir panel"}
            className="rounded-md px-2 py-1 text-xs text-slate-500 hover:bg-slate-100"
          >
            {open ? "▾" : "▸"}
          </button>
        </div>
      </div>

      {open && (
        <div className="px-4 py-3">
          {error && <p className="mb-3 text-sm text-red-600">{error}</p>}

          {stats && (
            <dl className="mb-3 grid grid-cols-3 gap-2 text-center">
              <div className="rounded-md bg-slate-50 p-2">
                <dt className="text-[10px] uppercase tracking-wide text-slate-500">Extraídos</dt>
                <dd className="text-sm font-semibold text-slate-800">{stats.extraidos}</dd>
              </div>
              <div className="rounded-md bg-slate-50 p-2">
                <dt className="text-[10px] uppercase tracking-wide text-slate-500">Nuevos</dt>
                <dd className="text-sm font-semibold text-slate-800">{stats.nuevos_guardados}</dd>
              </div>
              <div className="rounded-md bg-slate-50 p-2">
                <dt className="text-[10px] uppercase tracking-wide text-slate-500">Actualizados</dt>
                <dd className="text-sm font-semibold text-slate-800">{stats.actualizados ?? 0}</dd>
              </div>
            </dl>
          )}

          <ul className="space-y-2">
            {packages.slice(0, 6).map((pkg) => (
              <li
                key={pkg.id}
                className="flex items-center justify-between gap-2 rounded-md border border-slate-100 px-3 py-2"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm text-slate-800">{pkg.title}</p>
                  <p className="text-xs text-slate-500">
                    {pkg.destination ?? "—"} · {formatTimestamp(pkg.scraped_at)}
                  </p>
                </div>
                <span className="shrink-0 text-sm font-semibold text-slate-700">
                  {formatPrice(pkg.price, pkg.currency)}
                </span>
              </li>
            ))}
          </ul>
          {packages.length === 0 && !error && (
            <p className="text-sm text-slate-500">Sin paquetes scrapeados todavía.</p>
          )}
        </div>
      )}
    </section>
  );
}