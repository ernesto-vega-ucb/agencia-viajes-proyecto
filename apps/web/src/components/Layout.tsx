import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../lib/auth";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? "bg-brand-600 text-white" : "text-slate-700 hover:bg-brand-100"
  }`;

export default function Layout() {
  const { isAuthenticated, login, logout, getUserName } = useAuth();

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl">✈</span>
            <span className="text-lg font-bold text-brand-700">Agencia Viajes</span>
          </Link>

          <nav className="flex items-center gap-1">
            <NavLink to="/" end className={navLinkClass}>
              Inicio
            </NavLink>
            <NavLink to="/buscar" className={navLinkClass}>
              Buscar
            </NavLink>
            {isAuthenticated && (
              <NavLink to="/reserva" className={navLinkClass}>
                Reserva
              </NavLink>
            )}
            {isAuthenticated && (
              <NavLink to="/cuenta" className={navLinkClass}>
                Mi cuenta
              </NavLink>
            )}
          </nav>

          <div className="flex items-center gap-2">
            {isAuthenticated ? (
              <>
                <span className="text-sm text-slate-600">{getUserName()}</span>
                <button
                  onClick={() => void logout()}
                  className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100"
                >
                  Salir
                </button>
              </>
            ) : (
              <button
                onClick={() => void login()}
                className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
              >
                Iniciar sesión
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 py-6 text-center text-sm text-slate-500">
        Agencia de Viajes — Monorepo demo
      </footer>
    </div>
  );
}