// One test per mockup-parity.md checklist ID, titled with the ID so the report maps straight back.
// Each test has a `mockup` branch (the HTML the customer saw) and an `app` branch (the running app).
// The app branch is marked fixme for any item whose §81 phase Part 0 does not list as built, so it
// shows in the report as "Not built (Phase N)" rather than silently passing or failing.
import { expect, test, type Page } from "@playwright/test";
import {
  barListPanel,
  hasHorizontalScroll,
  openAppScreen,
  openMockupDashTab,
  openMockupScreen,
  kvValue,
  localeDateOnly,
  openModel360Tab,
  signInAs,
} from "../helpers";

/** Phases Part 0 lists as implemented: 1-4 and the core of 8. */
const BUILT = new Set(["1", "2", "3", "4", "8"]);
// "2A-core" is the core Model Risk Report (D12, plan G1.16–G1.18): add it to BUILT when G1.17 lands.
// Plain "2A" is the rest of Phase 2A, deferred by D12 — those items stay Not built, never failures.

interface Ctx {
  page: Page;
  isMockup: boolean;
}

function item(id: string, name: string, phase: string, body: (ctx: Ctx) => Promise<void>): void {
  test(`${id} ${name}`, async ({ page }, testInfo) => {
    const isMockup = testInfo.project.name === "mockup";
    // Must come before the first await.
    if (!isMockup) test.fixme(!BUILT.has(phase), `Not built (Phase ${phase})`);
    await body({ page, isMockup });
  });
}

/** Open the mock-up Model 360 panel by clicking the first model card. */
async function openMockupModel(page: Page): Promise<void> {
  await openMockupDashTab(page, "ops");
  const card = page.locator(".mcard[data-m]").first();
  await expect(card).toBeVisible();
  await card.click();
  await expect(page.locator("#m360")).toBeVisible();
}

/** Open a seeded model's Model 360 in the app. M-0012 is in the committed seed. */
async function openAppModel(page: Page, modelId = "M-0012"): Promise<void> {
  await page.goto(`/models/${modelId}`);
  await expect(page.getByText(modelId).first()).toBeVisible();
}

// --- Command Center -------------------------------------------------------------------------

item("MUP-01", "Command Center KPI tiles", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupDashTab(page, "cc");
    await expect(page.locator(".kpi")).not.toHaveCount(0);
    return;
  }
  await signInAs(page, "Executive");
  // "Models with open findings" is an accepted difference from the mock-up's "Open findings": CC-01
  // requires a tile to equal its own drill-down, and this tile opens a list of models (CR-05).
  for (const label of ["Total models", "In production", "High risk", "Revalidation queue",
                       "Models with open findings"]) {
    await expect(page.getByText(label, { exact: true }).first(), `tile "${label}"`).toBeVisible();
  }
});

item("MUP-02", "Command Center donuts by tier and lifecycle phase", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupDashTab(page, "cc");
    await expect(page.locator("#stage")).toContainText(/tier/i);
    return;
  }
  await signInAs(page, "Executive");
  await expect(barListPanel(page, "Risk tier")).toBeVisible();
  await expect(barListPanel(page, "Lifecycle stage")).toBeVisible();
  // Percentage labels are part of the item.
  await expect(page.locator("body")).toContainText(/%/);
});

item("MUP-03", "Lifecycle pipeline strip with click-through", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupDashTab(page, "cc");
    await expect(page.locator("#stage")).toContainText(/Monitoring|Development|Validation/);
    return;
  }
  await signInAs(page, "Executive");
  const stage = barListPanel(page, "Lifecycle stage");
  await expect(stage).toBeVisible();
  // Rows are <button class="barrow">, not links. Clicking one filters the Operations Board.
  await stage.getByRole("button", { name: /Monitoring/ }).first().click();
  await expect(page).toHaveURL(/\/operations\?.*column=/);
});

item("MUP-04", "Revalidation timeline by category", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupDashTab(page, "cc");
    await expect(page.locator("#stage")).toContainText(/Revalidation/i);
    return;
  }
  await signInAs(page, "Executive");
  await expect(page.getByText(/Revalidation/i).first()).toBeVisible();
});

item("MUP-05", "Regulatory / audit models and issues chart", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupDashTab(page, "cc");
    await expect(page.locator("#stage")).toContainText(/Reg\/Audit|Regulatory/i);
    return;
  }
  await signInAs(page, "Executive");
  await expect(page.getByText(/Reg\/Audit|Regulatory/i).first()).toBeVisible();
});

item("MUP-06", "Insights panel generated from rules", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupDashTab(page, "cc");
    await expect(page.locator("#stage")).toContainText(/Insight/i);
    return;
  }
  await signInAs(page, "Executive");
  await expect(page.getByText(/Insight/i).first()).toBeVisible();
  // Insights must reference real models, not fixed copy.
  await expect(page.locator("body")).toContainText(/M-\d{4}/);
});

// --- Operations Board -----------------------------------------------------------------------

item("MUP-07", "Operations Board filters update counts", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupDashTab(page, "ops");
    await expect(page.locator("#stage")).toContainText(/Tier|Filter/i);
    return;
  }
  await signInAs(page, "Validator");
  await openAppScreen(page, "Operations Board");
  await expect(page.getByLabel("Search models")).toBeVisible();
  const before = await page.locator(".mcard, tbody tr").count();
  await page.getByLabel("Tier").selectOption("High");
  await expect.poll(() => page.locator(".mcard, tbody tr").count()).not.toBe(before);
});

item("MUP-08", "Board columns per lifecycle phase with model cards", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupDashTab(page, "ops");
    await expect(page.locator(".mcard[data-m]")).not.toHaveCount(0);
    return;
  }
  await signInAs(page, "Validator");
  await openAppScreen(page, "Operations Board");
  await expect(page.locator('[role="list"][aria-label="Models by stage"]')).toBeVisible();
});

item("MUP-09", "Table view sortable, row click opens Model 360", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupDashTab(page, "ops");
    const row = page.locator("tr.click[data-m]").first();
    await expect(row).toBeVisible();
    await row.click();
    await expect(page.locator("#m360")).toBeVisible();
    return;
  }
  await signInAs(page, "Validator");
  await openAppScreen(page, "Operations Board");
  await expect(page.getByRole("columnheader", { name: /Tier/ })).toBeVisible();
  await page.locator("tbody tr").first().click();
  await expect(page).toHaveURL(/\/models\/M-\d{4}/);
});

// --- Model 360 ------------------------------------------------------------------------------

item("MUP-10", "Model 360 header fields", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupModel(page);
    await expect(page.locator("#m360")).toContainText(/M-\d{4}/);
    return;
  }
  await openAppModelAsValidator(page);
  const body = page.locator("body");
  await expect(body).toContainText(/M-0012/);
  await expect(body).toContainText(/High|Medium|Low/);

  // Review finding MP-10 (G0.24): every date-only value used to render one calendar day early in
  // any timezone behind UTC, because `new Date("2026-04-16")` is midnight UTC. These three are
  // M-0012's seeded values, asserted against an independent local-time calculation, so the test
  // fails on this host and passes in UTC only if the day is right — which is the whole defect.
  const dates: [string, string][] = [
    ["Last validation", "2026-04-16"],
    ["Next due", "2027-04-16"],
    ["Go-live", "2024-08-09"],
  ];
  for (const [term, iso] of dates) {
    expect(await kvValue(page, term), `Model 360 "${term}" must render ${iso} as a local calendar day`)
      .toBe(await localeDateOnly(page, iso));
  }
});

item("MUP-11", "Status chips and overdue badge", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupModel(page);
    await expect(page.locator("#m360 .pill, #m360 [class*=pill]")).not.toHaveCount(0);
    return;
  }
  await openAppModelAsValidator(page, "M-0042"); // Overdue in the seed
  await expect(page.locator(".pill, [class*=pill]")).not.toHaveCount(0);
  await expect(page.locator("body")).toContainText(/Overdue/i);
});

item("MUP-12", "Segregation-of-duties banner", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupModel(page);
    await expect(page.locator("#stage")).toContainText(/M-\d{4}/);
    return;
  }
  // M-0078 carries the seeded legacy owner/validator conflict.
  await openAppModelAsValidator(page, "M-0078");
  await expect(page.locator("body")).toContainText(/also the model owner|segregation|independence/i);
});

item("MUP-13", "Lifecycle stepper with current phase", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupModel(page);
    await expect(page.locator("#m360")).toContainText(/Monitoring|Validation|Development/);
    return;
  }
  await openAppModelAsValidator(page);
  await expect(page.locator("body")).toContainText(/Monitoring|Validation|Development/);
});

item("MUP-14", "Approval history and MRC decisions", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupModel(page);
    await expect(page.locator("#m360")).toContainText(/Approv|MRC/i);
    return;
  }
  await openAppModelAsValidator(page, "M-0071"); // 3 seeded decisions
  await openModel360Tab(page, "Approvals");
  await expect(page.locator("body")).toContainText(/Approved|Conditional|Rejected/);
});

item("MUP-15", "Validation history with notes", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupModel(page);
    await expect(page.locator("#m360")).toContainText(/Validation/i);
    return;
  }
  await openAppModelAsValidator(page);
  await openModel360Tab(page, "Validation");
  await expect(page.locator("body")).toContainText(/Periodic|Initial|Targeted|Change|Approved|In Progress/);
});

item("MUP-16", "Findings list with severity, status, due date", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupModel(page);
    await expect(page.locator("#m360")).toContainText(/Finding/i);
    return;
  }
  await openAppModelAsValidator(page);
  await openModel360Tab(page, "Findings");
  await expect(page.locator("body")).toContainText(/Critical|Medium|Low/);
});

item("MUP-17", "Score breakdown by component", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupModel(page);
    await expect(page.locator("#m360")).toContainText(/Score/i);
    return;
  }
  await openAppModelAsValidator(page);
  await openModel360Tab(page, "Score");
  await expect(page.locator("body")).toContainText(/Documentation/);
  await expect(page.locator("body")).toContainText(/Validation currency|Issue remediation|MRC compliance/);
});

item("MUP-18", "Backtesting grid and ROC / performance chart", "6", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "results");
    await expect(page.locator("#stage")).toContainText(/Backtest|ROC|AUC|performance/i);
    return;
  }
  await openAppModelAsValidator(page);
  await expect(page.locator("body")).toContainText(/Backtest/i);
});

item("MUP-19", "Monitoring KPIs with thresholds and Pass/Warn/Fail", "6", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "results");
    await expect(page.locator("#stage")).toContainText(/Pass|Warn|Fail/);
    return;
  }
  await openAppModelAsValidator(page);
  await expect(page.locator("body")).toContainText(/Pass|Warn|Fail/);
});

item("MUP-20", "Linked CDEs on Model 360", "7", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "cde");
    await expect(page.locator("#stage")).toContainText(/CDE|data element/i);
    return;
  }
  await openAppModelAsValidator(page);
  await expect(page.locator("body")).toContainText(/CDE|Critical data element/i);
});

item("MUP-21", "Empty state for a model with no history", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupModel(page);
    await expect(page.locator("#m360")).toBeVisible();
    return;
  }
  // M-0089 is the mock-up's empty model; the seed's Initiation models are the app equivalent.
  // Empty states live on the per-topic tabs, not the Overview tab.
  await signInAs(page, "Validator");
  await openAppScreen(page, "Operations Board");
  // "Stage" labels both the filter select and a sortable column header; target the select.
  await page.locator('select[aria-label="Stage"]').selectOption("Initiation");
  await expect(page.locator("tbody tr").first()).toBeVisible();
  await page.locator("tbody tr").first().click();
  await expect(page).toHaveURL(/\/models\/M-\d{4}/);
  await openModel360Tab(page, "Validation");
  await expect(page.getByText(/No validations recorded for this model/i)).toBeVisible();
});

// --- Import Centre --------------------------------------------------------------------------

item("MUP-22", "Template download for T01-T18", "3", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "policy");
    // The mock-up labels loaded template files (T12_policy_settings.xlsx), not a T01-T18 list.
    await expect(page.locator("#stage")).toContainText(/T\d\d|Template/i);
    return;
  }
  await signInAs(page, "Admin");
  await openAppScreen(page, "Import Centre");
  // The Import Centre has its own tabs (Upload / Templates / History), defaulting to Upload.
  await page.getByRole("tab", { name: /^Templates/ }).click();
  // The registry is the single source of truth, so the screen must list the template IDs themselves.
  // Scope to the template table: the screen also renders an upload list and a batch history.
  const templateTable = page.locator("table", {
    has: page.getByRole("columnheader", { name: "Loads into" }),
  });
  await expect(templateTable.locator("tbody tr").first()).toBeVisible();
  const ids = await templateTable.locator("td span.mono").allInnerTexts();
  const templateIds = ids.filter((t) => /^T\d\d$/.test(t.trim()));
  expect(templateIds.length, `expected the T01-T18 registry to be listed, saw ${templateIds.join(", ")}`)
    .toBeGreaterThanOrEqual(6);
  expect(templateIds).toContain("T02");
});

item("MUP-23", "T02 demo preview: 4 loaded, 1 rejected, message names field and row", "3", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "inventory");
    await expect(page.locator("#stage")).toContainText(/reject|invalid|error/i);
    return;
  }
  await signInAs(page, "Admin");
  await openAppScreen(page, "Import Centre");
  // The upload control must exist; the full preview assertion needs the demo file and is part of
  // the agent's judgement pass (screenshots), because it mutates the database.
  // (Two inputs: one for files, one for a folder.)
  expect(await page.locator('input[type="file"]').count()).toBeGreaterThanOrEqual(1);
});

item("MUP-24", "Load uses the same path as preview; audit entry visible", "3", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "inventory");
    await expect(page.locator("#stage")).toContainText(/audit|load/i);
    return;
  }
  await signInAs(page, "Admin");
  await openAppScreen(page, "Audit Trail");
  await expect(page.locator("body")).toContainText(/import|create|update/i);
});

// --- Documents ------------------------------------------------------------------------------

item("MUP-25", "Upload and required-document checklist per phase", "4", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "documents");
    await expect(page.locator("#stage")).toContainText(/document/i);
    return;
  }
  await signInAs(page, "Validator");
  await openAppScreen(page, "Document Centre");
  // The Document Centre has its own tabs (Register / Upload / Batches / Completeness), defaulting to
  // Register; the file inputs are hidden inputs on the Upload tab, driven by buttons.
  await page.getByRole("tab", { name: /^Upload/ }).click();
  expect(await page.locator('input[type="file"]').count()).toBeGreaterThanOrEqual(1);
  await page.getByRole("tab", { name: /^Completeness/ }).click();
  await expect(page.locator("body")).toContainText(/Terms of Reference|required|missing/i);
});

item("MUP-26", "AI extraction: proposed fields with confirm / drop", "5", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "documents");
    await expect(page.locator("#stage")).toContainText(/extract/i);
    return;
  }
  await signInAs(page, "Validator");
  await openAppScreen(page, "Document Centre");
  await expect(page.locator("body")).toContainText(/extract/i);
});

// --- Data Audit -----------------------------------------------------------------------------

item("MUP-27", "CDE list with DQ scores by source", "7", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "cde");
    await expect(page.locator("#stage")).toContainText(/CDE|data element/i);
    return;
  }
  await signInAs(page, "Data Owner");
  await openAppScreen(page, "Data Audit");
  await expect(page.locator("body")).toContainText(/CDE/i);
});

item("MUP-28", "DQ issue list and drill-down", "7", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "rules");
    await expect(page.locator("#stage")).toContainText(/issue|rule/i);
    return;
  }
  await signInAs(page, "Data Owner");
  await openAppScreen(page, "Data Audit");
  await expect(page.locator("body")).toContainText(/issue/i);
});

// --- Report ---------------------------------------------------------------------------------

item("MUP-29", "Governance report generated and downloadable", "2A-core", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "report");
    await expect(page.locator("#repDoc")).toBeVisible();
    return;
  }
  await signInAs(page, "Executive");
  await expect(page.getByRole("link", { name: /Report/i })).toBeVisible();
});

item("MUP-30", "MRC report pack (model risk report, REQ-REG-10; partial after the core report)", "2A", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "report");
    await expect(page.locator("#repDoc")).toContainText(/MRC|governance|model risk/i);
    return;
  }
  await signInAs(page, "Executive");
  await expect(page.getByRole("link", { name: /Report/i })).toBeVisible();
});

// --- Copilot --------------------------------------------------------------------------------

item("MUP-31", "Ask a question, answer cites models from the app", "9", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "copilot");
    await expect(page.locator("#ci")).toBeVisible();
    await expect(page.locator("#msgs")).toBeVisible();
    return;
  }
  await signInAs(page, "Executive");
  await expect(page.getByRole("link", { name: /Copilot/i })).toBeVisible();
});

item("MUP-32", "Suggested questions", "9", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "copilot");
    await expect(page.locator("#sugs button")).not.toHaveCount(0);
    return;
  }
  await signInAs(page, "Executive");
  await expect(page.getByRole("link", { name: /Copilot/i })).toBeVisible();
});

// --- Cross-cutting --------------------------------------------------------------------------

item("MUP-33", "Theme, no drop shadows, no horizontal scroll at 1440x900", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupDashTab(page, "cc");
  } else {
    await signInAs(page, "Executive");
  }
  expect(await hasHorizontalScroll(page), "page must not scroll horizontally at 1440x900").toBe(false);
  const shadows = await page.evaluate(() =>
    [...document.querySelectorAll("*")]
      .map((el) => getComputedStyle(el).boxShadow)
      .filter((s) => s && s !== "none").length,
  );
  expect(shadows, "the visual language forbids drop shadows").toBe(0);
});

item("MUP-34", "Counts agree across Command Center, Operations Board and Model 360", "8", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupDashTab(page, "cc");
    await expect(page.locator(".kpi")).not.toHaveCount(0);
    return;
  }
  await signInAs(page, "Executive");
  // The tile value is its <b>; the label and sub-line must not be scraped into the number.
  const tile = page.locator(".tile", { hasText: "Total models" }).first();
  const total = Number((await tile.locator("b").innerText()).replace(/[^\d]/g, ""));
  expect(total, "Command Center must report a model total").toBeGreaterThan(0);

  await openAppScreen(page, "Operations Board");
  // The board states its own total, so check that first: it separates "the board disagrees with the
  // Command Center" from "the board disagrees with its own table", which are different faults.
  await expect(page.getByText(/^\d+ models shown\.$/),
    "the Operations Board's own count must match the Command Center total")
    .toHaveText(`${total} models shown.`);
  // toHaveCount retries until the DOM settles. A one-shot count() could run while the table was
  // being replaced and read 0, which is what made this check flaky in a full run (G0.13).
  await expect(page.locator("div.tablewrap tbody tr"),
    `Operations Board rows must match the Command Center total (${total})`).toHaveCount(total);

  // Counts were never the only thing that had to agree across screens. The worse half of MP-10 was
  // that the Command Center's revalidation timeline printed the raw ISO string while Model 360
  // formatted it, so the same model showed two different due dates depending on the screen.
  await openAppScreen(page, "Command Center");
  const lede = page.getByText(/Model risk across the portfolio as of /);
  await expect(lede).toBeVisible();
  const asOf = (await lede.innerText()).match(/as of ([^.]+)\./)?.[1]?.trim();
  expect(asOf, "the Command Center lede must state the business date")
    .toBe(await localeDateOnly(page, "2026-09-30")); // MRM_TODAY_OVERRIDE, mockup-parity.md line 1

  const timeline = page.locator("section.panel")
    .filter({ has: page.getByRole("heading", { name: /Revalidation timeline/ }) });
  await expect(timeline).toBeVisible();
  const row = timeline.locator("tbody tr").first();
  const modelId = (await row.locator("td").first().innerText()).match(/M-\d{4}/)?.[0];
  expect(modelId, "the revalidation timeline must list a model").toMatch(/^M-\d{4}$/);
  const dueOnCommandCenter = (await row.locator("td").nth(2).innerText()).trim();
  // Not a raw ISO string any more, and not a different day from Model 360's own answer.
  expect(dueOnCommandCenter, "the timeline must format the due date, not print raw ISO")
    .not.toMatch(/^\d{4}-\d{2}-\d{2}$/);

  await page.goto(`/models/${modelId}`);
  await expect(page.getByText(modelId as string).first()).toBeVisible();
  expect(await kvValue(page, "Next due"),
    `${modelId}'s next due date must read the same on the Command Center and on Model 360`)
    .toBe(dueOnCommandCenter);
});

item("MUP-35", "Actions not permitted are hidden and refused by the API", "1", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "users");
    await expect(page.locator("#stage")).toContainText(/role/i);
    return;
  }
  await signInAs(page, "Executive");
  // Read-only role: no Admin link, no audit access, no create action.
  await expect(page.locator('nav.rail[aria-label="Main"]').getByRole("link", { name: "Audit Trail" }))
    .toHaveCount(0);
  await page.goto("/models/new");
  await expect(page.locator("body")).toContainText(/not permitted|forbidden|403/i);
});

// --- Screens added at the Gate 0 exit review (2026-10-07) -----------------------------------
// Admin and the Audit Trail are built screens (BRD §55.8, §55.9) that had no checklist item, and
// MUP-25 covered only the Document Centre's upload and completeness tabs.

item("MUP-36", "Admin policy settings listed and editable", "1", async ({ page, isMockup }) => {
  if (isMockup) {
    // Mock-up rail step 1 "Configure policy" is the T12 policy settings screen.
    await openMockupScreen(page, "policy");
    await expect(page.locator("#stage")).toContainText(/polic/i);
    return;
  }
  await signInAs(page, "Admin");
  await openAppScreen(page, "Admin");
  const policy = page.locator("section.panel").filter({ has: page.getByRole("heading", { name: /Policy settings/ }) });
  await expect(policy).toBeVisible();
  await expect(policy.getByRole("columnheader", { name: "Key" })).toBeVisible();
  await expect(policy.getByRole("columnheader", { name: "Value" })).toBeVisible();
  // Admin holds policy:edit, so the panel announces that changes are audited rather than read-only.
  await expect(policy).toContainText(/versioned and audited/i);
  await expect(policy.locator("tbody tr").first()).toBeVisible();
});

item("MUP-37", "Audit Trail filters by user, model, entity, action, batch, document and date", "1",
     async ({ page, isMockup }) => {
  if (isMockup) {
    // The mock-up has no Audit Trail screen; it reports audit_event as a governance table only.
    // Recorded as an accepted difference in mockup-parity.md (§55.9, AUD-03).
    await openMockupScreen(page, "overview");
    await expect(page.locator("body")).toContainText(/audit/i);
    return;
  }
  await signInAs(page, "Admin");
  await openAppScreen(page, "Audit Trail");
  for (const label of ["User", "Model", "Entity", "Action", "Batch", "Document", "From date", "To date"]) {
    await expect(page.getByLabel(label, { exact: true }), `audit filter "${label}"`).toBeVisible();
  }
  const rows = page.locator("div.tablewrap tbody tr");
  await expect(rows.first()).toBeVisible();
  const before = await rows.count();
  // A filter must actually narrow the list, not just exist.
  await page.getByLabel("Action", { exact: true }).fill("reset");
  await page.getByRole("button", { name: "Apply" }).click();
  await expect.poll(() => rows.count()).toBeLessThan(before);
  await expect(page.locator("div.tablewrap tbody")).toContainText(/reset/i);
});

item("MUP-38", "Document register with search / filter and version history", "4", async ({ page, isMockup }) => {
  if (isMockup) {
    await openMockupScreen(page, "documents");
    await expect(page.locator("#stage")).toContainText(/document/i);
    return;
  }
  await signInAs(page, "Validator");
  await openAppScreen(page, "Document Centre");
  await page.getByRole("tab", { name: /^Register/ }).click();
  const rows = page.locator("div.tablewrap tbody tr");
  await expect(rows.first(), "the seeded evidence must be listed").toBeVisible();
  const before = await rows.count();
  expect(before, "the Register tab must list documents").toBeGreaterThan(0);
  // Folder tree (§55.6): the folder hierarchy of the uploaded evidence is navigable.
  await expect(page.locator(".doc-layout")).toBeVisible();
  // Filtering must narrow the list, not merely exist.
  await page.getByPlaceholder("Model (M-0012)").fill("M-0012");
  await page.getByRole("button", { name: "Search" }).click();
  await expect.poll(() => rows.count()).toBeLessThan(before);
  // Opening a document shows its immutable version history (§36, DOC-17). The row is clickable;
  // its only <a> is the model link, which would navigate to Model 360 instead.
  await rows.first().locator("td").first().click();
  await expect(page.getByRole("heading", { name: /^Versions/ })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Version" })).toBeVisible();
});

/** Sign in as Validator and open a model page. */
async function openAppModelAsValidator(page: Page, modelId = "M-0012"): Promise<void> {
  await signInAs(page, "Validator");
  await openAppModel(page, modelId);
}
