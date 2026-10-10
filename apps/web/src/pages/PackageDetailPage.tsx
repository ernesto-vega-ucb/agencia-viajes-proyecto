import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { bookingApi, isNotFound, searchApi } from "../lib/api";
import { useAuth } from "../lib/auth";
import { addToCart } from "../lib/cart";
import type { TourPackage } from "../types/domain";

function isEngineId(value: string): boolean {
  if (!/^\d+$/.test(value)) return false;
  const n = Number(value);
  return (n >= 8000 && n <= 8899) || (n >= 9000 && n <= 9899);
}

export default function PackageDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { getAccessToken, isAuthenticated } = useAuth();
  const initialPkg = (location.state as { pkg?: TourPackage } | null)?.pkg;
  const [pkg, setPkg] = useState<TourPackage | null>(null);
  const [startDate, setStartDate] = useState("");
  const [travelers, setTravelers] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    const token = getAccessToken();
    const stateId = initialPkg ? String(initialPkg.id) : null;
    const candidates = [id, ...(stateId && stateId !== id ? [stateId] : [])];

    (async () => {
      setLoading(true);
      setError(null);
      try {
        let resolved: TourPackage | null = null;
        for (const candidate of candidates) {
          try {
            resolved = await bookingApi.getPackage(candidate, token);
            break;
          } catch (err) {
            if (!isNotFound(err)) throw err;
          }
          try {
            resolved = await searchApi.ensurePackage(candidate, token);
            break;
          } catch (err) {
            if (!isNotFound(err)) throw err;
          }
        }
        if (cancelled) return;
        if (!resolved) {
          setError("Paquete no encontrado.");
          return;
        }
        if (isEngineId(String(resolved.id))) {
          try {
            resolved = await bookingApi.syncExternal(resolved);
          } catch {
            // keep the engine document as an emergency fallback
          }
        }
        if (cancelled) return;
        if (String(resolved.id) !== id) {
          navigate(`/paquetes/${resolved.id}`, { replace: true, state: null });
        }
        setPkg(resolved);
      } catch (err) {
        if (!cancelled) {
          setError(
            isNotFound(err)
              ? "Paquete no encontrado."
              : err instanceof Error
                ? err.message
                : "Error al cargar el paquete",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [id, initialPkg, getAccessToken, navigate]);

  const fallbackPkg = pkg ?? initialPkg;

  if (loading && !fallbackPkg) return <p className="text-slate-500">Cargando detalle...</p>;
  if (error && !fallbackPkg) return <p className="text-red-600">{error}</p>;
  if (!fallbackPkg) return <p className="text-slate-600">Paquete no encontrado.</p>;

  const handleReserve = () => {
    if (!isAuthenticated) {
      navigate("/");
      return;
    }
    addToCart({ packageId: fallbackPkg.id, startDate, travelers });
    navigate("/reserva");
  };

  return (
    <article className="mx-auto max-w-3xl">
      <Link to="/buscar" className="text-sm text-brand-600 hover:underline">
        ← Volver a resultados
      </Link>
      {error && (
        <p className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          No se pudo verificar el paquete con el servidor; mostrando los datos de la búsqueda.
        </p>
      )}

      <div className="mt-2 flex items-center gap-2">
        <h1 className="text-3xl font-bold">{fallbackPkg.title}</h1>
        {fallbackPkg.source && fallbackPkg.source !== "MANUAL" && (
          <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800">
            {fallbackPkg.source}
          </span>
        )}
      </div>
      <p className="text-brand-700">
        {fallbackPkg.destination}, {fallbackPkg.country} · {fallbackPkg.durationDays} días
      </p>

      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="leading-relaxed text-slate-700">{fallbackPkg.description}</p>

        <dl className="mt-6 grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-slate-500">Precio base</dt>
            <dd className="font-semibold">
              {fallbackPkg.currency} {fallbackPkg.basePrice.toLocaleString("es-ES")}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Valoración</dt>
            <dd>{fallbackPkg.rating.toFixed(1)} / 5</dd>
          </div>
          <div>
            <dt className="text-slate-500">Fecha de salida</dt>
            <dd>
              <select
                value={startDate}
                onChange={(event) => setStartDate(event.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-1.5"
              >
                <option value="">Selecciona...</option>
                {fallbackPkg.startDates.map((date) => (
                  <option key={date} value={date}>
                    {date}
                  </option>
                ))}
              </select>
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Viajeros</dt>
            <dd>
              <input
                type="number"
                min={1}
                max={fallbackPkg.maxTravelers}
                value={travelers}
                onChange={(event) => setTravelers(Number(event.target.value))}
                className="w-full rounded-md border border-slate-300 px-3 py-1.5"
              />
            </dd>
          </div>
        </dl>

        <button
          onClick={handleReserve}
          disabled={!startDate || !fallbackPkg.startDates?.length}
          className="mt-6 w-full rounded-md bg-brand-600 py-2.5 font-medium text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isAuthenticated ? "Agregar al carrito y reservar" : "Inicia sesión para reservar"}
        </button>
      </div>
    </article>
  );
}