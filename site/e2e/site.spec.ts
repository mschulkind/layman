import { test, expect } from "@playwright/test";

test.describe("Landing page", () => {
  test("renders the hero section", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.locator(".hero h1").getByText("Per-workspace"),
    ).toBeVisible();
    await expect(
      page.locator(".hero h1").getByText("tiling"),
    ).toBeVisible();
  });

  test("has a working Get Started button", async ({ page }) => {
    await page.goto("/");
    const getStarted = page.getByRole("link", { name: /Get Started/i }).first();
    await expect(getStarted).toBeVisible();
  });

  test("renders the features section", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "Per-Workspace Layouts" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Zero Latency" }),
    ).toBeVisible();
  });

  test("renders the layout showcase", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("button", { name: "MasterStack" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Autotiling" }),
    ).toBeVisible();
  });

  test("layout tabs switch content", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Grid" }).click();
    await expect(page.locator("#layout-title")).toHaveText("Grid");
  });

  test("has a link to the demo", async ({ page }) => {
    await page.goto("/");
    const demoLink = page.getByRole("link", { name: /Try the Demo/i }).first();
    await expect(demoLink).toBeVisible();
  });
});

test.describe("404 page", () => {
  test("shows 404 for unknown routes", async ({ page }) => {
    await page.goto("/nonexistent-page/");
    await expect(page.getByText("404")).toBeVisible();
    await expect(page.getByText("Page not found")).toBeVisible();
  });

  test("has a link back to home", async ({ page }) => {
    await page.goto("/nonexistent-page/");
    const homeLink = page.getByRole("link", { name: /Back to Home/i });
    await expect(homeLink).toBeVisible();
    await expect(homeLink).toHaveAttribute("href", "/");
  });

  test("has a link to the demo", async ({ page }) => {
    await page.goto("/nonexistent-page/");
    const demoLink = page.getByRole("link", { name: /Try the Demo/i });
    await expect(demoLink).toBeVisible();
    await expect(demoLink).toHaveAttribute("href", "/demo/");
  });
});
