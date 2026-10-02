import { useEffect, useState } from "react";
import { bookingApi, searchApi } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { Booking } from "../types/domain";

export default function AccountPage() {
  const { getAccessToken, getUserName } = useAuth();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;

    Promise.all([
      bookingApi.getMyBookings(token),
      searchApi
        .recommendations(token ? "demo-user" : "anonymous", 5, token)
        .then((pkgs) => pkgs.map((p) => p.title))
        .catch(() => [] as string[]),
    ])
      .then(([bookingsData, recommendationsData]) => {
        setBookings(bookingsData);
        setRecommendations(recommendationsData);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [getAccessToken]);

  return (
    <section className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-semibold">Hola, {getUserName()}</h1>

      {error && <p className="mt-4 text-red-600">{error}</p>}
      {loading && <p className="mt-4 text-slate-500">Cargando...</p>}

      <h2 className="mt-8 mb-3 text-lg font-semibold">Mis reservas</h2>
      <div className="space-y-3">
        {bookings.map((booking) => (
          <div
            key={booking.id}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold">{booking.id}</span>
              <span className="rounded-full bg-brand-100 px-3 py-1 text-xs font-medium text-brand-800">
                {booking.status}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-600">
              {booking.items.map((i) => i.packageTitle).join(", ")}
            </p>
            <p className="mt-1 text-sm font-semibold">
              {booking.currency} {booking.totalPrice.toLocaleString("es-ES")}
            </p>
          </div>
        ))}
      </div>

      {recommendations.length > 0 && (
        <>
          <h2 className="mt-10 mb-3 text-lg font-semibold">
            Sugerencias para ti (NLP)
          </h2>
          <ul className="list-inside list-disc text-slate-700">
            {recommendations.map((title) => (
              <li key={title}>{title}</li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}