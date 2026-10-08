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

/**
 * A control in an open Model 360 action form, by its field label.
 *
 * `getByLabel("Severity", { exact: true })` cannot work here: `ActionForm` renders `<label
 * className="field">Severity<select>…</select></label>`, so the accessible name of the select is
 * "Severity" followed by every option's text. That is the same wrapping-label trap as harness
 * defect H-01, and it is why FS-11 and FS-12 timed out on their first select. XPath `text()`
 * selects only the label's *direct* text children, so the option text is excluded and one field
 * name cannot match another's ("Decision" vs "Decision date" vs "Decision type").
 */
function actionField(page: import("@playwright/test").Page, label: string) {
  return page.locator(
    `xpath=//form[contains(@class,"action-form")]//label[normalize-space(text())="${label}"]`
  ).locator("input, select, textarea");
}

test("FS-06 INV-03 a segregation-of-duties breach is refused in the UI and on import", async ({ page }) => {
  await signInAs(page, "Admin");
  const before = dbCount("model");
  const auditBefore = dbCount("audit_event", "entity = 'model'");

  // The person named as both Owner and Validator has to hold *both* roles, because the Validator
  // `<select>` lists only users with the Validator role (`ModelForm.tsx`, `userOpts("Validator")`).
  // U-003 holds Model Owner only, so the option could never exist and `selectOption` timed out for
  // 30 s — harness defect H-11, not a product defect: the UI not offering an impossible validator
  // is correct. U-101 (Jia Chen) is the seed's only Model Owner *and* Validator, which is exactly
  // the fixture an SoD breach needs. Asserted rather than assumed, so a reseed that drops the dual
  // role fails loudly here instead of timing out in the form.
  const dualRole = dbQuery(
    `SELECT u.user_id AS user_id FROM app_user u
      WHERE u.active = 1
        AND EXISTS (SELECT 1 FROM user_role r WHERE r.user_id = u.user_id AND r.role = 'Model Owner')
        AND EXISTS (SELECT 1 FROM user_role r WHERE r.user_id = u.user_id AND r.role = 'Validator')
      ORDER BY u.user_id`);
  expect(dualRole.length, "the seed must have a user holding both Model Owner and Validator")
    .toBeGreaterThan(0);
  const sameUser = String(dualRole[0].user_id);

  await fillNewModel(page, {
    "Model name": "SoD probe", "Model subtype": "PD", "Business line": "Business Banking",
    "Version": "v1.0", "Model type": "Credit Risk", "Lifecycle phase": "Validation",
    "Purpose": "Checks that a refused create writes nothing.",
    "Owner": sameUser, "Developer": "U-021", "Validator": sameUser,
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
    // Events are counted from here on, not for all time. A reset reloads the 256-model seed but
    // *keeps* the audit trail (Part 0), so the next free model id is handed out again and the
    // trail already holds a `create` for it from an earlier run — `= 1` then failed on a second
    // run against the same database while the product was behaving correctly (harness defect
    // H-15; the id reuse itself is reported as unspecified behaviour).
    const sinceEvent = Number(dbQuery("SELECT COALESCE(MAX(event_id), 0) AS n FROM audit_event")[0].n);

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

    // INV-01/INV-02: the create is audited — exactly once, by this scenario.
    expect(dbCount("audit_event",
      "entity = 'model' AND action = 'create' AND entity_id = ? AND event_id > ?",
      [modelId, sinceEvent])).toBe(1);

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
  // Two harness defects fixed here (H-02). The owner is *read* from the model rather than named:
  // the comment used to say U-003 owned M-0012, and the seed now owns it with U-101, so
  // `ensure_can_edit_finding` would have refused the write with a 403 that the scenario would have
  // reported as a product defect. And "Raise finding" lives behind the Findings tab of Model 360
  // (`Model360Page.tsx`, `tab === "Findings"`), so the tab has to be opened first.
  const modelId = "M-0012";
  const owner = String(dbQuery("SELECT owner_id FROM model WHERE model_id = ?", [modelId])[0].owner_id);
  await signInAsUser(page, owner, "Model Owner");
  const before = (await apiAs(page, "/api/dashboard/summary")).body as { tiles: Record<string, number> };

  await page.goto(`/models/${modelId}`);
  await page.getByRole("tab", { name: /^Findings/ }).click();
  await page.getByRole("button", { name: "Raise finding" }).click();
  await actionField(page, "Title").fill("Functional suite finding");
  await actionField(page, "Severity").selectOption("Low");
  await actionField(page, "Category").selectOption({ index: 1 });
  await actionField(page, "Due date").fill("2026-12-31");
  await actionField(page, "Description").fill("Raised by FS-11.");
  await page.getByRole("button", { name: "Save finding" }).click();

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

  // "Record decision" sits behind the Approvals tab of Model 360, and behind the `Reveal` toggle
  // that renders the form (H-02); the scenario used to look for it on the Overview tab.
  await page.goto("/models/M-0023");
  await page.getByRole("tab", { name: /^Approvals/ }).click();
  await page.getByRole("button", { name: "Record decision" }).click();
  await actionField(page, "Decision date").fill("2026-09-01");
  await actionField(page, "Forum").selectOption({ index: 1 });
  await actionField(page, "Decision type").selectOption({ index: 1 });
  await actionField(page, "Decision").selectOption("Conditional");
  await actionField(page, "Conditions").fill("Functional suite condition");
  await actionField(page, "Condition due date").fill("2026-12-31");
  await actionField(page, "Condition status").selectOption("Open");
  await page.getByRole("button", { name: "Save decision" }).click();

  await expect.poll(outstanding, { timeout: 15_000 }).toContain("M-0023");
  await checkpoint(page, "FS-12_outstanding");

  await page.reload();
  await page.getByRole("tab", { name: /^Approvals/ }).click();
  // The button reads "Mark conditions met" — lower-case "met", so the old case-sensitive /Met/
  // never matched it and the scenario timed out *after* proving the first half of APR-03.
  //
  // Every open condition is closed, not just the first. APR-03 is "stays visible as outstanding
  // until *every* condition is closed", so one click proves nothing when the model has two open
  // conditions — and it has two whenever this scenario has run before against the same database,
  // which is how it looked like a product defect on its first green run.
  const markMet = page.getByRole("button", { name: /Mark conditions met/i });
  for (let open = await markMet.count(); open > 0; open = await markMet.count()) {
    expect(await outstanding(), "APR-03: outstanding while a condition is still open")
      .toContain("M-0023");
    await markMet.first().click();
    await expect(markMet, "the closed condition leaves the open set").toHaveCount(open - 1,
      { timeout: 15_000 });
  }
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
