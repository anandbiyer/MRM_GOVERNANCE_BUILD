// FS-02 … FS-05, FS-21 — structured ingestion (§79 IMP-*) and reset determinism (GEN-01).
// FS-30 … FS-32 are unbuilt phases and appear as fixme.
import { expect, test } from "@playwright/test";
import path from "node:path";
import { apiAs, checkpoint, dbCount, openScreen, RUN_DIR, signInAs } from "./helpers";

const ENABLED = ["T12", "T01", "T02", "T03", "T04", "T05", "T17", "T18"];
const DISABLED = ["T06", "T07", "T08", "T09", "T10", "T11", "T13", "T14", "T15", "T16"];

async function openTemplates(page: import("@playwright/test").Page) {
  await openScreen(page, "Import Centre");
  await page.getByRole("tab", { name: /^Templates/ }).click();
}

test("FS-02 IMP-02 IMP-03 enabled templates download with registry columns; disabled ones do not",
  async ({ page }) => {
    await signInAs(page, "Admin");
    const templates = (await apiAs(page, "/api/imports/templates")).body as {
      template_id: string; available: boolean; columns: { name: string }[];
    }[];
    const byId = Object.fromEntries(templates.map((t) => [t.template_id, t]));

    expect(templates.filter((t) => t.available).map((t) => t.template_id).sort())
      .toEqual([...ENABLED].sort());
    for (const id of DISABLED) expect(byId[id]?.available, id).toBe(false);

    await openTemplates(page);
    await expect(page.locator("table", { has: page.getByRole("columnheader", { name: "Loads into" }) })
      .locator("tbody tr").first()).toBeVisible();
    await checkpoint(page, "FS-02_templates");

    // IMP-02: the blank template's header row equals the registry columns exactly.
    const token = await page.evaluate(() => localStorage.getItem("mrm.token"));
    for (const id of ENABLED) {
      const csv = await page.request.get(`/api/imports/templates/${id}/blank?format=csv`,
        { headers: { Authorization: `Bearer ${token}` } });
      expect(csv.status(), `${id} blank download`).toBe(200);
      const header = (await csv.text()).split(/\r?\n/)[0].replace(/^﻿/, "").split(",");
      expect(header, `${id} header`).toEqual(byId[id].columns.map((c) => c.name));
    }
    // IMP-03: a disabled template cannot be downloaded.
    for (const id of DISABLED.slice(0, 3)) {
      const resp = await page.request.get(`/api/imports/templates/${id}/blank`,
        { headers: { Authorization: `Bearer ${token}` } });
      expect(resp.status(), `${id} must not be downloadable`).toBeGreaterThanOrEqual(400);
    }
  });

test("FS-03 IMP-01 IMP-05 IMP-08 INV-03 T02 demo preview names field and row, then loads",
  async ({ page }) => {
    await signInAs(page, "Admin");
    const before = dbCount("model");

    await openScreen(page, "Import Centre");
    await page.locator('input[type="file"]').first()
      .setInputFiles(path.join(RUN_DIR, "inputs", "T02_new_models_demo.xlsx"));
    await page.getByRole("button", { name: /Upload and validate/i }).click();
    await expect(page.getByText(/Ready/)).toBeVisible({ timeout: 20_000 });
    await checkpoint(page, "FS-03_preview");

    // IMP-01: nothing is saved until Load.
    expect(dbCount("model"), "preview must not persist").toBe(before);

    // IMP-05: the rejected row names the field and the row; it is the SoD case (INV-03).
    const body = await page.locator("body").innerText();
    expect(body).toMatch(/validator_id/);
    expect(body).toMatch(/row\s*5|\b5\b/);
    expect(body).toMatch(/also the model owner/i);

    await page.getByRole("button", { name: /^Load/ }).click();
    await expect(page.getByText(/Partially Completed/)).toBeVisible({ timeout: 20_000 });
    await checkpoint(page, "FS-03_loaded");

    // IMP-04 partial acceptance: 4 of 5 rows load.
    expect(dbCount("model") - before).toBe(4);
    // IMP-08: every created record's audit event carries the batch id.
    expect(dbCount("audit_event", "entity = 'model' AND action = 'create' AND import_batch_id IS NOT NULL"))
      .toBeGreaterThanOrEqual(4);
  });

test("FS-04 IMP-01 IMP-07 re-loading the same file does not duplicate models", async ({ page }) => {
  await signInAs(page, "Admin");
  const file = path.join(RUN_DIR, "inputs", "T02_new_models_demo.xlsx");

  const load = async () => {
    await openScreen(page, "Import Centre");
    await page.locator('input[type="file"]').first().setInputFiles(file);
    await page.getByRole("button", { name: /Upload and validate/i }).click();
    await expect(page.getByText(/Ready|Validation Failed/)).toBeVisible({ timeout: 20_000 });
    const loadButton = page.getByRole("button", { name: /^Load/ });
    if (await loadButton.isEnabled().catch(() => false)) await loadButton.click();
    await page.waitForTimeout(1500);
  };

  await load();
  const afterFirst = dbCount("model");
  await load();
  await checkpoint(page, "FS-04_second_load");
  expect(dbCount("model"), "IMP-07: a re-import updates, it does not duplicate").toBe(afterFirst);
});

test("FS-05 VAL-01 FND-01 APR-01 T03–T05 load onto the right models", async ({ page }) => {
  await signInAs(page, "Admin");
  // The seed already loads T03–T05; this checks the records landed on their models and are visible.
  const findings = (await apiAs(page, "/api/findings?model_id=M-0012")).body as { model_id: string }[];
  expect(findings.length).toBeGreaterThan(0);
  expect(findings.every((f) => f.model_id === "M-0012")).toBe(true);

  const detail = (await apiAs(page, "/api/models/M-0012")).body as {
    validations: unknown[]; findings: unknown[]; approvals: unknown[];
  };
  expect(detail.validations.length, "validations on M-0012").toBeGreaterThan(0);
  expect(detail.findings.length, "findings on M-0012").toBeGreaterThan(0);

  expect(dbCount("validation")).toBe(415);
  expect(dbCount("finding")).toBe(206);
  expect(dbCount("approval")).toBe(383);
  await page.goto("/models/M-0012");
  await checkpoint(page, "FS-05_model360");
});

test("FS-21 GEN-01 two resets at the same business date give the same counts", async ({ page }) => {
  await signInAs(page, "Admin");
  const snapshot = () => ({
    models: dbCount("model"), users: dbCount("app_user"), validations: dbCount("validation"),
    findings: dbCount("finding"), approvals: dbCount("approval"), policy: dbCount("policy_setting"),
  });
  // A reset deletes and reloads `app_user`, so the acting token stops working part way through and
  // even signing in again fails for a moment. The token is therefore re-read when it is refused
  // rather than captured once (part of harness defect H-10; the product side is plan BL.1).
  const asAdmin = async (): Promise<Record<string, string>> => {
    const resp = await page.request.post("/api/auth/login", { data: { user_id: "U-001", role: "Admin" } });
    if (!resp.ok()) return {};
    return { Authorization: `Bearer ${(await resp.json()).access_token}` };
  };

  const reset = async () => {
    const resp = await page.request.post("/api/admin/reset", { headers: await asAdmin() });
    expect(resp.status(), await resp.text()).toBe(202);

    // Wait for the *reset*, not for the batch the caller is handed. A reset creates two batches —
    // the seed import and then one for the 1116 evidence files — so the id in the response reports
    // Completed while the reset is still writing. Polling it was harness defect H-10: the next
    // reset collided with the one still running. `/api/admin/reset/status` covers the whole
    // operation, which is why G0.18 added it.
    await expect
      .poll(async () => {
        const status = await page.request.get("/api/admin/reset/status", { headers: await asAdmin() });
        if (!status.ok()) return "unavailable";   // mid-reset there is briefly no one to authenticate as
        return (await status.json()).in_progress ? "running" : "idle";
      }, { timeout: 300_000, intervals: [2000], message: "the reset never finished" })
      .toBe("idle");

    // And it finished rather than failed: a reset that ends in Failed must not be read as a
    // successful one, which the old `/Completed|Failed/` poll allowed before asserting counts.
    const batches = await page.request.get("/api/imports/batches", { headers: await asAdmin() });
    const seedBatches = ((await batches.json()) as { source: string; status: string }[])
      .filter((b) => b.source === "reset" || b.source === "seed");
    expect(seedBatches.length, "the reset produced its batches").toBeGreaterThan(0);
    for (const b of seedBatches) {
      expect(b.status, `reset batch ${JSON.stringify(b)}`).not.toBe("Failed");
    }
  };

  await reset();
  const first = snapshot();
  await reset();
  const second = snapshot();
  await checkpoint(page, "FS-21_after_two_resets");
  expect(second, "GEN-01: a reset at the same business date is deterministic").toEqual(first);
  expect(first.models).toBe(256);
  expect(first.policy).toBe(67);
});

test.fixme("FS-25 REG-15 REG-16 REG-17 core Model Risk Report: figures, reproducibility and access",
  async () => {
    // Not built (G1.16–G1.18). The core report is specified as §12A REQ-REG-10A and is built ahead
    // of the rest of Phase 2A (D12), so this scenario precedes FS-31 rather than waiting on it.
  });

test.fixme("FS-30 MON-01 MON-02 MON-03 monitoring plan, metrics, results and breach", async () => {
  // Not built (Phase 6).
});

test.fixme("FS-31 REG-01 REG-14 inventory classes, vendor models, challenges, dependencies",
  async () => {
    // Not built (Phase 2A, deferred D12). The report half of this scenario moved to FS-25.
  });

test.fixme("FS-32 CDE and DQ results load and appear on Data Audit", async () => {
  // Not built (Phase 7); criteria set §76B does not exist yet (decision D8 unrecorded).
});
