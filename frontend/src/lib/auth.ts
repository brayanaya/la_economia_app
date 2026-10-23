import { API_URL } from "@/lib/api";

const BASE = `${API_URL}/api/v1`;
export type AuthUser = { id: string; email: string; nombre: string };
type AuthResponse = { user: AuthUser; csrf_token: string };
let csrfToken: string | null = null;
export const setCsrfToken = (token: string | null) => { csrfToken = token; };
export const getCsrfToken = () => csrfToken;

async function request(path: string, method: string, body?: unknown): Promise<AuthResponse> {
  const response = await fetch(`${BASE}/auth${path}`, {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(body === undefined ? {} : {}) },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail ?? data.message;
    throw new Error(typeof detail === "string" ? detail : "No pudimos completar la solicitud. Revisa tus datos e inténtalo de nuevo.");
  }
  const result = data as AuthResponse;
  if (result.csrf_token) setCsrfToken(result.csrf_token);
  return result;
}
export async function cargarSesion(): Promise<AuthUser | null> {
  try { return (await request("/me", "GET")).user; }
  catch { setCsrfToken(null); return null; }
}
export async function iniciarSesion(email: string, password: string) { return request("/login", "POST", { email, password }); }
export async function registrarCuenta(email: string, password: string, nombre: string) { return request("/register", "POST", { email, password, nombre }); }
export async function cerrarSesion() {
  const response = await fetch(`${BASE}/auth/logout`, { method: "POST", credentials: "include", headers: csrfToken ? { "X-CSRF-Token": csrfToken } : {} });
  if (!response.ok) throw new Error("No pudimos cerrar la sesión. Inténtalo de nuevo.");
  setCsrfToken(null);
}
