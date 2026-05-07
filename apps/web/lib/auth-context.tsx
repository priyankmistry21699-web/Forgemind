"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { apiFetch, setAuthToken } from "@/lib/api";

interface User {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
  created_at: string;
}

interface AuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = "forgemind_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const saveToken = useCallback((t: string) => {
    localStorage.setItem(TOKEN_KEY, t);
    setAuthToken(t);
    setToken(t);
  }, []);

  const clearAuth = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setAuthToken(null);
    setToken(null);
    setUser(null);
  }, []);

  const fetchMe = useCallback(async (t: string) => {
    try {
      const headers: Record<string, string> = {};
      if (t) headers["Authorization"] = `Bearer ${t}`;
      const me = await apiFetch<User>("/auth/me", { headers });
      setUser(me);
      return true;
    } catch {
      clearAuth();
      return false;
    }
  }, [clearAuth]);

  // Restore session on mount — try stored token first, then fall back to
  // no-token request (works in dev mode where the API returns a stub user).
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (stored) {
      setAuthToken(stored);
      setToken(stored);
      fetchMe(stored).finally(() => setLoading(false));
    } else {
      // Dev mode: API returns stub user without a token
      fetchMe("").finally(() => setLoading(false));
    }
  }, [fetchMe]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await apiFetch<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    saveToken(res.access_token);
    await fetchMe(res.access_token);
  }, [saveToken, fetchMe]);

  const register = useCallback(async (email: string, password: string, displayName: string) => {
    const res = await apiFetch<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, display_name: displayName }),
    });
    saveToken(res.access_token);
    await fetchMe(res.access_token);
  }, [saveToken, fetchMe]);

  const logout = useCallback(() => {
    clearAuth();
  }, [clearAuth]);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
