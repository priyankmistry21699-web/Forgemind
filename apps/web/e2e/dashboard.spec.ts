/**
 * E2E smoke tests — critical paths through the ForgeMind dashboard.
 *
 * These tests require a running dev server (npm run dev) and a live backend.
 * Run with: npx playwright test
 * Run against a different URL: E2E_BASE_URL=https://staging.example.com npx playwright test
 */

import { test, expect } from "@playwright/test";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function waitForAppReady(page: import("@playwright/test").Page) {
  // The top-nav "Online" badge confirms the shell rendered successfully.
  await expect(page.getByText("Online")).toBeVisible({ timeout: 15000 });
}

// ---------------------------------------------------------------------------
// Dashboard smoke
// ---------------------------------------------------------------------------

test.describe("Dashboard — smoke", () => {
  test("loads and shows the Dashboard heading", async ({ page }) => {
    await page.goto("/dashboard");
    await waitForAppReady(page);

    await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible();
    await expect(
      page.getByText(/overview of your projects/i),
    ).toBeVisible();
  });

  test("shows all four stat cards", async ({ page }) => {
    await page.goto("/dashboard");
    await waitForAppReady(page);

    // Wait until loading skeleton clears (at least one non-dash value appears)
    await expect(page.getByText("Projects")).toBeVisible();
    await expect(page.getByText("Running Agents")).toBeVisible();
    await expect(page.getByText("Pending Approvals")).toBeVisible();
    await expect(page.getByText("Health")).toBeVisible();
  });

  test("top-nav shows correct page title on dashboard", async ({ page }) => {
    await page.goto("/dashboard");
    await waitForAppReady(page);

    // Top-nav renders the current page name (from top-nav.tsx usePageTitle)
    const header = page.locator("header");
    await expect(header.getByText("Dashboard")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Sidebar navigation
// ---------------------------------------------------------------------------

test.describe("Sidebar — navigation", () => {
  test("clicking Agents nav item navigates to /dashboard/agents", async ({
    page,
  }) => {
    await page.goto("/dashboard");
    await waitForAppReady(page);

    await page.getByRole("link", { name: /^agents$/i }).click();
    await expect(page).toHaveURL(/\/dashboard\/agents/);
  });

  test("clicking Approvals nav item navigates to /dashboard/approvals", async ({
    page,
  }) => {
    await page.goto("/dashboard");
    await waitForAppReady(page);

    await page.getByRole("link", { name: /^approvals$/i }).click();
    await expect(page).toHaveURL(/\/dashboard\/approvals/);
  });

  test("top-nav updates title when navigating to Approvals", async ({
    page,
  }) => {
    await page.goto("/dashboard");
    await waitForAppReady(page);

    await page.getByRole("link", { name: /^approvals$/i }).click();
    const header = page.locator("header");
    await expect(header.getByText("Approvals")).toBeVisible({ timeout: 5000 });
  });
});

// ---------------------------------------------------------------------------
// New Project form
// ---------------------------------------------------------------------------

test.describe("New Project form", () => {
  test("opens and closes via the header button", async ({ page }) => {
    await page.goto("/dashboard");
    await waitForAppReady(page);

    // Form should not be visible initially
    await expect(page.getByLabel(/project name/i)).not.toBeVisible();

    // Open the form
    await page.getByRole("button", { name: /new project/i }).first().click();
    await expect(page.getByLabel(/project name/i)).toBeVisible();

    // Cancel closes it
    await page.getByRole("button", { name: /cancel/i }).click();
    await expect(page.getByLabel(/project name/i)).not.toBeVisible();
  });

  test("Plan from Prompt form opens and is mutually exclusive with New Project", async ({
    page,
  }) => {
    await page.goto("/dashboard");
    await waitForAppReady(page);

    // Open New Project
    await page.getByRole("button", { name: /new project/i }).first().click();
    await expect(page.getByLabel(/project name/i)).toBeVisible();

    // Switch to Plan from Prompt — New Project form should disappear
    await page.getByRole("button", { name: /plan from prompt/i }).first().click();
    await expect(page.getByLabel(/project name/i)).not.toBeVisible();
    await expect(
      page.getByPlaceholder(/describe what you want to build/i),
    ).toBeVisible();
  });
});
