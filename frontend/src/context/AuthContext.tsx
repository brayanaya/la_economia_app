"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { cargarSesion, iniciarSesion, registrarCuenta, cerrarSesion, type AuthUser } from "@/lib/auth";

type AuthContextValue = { user: AuthUser | null; loading: boolean; login: (email: string, password: string) => Promise<void>; register: (email: string, password: string, nombre: string) => Promise<void>; logout: () => Promise<void>; refresh: () => Promise<void> };
const AuthContext = createContext<AuthContextValue | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const refresh = useCallback(async () => { setLoading(true); try { setUser(await cargarSesion()); } finally { setLoading(false); } }, []);
  useEffect(() => { let active = true; void cargarSesion().then((current) => { if (active) setUser(current); }).finally(() => { if (active) setLoading(false); }); return () => { active = false; }; }, []);
  const login = useCallback(async (email: string, password: string) => { const result = await iniciarSesion(email, password); setUser(result.user); }, []);
  const register = useCallback(async (email: string, password: string, nombre: string) => { const result = await registrarCuenta(email, password, nombre); setUser(result.user); }, []);
  const logout = useCallback(async () => { await cerrarSesion(); setUser(null); }, []);
  const value = useMemo(() => ({ user, loading, login, register, logout, refresh }), [user, loading, login, register, logout, refresh]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error("useAuth debe usarse dentro de <AuthProvider>"); return value; }
