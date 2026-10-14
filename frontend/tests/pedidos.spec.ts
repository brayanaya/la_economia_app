import { expect, test } from "@playwright/test";
import {
  aceptarCookies,
  CABECERAS_CORS,
  ORDEN_ID,
  OTRO_ID,
  SEDE_ID,
  simularConsultaOrden,
} from "./utils";

test.describe("Consulta de pedidos", () => {
  test.beforeEach(async ({ page }) => {
    await aceptarCookies(page);
  });

  test("consultar un pedido por su numero muestra el ticket", async ({ page }) => {
    await simularConsultaOrden(page, () => ({ sede_id: SEDE_ID, cliente_nombre: "Cliente de Prueba" }));

    await page.goto("/pedidos");
    await expect(page.getByRole("heading", { level: 1, name: "Consulta tu pedido" })).toBeVisible({
      timeout: 30_000,
    });
    await page.getByLabel("Número de pedido").fill(ORDEN_ID);
    await page.getByRole("button", { name: "Consultar pedido" }).click();

    await expect(page).toHaveURL(new RegExp(`/pedidos/${ORDEN_ID}$`), { timeout: 30_000 });
    const ticket = page.getByRole("article", { name: "Ticket del pedido" });
    await expect(ticket.getByRole("heading", { level: 1, name: /Pedido #3F2A9C1E/ })).toBeVisible({
      timeout: 30_000,
    });
    await expect(ticket.getByText("Cliente de Prueba", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "¡Pedido confirmado!" })).toHaveCount(0);
  });

  test("un numero con formato invalido muestra un error y no navega", async ({ page }) => {
    await page.goto("/pedidos");
    await page.getByLabel("Número de pedido").fill("abc");
    await page.getByRole("button", { name: "Consultar pedido" }).click();

    // Next.js inyecta su propio role="alert" (route announcer): se usa el id del error del formulario.
    await expect(page.locator("#pedido-id-error")).toContainText("36 caracteres");
    await expect(page).toHaveURL(/\/pedidos$/);
  });

  test("un pedido inexistente muestra el estado de no encontrado", async ({ page }) => {
    await page.route(`**/api/v1/ordenes/${OTRO_ID}`, async (route) => {
      await route.fulfill({
        status: 404,
        headers: CABECERAS_CORS,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Pedido no encontrado" }),
      });
    });

    await page.goto("/pedidos");
    await page.getByLabel("Número de pedido").fill(OTRO_ID);
    await page.getByRole("button", { name: "Consultar pedido" }).click();

    await expect(page).toHaveURL(new RegExp(`/pedidos/${OTRO_ID}$`), { timeout: 30_000 });
    await expect(page.getByRole("heading", { name: "Pedido no encontrado" })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByRole("link", { name: "Consultar otro pedido" })).toBeVisible();
  });

  test("el footer enlaza a la consulta de pedidos", async ({ page }) => {
    await page.goto("/checkout");
    await page.getByRole("contentinfo").getByRole("link", { name: "Consultar mi pedido" }).click();
    await expect(page).toHaveURL(/\/pedidos$/, { timeout: 30_000 });
  });
});
