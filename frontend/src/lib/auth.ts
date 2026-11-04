import { API_URL } from "@/lib/api";

const BASE = `${API_URL}/api/v1`;

// Extended user type with new fields
export type AuthUser = {
  id: string;
  email: string;
  nombre: string;
  telefono?: string | null;
  fecha_nacimiento?: string | null;
  totp_enabled: boolean;
  google_linked: boolean;
  consentimiento_datos: boolean;
  consentimiento_marketing: boolean;
};

export type TotpSetup = {
  secret: string;
  uri: string;
  qr_code_url: string;
};

export type ConsentInfo = {
  consentimiento_datos: boolean;
  consentimiento_marketing: boolean;
  consentimiento_fecha: string | null;
  version: string;
  politica_url: string;
  terminos_url: string;
};

export type DataExport = {
  user: AuthUser;
  orders_count: number;
  sessions_count: number;
  created_at: string;
};

type AuthResponse = {
  user: AuthUser;
  csrf_token: string;
  requires_totp: boolean;
};

let csrfToken: string | null = null;
export const setCsrfToken = (token: string | null) => { csrfToken = token; };
export const getCsrfToken = () => csrfToken;

async function request<T>(
  path: string,
  method: string,
  body?: unknown,
  needsCsrf = false
): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (needsCsrf && csrfToken) headers["X-CSRF-Token"] = csrfToken;

  const response = await fetch(`${BASE}/auth${path}`, {
    method,
    credentials: "include",
    headers,
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail ?? data.message;
    throw new Error(typeof detail === "string" ? detail : "No pudimos completar la solicitud.");
  }

  const result = data as T & { csrf_token?: string };
  if (result.csrf_token) setCsrfToken(result.csrf_token);
  return result;
}

// ==================== CORE AUTH ====================
export async function cargarSesion(): Promise<AuthUser | null> {
  try { return (await request<AuthResponse>("/me", "GET")).user; }
  catch { setCsrfToken(null); return null; }
}

export async function iniciarSesion(email: string, password: string, totpCode?: string) {
  return request<AuthResponse>("/login", "POST", { email, password, totp_code: totpCode });
}

export async function registrarCuenta(email: string, password: string, nombre: string, telefono?: string) {
  return request<AuthResponse>("/register", "POST", { email, password, nombre, telefono, consentimiento_datos: true });
}

export async function cerrarSesion() {
  const response = await fetch(`${BASE}/auth/logout`, {
    method: "POST",
    credentials: "include",
    headers: csrfToken ? { "X-CSRF-Token": csrfToken } : {},
  });
  if (!response.ok) throw new Error("No pudimos cerrar la sesión. Inténtalo de nuevo.");
  setCsrfToken(null);
}

// ==================== GOOGLE OAUTH ====================
export async function loginConGoogle(idToken: string) {
  return request<AuthResponse>("/google", "POST", { id_token: idToken });
}

// ==================== MAGIC LINK ====================
export async function solicitarEnlaceMagico(email: string) {
  return request<{ ok: boolean; mensaje: string; dev_token?: string }>("/magic-link", "POST", { email });
}

export async function verificarEnlaceMagico(token: string, totpCode?: string) {
  return request<AuthResponse>("/magic-link/verify", "POST", { token, totp_code: totpCode });
}

// ==================== TOTP / GOOGLE AUTHENTICATOR ====================
export async function configurarTotp(): Promise<TotpSetup> {
  return request<TotpSetup>("/totp/setup", "POST", {}, true);
}

export async function verificarTotp(code: string) {
  return request<{ ok: boolean; mensaje: string }>("/totp/verify", "POST", { code }, true);
}

export async function desactivarTotp(code: string) {
  return request<{ ok: boolean; mensaje: string }>("/totp/disable", "POST", { code }, true);
}

export async function obtenerEstadoTotp(): Promise<{ enabled: boolean }> {
  return request<{ enabled: boolean }>("/totp/status", "GET");
}

// ==================== PERFIL Y CONSENTIMIENTO ====================
export async function actualizarPerfil(data: Partial<{ nombre: string; telefono: string; consentimiento_datos: boolean; consentimiento_marketing: boolean }>) {
  return request<AuthUser>("/me", "PATCH", data, true);
}

export async function obtenerConsentimiento(): Promise<ConsentInfo> {
  return request<ConsentInfo>("/consent", "GET");
}

export async function exportarDatos(): Promise<DataExport> {
  return request<DataExport>("/me/export", "GET");
}

export async function eliminarCuenta(): Promise<{ ok: boolean; mensaje: string }> {
  return request<{ ok: boolean; mensaje: string }>("/me", "DELETE", {}, true);
}