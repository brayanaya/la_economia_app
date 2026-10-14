import { readFileSync } from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";
import {
  aceptarCookies,
  CABECERAS_CORS,
  CLAVE_CARRITO,
  ORDEN_ID,
  simularConsultaOrden,
  type CuerpoOrden,
} from "./utils";

// Respuesta de busqueda del catalogo (tests/fixtures/busqueda.json).
const BUSQUEDA_MOCK = readFileSync(path.join(process.cwd(), "tests", "fixtures", "busqueda.json"), "utf-8");

test.describe("Checkout", () => {
  test("flujo de compra con red simulada: buscar, agregar, pagar y ver el ticket", async ({ page }) => {
    test.setTimeout(90_000);
    await aceptarCookies(page);

    // Busqueda del catalogo: respuesta instantanea con el fixture.
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

    // Creacion de orden: 201 simulado, sin escribir en la base de datos.
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
          id: ORDEN_ID,
          sede_id: cuerpo.sede_id,
          cliente_nombre: cuerpo.cliente_nombre,
          total: "4500.00",
          estado: "pendiente",
          creado_en: new Date().toISOString(),
        }),
      });
    });

    // Consulta del ticket tras la redireccion.
    await simularConsultaOrden(page, () => ({
      sede_id: captura.cuerpo?.sede_id ?? "",
      cliente_nombre: captura.cuerpo?.cliente_nombre ?? "",
    }));

    // 1. Home, busqueda y agregar al carrito.
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

    // 3. Formulario de cliente con datos validos.
    await page.getByLabel("Nombre completo").fill("Cliente de Prueba");
    await page.getByLabel("Teléfono celular").fill("3101234567");
    await page.getByLabel("Dirección de entrega").fill("Calle 10 # 5-20, Neiva");
    await page.getByLabel("Método de pago").selectOption("Nequi");
    await page.getByLabel(/Autorizo el tratamiento/).check();

    // 4. Envio: 201 simulado y redireccion al ticket.
    await page.getByRole("button", { name: /Confirmar pedido/ }).click();
    await expect(page).toHaveURL(new RegExp(`/pedidos/${ORDEN_ID}`), { timeout: 30_000 });
    await expect(page.getByRole("heading", { name: "¡Pedido confirmado!" })).toBeVisible({ timeout: 30_000 });

    const ticket = page.getByRole("article", { name: "Ticket del pedido" });
    await expect(ticket.getByRole("heading", { name: /Pedido #3F2A9C1E/ })).toBeVisible();
    await expect(ticket.getByText(ORDEN_ID)).toBeVisible();
    await expect(ticket.getByText("Cliente de Prueba", { exact: true })).toBeVisible();
    await expect(ticket.getByText("Leche Entera 1L")).toBeVisible();
    await expect(ticket.getByText(/4\.500/).first()).toBeVisible();

    // 5. Carrito vacio y payload correcto.
    await expect
      .poll(async () => page.evaluate((clave) => window.localStorage.getItem(clave), CLAVE_CARRITO))
      .toBe("[]");

    const cuerpo = captura.cuerpo;
    if (!cuerpo) throw new Error("No se envio ninguna orden al backend simulado");
    expect(cuerpo.cliente_nombre).toBe("Cliente de Prueba");
    expect(cuerpo.cliente_telefono).toBe("3101234567");
    expect(cuerpo.notas).toContain("Calle 10 # 5-20, Neiva");
    expect(cuerpo.notas).toContain("Nequi");
    expect(cuerpo.items).toHaveLength(1);
    expect(cuerpo.items[0].cantidad).toBe(1);
    expect(cuerpo.items[0].precio_unitario).toBeGreaterThan(0);

    // La busqueda se atendio con el mock, no con el backend real.
    expect(busquedas).toBeGreaterThan(0);
  });

  test("con el carrito vacio muestra el estado vacio", async ({ page }) => {
    await aceptarCookies(page);

    await page.goto("/checkout");
    await expect(page.getByRole("heading", { name: "Tu carrito está vacío" })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByRole("link", { name: "Volver al catálogo" })).toBeVisible();
  });
});
