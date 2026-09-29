import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";

import { api, UNAUTHORIZED_EVENT } from "@/lib/api";
import { getToken, setToken, clearToken } from "@/lib/token";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load the current user once on mount if a token is stored.
  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!getToken()) {
        setLoading(false);
        return;
      }
      try {
        const me = await api("/auth/me");
        if (!cancelled) setUser(me);
      } catch {
        clearToken();
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  // Expired/invalid token anywhere -> drop the user.
  useEffect(() => {
    const onUnauthorized = () => setUser(null);
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, []);

  const authenticate = useCallback(async (path, body) => {
    const data = await api(path, { method: "POST", body });
    setToken(data.token);
    setUser(data.user);
    return data.user;
  }, []);

  const login = useCallback((email, password) => authenticate("/auth/login", { email, password }), [authenticate]);
  const register = useCallback(
    (full_name, email, password) => authenticate("/auth/register", { full_name, email, password }),
    [authenticate]
  );

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    router.push("/");
  }, [router]);

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

// Page guard: redirects to /login when logged out (keeping a ?next= return path),
// and away when a required role is missing. `ready` is true once the page may render.
export function useRequireAuth({ role } = {}) {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (loading || !router.isReady) return;
    if (!user) {
      router.replace(`/login?next=${encodeURIComponent(router.asPath)}`);
    } else if (role && user.role !== role) {
      router.replace("/booking");
    }
  }, [loading, user, role, router]);

  const ready = !loading && !!user && (!role || user.role === role);
  return { user, loading, ready };
}

// Only allow same-site relative redirects.
export function safeNext(next) {
  return typeof next === "string" && next.startsWith("/") && !next.startsWith("//") ? next : "/booking";
}
