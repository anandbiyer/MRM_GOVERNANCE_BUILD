// FS-20, FS-24 — the audit trail (AUD-03) and refusals leaving no trace (AUD-01).
import { expect, test } from "@playwright/test";
import { apiAs, checkpoint, dbCount, highlight, openScreen, signInAs } from "./helpers";

/** The hard limit `/api/audit` applies to `limit`. A result of exactly this size may be truncated. */
const CAP = 1000;

test("FS-20 AUD-03 the audit trail filters by each documented dimension", async ({ page }) => {
  await signInAs(page, "Auditor");
  const all = (await apiAs(page, "/api/audit?limit=1000")).body as {
    event_id: number; user_id: string | null; model_id: string | null; entity: string;
    action: string; import_batch_id: string | null; document_id: string | null; occurred_at: string;
  }[];
  expect(all.length, "the seed load should leave audit events").toBeGreaterThan(0);

  const check = async (query: string, predicate: (e: typeof all[number]) => boolean, label: string) => {
    const got = (await apiAs(page, `/api/audit?limit=1000&${query}`)).body as typeof all;
    expect(got.length, `${label} returns nothing`).toBeGreaterThan(0);
    // Including: everything returned matches.
    expect(got.every(predicate), `${label} returned a non-matching event`).toBe(true);

    // Excluding — the other half of AUD-03, and the half that needs no totals. An event that does
    // not match the filter must not come back.
    const outsider = all.find((e) => !predicate(e));
    if (outsider) {
      expect(got.some((e) => e.event_id === outsider.event_id),
        `${label} returned an event it should have excluded`).toBe(false);
    }

    // A count comparison is only meaningful when neither side is truncated. The endpoint caps
    // `limit` at 1000 and returns no total, so with 2500+ seeded events the baseline is capped and
    // `all.filter(...).length` is not the real total — comparing the two was harness defect H-05
    // ("expected 999, received 1000", where both numbers were artefacts of the cap). Asserting a
    // count at all needs the endpoint to report a total, which is plan BL.4.
    if (got.length < CAP && all.length < CAP) {
      expect(got.length, `${label} count`).toBe(all.filter(predicate).length);
    }
  };

  const sample = all.find((e) => e.model_id) ?? all[0];
  await check(`entity=${sample.entity}`, (e) => e.entity === sample.entity, "entity");
  await check(`action=${sample.action}`, (e) => e.action === sample.action, "action");
  if (sample.model_id) {
    await check(`model_id=${sample.model_id}`, (e) => e.model_id === sample.model_id, "model_id");
  }
  const withUser = all.find((e) => e.user_id);
  if (withUser) await check(`user_id=${withUser.user_id}`, (e) => e.user_id === withUser.user_id, "user_id");
  const withBatch = all.find((e) => e.import_batch_id);
  if (withBatch) {
    await check(`batch_id=${withBatch.import_batch_id}`,
      (e) => e.import_batch_id === withBatch.import_batch_id, "batch_id");
  }
  const withDoc = all.find((e) => e.document_id);
  if (withDoc) {
    await check(`document_id=${withDoc.document_id}`, (e) => e.document_id === withDoc.document_id, "document_id");
  }

  // The date range is the half of AUD-03 that no unit test exercises (TR-12).
  const day = all[0].occurred_at.slice(0, 10);
  const sameDay = (await apiAs(page, `/api/audit?limit=1000&date_from=${day}&date_to=${day}`)).body as typeof all;
  expect(sameDay.length, "date_from/date_to for the day of the newest event").toBeGreaterThan(0);
  expect(sameDay.every((e) => e.occurred_at.slice(0, 10) === day),
    "the date range must exclude other days").toBe(true);

  // The screenshot used to be taken the moment the link was clicked, so the saved evidence read
  // "Loading…" with no rows even though every assertion above had passed (harness defect H-14).
  // Waiting for the first row means the evidence shows what a user sees.
  await openScreen(page, "Audit Trail");
  await expect(page.locator("table tbody tr").first()).toBeVisible({ timeout: 15_000 });
  await checkpoint(page, "FS-20_audit_trail");
});

test("FS-24 AUD-01 refused writes leave no audit event; a permitted write adds exactly one",
  async ({ page }) => {
    await signInAs(page, "Admin");
    const token = await page.evaluate(() => localStorage.getItem("mrm.token"));
    const h = { Authorization: `Bearer ${token}` };
    const modelCreates = () => dbCount("audit_event", "entity = 'model' AND action = 'create'");
    const policyUpdates = () => dbCount("audit_event", "entity = 'policy_setting' AND action = 'update'");
    const overrides = () => dbCount("audit_event", "action = 'tier_override'");

    // 1. A segregation-of-duties breach.
    const before = modelCreates();
    const sod = await page.request.post("/api/models", { headers: h, data: {
      model_id: "M-0901", model_name: "FS-24 probe", model_type: "Credit Risk", model_subtype: "PD",
      purpose: "Refusal probe.", business_line: "Business Banking", owner_id: "U-003",
      developer_id: "U-021", validator_id: "U-003", lifecycle_phase: "Validation", version: "v1.0",
      q_materiality: 2, q_complexity: 2, q_reliance: 2, q_regulatory_use: 2 } });
    expect(sod.status()).toBe(422);
    expect(dbCount("model", "model_id = ?", ["M-0901"]), "no model saved").toBe(0);
    expect(modelCreates(), "no audit event for the refused create").toBe(before);

    // 2. A tier override without a reason.
    const overridesBefore = overrides();
    const model = (await apiAs(page, "/api/models/M-0015")).body as { model: { row_version: number } };
    const noReason = await page.request.post("/api/models/M-0015/tier-override", { headers: h,
      data: { tier: "Low", reason: " ", row_version: model.model.row_version } });
    expect(noReason.status()).toBe(422);
    expect(overrides(), "no audit event for the refused override").toBe(overridesBefore);

    // 3. An action without permission.
    await signInAs(page, "Auditor");
    const auditorToken = await page.evaluate(() => localStorage.getItem("mrm.token"));
    const settings = (await apiAs(page, "/api/admin/policy")).body as
      { setting_key: string; value: string; row_version: number }[];
    const lead = settings.find((s) => s.setting_key === "reval_lead_days")!;
    const policyBefore = policyUpdates();
    const forbidden = await page.request.put("/api/admin/policy/reval_lead_days", {
      headers: { Authorization: `Bearer ${auditorToken}` },
      data: { value: "90", row_version: lead.row_version } });
    expect(forbidden.status()).toBe(403);
    expect(policyUpdates(), "no audit event for the refused policy edit").toBe(policyBefore);

    await signInAs(page, "Admin");
    const stillThere = ((await apiAs(page, "/api/admin/policy")).body as typeof settings)
      .find((s) => s.setting_key === "reval_lead_days")!;
    expect(stillThere.value, "the refused edit left the value alone").toBe(lead.value);

    // Control: a permitted write adds exactly one event, so the three negatives mean something.
    const adminToken = await page.evaluate(() => localStorage.getItem("mrm.token"));
    const ok = await page.request.put("/api/admin/policy/reval_lead_days", {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: { value: "90", row_version: stillThere.row_version, reason: "FS-24 control" } });
    expect(ok.status(), await ok.text()).toBe(200);
    expect(policyUpdates(), "the permitted write adds exactly one event").toBe(policyBefore + 1);

    await openScreen(page, "Audit Trail");
    const row = page.locator("tbody tr").first();
    if (await row.count()) await highlight(row);
    await checkpoint(page, "FS-24_audit_after_control");
  });
