"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, setAuthToken } from "./api";
import type { UserOut } from "./types";

const STORAGE_KEY = "merchantgpt_token";

interface AuthContextValue {
  user: UserOut | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: { merchant_name: string; name: string; email: string; password: string; industry?: string }) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const token = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null;
    if (!token) {
      setIsLoading(false);
      return;
    }
    setAuthToken(token);
    api.auth
      .me()
      .then(setUser)
      .catch(() => {
        window.localStorage.removeItem(STORAGE_KEY);
        setAuthToken(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const applySession = useCallback((token: string, userOut: UserOut) => {
    window.localStorage.setItem(STORAGE_KEY, token);
    setAuthToken(token);
    setUser(userOut);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      setError(null);
      try {
        const res = await api.auth.login({ email, password });
        applySession(res.access_token, res.user);
        router.push("/dashboard");
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Login failed. Please try again.");
        throw err;
      }
    },
    [applySession, router],
  );

  const register = useCallback(
    async (payload: { merchant_name: string; name: string; email: string; password: string; industry?: string }) => {
      setError(null);
      try {
        const res = await api.auth.register(payload);
        applySession(res.access_token, res.user);
        router.push("/dashboard");
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Registration failed. Please try again.");
        throw err;
      }
    },
    [applySession, router],
  );

  const logout = useCallback(() => {
    window.localStorage.removeItem(STORAGE_KEY);
    setAuthToken(null);
    setUser(null);
    router.push("/login");
  }, [router]);

  const clearError = useCallback(() => setError(null), []);

  return (
    <AuthContext.Provider value={{ user, isLoading, error, login, register, logout, clearError }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
