// FS-06 … FS-14 — inventory, tiering, lifecycle, validation, findings, approvals, score, policy.
import { expect, test } from "@playwright/test";
import path from "node:path";
import { apiAs, checkpoint, dbCount, dbQuery, highlight, openScreen, RUN_DIR, signInAs, signInAsUser } from "./helpers";

/** Fill the registration form. Labels come from ModelForm's `field()` helper. */
async function fillNewModel(page: import("@playwright/test").Page, values: Record<string, string>) {
  await page.goto("/models/new");
  await expect(page.getByLabel("Model name")).toBeVisible();
  for (const [label, value] of Object.entries(values)) {
    // Not `{ exact: true }`: these labels *wrap* their control, so a <select>'s label text is the
    // field name followed by every option's text ("Model type" + "Credit Risk" + ...). Exact
    // matching therefore worked for text inputs and could never work for a select, which is why
    // FS-06 and FS-07 timed out on "Model type" (harness defect H-01). Anchored to the start of
    // the label so one field name cannot match another's.
    const control = page.getByLabel(new RegExp(`^\s*${label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`));
    const tag = await control.evaluate((el) => el.tagName.toLowerCase());
    if (tag === "select") await control.selectOption(value);
    else await control.fill(value);
  }
  // The four tiering answers are selects in the Risk tiering panel; their labels come from policy.
  const tiering = page.locator("section.panel", { hasText: "Risk tiering" }).locator("select");
  for (let i = 0; i < 4; i++) await tiering.nth(i).selectOption("2");
}

test("FS-06 INV-03 a segregation-of-duties breach is refused in the UI and on import", async ({ page }) => {
  await signInAs(page, "Admin");
  const before = dbCount("model");
  const auditBefore = dbCount("audit_event", "entity = 'model'");

  await fillNewModel(page, {
    "Model name": "SoD probe", "Model subtype": "PD", "Business line": "Business Banking",
    "Version": "v1.0", "Model type": "Credit Risk", "Lifecycle phase": "Validation",
    "Purpose": "Checks that a refused create writes nothing.",
    "Owner": "U-003", "Developer": "U-021", "Validator": "U-003",
  });
  await page.getByRole("button", { name: /Register|Save/ }).first().click();

  const error = page.locator(".errline, .field-error").first();
  await expect(error).toBeVisible({ timeout: 10_000 });
  await expect(page.locator("body")).toContainText(/also the model owner/i);
  await highlight(error);
  await checkpoint(page, "FS-06_ui_refusal");

  // INV-03 + AUD-01: nothing saved, nothing audited.
  expect(dbCount("model"), "no model created").toBe(before);
  expect(dbCount("audit_event", "entity = 'model'"), "no audit event").toBe(auditBefore);

  // The same breach on the import path.
  await openScreen(page, "Import Centre");
  await page.locator('input[type="file"]').first()
    .setInputFiles(path.join(RUN_DIR, "inputs", "T02_sod_breach.csv"));
  await page.getByRole("button", { name: /Upload and validate/i }).click();
  await expect(page.locator("body")).toContainText(/also the model owner/i, { timeout: 20_000 });
  await checkpoint(page, "FS-06_import_refusal");
  expect(dbCount("model"), "import must not create the breaching model").toBe(before);
});

test("FS-07 INV-01 INV-02 AUD-01 CC-01 create then edit, with before/after in the audit trail",
  async ({ page }) => {
    // Admin, because a Model Owner may only edit models already assigned to them (SEC-03).
    await signInAs(page, "Admin");
    const tilesBefore = (await apiAs(page, "/api/dashboard/summary")).body as { tiles: Record<string, number> };

    await fillNewModel(page, {
      "Model name": "Functional probe PD", "Model subtype": "PD", "Business line": "Business Banking",
      "Version": "v1.0", "Model type": "Credit Risk", "Lifecycle phase": "Validation",
      "Purpose": "Created by the functional suite to prove INV-01, INV-02 and CR-06.",
      "Owner": "U-003", "Developer": "U-021", "Validator": "U-016",
    });
    await page.getByRole("button", { name: /Register|Save/ }).first().click();
    await expect(page).toHaveURL(/\/models\/M-\d{4}/, { timeout: 15_000 });
    const modelId = page.url().split("/").pop()!;
    await checkpoint(page, "FS-07_created");

    // INV-01/INV-02: the create is audited.
    expect(dbCount("audit_event", "entity = 'model' AND action = 'create' AND entity_id = ?", [modelId]))
      .toBe(1);

    // CR-06 / G0.5 at runtime: the Command Center reflects the new model without a reload.
    await openScreen(page, "Command Center");
    await expect.poll(async () =>
      ((await apiAs(page, "/api/dashboard/summary")).body as { tiles: Record<string, number> })
        .tiles.total_models, { timeout: 15_000 }).toBe(tilesBefore.tiles.total_models + 1);
    const total = page.locator(".tile", { hasText: "Total models" }).first();
    await expect(total).toContainText(String(tilesBefore.tiles.total_models + 1));
    await checkpoint(page, "FS-07_command_center");

    // Edit it, with a reason, and check before/after are recorded.
    await page.goto(`/models/${modelId}/edit`);
    await page.getByLabel("Business line", { exact: true }).fill("Corporate Banking");
    await page.getByLabel(/^Reason for change/).fill("Functional suite: FS-07");
    await page.getByRole("button", { name: /Register|Save/ }).first().click();
    await expect(page).toHaveURL(new RegExp(`/models/${modelId}$`), { timeout: 15_000 });

    const updates = dbQuery(
      "SELECT before_json, after_json, user_id, role, reason FROM audit_event " +
      "WHERE entity = 'model' AND action = 'update' AND entity_id = ? ORDER BY event_id DESC LIMIT 1",
      [modelId]);
    expect(updates.length, "INV-02: the edit is audited").toBe(1);
    expect(String(updates[0].before_json)).toContain("Business Banking");
    expect(String(updates[0].after_json)).toContain("Corporate Banking");
    expect(updates[0].reason).toBe("Functional suite: FS-07");
    await page.goto("/audit");
    await checkpoint(page, "FS-07_audit_trail");
  });

test("FS-08 TIR-01 TIR-04 TIR-05 tiering follows policy; an override needs a reason", async ({ page }) => {
  await signInAs(page, "Admin");  // TIR-04: only an authorised role may override
  const meta = (await apiAs(page, "/api/models/meta")).body as { tiers: string[] };
  expect(meta.tiers.length).toBeGreaterThan(0);

  // TIR-01: the preview endpoint scores the four answers against the policy minima.
  const preview = await page.request.post("/api/models/tier-preview", {
    headers: { Authorization: `Bearer ${await page.evaluate(() => localStorage.getItem("mrm.token"))}` },
    data: { q_materiality: 3, q_complexity: 3, q_reliance: 2, q_regulatory_use: 2 },
  });
  expect((await preview.json()).tier).toBe("High");

  await page.goto("/models/M-0012");
  const detail = (await apiAs(page, "/api/models/M-0012")).body as { model: { calculated_tier: string } };
  await page.getByRole("button", { name: "Override tier" }).click();
  await page.getByLabel(/^Override tier/).selectOption("Medium");
  await page.getByRole("button", { name: "Apply" }).click();
  // TIR-04: a blank justification is refused.
  await expect(page.locator(".errline")).toBeVisible({ timeout: 10_000 });
  await checkpoint(page, "FS-08_override_without_reason");

  await page.getByLabel(/^Justification/).fill("Exposure run-off (functional suite)");
  await page.getByRole("button", { name: "Apply" }).click();
  await expect.poll(async () =>
    ((await apiAs(page, "/api/models/M-0012")).body as { model: { effective_tier: string } })
      .model.effective_tier, { timeout: 15_000 }).toBe("Medium");

  // TIR-05: the calculated tier is kept alongside the override.
  const after = (await apiAs(page, "/api/models/M-0012")).body as {
    model: { calculated_tier: string }; tier_overrides: { previous_tier: string }[];
  };
  expect(after.model.calculated_tier).toBe(detail.model.calculated_tier);
  expect(after.tier_overrides[0].previous_tier).toBe(detail.model.calculated_tier);
  await checkpoint(page, "FS-08_override_applied");
});

test("FS-09 LIF-01 INV-05 a phase move without required data is refused", async ({ page }) => {
  await signInAs(page, "Admin");
  // M-0085 sits before Validation in the seed and has no validator, so the move must be refused.
  await page.goto("/models/M-0085");
  await page.getByRole("button", { name: "Change phase" }).click();
  await page.getByLabel("New phase").selectOption("Validation");
  await page.getByLabel("Reason", { exact: true }).fill("Functional suite: FS-09");
  await page.getByRole("button", { name: /Record|Save|Change/ }).first().click();
  await expect(page.locator(".errline")).toBeVisible({ timeout: 10_000 });
  await expect(page.locator("body")).toContainText(/validator is required/i);
  await highlight(page.locator(".errline").first());
  await checkpoint(page, "FS-09_refused");

  const phase = dbQuery("SELECT lifecycle_phase FROM model WHERE model_id = 'M-0085'")[0];
  expect(phase.lifecycle_phase, "the phase must not have moved").not.toBe("Validation");
});

test("FS-10 VAL-02 VAL-04 revalidation status is correct for the fixed business date", async ({ page }) => {
  await signInAs(page, "Validator");
  const rows = (await apiAs(page, "/api/models")).body as {
    model_id: string; state: { next_due: string | null; days_to_due: number | null; revalidation_status: string | null };
  }[];
  const scored = rows.filter((r) => r.state.next_due);
  expect(scored.length).toBeGreaterThan(0);
  for (const r of scored.slice(0, 40)) {
    const days = r.state.days_to_due!;
    const expected = days < 0 ? "Overdue" : days <= 30 ? "Due Soon" : "Scheduled";
    expect(r.state.revalidation_status, `${r.model_id} at ${days} days`).toBe(expected);
  }
  // VAL-03: no last validation date means no due date.
  expect(rows.filter((r) => !r.state.next_due).every((r) => r.state.revalidation_status === null)).toBe(true);
  await openScreen(page, "Operations Board");
  await checkpoint(page, "FS-10_revalidation");
});

test("FS-11 FND-02 FND-04 CC-01 raise a finding and watch the overdue counts move", async ({ page }) => {
  await signInAsUser(page, "U-003", "Model Owner");  // the owner of M-0012 in the seed
  const before = (await apiAs(page, "/api/dashboard/summary")).body as { tiles: Record<string, number> };

  await page.goto("/models/M-0012");
  await page.getByRole("button", { name: "Raise finding" }).click();
  await page.getByLabel("Title", { exact: true }).fill("Functional suite finding");
  await page.getByLabel("Severity", { exact: true }).selectOption("Low");
  await page.getByLabel("Category", { exact: true }).selectOption({ index: 1 });
  await page.getByLabel("Due date", { exact: true }).fill("2026-12-31");
  await page.getByLabel("Description", { exact: true }).fill("Raised by FS-11.");
  await page.getByRole("button", { name: /Save|Raise/ }).first().click();

  await expect.poll(async () =>
    ((await apiAs(page, "/api/dashboard/summary")).body as { tiles: Record<string, number> })
      .tiles.open_findings, { timeout: 15_000 }).toBe(before.tiles.open_findings + 1);
  await checkpoint(page, "FS-11_finding_raised");
  expect(dbCount("audit_event", "entity = 'finding' AND action = 'create'")).toBeGreaterThan(0);
});

test("FS-12 APR-03 a conditional approval stays outstanding until its conditions close", async ({ page }) => {
  await signInAs(page, "MRC Member");
  const outstanding = async () =>
    ((await apiAs(page, "/api/models?flag=open_conditions")).body as { model_id: string }[])
      .map((m) => m.model_id);

  await page.goto("/models/M-0023");
  await page.getByRole("button", { name: "Record decision" }).click();
  await page.getByLabel("Decision date", { exact: true }).fill("2026-09-01");
  await page.getByLabel("Forum", { exact: true }).selectOption({ index: 1 });
  await page.getByLabel("Decision type", { exact: true }).selectOption({ index: 1 });
  await page.getByLabel("Decision", { exact: true }).selectOption("Conditional");
  await page.getByLabel("Conditions", { exact: true }).fill("Functional suite condition");
  await page.getByLabel("Condition due date", { exact: true }).fill("2026-12-31");
  await page.getByLabel("Condition status", { exact: true }).selectOption("Open");
  await page.getByRole("button", { name: /Save|Record/ }).first().click();

  await expect.poll(outstanding, { timeout: 15_000 }).toContain("M-0023");
  await checkpoint(page, "FS-12_outstanding");

  await page.reload();
  await page.getByRole("tab", { name: /^Approvals/ }).click();
  await page.getByRole("button", { name: /Met/ }).first().click();
  await expect.poll(outstanding, { timeout: 15_000 }).not.toContain("M-0023");
  await checkpoint(page, "FS-12_cleared");
});

test("FS-13 SCR-01 SCR-05 the score breakdown matches an independent calculation", async ({ page }) => {
  await signInAs(page, "Validator");
  for (const modelId of ["M-0012", "M-0023", "M-0042"]) {
    const d = (await apiAs(page, `/api/models/${modelId}`)).body as {
      score: { overall: string | null; components: { key: string; score: string | null; weight: string;
                                                    effective_weight: string | null; inputs: unknown }[] };
    };
    const applicable = d.score.components.filter((c) => c.score !== null);
    if (!applicable.length) continue;

    // SCR-01: recompute from the parts rather than trusting the total.
    const weighted = applicable.reduce((s, c) => s + Number(c.score) * Number(c.effective_weight), 0);
    const weights = applicable.reduce((s, c) => s + Number(c.effective_weight), 0);
    expect(Math.abs(weights - 100), `${modelId} effective weights must total 100`).toBeLessThan(0.3);
    expect(Math.abs(weighted / 100 - Number(d.score.overall)), `${modelId} overall`).toBeLessThan(0.15);

    // SCR-05: each component is explainable.
    for (const c of applicable) {
      expect(Number(c.weight), `${modelId}/${c.key} weight`).toBeGreaterThan(0);
      expect(c.inputs, `${modelId}/${c.key} inputs`).toBeTruthy();
    }
  }
  await page.goto("/models/M-0012");
  await page.getByRole("tab", { name: /^Score/ }).click();
  await checkpoint(page, "FS-13_score_breakdown");
});

test("FS-14 CFG-02 CFG-03 TIR-03 a policy change moves tiers and is audited", async ({ page }) => {
  await signInAs(page, "Admin");
  await openScreen(page, "Admin");
  const token = await page.evaluate(() => localStorage.getItem("mrm.token"));
  const settings = (await apiAs(page, "/api/admin/policy")).body as
    { setting_key: string; value: string; row_version: number }[];
  const high = settings.find((s) => s.setting_key === "tier_high_min")!;

  const highBefore = ((await apiAs(page, "/api/models?tier=High")).body as unknown[]).length;
  const resp = await page.request.put("/api/admin/policy/tier_high_min", {
    headers: { Authorization: `Bearer ${token}` },
    data: { value: "12", row_version: high.row_version, reason: "Functional suite: FS-14" },
  });
  expect(resp.status(), await resp.text()).toBe(200);

  // TIR-03 + CFG-02: the change takes effect on the next read.
  const highAfter = ((await apiAs(page, "/api/models?tier=High")).body as unknown[]).length;
  expect(highAfter, "raising the High minimum cannot increase the High count")
    .toBeLessThanOrEqual(highBefore);

  // CFG-03: before and after are audited.
  const events = dbQuery(
    "SELECT before_json, after_json, reason FROM audit_event WHERE entity = 'policy_setting' " +
    "AND entity_id = 'tier_high_min' ORDER BY event_id DESC LIMIT 1");
  expect(events.length).toBe(1);
  expect(String(events[0].before_json)).toContain(high.value);
  expect(String(events[0].after_json)).toContain("12");
  await page.reload();
  await checkpoint(page, "FS-14_policy_changed");
});
