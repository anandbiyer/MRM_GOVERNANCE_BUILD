// Shared helpers for the parity checklist. Locators use role, label and text only — never
// data-testid, and never a change to product code (see the mockup-parity-tester agent rules).
import { expect, type Locator, type Page } from "@playwright/test";
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
/**
 * Navigate by sidebar link and wait until the destination screen is actually on the page.
 *
 * Without the wait, the click returns while the previous screen is still mounted, so a locator
 * that is not specific to the destination can match the screen being left — look visible, and
 * then resolve to nothing once the route swaps and the new screen is still loading. Every screen
 * reachable this way renders its name as an `<h1>` through `PageHeader`, so the heading is the
 * signal that the swap is done. MUP-34 read 0 Operations Board rows this way (G0.13).
 */
export async function openAppScreen(page: Page, linkName: string): Promise<void> {
  await page.locator('nav.rail[aria-label="Main"]').getByRole("link", { name: linkName }).click();
  await expect(page.getByRole("heading", { level: 1, name: linkName })).toBeVisible();
}

/**
 * Model 360 panels sit behind tabs (Model360Page.tsx `TABS`), defaulting to Overview, so a panel's
 * content is not in the DOM until its tab is selected.
 */
export type Model360Tab =
  | "Overview" | "Validation" | "Findings" | "Approvals" | "Score"
  | "Documents" | "Monitoring" | "CDE / DQ" | "History";

export async function openModel360Tab(page: Page, tab: Model360Tab): Promise<void> {
  // Not an exact match: the Findings and Approvals tabs append a <span class="count"> badge, so
  // their accessible names read "Findings4" / "Approvals3" when there is anything outstanding.
  const button = page.locator('nav.tabs[role="tablist"]').getByRole("tab", { name: new RegExp(`^${tab}`) });
  await expect(button, `Model 360 tab "${tab}" should exist`).toBeVisible();
  await button.click();
  await expect(button).toHaveAttribute("aria-selected", "true");
}

/**
 * A Command Center distribution panel, located by its heading.
 *
 * CommandCenter.tsx renders `<h4>{title}{note && <small>{note}</small>}</h4>`, so a panel that has a
 * note (e.g. "Lifecycle stage") has extra text inside the same heading and cannot be matched exactly.
 */
export function barListPanel(page: Page, title: string) {
  return page.locator("section.panel").filter({ has: page.getByRole("heading", { name: new RegExp(title) }) });
}

/** True when the page has no horizontal overflow at the configured viewport (MUP-33). */
export async function hasHorizontalScroll(page: Page): Promise<boolean> {
  return page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * The exact string the browser renders for a date-only API value, computed in the page's own
 * locale by the rule `AC_frontend/src/format.ts` uses: the three numbers, built in **local** time.
 *
 * Asserting against this instead of a hard-coded "9/30/2026" keeps the check locale-independent
 * while still being an independent calculation — it never calls the app's own formatter. The whole
 * point of review finding MP-10 was that `new Date("2026-09-30")` is UTC midnight and so renders
 * the previous day west of UTC, which is why this helper must not go through `Date`'s parser
 * either.
 */
export async function localeDateOnly(page: Page, isoDate: string): Promise<string> {
  const [year, month, day] = isoDate.slice(0, 10).split("-").map(Number);
  return page.evaluate(
    ([y, m, d]) => new Date(y, m - 1, d).toLocaleDateString(),
    [year, month, day],
  );
}

/** Read a Model 360 `<dl class="kv">` value by its term, e.g. "Next due". */
export async function kvValue(page: Page, term: string): Promise<string> {
  const dd = page.locator("dl.kv div", { has: page.getByText(term, { exact: true }) }).locator("dd").first();
  await expect(dd, `Model 360 should show "${term}"`).toBeVisible();
  return (await dd.innerText()).trim();
}

/**
 * The `cellIndex` of a table column, found by its header text rather than counted by hand.
 *
 * A positional `td.nth(2)` is a trap: BL.24 inserted Owner and Last validation into the Command
 * Center's revalidation timeline, and every positional locator two columns downstream silently
 * began reading a different column. One that happens to compare unequal values fails loudly; one
 * that compares equal values passes while proving nothing. Ask the DOM where the column is.
 */
export async function columnIndex(table: Locator, header: string): Promise<number> {
  const th = table.locator("thead th", { hasText: new RegExp(`^${escapeRegExp(header)}$`) }).first();
  await expect(th, `table should have a "${header}" column`).toHaveCount(1);
  const index = await th.evaluate((el) => (el as HTMLTableCellElement).cellIndex);
  expect(index, `"${header}" column index`).toBeGreaterThanOrEqual(0);
  return index;
}

/** Read one body cell of a table by row number and header text. */
export async function cellByHeader(table: Locator, row: number, header: string): Promise<string> {
  const index = await columnIndex(table, header);
  return (await table.locator("tbody tr").nth(row).locator("td").nth(index).innerText()).trim();
}
