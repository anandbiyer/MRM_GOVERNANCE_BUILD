// Shared helpers for the parity checklist. Locators use role, label and text only — never
// data-testid, and never a change to product code (see the mockup-parity-tester agent rules).
import { expect, type Page } from "@playwright/test";
import { MOCKUP_URL } from "../playwright.config";

/**
 * Rail steps in the mock-up. Confirmed against the generated markup:
 *   <button class="step …" data-i="${i}">  (MRM_Governance_MIS_Demo.html, the step list renderer)
 * The buttons are rendered by script, so they are absent from the raw file and must be waited for.
 */
export const STEP = {
  overview: 0,
  policy: 1,
  users: 2,
  inventory: 3,
  history: 4,
  documents: 5,
  cde: 6,
  results: 7,
  rules: 8,
  dashboards: 9,
  report: 10,
  copilot: 11,
} as const;

export type StepName = keyof typeof STEP;

/** Open one mock-up screen by its rail step and wait until the stage has rendered it. */
export async function openMockupScreen(page: Page, step: StepName | number): Promise<void> {
  const index = typeof step === "number" ? step : STEP[step];
  if (!page.url().startsWith("file:")) {
    await page.goto(MOCKUP_URL);
  }
  // The walkthrough autoplays unless reduced motion is set (config) — stop it defensively too.
  const play = page.locator("#bPlay");
  await expect(play).toBeVisible();
  const rail = page.locator(`.step[data-i="${index}"]`);
  await expect(rail, `mock-up rail step ${index} should exist`).toBeVisible();
  await rail.click();
  await expect(page.locator("#stage")).not.toBeEmpty();
}

/** Switch the mock-up dashboard tab. Confirmed hook: .tabs button[data-t=cc|ops|da]. */
export async function openMockupDashTab(page: Page, tab: "cc" | "ops" | "da"): Promise<void> {
  await openMockupScreen(page, "dashboards");
  const button = page.locator(`.tabs button[data-t="${tab}"]`);
  await expect(button, `mock-up dashboard tab ${tab} should exist`).toBeVisible();
  await button.click();
}

/**
 * Sign in to the app through the development role picker.
 *
 * The picker is a single select labelled "Act as user and role" whose options read
 * "<Role> — <Full name> (<U-id>)" (AC_frontend/src/components/RoleSwitcher.tsx). Passing a role
 * selects that role's first user, which is all the checklist needs.
 */
export async function signInAs(page: Page, role: string): Promise<void> {
  await page.goto("/");
  const picker = page.getByLabel("Act as user and role");
  await expect(picker, "development role picker should be present").toBeVisible();
  const option = page.locator("option", { hasText: new RegExp(`^${escapeRegExp(role)} — `) }).first();
  await expect(option, `no user holds the role "${role}"`).toHaveCount(1);
  await picker.selectOption(await option.getAttribute("value") ?? "");
  // The rail only renders once a session exists.
  await expect(page.locator('nav.rail[aria-label="Main"]')).toBeVisible();
}

/** Navigate the signed-in app by its sidebar link. */
export async function openAppScreen(page: Page, linkName: string): Promise<void> {
  await page.locator('nav.rail[aria-label="Main"]').getByRole("link", { name: linkName }).click();
}

/** True when the page has no horizontal overflow at the configured viewport (MUP-33). */
export async function hasHorizontalScroll(page: Page): Promise<boolean> {
  return page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
