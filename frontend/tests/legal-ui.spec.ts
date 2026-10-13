import { expect, test } from "@playwright/test";

const CLAVE_COOKIES = "la_economia_cookies_v1";

test.describe("UI legal", () => {
  test("footer visible, banner de cookies y persistencia de la decision", async ({ page }) => {
    await page.goto("/");

    const footer = page.getByRole("contentinfo");
    await expect(footer).toBeVisible();
    await expect(footer.getByRole("link", { name: "Política de privacidad" })).toBeVisible();
    await expect(footer.getByRole("link", { name: "Términos y condiciones" })).toBeVisible();

    const banner = page.getByRole("dialog", { name: "Preferencias de cookies" });
    await expect(banner).toBeVisible();

    await banner.getByRole("button", { name: "Aceptar todas" }).click();
    await expect(banner).toBeHidden();

    const guardado = await page.evaluate((clave) => window.localStorage.getItem(clave), CLAVE_COOKIES);
    expect(guardado).not.toBeNull();
    expect(JSON.parse(guardado as string).analiticas).toBe(true);
  });

  test("los enlaces del footer abren las paginas legales", async ({ page }) => {
    await page.addInitScript((clave) => {
      window.localStorage.setItem(clave, JSON.stringify({ analiticas: false, fecha: new Date().toISOString() }));
    }, CLAVE_COOKIES);

    await page.goto("/");
    const footer = page.getByRole("contentinfo");

    await footer.getByRole("link", { name: "Política de privacidad" }).click();
    await expect(page).toHaveURL(/\/privacidad$/);
    await expect(
      page.getByRole("heading", { level: 1, name: "Política de Tratamiento de Datos Personales" }),
    ).toBeVisible();
    await expect(page.getByText(/Ley 1581 de 2012/).first()).toBeVisible();

    await page.goto("/");
    await page.getByRole("contentinfo").getByRole("link", { name: "Términos y condiciones" }).click();
    await expect(page).toHaveURL(/\/terminos$/);
    await expect(page.getByRole("heading", { level: 1, name: "Términos y Condiciones de Uso" })).toBeVisible();
    await expect(page.getByText(/Ley 1480 de 2011/).first()).toBeVisible();
  });
});
