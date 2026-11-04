// carrito-v1
import { getCsrfToken } from "@/lib/auth";
const RAW = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const ORDENES_API = RAW.replace(/\/+$/, "").replace(/\/api\/v1$/, "") + "/api/v1";

export interface ItemOrdenPayload {
  producto_id: string;
  nombre: string;
  cantidad: number;
  precio_unitario: number;
  imagen_url?: string | null;
}

export type MetodoPago = "contra_entrega" | "bre_b" | "wompi";

export interface OrdenPayload {
  sede_id: string;
  cliente_nombre: string;
  cliente_telefono?: string | null;
  notas?: string | null;
  metodo_pago?: MetodoPago;
  items: ItemOrdenPayload[];
}

export interface OrdenCreada {
  id: string;
  sede_id: string;
  cliente_nombre: string;
  total: string | number;
  estado: string;
  creado_en: string;
}

export interface DetalleOrdenConsulta {
  nombre: string;
  imagen_url: string | null;
  cantidad: number;
  precio_unitario: string | number;
  subtotal: string | number;
}

/** Vista publica de un pedido: el backend no incluye telefono ni notas. */
export interface OrdenConsulta {
  id: string;
  sede_id: string;
  cliente_nombre: string;
  total: string | number;
  estado: string;
  creado_en: string;
  items: DetalleOrdenConsulta[];
  metodo_pago?: string | null;
}

function mensajeError(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { loc?: unknown[]; msg?: string };
    const campo = Array.isArray(first.loc) ? String(first.loc[first.loc.length - 1]) : "dato";
    return `Dato invalido (${campo}): ${first.msg ?? "revisa el formulario"}`;
  }
  return "No se pudo procesar la orden";
}

export async function crearOrden(payload: OrdenPayload): Promise<OrdenCreada> {
  const res = await fetch(`${ORDENES_API}/ordenes/`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(getCsrfToken() ? { "X-CSRF-Token": getCsrfToken()! } : {}) },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let detail: unknown = null;
    try {
      detail = ((await res.json()) as { detail?: unknown }).detail;
    } catch {
      /* sin cuerpo JSON */
    }
    throw new Error(mensajeError(detail));
  }
  return (await res.json()) as OrdenCreada;
}

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function esIdPedidoValido(id: string): boolean {
  return UUID_RE.test(id.trim());
}

export class PedidoNoEncontradoError extends Error {
  constructor() {
    super("Pedido no encontrado");
    this.name = "PedidoNoEncontradoError";
  }
}

export async function consultarOrden(id: string, signal?: AbortSignal): Promise<OrdenConsulta> {
  const res = await fetch(`${ORDENES_API}/ordenes/${encodeURIComponent(id.trim())}`, {
    cache: "no-store",
    signal,
  });
  if (res.status === 404) throw new PedidoNoEncontradoError();
  if (!res.ok) throw new Error("No se pudo consultar el pedido");
  return (await res.json()) as OrdenConsulta;
}

export interface InicioPagoWompi {
  pago: {
    id: string;
    estado: string;
    referencia: string;
    monto_centavos: number;
    moneda: string;
    transaccion_id?: string | null;
    creado_en: string;
  };
  accion: string;
  campos: Record<string, string>;
}

export async function iniciarPagoWompi(ordenId: string): Promise<InicioPagoWompi> {
  const res = await fetch(`${ORDENES_API}/pagos/ordenes/${encodeURIComponent(ordenId)}/iniciar`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(getCsrfToken() ? { "X-CSRF-Token": getCsrfToken()! } : {}),
    },
    body: JSON.stringify({ metodo: "wompi" }),
  });
  if (!res.ok) {
    let detail: unknown = null;
    try { detail = ((await res.json()) as { detail?: unknown }).detail; } catch {}
    if (typeof detail === "string" && detail.includes("pasarela de pago en linea no esta configurada")) {
      throw new Error("El pago en línea no está disponible en este momento. Puedes usar contra entrega o Bre-B.");
    }
    throw new Error(typeof detail === "string" ? detail : "No se pudo iniciar el pago con Wompi");
  }
  return (await res.json()) as InicioPagoWompi;
}

export async function consultarEstadoPago(ordenId: string, signal?: AbortSignal): Promise<{
  orden_id: string;
  orden_estado: string;
  metodo?: string | null;
  pasarela_configurada: boolean;
  pago?: {
    id: string;
    estado: string;
    referencia: string;
    monto_centavos: number;
    moneda: string;
    transaccion_id?: string | null;
    creado_en: string;
  } | null;
}> {
  const res = await fetch(`${ORDENES_API}/pagos/ordenes/${encodeURIComponent(ordenId)}`, {
    cache: "no-store",
    signal,
  });
  if (res.status === 404) throw new PedidoNoEncontradoError();
  if (!res.ok) throw new Error("No se pudo consultar el estado del pago");
  return (await res.json()) as {
    orden_id: string;
    orden_estado: string;
    metodo?: string | null;
    pasarela_configurada: boolean;
    pago?: {
      id: string;
      estado: string;
      referencia: string;
      monto_centavos: number;
      moneda: string;
      transaccion_id?: string | null;
      creado_en: string;
    } | null;
  };
}

export async function obtenerConfiguracionPagos(): Promise<{ pasarela_configurada: boolean }> {
  const res = await fetch(`${ORDENES_API}/pagos/configuracion`, { cache: "no-store" });
  if (!res.ok) throw new Error("No se pudo obtener la configuración de pagos");
  return (await res.json()) as { pasarela_configurada: boolean };
}
