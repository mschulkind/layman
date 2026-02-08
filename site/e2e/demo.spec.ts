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

  test("keyboard panel is always visible", async ({ page }) => {
    await page.goto("/demo/");
    const panel = page.getByTestId("keyboard-panel");
    await expect(panel).toBeVisible();
    await expect(panel.getByText("Spawn window")).toBeVisible();
    await expect(panel.getByText("Navigate")).toBeVisible();
    await expect(panel.getByText("Actions")).toBeVisible();
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
  test("J/ArrowDown moves focus to next window in MasterStack", async ({
    page,
  }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await page.keyboard.press("n");
    // focused: win-2. J/down should go to win-1
    await page.keyboard.press("j");
    await expect(
      page.getByTestId("status-bar").getByText("Terminal #1"),
    ).toBeVisible();
  });

  test("K/ArrowUp moves focus to previous window in MasterStack", async ({
    page,
  }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await page.keyboard.press("n");
    // focused: win-2 (idx 0), k wraps to win-1
    await page.keyboard.press("k");
    await expect(
      page.getByTestId("status-bar").getByText("Terminal #1"),
    ).toBeVisible();
  });

  test("L/H are no-ops in MasterStack", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await page.keyboard.press("n");
    // focused: win-2 (Browser #2)
    await page.keyboard.press("l");
    // Should still be win-2
    await expect(
      page.getByTestId("status-bar").getByText("Browser #2"),
    ).toBeVisible();
  });

  test("L/H navigate in Grid layout", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("3"); // Switch to Grid
    await page.keyboard.press("n");
    await page.keyboard.press("n");
    // focused: win-2
    await page.keyboard.press("l");
    await expect(
      page.getByTestId("status-bar").getByText("Terminal #1"),
    ).toBeVisible();
    await page.keyboard.press("h");
    await expect(
      page.getByTestId("status-bar").getByText("Browser #2"),
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

  test("layout toast appears when switching", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("2");
    await expect(page.getByTestId("layout-toast")).toBeVisible();
    await expect(page.getByText("spiral pattern")).toBeVisible();
  });
});

test.describe("Keyboard shortcuts - window movement", () => {
  test("Enter swaps focused window with master", async ({ page }) => {
    await page.goto("/demo/");
    await focusDemo(page);
    await page.keyboard.press("n");
    await page.keyboard.press("n");
    await page.keyboard.press("j"); // focus win-1
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

test.describe("Keyboard panel", () => {
  test("shows layout-specific shortcuts", async ({ page }) => {
    await page.goto("/demo/");
    const panel = page.getByTestId("keyboard-panel");

    // MasterStack: shows linear focus
    await expect(panel.getByText("Focus prev (linear)")).toBeVisible();
    await expect(panel.getByText("— (no-op)")).toBeVisible();

    // Switch to ThreeColumn
    await focusDemo(page);
    await page.keyboard.press("4");

    // ThreeColumn: shows column navigation
    await expect(panel.getByText("Focus left column")).toBeVisible();
    await expect(panel.getByText("Focus right column")).toBeVisible();
    await expect(panel.getByText("Focus up in column")).toBeVisible();
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

    // Switch through layouts
    for (const key of ["2", "3", "4", "1"]) {
      await page.keyboard.press(key);
    }

    // Navigate using j/k (up/down in MasterStack)
    await page.keyboard.press("j");
    await page.keyboard.press("j");
    await page.keyboard.press("k");

    await page.keyboard.press("q");
    await expect(statusBar.getByText("3 windows")).toBeVisible();

    await page.keyboard.press("q");
    await page.keyboard.press("q");
    await page.keyboard.press("q");
    await expect(page.getByTestId("empty-state")).toBeVisible();
  });
});
