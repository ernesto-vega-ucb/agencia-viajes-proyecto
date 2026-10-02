import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { searchApi } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { TourPackage } from "../types/domain";

export default function SearchPage() {
  const { getAccessToken } = useAuth();
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [results, setResults] = useState<TourPackage[]>([]);
  const [searched, setSearched] = useState(false);

  const handleSearch = useCallback(
    async (value: string) => {
      const token = getAccessToken();
      const data = await searchApi.search(value, token);
      setResults(data.packages);
      setSuggestions(data.suggestions);
      setSearched(true);
    },
    [getAccessToken],
  );

  return (
    <section>
      <h1 className="text-2xl font-semibold">Buscador avanzado</h1>

      <form
        className="mt-6 flex gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          void handleSearch(query);
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
          Buscar con IA
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
            <div className="text-xs font-medium uppercase tracking-wide text-brand-600">
              {pkg.destination}, {pkg.country}
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
  );
}