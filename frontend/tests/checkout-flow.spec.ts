import { readFileSync } from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

const CLAVE_COOKIES = "la_economia_cookies_v1";
const CLAVE_CARRITO = "la_economia_carrito_v1";

// Respuesta real de la API capturada una sola vez (tests/fixtures/busqueda.json).
const BUSQUEDA_MOCK = readFileSync(path.join(process.cwd(), "tests", "fixtures", "busqueda.json"), "utf-8");

const CABECERAS_CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "content-type",
  "access-control-allow-methods": "POST, OPTIONS",
};

interface CuerpoOrden {
  sede_id: string;
  cliente_nombre: string;
  cliente_telefono: string | null;
  notas: string | null;
  items: { producto_id: string; nombre: string; cantidad: number; precio_unitario: number }[];
}

test.describe("Checkout", () => {
  test("flujo de compra con red simulada: buscar, agregar, pagar y confirmar", async ({ page }) => {
    test.setTimeout(90_000);

    await page.addInitScript((clave) => {
      window.localStorage.setItem(clave, JSON.stringify({ analiticas: false, fecha: new Date().toISOString() }));
    }, CLAVE_COOKIES);

    // Búsqueda del catálogo: respuesta instantánea con el fixture.
    let busquedas = 0;
    await page.route("**/api/v1/busqueda/busqueda/semantica", async (route) => {
      if (route.request().method() === "OPTIONS") {
        await route.fulfill({ status: 204, headers: CABECERAS_CORS });
        return;
      }
      busquedas += 1;
      await route.fulfill({
        status: 200,
        headers: CABECERAS_CORS,
        contentType: "application/json",
        body: BUSQUEDA_MOCK,
      });
    });

    // Creación de orden: 201 simulado, sin escribir en la base de datos.
    const captura: { cuerpo: CuerpoOrden | null } = { cuerpo: null };
    await page.route("**/api/v1/ordenes/", async (route) => {
      const peticion = route.request();
      if (peticion.method() === "OPTIONS") {
        await route.fulfill({ status: 204, headers: CABECERAS_CORS });
        return;
      }
      if (peticion.method() !== "POST") {
        await route.continue();
        return;
      }
      const cuerpo = peticion.postDataJSON() as CuerpoOrden;
      captura.cuerpo = cuerpo;
      await route.fulfill({
        status: 201,
        headers: CABECERAS_CORS,
        contentType: "application/json",
        body: JSON.stringify({
          id: "test-orden-123",
          sede_id: cuerpo.sede_id,
          cliente_nombre: cuerpo.cliente_nombre,
          total: 5000,
          estado: "pendiente",
          creado_en: new Date().toISOString(),
        }),
      });
    });

    // 1. Home, búsqueda y agregar al carrito.
    await page.goto("/");
    await page.getByLabel("Buscar productos").fill("leche");
    await page.getByRole("button", { name: "Buscar", exact: true }).click();

    const botonAgregar = page.locator("article button:not([disabled])", { hasText: "Agregar al carrito" }).first();
    await expect(botonAgregar).toBeVisible({ timeout: 30_000 });
    await botonAgregar.click();

    const botonCarrito = page.getByRole("button", { name: "Abrir carrito, 1 artículos" });
    await expect(botonCarrito).toBeVisible();

    // 2. Drawer y paso a /checkout.
    await botonCarrito.click();
    const drawer = page.getByRole("dialog", { name: "Carrito de compras" });
    await expect(drawer).toBeVisible();
    await drawer.getByRole("link", { name: "Ir a pagar" }).click();
    await expect(page).toHaveURL(/\/checkout$/, { timeout: 30_000 });
    await expect(page.getByRole("heading", { level: 1, name: "Finalizar compra" })).toBeVisible({ timeout: 30_000 });

    // 3. Formulario de cliente con datos válidos.
    await page.getByLabel("Nombre completo").fill("Cliente de Prueba");
    await page.getByLabel("Teléfono celular").fill("3101234567");
    await page.getByLabel("Dirección de entrega").fill("Calle 10 # 5-20, Neiva");
    await page.getByLabel("Método de pago").selectOption("Nequi");
    await page.getByLabel(/Autorizo el tratamiento/).check();

    // 4. Envío y confirmación (201 simulado).
    await page.getByRole("button", { name: /Confirmar pedido/ }).click();
    await expect(page.getByRole("heading", { name: "¡Pedido confirmado!" })).toBeVisible();
    await expect(page.getByText(/Pedido #TEST-ORD/)).toBeVisible();
    await expect(page.getByText(/5\.000/).first()).toBeVisible();

    // 5. Carrito vacío y payload correcto.
    await expect
      .poll(async () => page.evaluate((clave) => window.localStorage.getItem(clave), CLAVE_CARRITO))
      .toBe("[]");

    const cuerpo = captura.cuerpo;
    if (!cuerpo) throw new Error("No se envió ninguna orden al backend simulado");
    expect(cuerpo.cliente_nombre).toBe("Cliente de Prueba");
    expect(cuerpo.cliente_telefono).toBe("3101234567");
    expect(cuerpo.notas).toContain("Calle 10 # 5-20, Neiva");
    expect(cuerpo.notas).toContain("Nequi");
    expect(cuerpo.items).toHaveLength(1);
    expect(cuerpo.items[0].cantidad).toBe(1);
    expect(cuerpo.items[0].precio_unitario).toBeGreaterThan(0);

    // La búsqueda se atendió con el mock, no con el backend real.
    expect(busquedas).toBeGreaterThan(0);
  });

  test("con el carrito vacío muestra el estado vacío", async ({ page }) => {
    await page.addInitScript((clave) => {
      window.localStorage.setItem(clave, JSON.stringify({ analiticas: false, fecha: new Date().toISOString() }));
    }, CLAVE_COOKIES);

    await page.goto("/checkout");
    await expect(page.getByRole("heading", { name: "Tu carrito está vacío" })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByRole("link", { name: "Volver al catálogo" })).toBeVisible();
  });
});
