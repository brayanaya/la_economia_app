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

// ===== NUEVO: Tipos para Recetas =====
export type RecetaIngrediente = {
  nombre: string;
  cantidad: string;
  busqueda_catalogo: string;
  obligatorio: boolean;
  notas: string;
};

export type Receta = {
  id: string;
  nombre: string;
  descripcion: string;
  categoria: string;
  tiempo_min: number;
  porciones: number;
  costo_estimado_cop: number;
  imagen_url: string | null;
  ingredientes: RecetaIngrediente[];
  pasos: string[];
  tags: string[];
};

// ===== NUEVO: Tipos para Presupuesto =====
export type PresupuestoItem = {
  termino_busqueda: string;
  cantidad: number;
  unidad: string;
  producto_id?: string;
  producto_nombre?: string;
  producto_imagen_url?: string;
  precio_unitario: number;
  subtotal: number;
  estado: string;
  mensaje: string;
};

export type Presupuesto = {
  items: PresupuestoItem[];
  presupuesto_limite?: number;
  total_con_precio: number;
  total_sin_precio: number;
  total_no_encontrados: number;
  total_sin_stock: number;
  estado: string;
  mensaje: string;
  presupuesto_excedido: boolean;
  diferencia_presupuesto: number;
  sede_id?: string;
  catalogo_conectado: boolean;
  proveedor_usado: string;
  resumen_usuario: string;
  limitaciones?: string[];
};

// ===== NUEVO: Tipos para Comparación =====
export type ComparacionItem = {
  id: string;
  sku: string;
  nombre: string;
  marca?: string;
  presentacion?: string;
  imagen_url?: string;
  precio_final: number;
  precio_por_unidad_base?: number;
  unidad_medida?: string;
  stock: number;
  disponible: boolean;
  tiene_promocion: boolean;
  puntuacion: number;
  razones: string[];
};

export type Comparacion = {
  tipo_comparacion: string;
  criterio: string;
  productos: ComparacionItem[];
  mejor_opcion_id?: string;
  explicacion: string;
  limitaciones: string[];
  sede_id?: string;
  comparables: boolean;
};

// ===== NUEVO: Tipos para Acciones de Carrito =====
export type CartActionItem = {
  producto_id: string;
  nombre: string;
  cantidad: number;
  precio_unitario: number;
  sede_id: string;
  imagen_url?: string;
};

export type CartActionAdd = {
  tipo: "add";
  items: CartActionItem[];
};

export type CartActionRemove = {
  tipo: "remove";
  producto_ids: string[];
  sede_id: string;
};

export type CartActionUpdate = {
  tipo: "update";
  items: CartActionItem[];
};

export type CartActionClear = {
  tipo: "clear";
  sede_id?: string;
};

export type CartActionList = {
  tipo: "list";
  sede_id?: string;
};

export type CartActionConfirmClear = {
  tipo: "confirm_clear";
  sede_id?: string;
  mensaje: string;
};

export type CartAction = CartActionAdd | CartActionRemove | CartActionUpdate | CartActionClear | CartActionList | CartActionConfirmClear;

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
): Promise<{
  respuesta: string;
  productos: Producto[];
  receta?: Receta;
  presupuesto?: Presupuesto;
  comparacion?: Comparacion;
  cart_actions?: CartAction[];
}> {
  const data = (await post("/agente/chat", { mensaje, sede_id: sedeId })) as Raw;
  const respuesta = String(data.respuesta ?? data.response ?? data.message ?? "No pude generar una respuesta.");
  const productos = extraerLista({ productos: data.productos_recomendados }).map(normalizarProducto);
  const receta = data.receta ? (data.receta as Raw) : undefined;
  const presupuesto = data.presupuesto ? (data.presupuesto as Raw) : undefined;
  const comparacion = data.comparacion ? (data.comparacion as Raw) : undefined;
  const cart_actions = data.cart_actions ? (data.cart_actions as Raw[]) : undefined;
  return {
    respuesta,
    productos,
    receta: receta ? normalizarReceta(receta) : undefined,
    presupuesto: presupuesto ? normalizarPresupuesto(presupuesto) : undefined,
    comparacion: comparacion ? normalizarComparacion(comparacion) : undefined,
    cart_actions: cart_actions ? cart_actions.map(normalizarCartAction) : undefined,
  };
}

function normalizarReceta(raw: Raw): Receta {
  return {
    id: String(raw.id ?? ""),
    nombre: String(raw.nombre ?? ""),
    descripcion: String(raw.descripcion ?? ""),
    categoria: String(raw.categoria ?? ""),
    tiempo_min: num(raw.tiempo_min ?? raw.tiempoMin),
    porciones: num(raw.porciones),
    costo_estimado_cop: num(raw.costo_estimado_cop ?? raw.costoEstimadoCop),
    imagen_url: raw.imagen_url ? String(raw.imagen_url) : null,
    ingredientes: Array.isArray(raw.ingredientes) ? raw.ingredientes.map((i: unknown) => normalizarIngrediente(i as Raw)) : [],
    pasos: Array.isArray(raw.pasos) ? raw.pasos.map(String) : [],
    tags: Array.isArray(raw.tags) ? raw.tags.map(String) : [],
  };
}

function normalizarIngrediente(raw: Raw): RecetaIngrediente {
  return {
    nombre: String(raw.nombre ?? ""),
    cantidad: String(raw.cantidad ?? ""),
    busqueda_catalogo: String(raw.busqueda_catalogo ?? raw.busquedaCatalogo ?? ""),
    obligatorio: Boolean(raw.obligatorio ?? true),
    notas: String(raw.notas ?? ""),
  };
}

function normalizarPresupuesto(raw: Raw): Presupuesto {
  return {
    items: Array.isArray(raw.items) ? raw.items.map((i: unknown) => normalizarPresupuestoItem(i as Raw)) : [],
    presupuesto_limite: raw.presupuesto_limite !== undefined ? num(raw.presupuesto_limite) : undefined,
    total_con_precio: num(raw.total_con_precio),
    total_sin_precio: num(raw.total_sin_precio),
    total_no_encontrados: num(raw.total_no_encontrados),
    total_sin_stock: num(raw.total_sin_stock),
    estado: String(raw.estado ?? "ok"),
    mensaje: String(raw.mensaje ?? ""),
    presupuesto_excedido: Boolean(raw.presupuesto_excedido ?? false),
    diferencia_presupuesto: num(raw.diferencia_presupuesto),
    sede_id: raw.sede_id ? String(raw.sede_id) : undefined,
    catalogo_conectado: Boolean(raw.catalogo_conectado ?? true),
    proveedor_usado: String(raw.proveedor_usado ?? "desconocido"),
    resumen_usuario: String(raw.resumen_usuario ?? ""),
  };
}

function normalizarPresupuestoItem(raw: Raw): PresupuestoItem {
  return {
    termino_busqueda: String(raw.termino_busqueda ?? ""),
    cantidad: num(raw.cantidad),
    unidad: String(raw.unidad ?? ""),
    producto_id: raw.producto_id ? String(raw.producto_id) : undefined,
    producto_nombre: raw.producto_nombre ? String(raw.producto_nombre) : undefined,
    producto_imagen_url: raw.producto_imagen_url ? String(raw.producto_imagen_url) : undefined,
    precio_unitario: num(raw.precio_unitario),
    subtotal: num(raw.subtotal),
    estado: String(raw.estado ?? ""),
    mensaje: String(raw.mensaje ?? ""),
  };
}

function normalizarComparacion(raw: Raw): Comparacion {
  return {
    tipo_comparacion: String(raw.tipo_comparacion ?? ""),
    criterio: String(raw.criterio ?? ""),
    productos: Array.isArray(raw.productos) ? raw.productos.map((i: unknown) => normalizarComparacionItem(i as Raw)) : [],
    mejor_opcion_id: raw.mejor_opcion_id ? String(raw.mejor_opcion_id) : undefined,
    explicacion: String(raw.explicacion ?? ""),
    limitaciones: Array.isArray(raw.limitaciones) ? raw.limitaciones.map(String) : [],
    sede_id: raw.sede_id ? String(raw.sede_id) : undefined,
    comparables: Boolean(raw.comparables ?? true),
  };
}

function normalizarComparacionItem(raw: Raw): ComparacionItem {
  return {
    id: String(raw.id ?? ""),
    sku: String(raw.sku ?? ""),
    nombre: String(raw.nombre ?? ""),
    marca: raw.marca ? String(raw.marca) : undefined,
    presentacion: raw.presentacion ? String(raw.presentacion) : undefined,
    imagen_url: raw.imagen_url ? String(raw.imagen_url) : undefined,
    precio_final: num(raw.precio_final),
    precio_por_unidad_base: raw.precio_por_unidad_base !== undefined ? num(raw.precio_por_unidad_base) : undefined,
    unidad_medida: raw.unidad_medida ? String(raw.unidad_medida) : undefined,
    stock: num(raw.stock),
    disponible: Boolean(raw.disponible ?? false),
    tiene_promocion: Boolean(raw.tiene_promocion ?? false),
    puntuacion: num(raw.puntuacion),
    razones: Array.isArray(raw.razones) ? raw.razones.map(String) : [],
  };
}

function normalizarCartAction(raw: Raw): CartAction {
  const tipo = String(raw.tipo ?? "");
  if (tipo === "add") {
    return {
      tipo: "add",
      items: Array.isArray(raw.items) ? raw.items.map((i: unknown) => normalizarCartActionItem(i as Raw)) : [],
    };
  }
  if (tipo === "remove") {
    return {
      tipo: "remove",
      producto_ids: Array.isArray(raw.producto_ids) ? raw.producto_ids.map(String) : [],
      sede_id: String(raw.sede_id ?? ""),
    };
  }
  if (tipo === "update") {
    return {
      tipo: "update",
      items: Array.isArray(raw.items) ? raw.items.map((i: unknown) => normalizarCartActionItem(i as Raw)) : [],
    };
  }
  if (tipo === "clear") {
    return {
      tipo: "clear",
      sede_id: raw.sede_id ? String(raw.sede_id) : undefined,
    };
  }
  if (tipo === "list") {
    return {
      tipo: "list",
      sede_id: raw.sede_id ? String(raw.sede_id) : undefined,
    };
  }
  if (tipo === "confirm_clear") {
    return {
      tipo: "confirm_clear",
      sede_id: raw.sede_id ? String(raw.sede_id) : undefined,
      mensaje: String(raw.mensaje ?? "¿Estás seguro de que quieres vaciar el carrito? Esta acción no se puede deshacer."),
    };
  }
  // Fallback - should not happen
  return { tipo: "list" };
}

function normalizarCartActionItem(raw: Raw): CartActionItem {
  return {
    producto_id: String(raw.producto_id ?? ""),
    nombre: String(raw.nombre ?? ""),
    cantidad: num(raw.cantidad),
    precio_unitario: num(raw.precio_unitario),
    sede_id: String(raw.sede_id ?? ""),
    imagen_url: raw.imagen_url ? String(raw.imagen_url) : undefined,
  };
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