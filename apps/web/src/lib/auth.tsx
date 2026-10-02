import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";
import type { User } from "oidc-client-ts";
import { UserManager, WebStorageStateStore } from "oidc-client-ts";
import { env } from "../config/env";

export const userManager = new UserManager({
  authority: env.oidcAuthority,
  client_id: env.oidcClientId,
  redirect_uri: env.oidcRedirectUri,
  post_logout_redirect_uri: window.location.origin,
  response_type: "code",
  scope: "openid profile email",
  userStore: new WebStorageStateStore({ store: window.localStorage }),
  automaticSilentRenew: true,
});

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  getAccessToken: () => string | undefined;
  getUserName: () => string;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    void userManager
      .getUser()
      .then((current) => {
        setUser(current);
        setIsLoading(false);
      })
      .catch(() => setIsLoading(false));

    const onUserLoaded = (loaded: User) => setUser(loaded);
    const onUserUnloaded = () => setUser(null);
    userManager.events.addUserLoaded(onUserLoaded);
    userManager.events.addUserUnloaded(onUserUnloaded);
    return () => {
      userManager.events.removeUserLoaded(onUserLoaded);
      userManager.events.removeUserUnloaded(onUserUnloaded);
    };
  }, []);

  const login = useCallback(() => userManager.signinRedirect(), []);

  const logout = useCallback(() => userManager.signoutRedirect(), []);

  const getAccessToken = useCallback(() => user?.access_token, [user]);

  const getUserName = useCallback(() => {
    return (
      user?.profile?.name ??
      String(user?.profile?.preferred_username ?? user?.profile?.email ?? "usuario")
    );
  }, [user]);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: user !== null && user.expired !== true,
      isLoading,
      login,
      logout,
      getAccessToken,
      getUserName,
    }),
    [user, isLoading, login, logout, getAccessToken, getUserName],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  }
  return ctx;
}