import { useEffect, useState } from "react";
import { userManager } from "../lib/auth";
import { useNavigate } from "react-router-dom";

export default function CallbackPage() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    userManager
      .signinRedirectCallback()
      .then(() => navigate("/", { replace: true }))
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Error al completar el login"),
      );
  }, [navigate]);

  if (error) {
    return <div className="text-red-600">{error}</div>;
  }
  return <div className="text-slate-600">Completando inicio de sesión...</div>;
}