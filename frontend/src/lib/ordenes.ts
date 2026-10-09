// carrito-v1
const RAW = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const ORDENES_API = RAW.replace(/\/+$/, "").replace(/\/api\/v1$/, "") + "/api/v1";

export interface ItemOrdenPayload {
  producto_id: string;
  nombre: string;
  cantidad: number;
  precio_unitario: number;
  imagen_url?: string | null;
}

export interface OrdenPayload {
  sede_id: string;
  cliente_nombre: string;
  cliente_telefono?: string | null;
  notas?: string | null;
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
    headers: { "Content-Type": "application/json" },
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
