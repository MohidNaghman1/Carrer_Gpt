"use client";

import React, {
  createContext,
  useContext,
  useMemo,
  useState,
  ReactNode,
} from "react";

type AuthContextValue = {
  user: unknown | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  hasHydrated: boolean;
  login: (token: string, user?: unknown) => void;
  logout: () => void;
  setUser: (user: unknown | null) => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUserState] = useState<unknown | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [hasHydrated, setHasHydrated] = useState<boolean>(false);

  const isAuthenticated = Boolean(token);

  // Hydrate token on client mount to avoid SSR mismatch
  React.useEffect(() => {
    try {
      const t = localStorage.getItem("accessToken");
      setToken(t);
    } finally {
      setHasHydrated(true);
    }
  }, []);

  const login = (newToken: string, newUser?: unknown) => {
    setIsLoading(true);
    try {
      localStorage.setItem("accessToken", newToken);
      setToken(newToken);
      if (newUser !== undefined) setUserState(newUser);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setIsLoading(true);
    try {
      localStorage.removeItem("accessToken");
      setToken(null);
      setUserState(null);
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    } finally {
      setIsLoading(false);
    }
  };

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated,
      isLoading,
      hasHydrated,
      login,
      logout,
      setUser: setUserState,
    }),
    [user, isAuthenticated, isLoading, hasHydrated]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
