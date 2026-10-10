import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { SearchSessionProvider } from "./lib/searchSession";
import AccountPage from "./pages/AccountPage";
import CallbackPage from "./pages/CallbackPage";
import CheckoutPage from "./pages/CheckoutPage";
import HomePage from "./pages/HomePage";
import PackageDetailPage from "./pages/PackageDetailPage";
import SearchPage from "./pages/SearchPage";

export default function App() {
  return (
    <SearchSessionProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="buscar" element={<SearchPage />} />
          <Route path="paquetes/:id" element={<PackageDetailPage />} />
          <Route path="reserva" element={<CheckoutPage />} />
          <Route path="cuenta" element={<AccountPage />} />
        </Route>
        <Route path="/callback" element={<CallbackPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </SearchSessionProvider>
  );
}