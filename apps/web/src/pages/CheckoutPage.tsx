import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { bookingApi } from "../lib/api";
import { useAuth } from "../lib/auth";
import { clearCart, getCart } from "../lib/cart";
import type { Booking } from "../types/domain";

export default function CheckoutPage() {
  const { getAccessToken, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [cart, setCart] = useState(() => getCart());
  const [submitting, setSubmitting] = useState(false);
  const [created, setCreated] = useState<Booking | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async () => {
    const token = getAccessToken();
    if (!token || cart.length === 0) return;
    setSubmitting(true);
    try {
      const booking = await bookingApi.createBooking({ items: cart }, token);
      clearCart();
      setCreated(booking);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear la reserva");
    } finally {
      setSubmitting(false);
    }
  };

  if (created) {
    return (
      <section className="mx-auto max-w-xl rounded-xl border border-green-200 bg-green-50 p-8 text-center">
        <h1 className="text-2xl font-bold text-green-800">Reserva confirmada</h1>
        <p className="mt-2 text-green-700">
          Tu reserva {created.id} quedó en estado {created.status} por un total de{" "}
          {created.currency} {created.totalPrice.toLocaleString("es-ES")}.
        </p>
        <Link to="/cuenta" className="mt-6 inline-block text-brand-600 hover:underline">
          Ver mis reservas
        </Link>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-semibold">Proceso de reserva</h1>

      {error && <p className="mt-4 text-red-600">{error}</p>}

      <div className="mt-6 space-y-4">
        {cart.length === 0 && (
          <p className="text-slate-500">
            Tu carrito está vacío.{" "}
            <Link to="/buscar" className="text-brand-600 hover:underline">
              Busca paquetes
            </Link>
            .
          </p>
        )}

        {cart.map((item, index) => (
          <div
            key={`${item.packageId}-${item.startDate}`}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold">Paquete {item.packageId}</p>
                <p className="text-sm text-slate-500">
                  Salida {item.startDate} · {item.travelers} viajero(s)
                </p>
              </div>
              <button
                onClick={() => {
                  const next = cart.filter((_, i) => i !== index);
                  setCart(next);
                }}
                className="text-sm text-red-500 hover:underline"
              >
                Quitar
              </button>
            </div>
          </div>
        ))}
      </div>

      {cart.length > 0 && (
        <button
          onClick={() => void handleSubmit()}
          disabled={submitting}
          className="mt-6 w-full rounded-md bg-brand-600 py-2.5 font-medium text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {submitting ? "Procesando..." : "Confirmar reserva"}
        </button>
      )}
    </section>
  );
}