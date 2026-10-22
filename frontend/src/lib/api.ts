// Acepta NEXT_PUBLIC_API_URL con o sin el sufijo /api/v1 y barras finales: BASE agrega /api/v1 una sola vez.
export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
  .replace(/\/+$/, "")
  .replace(/\/api\/v1$/, "");
const BASE = `${API_URL}/api/v1`;

export type Sede = { nombre: string; id: string | null };

// IDs reales de la tabla sedes (UUID); si cambias el seed, actualiza estos valores.
export const SEDES: Sede[] = [
  { nombre: "Todas", id: null },
  { nombre: "Santa Isabel", id: "a0000000-0000-0000-0000-000000000001" },
  { nombre: "Machines", id: "a0000000-0000-0000-0000-000000000002" },
];

// Admin types
export type VentasResumen = {
  total_ingresos: number;
  ordenes_pagadas: number;
  periodo_dias: number;
};

export type ProductoStockBajo = {
  producto_id: string;
  producto_nombre: string;
  codigo_barras: string;
  sede_id: string;
  sede_nombre: string;
  stock_actual: number;
  stock_minimo: number;
  stock_reservado: number;
  disponible: number;
};

export type InventarioEstado = {
  productos_bajo_stock: ProductoStockBajo[];
  total_productos_bajo_stock: number;
};

export type MetricasIA = {
  busquedas_semanticas: number;
  interacciones_agente: number;
  embeddings_productos: number;
  periodo_dias: number;
};

export type EstadisticasAdmin = {
  ventas: VentasResumen;
  inventario: InventarioEstado;
  ia: MetricasIA;
};

export type OrdenReciente = {
  id: string;
  ticket_id: string;
  sede_id: string;
  sede_nombre: string;
  cliente_nombre: string;
  total: number;
  estado: string;
  creado_en: string | null;
  items_count: number;
};

export type Producto = {
  id: string | number;
  nombre: string;
  precio: number;
  stock: number;
  sede?: string;
  imagen?: string;
  similitud?: number; // 0 a 1
};

type Raw = Record<string, unknown>;

function num(v: unknown, def = 0): number {
  const n = Number(v);
  return Number.isFinite(n) ? n : def;
}

export function normalizarProducto(raw: Raw, i = 0): Producto {
  const sim = raw.similitud ?? raw.similarity ?? raw.score;
  let similitud: number | undefined;
  if (sim !== undefined && sim !== null) {
    const s = num(sim, NaN);
    if (!Number.isNaN(s)) similitud = s > 1 ? s / 100 : s;
  }
  const sede = raw.sede ?? raw.sede_nombre;
  const imagen = raw.imagen ?? raw.imagen_url ?? raw.image;
  return {
    id: (raw.id ?? raw.producto_id ?? i) as string | number,
    nombre: String(raw.nombre ?? raw.name ?? raw.descripcion ?? "Producto"),
    precio: num(raw.precio ?? raw.precio_venta ?? raw.price),
    stock: Number(raw.stock_sede ?? raw.stock ?? 0) || 0,
    sede: sede ? String(sede) : undefined,
    imagen: imagen ? String(imagen) : undefined,
    similitud,
  };
}

function extraerLista(data: unknown): Raw[] {
  if (Array.isArray(data)) return data as Raw[];
  if (data && typeof data === "object") {
    const d = data as Raw;
    for (const k of ["resultados", "productos", "items", "data"]) {
      if (Array.isArray(d[k])) return d[k] as Raw[];
    }
  }
  return [];
}

async function post(path: string, body: unknown): Promise<unknown> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function buscarSemantica(consulta: string, sedeId: string | null, topK = 8): Promise<Producto[]> {
  const data = await post("/busqueda/busqueda/semantica", { consulta, sede_id: sedeId, top_k: topK });
  return extraerLista(data).map(normalizarProducto);
}

export async function chatear(
  mensaje: string,
  sedeId: string | null
): Promise<{ respuesta: string; productos: Producto[] }> {
  const data = (await post("/agente/chat", { mensaje, sede_id: sedeId })) as Raw;
  const respuesta = String(data.respuesta ?? data.response ?? data.message ?? "No pude generar una respuesta.");
  const productos = extraerLista({ productos: data.productos_recomendados }).map(normalizarProducto);
  return { respuesta, productos };
}

export async function registrarConsentimiento(
  aceptoPolitica: boolean,
  aceptoCookies: boolean,
  versionPolitica: string
): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/legal/consentimiento`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        acepto_politica: aceptoPolitica,
        acepto_cookies: aceptoCookies,
        version_politica: versionPolitica,
      }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

async function get(path: string): Promise<unknown> {
  const res = await fetch(`${BASE}${path}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function obtenerEstadisticasAdmin(
  periodoDias = 30
): Promise<EstadisticasAdmin> {
  return (await get(`/admin/estadisticas?periodo_dias=${periodoDias}`)) as EstadisticasAdmin;
}

export async function obtenerOrdenesRecientes(
  limite = 10
): Promise<OrdenReciente[]> {
  return (await get(`/admin/ordenes-recientes?limite=${limite}`)) as OrdenReciente[];
}
