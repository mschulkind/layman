import { test, expect } from "@playwright/test";

async function focusDemo(page: import("@playwright/test").Page) {
  await page.getByTestId("demo-container").click();
}

test.describe("Demo page loads", () => {
  test("renders the title and empty state", async ({ page }) => {
    await page.goto("/demo/");
    await expect(page.getByText("Interactive Demo")).toBeVisible();
    await expect(page.getByTestId("demo-container")).toBeVisible();
    await expect(page.getByTestId("empty-state")).toBeVisible();
    await expect(page.getByText("to spawn a window")).toBeVisible();
  });

  test("renders layout switcher with all layouts", async ({ page }) => {
    await page.goto("/demo/");
    await expect(page.getByTestId("layout-switcher")).toBeVisible();
    await expect(page.getByTestId("layout-btn-MasterStack")).toBeVisible();
    await expect(page.getByTestId("layout-btn-Autotiling")).toBeVisible();
    await expect(page.getByTestId("layout-btn-Grid")).toBeVisible();
    await expect(page.getByTestId("layout-btn-ThreeColumn")).toBeVisible();
  });

  test("renders status bar showing 0 windows", async ({ page }) => {
    await page.goto("/demo/");
    const statusBar = page.getByTestId("status-bar");
    await expect(statusBar).toBeVisible();
    await expect(statusBar.getByText("0 windows")).toBeVisible();
    await expect(statusBar.getByText("MasterStack")).toBeVisible();
  });
});

test.describe("Keyboard shortcuts - window management", () => {
  test("N spawns a window", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await expect(page.getByTestId("window-win-1")).toBeVisible();
    await expect(
      page.getByTestId("status-bar").getByText("1 window"),
    ).toBeVisible();
    await expect(page.getByTestId("empty-state")).not.toBeVisible();
  });

  test("spawning multiple windows works", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await page.keyboard.press("n");
    await page.keyboard.press("n");
    await expect(page.getByTestId("window-win-1")).toBeVisible();
    await expect(page.getByTestId("window-win-2")).toBeVisible();
    await expect(page.getByTestId("window-win-3")).toBeVisible();
    await expect(
      page.getByTestId("status-bar").getByText("3 windows"),
    ).toBeVisible();
  });

  test("Q closes the focused window", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await page.keyboard.press("n");
    await expect(
      page.getByTestId("status-bar").getByText("2 windows"),
    ).toBeVisible();
    await page.keyboard.press("q");
    await expect(
      page.getByTestId("status-bar").getByText("1 window"),
    ).toBeVisible();
  });

  test("Q on last window returns to empty state", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await page.keyboard.press("q");
    await expect(page.getByTestId("empty-state")).toBeVisible();
    await expect(
      page.getByTestId("status-bar").getByText("0 windows"),
    ).toBeVisible();
  });
});

test.describe("Keyboard shortcuts - focus navigation", () => {
  test("L moves focus to next window", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await page.keyboard.press("n");
    await page.keyboard.press("l");
    await expect(
      page.getByTestId("status-bar").getByText("Terminal #1"),
    ).toBeVisible();
  });

  test("H moves focus to previous window", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await page.keyboard.press("n");
    await page.keyboard.press("h");
    await expect(
      page.getByTestId("status-bar").getByText("Terminal #1"),
    ).toBeVisible();
  });

  test("arrow keys work for focus navigation", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await page.keyboard.press("n");
    await page.keyboard.press("ArrowRight");
    await expect(
      page.getByTestId("status-bar").getByText("Terminal #1"),
    ).toBeVisible();
  });
});

test.describe("Keyboard shortcuts - layout switching", () => {
  test("1-4 switches layouts", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await page.keyboard.press("n");

    const statusBar = page.getByTestId("status-bar");

    await page.keyboard.press("2");
    await expect(statusBar.getByText("Autotiling")).toBeVisible();

    await page.keyboard.press("3");
    await expect(statusBar.getByText("Grid")).toBeVisible();

    await page.keyboard.press("4");
    await expect(statusBar.getByText("ThreeColumn")).toBeVisible();

    await page.keyboard.press("1");
    await expect(statusBar.getByText("MasterStack")).toBeVisible();
  });
});

test.describe("Keyboard shortcuts - window movement", () => {
  test("Enter swaps focused window with master", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await page.keyboard.press("n");
    await page.keyboard.press("l");
    await page.keyboard.press("Enter");
    await expect(
      page.getByTestId("status-bar").getByText("Terminal #1"),
    ).toBeVisible();
  });

  test("Shift+J moves window down in stack", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await page.keyboard.press("n");
    await page.keyboard.press("n");
    await page.keyboard.press("Shift+J");
    await expect(
      page.getByTestId("status-bar").getByText("3 windows"),
    ).toBeVisible();
  });
});

test.describe("Help overlay", () => {
  test("? toggles help overlay", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await expect(page.getByTestId("help-overlay")).not.toBeVisible();

    await page.keyboard.press("?");
    const helpOverlay = page.getByTestId("help-overlay");
    await expect(helpOverlay).toBeVisible();
    await expect(
      helpOverlay.getByRole("heading", { name: /Keyboard Shortcuts/ }),
    ).toBeVisible();
    await expect(helpOverlay.getByText("Spawn window")).toBeVisible();

    await page.keyboard.press("?");
    await expect(page.getByTestId("help-overlay")).not.toBeVisible();
  });

  test("clicking backdrop closes help overlay", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("?");
    await expect(page.getByTestId("help-overlay")).toBeVisible();

    await page
      .getByTestId("help-overlay")
      .click({ position: { x: 10, y: 10 } });
    await expect(page.getByTestId("help-overlay")).not.toBeVisible();
  });
});

test.describe("Layout switcher buttons", () => {
  test("clicking layout buttons switches the layout", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await page.keyboard.press("n");

    const statusBar = page.getByTestId("status-bar");

    await page.getByTestId("layout-btn-Grid").click();
    await expect(statusBar.getByText("Grid")).toBeVisible();

    await page.getByTestId("layout-btn-ThreeColumn").click();
    await expect(statusBar.getByText("ThreeColumn")).toBeVisible();

    await page.getByTestId("layout-btn-MasterStack").click();
    await expect(statusBar.getByText("MasterStack")).toBeVisible();
  });
});

test.describe("Window clicking", () => {
  test("clicking a window focuses it", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await page.keyboard.press("n");

    await page.getByTestId("window-win-1").click();
    await expect(
      page.getByTestId("status-bar").getByText("Terminal #1"),
    ).toBeVisible();
  });
});

test.describe("Full workflow", () => {
  test("spawn windows, switch layouts, navigate, and close", async ({
    page,
  }) => {
    await page.goto("/demo/");
    await focusDemo(page);

    const statusBar = page.getByTestId("status-bar");

    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("n");
    }
    await expect(statusBar.getByText("4 windows")).toBeVisible();

    for (const key of ["2", "3", "4", "1"]) {
      await page.keyboard.press(key);
    }

    await page.keyboard.press("l");
    await page.keyboard.press("l");
    await page.keyboard.press("h");

    await page.keyboard.press("q");
    await expect(statusBar.getByText("3 windows")).toBeVisible();

    await page.keyboard.press("?");
    await expect(page.getByTestId("help-overlay")).toBeVisible();
    await page.keyboard.press("?");
    await expect(page.getByTestId("help-overlay")).not.toBeVisible();

    await page.keyboard.press("q");
    await page.keyboard.press("q");
    await page.keyboard.press("q");
    await expect(page.getByTestId("empty-state")).toBeVisible();
  });
});
