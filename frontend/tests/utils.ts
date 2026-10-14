import type { Page } from "@playwright/test";

export const CLAVE_COOKIES = "la_economia_cookies_v1";
export const CLAVE_CARRITO = "la_economia_carrito_v1";
export const ORDEN_ID = "3f2a9c1e-7b4d-4e0a-9c55-2d1f8a6b7e90";
export const OTRO_ID = "0b7e5d52-4c1a-4f0e-8a31-6d9c2e4f1a77";
export const SEDE_ID = "a0000000-0000-0000-0000-000000000002";

export const CABECERAS_CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "content-type",
  "access-control-allow-methods": "GET, POST, OPTIONS",
};

export interface CuerpoOrden {
  sede_id: string;
  cliente_nombre: string;
  cliente_telefono: string | null;
  notas: string | null;
  items: { producto_id: string; nombre: string; cantidad: number; precio_unitario: number }[];
}

/** Evita que el banner de cookies tape la interfaz durante la prueba. */
export async function aceptarCookies(page: Page) {
  await page.addInitScript((clave) => {
    window.localStorage.setItem(clave, JSON.stringify({ analiticas: false, fecha: new Date().toISOString() }));
  }, CLAVE_COOKIES);
}

/** Simula GET /api/v1/ordenes/{uuid} con un ticket de ejemplo. */
export async function simularConsultaOrden(
  page: Page,
  obtenerDatos: () => { sede_id: string; cliente_nombre: string },
) {
  await page.route(/\/api\/v1\/ordenes\/[0-9a-f-]{36}$/i, async (route) => {
    if (route.request().method() !== "GET") {
      await route.fallback();
      return;
    }
    const datos = obtenerDatos();
    await route.fulfill({
      status: 200,
      headers: CABECERAS_CORS,
      contentType: "application/json",
      body: JSON.stringify({
        id: ORDEN_ID,
        sede_id: datos.sede_id,
        cliente_nombre: datos.cliente_nombre,
        total: "4500.00",
        estado: "pendiente",
        creado_en: "2026-10-13T21:30:00Z",
        items: [
          {
            nombre: "Leche Entera 1L",
            imagen_url: null,
            cantidad: 1,
            precio_unitario: "4500.00",
            subtotal: "4500.00",
          },
        ],
      }),
    });
  });
}
