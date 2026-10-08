import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getToken, setToken } from "../api/client";
import { resetCachesAndIdentity } from "../api/queries";
import type { Me } from "../api/types";

interface AuthState {
  me: Me | undefined;
  isLoading: boolean;
  signIn: (userId: string, role: string) => Promise<void>;
  signOut: () => void;
  /** Display hint only — the server enforces every permission. */
  can: (permission: string) => boolean;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const [hasToken, setHasToken] = useState(() => getToken() !== null);

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: () => api<Me>("/api/auth/me"),
    enabled: hasToken,
    retry: false,
  });

  const signIn = useCallback(
    async (userId: string, role: string) => {
      const { access_token } = await api<{ access_token: string }>("/api/auth/login", {
        method: "POST",
        json: { user_id: userId, role },
      });
      setToken(access_token);
      setHasToken(true);
      // Not `qc.clear()` on its own: see resetCachesAndIdentity. Dropping the cache left `me` at
      // the previous role, so the picker and every permission-gated control kept showing it.
      await resetCachesAndIdentity(qc);
    },
    [qc],
  );

  const signOut = useCallback(() => {
    setToken(null);
    setHasToken(false);
    // Clearing is enough here, and a refetch would be wrong: `hasToken` goes false, which disables
    // the identity query, so `me` really does become undefined. There is no stale identity to fix.
    qc.clear();
  }, [qc]);

  const me = hasToken && !meQuery.isError ? meQuery.data : undefined;
  const can = useCallback((p: string) => me?.permissions.includes(p) ?? false, [me]);

  return (
    <AuthContext.Provider value={{ me, isLoading: hasToken && meQuery.isLoading, signIn, signOut, can }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
