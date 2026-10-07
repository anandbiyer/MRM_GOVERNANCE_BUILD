// FS-01, FS-22, FS-23 — roles, permissions and session invalidation (§76A.9 SEC-*).
import { expect, test } from "@playwright/test";
import path from "node:path";
import { apiAs, checkpoint, dbCount, findSeedEvidence, openScreen, RUN_DIR, signInAs, signInAsUser } from "./helpers";

const READ_ONLY = ["Auditor", "Executive"];

test("FS-01 SEC-01 SEC-02 SEC-03 SEC-04 read-only roles see no write actions and the API refuses their writes",
  async ({ page }) => {
    for (const role of READ_ONLY) {
      await signInAs(page, role);
      const me = await apiAs(page, "/api/auth/me");
      const permissions = (me.body as { permissions: string[] }).permissions;
      // SEC-02: "Auditor and Executive hold no write permission"
      expect(permissions.filter((p) => p !== "read" && p !== "audit:read"), role).toEqual([]);

      // The UI offers no create action...
      await openScreen(page, "Operations Board");
      await expect(page.getByRole("button", { name: "Register model" }), role).toHaveCount(0);

      // ...and the server refuses one anyway (SEC-02: enforced server-side, not hidden).
      const token = await page.evaluate(() => localStorage.getItem("mrm.token"));
      const refused = await page.request.post("/api/models", {
        headers: { Authorization: `Bearer ${token}` },
        data: { model_id: "M-0900", model_name: "probe", model_type: "Credit Risk", model_subtype: "PD",
                purpose: "probe", business_line: "Business Banking", owner_id: "U-003",
                developer_id: "U-021", lifecycle_phase: "Validation", version: "v1.0",
                q_materiality: 2, q_complexity: 2, q_reliance: 2, q_regulatory_use: 2 },
      });
      expect(refused.status(), `${role} POST /api/models`).toBe(403);
      expect(dbCount("model", "model_id = ?", ["M-0900"])).toBe(0);
      await checkpoint(page, `FS-01_${role.replace(/\W/g, "")}`);
    }

    // SEC-04: a role the user does not hold is refused at sign-in.
    const login = await page.request.post("/api/auth/login", { data: { user_id: "U-041", role: "Admin" } });
    expect(login.status()).toBe(403);
  });

test("FS-22 SEC-02 DOC-03 upload is allowed but batch review needs document:review", async ({ page }) => {
  // The seed lays evidence out under the model's *business line*, so the path cannot be guessed
  // from the model id: M-0012 is Commercial Banking, not Credit Risk (harness defect H-06). Found
  // rather than hard-coded, so a reseed that moves a model does not silently break this.
  const pdf = findSeedEvidence("M-0012", "Governance", "TOR.pdf");

  for (const [userId, role] of [["U-021", "Model Developer"], ["U-031", "Data Owner"]] as const) {
    await signInAsUser(page, userId, role);
    const me = await apiAs(page, "/api/auth/me");
    const perms = (me.body as { permissions: string[] }).permissions;
    expect(perms, role).toContain("document:upload");
    expect(perms, role).not.toContain("document:review");
  }

  // An Admin stages a batch; the developer may not decide what it becomes.
  await signInAs(page, "Admin");
  const adminToken = await page.evaluate(() => localStorage.getItem("mrm.token"));
  const staged = await page.request.post("/api/documents/batches", {
    headers: { Authorization: `Bearer ${adminToken}` },
    multipart: {
      files: { name: "TOR.pdf", mimeType: "application/pdf", buffer: require("node:fs").readFileSync(pdf) },
      paths: "M-0012/Governance/TOR.pdf", source: "batch",
    },
  });
  expect(staged.status(), await staged.text()).toBe(201);
  const batch = await staged.json();
  const itemId = batch.items[0].item_id;
  const documentsBefore = dbCount("document");

  await signInAsUser(page, "U-021", "Model Developer");
  const devToken = await page.evaluate(() => localStorage.getItem("mrm.token"));
  for (const [label, call] of [
    ["remap", () => page.request.patch(`/api/documents/batches/${batch.batch_id}/items`, {
      headers: { Authorization: `Bearer ${devToken}` },
      data: { item_ids: [itemId], model_id: "M-0012", document_type: "Other" } })],
    ["confirm", () => page.request.post(`/api/documents/batches/${batch.batch_id}/confirm`,
      { headers: { Authorization: `Bearer ${devToken}` } })],
    ["cancel", () => page.request.post(`/api/documents/batches/${batch.batch_id}/cancel`,
      { headers: { Authorization: `Bearer ${devToken}` } })],
  ] as const) {
    const resp = await call();
    expect(resp.status(), `${label} as Model Developer`).toBe(403);
  }
  expect(dbCount("document"), "nothing stored by the refused calls").toBe(documentsBefore);

  // A Validator holds document:review, so the same batch goes through.
  await signInAs(page, "Validator");
  const valToken = await page.evaluate(() => localStorage.getItem("mrm.token"));
  const ok = await page.request.patch(`/api/documents/batches/${batch.batch_id}/items`, {
    headers: { Authorization: `Bearer ${valToken}` },
    data: { item_ids: [itemId], model_id: "M-0012", document_type: "Other" },
  });
  expect(ok.status(), await ok.text()).toBe(200);
  await checkpoint(page, "FS-22_review_allowed_for_validator");
});

test("FS-23 SEC-05 re-importing T01 without a role invalidates that role's session", async ({ page }) => {
  // U-040 holds MRC Member and Executive in the seed.
  await signInAsUser(page, "U-040", "MRC Member");
  const mrcToken = await page.evaluate(() => localStorage.getItem("mrm.token"));
  await signInAsUser(page, "U-040", "Executive");
  const execToken = await page.evaluate(() => localStorage.getItem("mrm.token"));

  const headers = (t: string | null) => ({ Authorization: `Bearer ${t}` });
  expect((await page.request.get("/api/auth/me", { headers: headers(mrcToken) })).status()).toBe(200);

  // There is no role-edit screen or API (CR-19), so the role is removed the only supported way:
  // re-importing T01 through the Import Centre.
  await signInAs(page, "Admin");
  await openScreen(page, "Import Centre");
  const input = page.locator('input[type="file"]').first();
  await input.setInputFiles(path.join(RUN_DIR, "inputs", "T01_role_removed.csv"));
  await page.getByRole("button", { name: /Upload and validate/i }).click();
  await expect(page.getByText(/Ready|Validation Failed/)).toBeVisible({ timeout: 15_000 });
  await checkpoint(page, "FS-23_t01_preview");
  await page.getByRole("button", { name: /^Load/ }).click();
  await expect(page.getByText(/Completed|Partially Completed/)).toBeVisible({ timeout: 20_000 });

  // The removed role's session is refused at once; the retained role still works.
  expect((await page.request.get("/api/auth/me", { headers: headers(mrcToken) })).status(),
         "the removed role's token").toBe(403);
  expect((await page.request.get("/api/auth/me", { headers: headers(execToken) })).status(),
         "the retained role's token").toBe(200);
  await checkpoint(page, "FS-23_after_reimport");
});
