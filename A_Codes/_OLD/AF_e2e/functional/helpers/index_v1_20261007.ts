// Helpers for the functional suite (review agent 4). Locators are role/label/text only — never a
// data-testid, because adding one would mean editing product code to make a test pass.
import { DatabaseSync } from "node:sqlite";
import path from "node:path";
import { expect, type APIRequestContext, type Locator, type Page } from "@playwright/test";

export const RUN_DIR = process.env.FT_RUN_DIR ?? "";

/** Sign in through the development role picker. Same mechanism as the `app` project's helper. */
export async function signInAs(page: Page, role: string): Promise<void> {
  await page.goto("/");
  const picker = page.getByLabel("Act as user and role");
  await expect(picker, "development role picker should be present").toBeVisible();
  const option = page.locator("option", { hasText: new RegExp(`^${escapeRegExp(role)} — `) }).first();
  await expect(option, `no user holds the role "${role}"`).toHaveCount(1);
  await picker.selectOption((await option.getAttribute("value")) ?? "");
  await expect(page.locator('nav.rail[aria-label="Main"]')).toBeVisible();
}

/** Sign in as a named user and role, when a scenario needs a specific person. */
export async function signInAsUser(page: Page, userId: string, role: string): Promise<void> {
  await page.goto("/");
  const picker = page.getByLabel("Act as user and role");
  await expect(picker).toBeVisible();
  await picker.selectOption(`${userId}|${role}`);
  await expect(page.locator('nav.rail[aria-label="Main"]')).toBeVisible();
}

/** Navigate by sidebar link, as a user would. */
export async function openScreen(page: Page, linkName: string): Promise<void> {
  await page.locator('nav.rail[aria-label="Main"]').getByRole("link", { name: linkName }).click();
}

/** Upload through a real file input. `control` is a locator for the input itself (often hidden). */
export async function uploadFile(page: Page, control: Locator, filePath: string): Promise<void> {
  await control.setInputFiles(filePath);
}

/** Read-only API check, using the signed-in session's token from the page. */
export async function apiAs(page: Page, pathname: string): Promise<{ status: number; body: unknown }> {
  const token = await page.evaluate(() => localStorage.getItem("mrm.token"));
  const resp = await page.request.get(pathname, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  let body: unknown = null;
  try {
    body = await resp.json();
  } catch {
    body = await resp.text();
  }
  return { status: resp.status(), body };
}

/** Unauthenticated API probe, for checking that a route refuses rather than hides. */
export async function api(request: APIRequestContext, pathname: string) {
  return request.get(pathname);
}

/**
 * Read-only query against the *test* database only.
 *
 * Refuses anything but a single SELECT, and refuses a path outside the run folder — the suite must
 * never be able to read, let alone touch, the demo database at A_Codes/AB_backend/var/dev.db.
 */
export function dbQuery(sql: string, params: unknown[] = []): Record<string, unknown>[] {
  const trimmed = sql.trim().replace(/;$/, "");
  if (!/^select\s/i.test(trimmed) || /;/.test(trimmed)) {
    throw new Error(`dbQuery accepts a single SELECT only, got: ${sql}`);
  }
  const dbPath = process.env.FT_DB_PATH;
  if (!dbPath) throw new Error("FT_DB_PATH is not set; refusing to guess a database");
  const resolved = path.resolve(dbPath);
  if (!resolved.includes(path.join("D_Reviews", "DD_functional_test"))) {
    throw new Error(`refusing to query ${resolved}: not inside the functional run folder`);
  }
  const db = new DatabaseSync(resolved, { readOnly: true });
  try {
    return db.prepare(trimmed).all(...(params as never[])) as Record<string, unknown>[];
  } finally {
    db.close();
  }
}

/** Count rows, for the common "nothing was written" check. */
export function dbCount(table: string, where = "1=1", params: unknown[] = []): number {
  if (!/^[a-z_]+$/.test(table)) throw new Error(`suspicious table name: ${table}`);
  const rows = dbQuery(`SELECT COUNT(*) AS n FROM ${table} WHERE ${where}`, params);
  return Number(rows[0].n);
}

/** Outline an element in red before a screenshot. Test-only; product code is untouched. */
export async function highlight(locator: Locator): Promise<void> {
  await locator.evaluate((el: HTMLElement) => {
    el.style.outline = "3px solid red";
    el.style.outlineOffset = "2px";
  });
}

/** Save a checkpoint screenshot as screens/<name>.png in the run folder. */
export async function checkpoint(page: Page, name: string): Promise<string> {
  const file = path.join(RUN_DIR || ".", "screens", `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  return file;
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
