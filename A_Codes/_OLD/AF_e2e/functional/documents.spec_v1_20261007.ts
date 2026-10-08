// FS-15 … FS-17 — the Document Centre (§78 DOC-*). FS-33 is Phase 5 and appears as fixme.
import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { apiAs, checkpoint, dbCount, dbQuery, openScreen, RUN_DIR, signInAs } from "./helpers";

const INPUTS = path.join(RUN_DIR, "inputs");

test("FS-15 DOC-01 DOC-08 DOC-17 single upload, a new version, and a refused duplicate",
  async ({ page }) => {
    await signInAs(page, "Admin");
    const token = await page.evaluate(() => localStorage.getItem("mrm.token"));
    const first = fs.readFileSync(path.join(INPUTS, "ft_tor_v1.pdf"));
    const second = fs.readFileSync(path.join(INPUTS, "ft_tor_v2.pdf"));
    const upload = (buffer: Buffer, name: string, extra: Record<string, string> = {}) =>
      page.request.post("/api/documents", {
        headers: { Authorization: `Bearer ${token}` },
        multipart: {
          file: { name, mimeType: "application/pdf", buffer },
          model_id: "M-0012", document_type: "Terms of Reference", ...extra,
        },
      });

    // DOC-01: a single PDF stores and downloads intact.
    const created = await upload(first, "FT_TOR.pdf");
    expect(created.status(), await created.text()).toBe(201);
    const doc = await created.json();
    expect(doc.current_version).toBe("1.0");
    const back = await page.request.get(
      `/api/documents/${doc.document_id}/versions/1.0/download`,
      { headers: { Authorization: `Bearer ${token}` } });
    expect(Buffer.from(await back.body()).equals(first), "the stored bytes must come back").toBe(true);

    // DOC-08: the same bytes again are refused as a duplicate.
    const dup = await upload(first, "FT_TOR_copy.pdf");
    expect(dup.status()).toBe(409);
    expect((await dup.json()).detail).toMatch(/SHA-256/);

    // DOC-17: a changed file becomes the next version and both stay downloadable.
    const v2 = await upload(second, "FT_TOR_v2.0.pdf", { version: "2.0" });
    expect(v2.status(), await v2.text()).toBe(201);
    const versions = (await v2.json()).versions.map((v: { version: string }) => v.version);
    expect(versions).toContain("1.0");
    expect(versions).toContain("2.0");
    for (const v of ["1.0", "2.0"]) {
      const resp = await page.request.get(`/api/documents/${doc.document_id}/versions/${v}/download`,
        { headers: { Authorization: `Bearer ${token}` } });
      expect(resp.status(), `version ${v} must stay downloadable`).toBe(200);
    }

    await openScreen(page, "Document Centre");
    await checkpoint(page, "FS-15_register");
  });

test("FS-16 DOC-03 DOC-04 DOC-05 DOC-06 DOC-10 DOC-15 batch and ZIP upload with a manifest",
  async ({ page }) => {
    await signInAs(page, "Admin");
    const token = await page.evaluate(() => localStorage.getItem("mrm.token"));

    // DOC-05: a ZIP expands with its paths preserved; DOC-15: a T17 manifest overrides heuristics.
    const zip = fs.readFileSync(path.join(INPUTS, "ft_evidence.zip"));
    const staged = await page.request.post("/api/documents/batches", {
      headers: { Authorization: `Bearer ${token}` },
      multipart: {
        files: { name: "ft_evidence.zip", mimeType: "application/zip", buffer: zip },
        paths: "ft_evidence.zip", source: "batch",
      },
    });
    expect(staged.status(), await staged.text()).toBe(201);
    const batch = await staged.json();
    expect(batch.source, "a .zip upload is recorded as a zip batch").toBe("zip");

    // DOC-06: the folder hierarchy is preserved on the items.
    const paths = batch.items.map((i: { relative_path: string }) => i.relative_path);
    expect(paths.some((p: string) => p.includes("M-0012/Governance"))).toBe(true);

    // DOC-10: a bad file does not stop the others.
    const invalid = batch.items.filter((i: { status: string }) => i.status === "Invalid");
    expect(invalid.length, "the deliberately broken file is isolated").toBeGreaterThan(0);
    const ready = batch.items.filter((i: { status: string }) => i.status === "Ready");
    expect(ready.length, "the valid files are still Ready").toBeGreaterThan(0);

    await page.goto(`/documents/batches/${batch.batch_id}`);
    await checkpoint(page, "FS-16_batch_review");

    const before = dbCount("document");
    const confirm = await page.request.post(`/api/documents/batches/${batch.batch_id}/confirm`,
      { headers: { Authorization: `Bearer ${token}` } });
    expect(confirm.status(), await confirm.text()).toBe(200);
    await expect.poll(() => dbCount("document"), { timeout: 30_000 }).toBeGreaterThan(before);
    const done = await confirm.json();
    expect(done.status, "DOC-10: a partially valid batch completes partially").toMatch(/Partially Completed|Completed/);
    await checkpoint(page, "FS-16_confirmed");
  });

test("FS-17 DOC-20 completeness on Model 360 changes after an upload", async ({ page }) => {
  await signInAs(page, "Admin");
  const token = await page.evaluate(() => localStorage.getItem("mrm.token"));
  const completeness = async () =>
    ((await apiAs(page, "/api/documents/completeness?model_id=M-0042")).body as
      { present: string[]; missing: string[]; score: number | null }[])[0];

  const before = await completeness();
  expect(before.missing.length, "the model should start with a gap to close").toBeGreaterThan(0);
  const target = before.missing[0];

  const resp = await page.request.post("/api/documents", {
    headers: { Authorization: `Bearer ${token}` },
    multipart: {
      file: { name: "FT_completeness.pdf", mimeType: "application/pdf",
              buffer: fs.readFileSync(path.join(INPUTS, "ft_completeness.pdf")) },
      model_id: "M-0042", document_type: target,
    },
  });
  expect(resp.status(), await resp.text()).toBe(201);

  const after = await completeness();
  expect(after.present, `${target} should now be present`).toContain(target);
  expect(after.missing).not.toContain(target);
  expect(Number(after.score), "DOC-20: the completeness score rises").toBeGreaterThan(Number(before.score));

  // The documentation component of the score follows it (§40).
  const comps = ((await apiAs(page, "/api/models/M-0042")).body as
    { score: { components: { key: string; score: string | null }[] } }).score.components;
  const documentation = comps.find((c) => c.key === "documentation");
  expect(documentation?.score, "the documentation component reflects completeness").not.toBeNull();

  await page.goto("/models/M-0042");
  await page.getByRole("tab", { name: /^Documents/ }).click();
  await checkpoint(page, "FS-17_completeness");
  expect(dbQuery("SELECT COUNT(*) AS n FROM document WHERE model_id = 'M-0042'")[0].n).toBeTruthy();
});

test.fixme("FS-33 DOC-16 AI extraction proposals are confirmed or dropped", async () => {
  // Not built (Phase 5). document.extraction_status is still defaulted to "Not started".
});
