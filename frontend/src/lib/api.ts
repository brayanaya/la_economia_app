// Acepta NEXT_PUBLIC_API_URL con o sin el sufijo /api/v1 y barras finales: BASE agrega /api/v1 una sola vez.
export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
  .replace(/\/+$/, "")
  .replace(/\/api\/v1$/, "");
const BASE = `${API_URL}/api/v1`;

export type Sede = { nombre: string; id: number | null };

// AJUSTA los IDs a los reales de tu base de datos
export const SEDES: Sede[] = [
  { nombre: "Todas", id: null },
  { nombre: "Santa Isabel", id: 1 },
  { nombre: "Machines", id: 2 },
];

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
    stock: num(raw.stock ?? raw.stock_disponible ?? raw.cantidad),
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

export async function buscarSemantica(consulta: string, sedeId: number | null, topK = 8): Promise<Producto[]> {
  const data = await post("/busqueda/busqueda/semantica", { consulta, sede_id: sedeId, top_k: topK });
  return extraerLista(data).map(normalizarProducto);
}

export async function chatear(
  mensaje: string,
  sedeId: number | null
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
