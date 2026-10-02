import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { bookingApi } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { TourPackage } from "../types/domain";

export default function HomePage() {
  const { getAccessToken } = useAuth();
  const [packages, setPackages] = useState<TourPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    bookingApi
      .listPackages(getAccessToken())
      .then(setPackages)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [getAccessToken]);

  return (
    <section>
      <div className="rounded-2xl bg-gradient-to-r from-brand-600 to-brand-800 p-10 text-white">
        <h1 className="text-3xl font-bold">
          Explora los mejores paquetes turísticos
        </h1>
        <p className="mt-2 text-brand-100">
          Reserva experiencias únicas con un proceso rápido, seguro y con
          autenticación centralizada.
        </p>
        <Link
          to="/buscar"
          className="mt-6 inline-block rounded-md bg-white px-4 py-2 font-medium text-brand-700 hover:bg-brand-50"
        >
          Buscar paquetes
        </Link>
      </div>

      <h2 className="mt-10 mb-4 text-xl font-semibold">Paquetes destacados</h2>

      {error && <p className="text-red-600">{error}</p>}
      {loading && <p className="text-slate-500">Cargando paquetes...</p>}

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {packages.map((pkg) => (
          <Link
            key={pkg.id}
            to={`/paquetes/${pkg.id}`}
            className="group rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md"
          >
            <div className="text-xs font-medium uppercase tracking-wide text-brand-600">
              {pkg.destination}, {pkg.country}
            </div>
            <h3 className="mt-1 text-lg font-semibold group-hover:text-brand-700">
              {pkg.title}
            </h3>
            <p className="mt-2 line-clamp-2 text-sm text-slate-600">
              {pkg.description}
            </p>
            <div className="mt-3 flex items-center justify-between text-sm">
              <span>{pkg.durationDays} días</span>
              <span className="font-semibold">
                {pkg.currency} {pkg.basePrice.toLocaleString("es-ES")}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}