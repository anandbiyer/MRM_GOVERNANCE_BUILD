# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ..\functional\reports.spec.ts >> FS-25 REG-15 REG-16 REG-17 generate the core report, reconcile it, and read it as other roles
- Location: functional\reports.spec.ts:14:5

# Error details

```
Error: no user holds the role "Validator"

expect(locator).toHaveCount(expected) failed

Locator:  locator('option').filter({ hasText: /^Validator — / }).first()
Expected: 1
Received: 0
Timeout:  5000ms

Call log:
  - no user holds the role "Validator" locator('option').filter({ hasText: /^Validator — / }).first() with timeout 5000ms
  - waiting for locator('option').filter({ hasText: /^Validator — / }).first()
    14 × locator resolved to 0 elements
       - unexpected value "0"

```

# Page snapshot

```yaml
- generic [ref=e4]:
  - generic [ref=e5]: Development sign-in
  - heading "MRM Governance MIS" [level=2] [ref=e6]
  - paragraph [ref=e7]: Choose a user and one of their roles. What you can do is decided by the server for that role. Production uses the enterprise identity provider instead.
  - generic [ref=e8]:
    - text: Act as
    - combobox "Act as user and role" [ref=e9]:
      - option "Choose user and role…" [selected]
```

# Test source

```ts
  1   | // Helpers for the functional suite (review agent 4). Locators are role/label/text only — never a
  2   | // data-testid, because adding one would mean editing product code to make a test pass.
  3   | import fs from "node:fs";
  4   | import { DatabaseSync } from "node:sqlite";
  5   | import path from "node:path";
  6   | import zlib from "node:zlib";
  7   | import { expect, type APIRequestContext, type Locator, type Page } from "@playwright/test";
  8   | 
  9   | export const RUN_DIR = process.env.FT_RUN_DIR ?? "";
  10  | 
  11  | /**
  12  |  * Wait until the server agrees who we are.
  13  |  *
  14  |  * Waiting for the nav rail proved nothing: it is already on the page from the *previous* session, so
  15  |  * a role switch that silently did not happen looked like a success and the scenario went on to test
  16  |  * the wrong role (harness defect H-07). That is a false-negative generator — the worst kind of
  17  |  * harness bug, because it makes a passing run meaningless rather than failing loudly. The identity
  18  |  * is therefore read back from `/api/auth/me`, which is the only authority on it.
  19  |  */
  20  | async function confirmIdentity(page: Page, role: string, userId?: string): Promise<void> {
  21  |   await expect(page.locator('nav.rail[aria-label="Main"]')).toBeVisible();
  22  |   const want = userId ? `${userId}|${role}` : role;
  23  |   await expect
  24  |     .poll(async () => {
  25  |       const token = await page.evaluate(() => localStorage.getItem("mrm.token"));
  26  |       if (!token) return "no token";
  27  |       const resp = await page.request.get("/api/auth/me", {
  28  |         headers: { Authorization: `Bearer ${token}` },
  29  |       });
  30  |       if (!resp.ok()) return `HTTP ${resp.status()}`;
  31  |       const me = (await resp.json()) as { user_id: string; role: string };
  32  |       return userId ? `${me.user_id}|${me.role}` : me.role;
  33  |     }, { timeout: 10_000, message: `the session never became ${want}` })
  34  |     .toBe(want);
  35  | }
  36  | 
  37  | /** Sign in through the development role picker. Same mechanism as the `app` project's helper. */
  38  | export async function signInAs(page: Page, role: string): Promise<void> {
  39  |   await page.goto("/");
  40  |   const picker = page.getByLabel("Act as user and role");
  41  |   await expect(picker, "development role picker should be present").toBeVisible();
  42  |   const option = page.locator("option", { hasText: new RegExp(`^${escapeRegExp(role)} — `) }).first();
> 43  |   await expect(option, `no user holds the role "${role}"`).toHaveCount(1);
      |                                                            ^ Error: no user holds the role "Validator"
  44  |   await picker.selectOption((await option.getAttribute("value")) ?? "");
  45  |   await confirmIdentity(page, role);
  46  | }
  47  | 
  48  | /** Sign in as a named user and role, when a scenario needs a specific person. */
  49  | export async function signInAsUser(page: Page, userId: string, role: string): Promise<void> {
  50  |   await page.goto("/");
  51  |   const picker = page.getByLabel("Act as user and role");
  52  |   await expect(picker).toBeVisible();
  53  |   await picker.selectOption(`${userId}|${role}`);
  54  |   await confirmIdentity(page, role, userId);
  55  | }
  56  | 
  57  | /** Navigate by sidebar link, as a user would. */
  58  | export async function openScreen(page: Page, linkName: string): Promise<void> {
  59  |   await page.locator('nav.rail[aria-label="Main"]').getByRole("link", { name: linkName }).click();
  60  | }
  61  | 
  62  | /** Upload through a real file input. `control` is a locator for the input itself (often hidden). */
  63  | export async function uploadFile(page: Page, control: Locator, filePath: string): Promise<void> {
  64  |   await control.setInputFiles(filePath);
  65  | }
  66  | 
  67  | /** Read-only API check, using the signed-in session's token from the page. */
  68  | export async function apiAs(page: Page, pathname: string): Promise<{ status: number; body: unknown }> {
  69  |   const token = await page.evaluate(() => localStorage.getItem("mrm.token"));
  70  |   const resp = await page.request.get(pathname, {
  71  |     headers: token ? { Authorization: `Bearer ${token}` } : {},
  72  |   });
  73  |   let body: unknown = null;
  74  |   try {
  75  |     body = await resp.json();
  76  |   } catch {
  77  |     body = await resp.text();
  78  |   }
  79  |   return { status: resp.status(), body };
  80  | }
  81  | 
  82  | /** Unauthenticated API probe, for checking that a route refuses rather than hides. */
  83  | export async function api(request: APIRequestContext, pathname: string) {
  84  |   return request.get(pathname);
  85  | }
  86  | 
  87  | /**
  88  |  * Read-only query against the *test* database only.
  89  |  *
  90  |  * Refuses anything but a single SELECT, and refuses a path outside the run folder — the suite must
  91  |  * never be able to read, let alone touch, the demo database at A_Codes/AB_backend/var/dev.db.
  92  |  */
  93  | export function dbQuery(sql: string, params: unknown[] = []): Record<string, unknown>[] {
  94  |   const trimmed = sql.trim().replace(/;$/, "");
  95  |   if (!/^select\s/i.test(trimmed) || /;/.test(trimmed)) {
  96  |     throw new Error(`dbQuery accepts a single SELECT only, got: ${sql}`);
  97  |   }
  98  |   const dbPath = process.env.FT_DB_PATH;
  99  |   if (!dbPath) throw new Error("FT_DB_PATH is not set; refusing to guess a database");
  100 |   const resolved = path.resolve(dbPath);
  101 |   if (!resolved.includes(path.join("D_Reviews", "DD_functional_test"))) {
  102 |     throw new Error(`refusing to query ${resolved}: not inside the functional run folder`);
  103 |   }
  104 |   const db = new DatabaseSync(resolved, { readOnly: true });
  105 |   try {
  106 |     return db.prepare(trimmed).all(...(params as never[])) as Record<string, unknown>[];
  107 |   } finally {
  108 |     db.close();
  109 |   }
  110 | }
  111 | 
  112 | /** Count rows, for the common "nothing was written" check. */
  113 | export function dbCount(table: string, where = "1=1", params: unknown[] = []): number {
  114 |   if (!/^[a-z_]+$/.test(table)) throw new Error(`suspicious table name: ${table}`);
  115 |   const rows = dbQuery(`SELECT COUNT(*) AS n FROM ${table} WHERE ${where}`, params);
  116 |   return Number(rows[0].n);
  117 | }
  118 | 
  119 | /** Outline an element in red before a screenshot. Test-only; product code is untouched. */
  120 | export async function highlight(locator: Locator): Promise<void> {
  121 |   await locator.evaluate((el: HTMLElement) => {
  122 |     el.style.outline = "3px solid red";
  123 |     el.style.outlineOffset = "2px";
  124 |   });
  125 | }
  126 | 
  127 | /** Save a checkpoint screenshot as screens/<name>.png in the run folder. */
  128 | export async function checkpoint(page: Page, name: string): Promise<string> {
  129 |   const file = path.join(RUN_DIR || ".", "screens", `${name}.png`);
  130 |   await page.screenshot({ path: file, fullPage: true });
  131 |   return file;
  132 | }
  133 | 
  134 | function escapeRegExp(value: string): string {
  135 |   return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  136 | }
  137 | 
  138 | /**
  139 |  * Find a seeded evidence file by model and area, instead of composing its path.
  140 |  *
  141 |  * The seed lays documents out as `Model_Governance/<Business_Line>/<Model>/<Area>/`, so the path
  142 |  * depends on the model's business line — M-0012 is Commercial Banking, not Credit Risk, which is
  143 |  * what harness defect H-06 assumed. Searching means a reseed that moves a model between business
```