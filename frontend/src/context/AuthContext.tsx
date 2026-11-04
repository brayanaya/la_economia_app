"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  cargarSesion,
  iniciarSesion,
  registrarCuenta,
  cerrarSesion,
  loginConGoogle,
  solicitarEnlaceMagico,
  verificarEnlaceMagico,
  configurarTotp,
  verificarTotp,
  desactivarTotp,
  obtenerEstadoTotp,
  actualizarPerfil,
  obtenerConsentimiento,
  exportarDatos,
  eliminarCuenta,
  type AuthUser,
  type TotpSetup,
  type ConsentInfo,
  type DataExport,
} from "@/lib/auth";

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string, totpCode?: string) => Promise<void>;
  register: (email: string, password: string, nombre: string, telefono?: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  // Google OAuth
  loginWithGoogle: (idToken: string) => Promise<void>;
  // Magic Link
  requestMagicLink: (email: string) => Promise<{ ok: boolean; mensaje: string; dev_token?: string }>;
  verifyMagicLink: (token: string, totpCode?: string) => Promise<void>;
  // TOTP
  setupTotp: () => Promise<TotpSetup>;
  verifyTotp: (code: string) => Promise<{ ok: boolean; mensaje: string }>;
  disableTotp: (code: string) => Promise<{ ok: boolean; mensaje: string }>;
  checkTotpStatus: () => Promise<{ enabled: boolean }>;
  // Profile
  updateProfile: (data: Partial<{ nombre: string; telefono: string; consentimiento_datos: boolean; consentimiento_marketing: boolean }>) => Promise<AuthUser>;
  getConsent: () => Promise<ConsentInfo>;
  exportData: () => Promise<DataExport>;
  deleteAccount: () => Promise<{ ok: boolean; mensaje: string }>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setUser(await cargarSesion());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    void cargarSesion().then((current) => {
      if (active) setUser(current);
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, []);

  const login = useCallback(async (email: string, password: string, totpCode?: string) => {
    const result = await iniciarSesion(email, password, totpCode);
    setUser(result.user);
  }, []);

  const register = useCallback(async (email: string, password: string, nombre: string, telefono?: string) => {
    const result = await registrarCuenta(email, password, nombre, telefono);
    setUser(result.user);
  }, []);

  const logout = useCallback(async () => {
    await cerrarSesion();
    setUser(null);
  }, []);

  // Google OAuth
  const loginWithGoogle = useCallback(async (idToken: string) => {
    const result = await loginConGoogle(idToken);
    setUser(result.user);
  }, []);

  // Magic Link
  const requestMagicLink = useCallback(async (email: string) => {
    return await solicitarEnlaceMagico(email);
  }, []);

  const verifyMagicLink = useCallback(async (token: string, totpCode?: string) => {
    const result = await verificarEnlaceMagico(token, totpCode);
    setUser(result.user);
  }, []);

  // TOTP
  const setupTotp = useCallback(async () => {
    return await configurarTotp();
  }, []);

  const verifyTotp = useCallback(async (code: string) => {
    return await verificarTotp(code);
  }, []);

  const disableTotp = useCallback(async (code: string) => {
    return await desactivarTotp(code);
  }, []);

  const checkTotpStatus = useCallback(async () => {
    return await obtenerEstadoTotp();
  }, []);

  // Profile
  const updateProfile = useCallback(async (data: Partial<{ nombre: string; telefono: string; consentimiento_datos: boolean; consentimiento_marketing: boolean }>) => {
    const updated = await actualizarPerfil(data);
    setUser(updated);
    return updated;
  }, []);

  const getConsent = useCallback(async () => {
    return await obtenerConsentimiento();
  }, []);

  const exportData = useCallback(async () => {
    return await exportarDatos();
  }, []);

  const deleteAccount = useCallback(async () => {
    const result = await eliminarCuenta();
    setUser(null);
    return result;
  }, []);

  const value = useMemo(() => ({
    user, loading, login, register, logout, refresh,
    loginWithGoogle, requestMagicLink, verifyMagicLink,
    setupTotp, verifyTotp, disableTotp, checkTotpStatus,
    updateProfile, getConsent, exportData, deleteAccount,
  }), [user, loading, login, register, logout, refresh, loginWithGoogle, requestMagicLink, verifyMagicLink, setupTotp, verifyTotp, disableTotp, checkTotpStatus, updateProfile, getConsent, exportData, deleteAccount]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return value;
}