export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8081/api/v1",
  searchApiBaseUrl:
    import.meta.env.VITE_SEARCH_API_BASE_URL ?? "http://localhost:8082/api/v1",
  oidcAuthority:
    import.meta.env.VITE_OIDC_AUTHORITY ??
    "http://localhost:8080/realms/agencia-viajes",
  oidcClientId: import.meta.env.VITE_OIDC_CLIENT_ID ?? "agencia-web",
  oidcRedirectUri:
    import.meta.env.VITE_OIDC_REDIRECT_URI ?? "http://localhost:5173/callback",
} as const;