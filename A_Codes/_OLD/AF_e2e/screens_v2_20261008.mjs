// Side-by-side screenshot capture for the mockup-parity judgement pass.
//
// Deliberately NOT under tests/, so `npx playwright test` does not collect it: these are evidence
// captures for a review, not assertions. The assertions live in tests/parity.spec.ts.
//
//   node screens.mjs <YYYYMMDD>          # app must already be running on :5173
//
// Writes D_Reviews/DC_mockup_review/<YYYYMMDD>/<MUP-ID>_{mockup,app}.png.
import { chromium } from "@playwright/test";
import path from "node:path";
import fs from "node:fs";
import { pathToFileURL } from "node:url";

const DATE = process.argv[2];
if (!DATE) {
  console.error("usage: node screens.mjs <YYYYMMDD>");
  process.exit(2);
}
const REPO_ROOT = path.resolve(import.meta.dirname, "..", "..");
const MOCKUP_URL = pathToFileURL(
  path.join(REPO_ROOT, "C_Requirements", "_OLD", "MRM_Governance_MIS_Demo.html"),
).href;
const APP_URL = process.env.APP_URL ?? "http://localhost:5173";
const OUT = path.join(REPO_ROOT, "D_Reviews", "DC_mockup_review", DATE);
fs.mkdirSync(OUT, { recursive: true });

const VIEWPORT = { width: 1440, height: 900 };

/** Mock-up rail step indices (mockup-parity.md "Mock-up hooks"). */
const STEP = {
  overview: 0, policy: 1, users: 2, inventory: 3, history: 4, documents: 5,
  cde: 6, results: 7, rules: 8, dashboards: 9, report: 10, copilot: 11,
};

/**
 * `full: false` captures the 1440x900 viewport only. Needed for the Operations Board, whose table
 * lists all 256 seeded models: a full-page capture there is 11,000px tall and unreadable.
 */
async function shot(page, id, side, full = true) {
  const file = path.join(OUT, `${id}_${side}.png`);
  await page.screenshot({ path: file, fullPage: full });
  console.log(`  ${path.basename(file)}`);
}

async function mockupStep(page, step, tab) {
  await page.goto(MOCKUP_URL);
  await page.locator(`.step[data-i="${STEP[step]}"]`).click();
  if (tab) await page.locator(`.tabs button[data-t="${tab}"]`).click();
  await page.locator("#stage").waitFor();
  await page.waitForTimeout(400);
}

async function mockupModel(page) {
  await mockupStep(page, "dashboards", "ops");
  await page.locator(".mcard[data-m]").first().click();
  await page.locator("#m360").waitFor();
  await page.waitForTimeout(300);
}

async function signInAs(page, role) {
  await page.goto(APP_URL);
  const picker = page.getByLabel("Act as user and role");
  await picker.waitFor();
  const option = page.locator("option", { hasText: new RegExp(`^${role} — `) }).first();
  await picker.selectOption((await option.getAttribute("value")) ?? "");
  await page.locator('nav.rail[aria-label="Main"]').waitFor();
}

async function appScreen(page, linkName) {
  await page.locator('nav.rail[aria-label="Main"]').getByRole("link", { name: linkName }).click();
  await page.getByRole("heading", { level: 1, name: linkName }).waitFor();
  await page.waitForTimeout(400);
}

async function appTab(page, name) {
  await page.getByRole("tab", { name: new RegExp(`^${name}`) }).click();
  await page.waitForTimeout(400);
}

/**
 * Open a Model 360 page. Retried once: a bare goto occasionally returns before React has mounted
 * the page header, and a capture script should not abandon a 40-screenshot run for that.
 */
async function appModel(page, modelId) {
  for (let attempt = 0; attempt < 2; attempt++) {
    await page.goto(`${APP_URL}/models/${modelId}`, { waitUntil: "domcontentloaded" });
    try {
      await page.getByRole("heading", { level: 1 }).waitFor({ timeout: 15000 });
      return;
    } catch (err) {
      if (attempt === 1) throw err;
    }
  }
}

const browser = await chromium.launch();

// --- mock-up side ---------------------------------------------------------------------------
{
  // colorScheme dark: both stylesheets are dark-first with the same tokens (BRD §52), but the
  // mock-up also carries a `prefers-color-scheme: light` override and the app does not. Playwright
  // defaults a page to light, which would render the mock-up light and the app dark and make every
  // side-by-side capture look like a theme difference that is not there.
  const page = await browser.newPage({ viewport: VIEWPORT, reducedMotion: "reduce", colorScheme: "dark" });
  const dash = [["MUP-01", "cc"], ["MUP-02", "cc"], ["MUP-04", "cc"], ["MUP-05", "cc"],
                ["MUP-06", "cc"], ["MUP-07", "ops"], ["MUP-08", "ops"], ["MUP-09", "ops"],
                ["MUP-33", "cc"]];
  for (const [id, tab] of dash) {
    await mockupStep(page, "dashboards", tab);
    await shot(page, id, "mockup");
  }
  for (const id of ["MUP-10", "MUP-11", "MUP-13", "MUP-14", "MUP-15", "MUP-16", "MUP-17", "MUP-21"]) {
    await mockupModel(page);
    await shot(page, id, "mockup");
  }
  for (const [id, step] of [["MUP-18", "results"], ["MUP-19", "results"], ["MUP-20", "cde"],
                            ["MUP-22", "policy"], ["MUP-23", "inventory"], ["MUP-24", "inventory"],
                            ["MUP-25", "documents"], ["MUP-26", "documents"], ["MUP-27", "cde"],
                            ["MUP-28", "rules"], ["MUP-29", "report"], ["MUP-30", "report"],
                            ["MUP-31", "copilot"], ["MUP-32", "copilot"], ["MUP-35", "users"]]) {
    await mockupStep(page, step);
    await shot(page, id, "mockup");
  }
  await page.close();
}

// --- app side -------------------------------------------------------------------------------
{
  const page = await browser.newPage({ viewport: VIEWPORT });
  await signInAs(page, "Executive");
  for (const id of ["MUP-01", "MUP-02", "MUP-04", "MUP-05", "MUP-06", "MUP-33"]) {
    await appScreen(page, "Command Center");
    await shot(page, id, "app");
  }
  await page.close();
}
{
  const page = await browser.newPage({ viewport: VIEWPORT });
  await signInAs(page, "Validator");
  for (const id of ["MUP-07", "MUP-08", "MUP-09"]) {
    await appScreen(page, "Operations Board");
    await shot(page, id, "app", false); // viewport only: the full board is 256 rows tall
  }
  // Model 360: one capture per panel, each behind its tab.
  for (const [id, model, tab] of [["MUP-10", "M-0012", null], ["MUP-11", "M-0042", null],
                                  ["MUP-12", "M-0078", null], ["MUP-13", "M-0012", null],
                                  ["MUP-14", "M-0071", "Approvals"], ["MUP-15", "M-0012", "Validation"],
                                  ["MUP-16", "M-0012", "Findings"], ["MUP-17", "M-0012", "Score"],
                                  ["MUP-18", "M-0012", "Monitoring"], ["MUP-19", "M-0012", "Monitoring"],
                                  ["MUP-20", "M-0012", "CDE / DQ"]]) {
    await appModel(page, model);
    if (tab) await appTab(page, tab);
    await page.waitForTimeout(400);
    await shot(page, id, "app");
  }
  // MUP-21: an Initiation model has no validation history.
  await appScreen(page, "Operations Board");
  await page.locator('select[aria-label="Stage"]').selectOption("Initiation");
  await page.locator("tbody tr").first().click();
  await page.getByRole("heading", { level: 1 }).waitFor();
  await appTab(page, "Validation");
  await shot(page, "MUP-21", "app");
  // Documents
  await appScreen(page, "Document Centre");
  await appTab(page, "Upload");
  await shot(page, "MUP-25", "app");
  await appTab(page, "Completeness");
  await shot(page, "MUP-25b", "app");
  await appTab(page, "Register");
  await shot(page, "MUP-26", "app");
  await page.close();
}
{
  const page = await browser.newPage({ viewport: VIEWPORT });
  await signInAs(page, "Admin");
  await appScreen(page, "Import Centre");
  await appTab(page, "Templates");
  await shot(page, "MUP-22", "app");
  await appTab(page, "Upload");
  await shot(page, "MUP-23", "app");
  await appScreen(page, "Audit Trail");
  await shot(page, "MUP-24", "app");
  await appScreen(page, "Monitoring");
  await shot(page, "MUP-19b", "app");
  await page.close();
}
{
  const page = await browser.newPage({ viewport: VIEWPORT });
  await signInAs(page, "Data Owner");
  await appScreen(page, "Data Audit");
  await shot(page, "MUP-27", "app");
  await shot(page, "MUP-28", "app");
  await page.close();
}
{
  // Report and Copilot have no route on this branch: capture what an Executive actually sees.
  const page = await browser.newPage({ viewport: VIEWPORT });
  await signInAs(page, "Executive");
  await shot(page, "MUP-29", "app");
  await page.goto(`${APP_URL}/models/new`);
  await page.waitForTimeout(500);
  await shot(page, "MUP-35", "app");
  await page.close();
}

// --- Date rendering evidence (review finding MP-10, fixed by G0.24) --------------------------
// Not a mock-up comparison: these are the two screens that disagreed with each other about the
// same model's due date, captured so the agreement can be read off the evidence rather than taken
// on trust. The host timezone must be behind UTC for them to be worth anything.
{
  const page = await browser.newPage({ viewport: VIEWPORT });
  await signInAs(page, "Executive");
  await appScreen(page, "Command Center");
  await shot(page, "MP-10_command_center", "app");
  const first = await page.locator("section.panel")
    .filter({ has: page.getByRole("heading", { name: /Revalidation timeline/ }) })
    .locator("tbody tr").first().locator("td").first().innerText();
  const modelId = first.match(/M-\d{4}/)?.[0] ?? "M-0012";
  await appModel(page, modelId);
  await shot(page, "MP-10_model360", "app");
  console.log("  (revalidation timeline first row: " + modelId + ")");
  await page.close();
}

// --- Screens added at the Gate 0 exit review, plus the document detail KV list (CR-34) ------
{
  const page = await browser.newPage({ viewport: VIEWPORT });
  await signInAs(page, "Admin");
  await appScreen(page, "Admin");
  await shot(page, "MUP-36", "app");
  await appScreen(page, "Audit Trail");
  await shot(page, "MUP-37", "app");
  await page.close();
}
{
  const page = await browser.newPage({ viewport: VIEWPORT });
  await signInAs(page, "Validator");
  await appScreen(page, "Document Centre");
  await appTab(page, "Register");
  await shot(page, "MUP-38", "app");
  // The Details KV list: "Effective date" is formatted, "Retention" is not (review finding CR-34).
  await page.locator("div.tablewrap tbody tr").first().locator("td").first().click();
  await page.getByRole("heading", { name: /^Versions/ }).waitFor();
  await page.waitForTimeout(300);
  await shot(page, "MUP-38b", "app");
  await page.close();
}

await browser.close();
console.log(`\nScreenshots in ${OUT}`);
