// FS-15 … FS-17 — the Document Centre (§78 DOC-*). FS-33 is Phase 5 and appears as fixme.
import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { apiAs, checkpoint, dbCount, openScreen, RUN_DIR, signInAs } from "./helpers";

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

    // Analysis is a background job (Part 0 → Documents: "upload → stage bytes → analyse in
    // background"), so the POST response is the *staged* state: items read "Uploaded" and reach
    // "Ready" about a second later. Asserting the final status on the create response was harness
    // defect H-03 — it tested the asynchrony, not the criterion. Read the batch back instead.
    type Item = { status: string; relative_path: string; document_type: string | null;
                  type_source: string | null; model_id: string | null; model_source: string | null;
                  duplicate_kind: string | null; checksum: string };
    const items = async (): Promise<Item[]> => {
      const resp = await page.request.get(`/api/documents/batches/${batch.batch_id}`,
        { headers: { Authorization: `Bearer ${token}` } });
      expect(resp.ok(), await resp.text()).toBe(true);
      return (await resp.json()).items as Item[];
    };
    await expect.poll(async () => (await items()).every((i) => i.status !== "Uploaded"),
      { timeout: 30_000, message: "the analysis job never finished classifying the batch" }).toBe(true);
    const analysed = await items();

    // DOC-10: the bad file is isolated and the good ones are not lost with it.
    const broken = analysed.find((i) => i.relative_path.endsWith("FT_broken.pdf"));
    expect(broken?.status, "the deliberately broken file is isolated").toBe("Invalid");
    for (const name of ["FT_MDD.pdf", "FT_Validation_Report.pdf"]) {
      const item = analysed.find((i) => i.relative_path.endsWith(name));
      // "Ready" the first time these bytes are seen; "Skipped" with an exact duplicate on a re-run,
      // which is §35 working as specified, not a loss. Either way the file survived the bad one.
      expect([item?.status, item?.duplicate_kind], `${name} after analysis`)
        .toEqual(item?.status === "Ready" ? ["Ready", null] : ["Skipped", "exact"]);
    }

    // DOC-15: the T17 manifest overrides the heuristic classification (§33 Method D).
    const fromManifest = analysed.find((i) => i.relative_path.endsWith("FT_MDD.pdf"));
    expect(fromManifest?.type_source, "the manifest classified this file").toBe("manifest");
    expect(fromManifest?.document_type).toBe("Model Development Document");
    // DOC-13: and the manifest maps it to its model.
    expect(fromManifest?.model_id).toBe("M-0012");

    await page.goto(`/documents/batches/${batch.batch_id}`);
    await checkpoint(page, "FS-16_batch_review");

    // DOC-03, DOC-07, DOC-10, and Confirm → Stored, through the real multi-file control in the
    // Document Centre. Separate from the ZIP step because the bytes have to be new on every run:
    // the ZIP is a fixture, so its files are exact duplicates the second time the scenario runs and
    // the Store path can then never be exercised (harness defect H-09). A unique trailing PDF
    // comment is enough — `validate_document` checks the `%PDF-` header, and the checksum changes.
    const nonce = `FT-${Date.now()}`;
    const base = fs.readFileSync(path.join(INPUTS, "ft_tor_v1.pdf"));
    const unique = (label: string) => {
      const file = path.join(INPUTS, `ft_batch_${nonce}_${label}.pdf`);
      fs.writeFileSync(file, Buffer.concat([base, Buffer.from(`\n% ${nonce} ${label}\n`)]));
      return file;
    };
    const uploads = [unique("M-0012_TOR"), unique("M-0012_MDD"),
                     path.join(INPUTS, `ft_batch_${nonce}_broken.pdf`)];
    fs.writeFileSync(uploads[2], Buffer.from(`not a pdf at all ${nonce}`));

    await openScreen(page, "Document Centre");
    await page.getByRole("tab", { name: /^Upload/ }).click();
    await page.locator('input[type="file"][multiple]').setInputFiles(uploads);
    const documentsBefore = dbCount("document");
    await page.getByRole("button", { name: /Upload and analyse/i }).click();
    await expect(page).toHaveURL(/\/documents\/batches\/B-/, { timeout: 20_000 });
    const multiId = /batches\/(B-[\d-]+)/.exec(page.url())![1];

    const multiItems = async (): Promise<Item[]> => {
      const resp = await page.request.get(`/api/documents/batches/${multiId}`,
        { headers: { Authorization: `Bearer ${token}` } });
      return (await resp.json()).items as Item[];
    };
    await expect.poll(async () => (await multiItems()).every((i) => i.status !== "Uploaded"),
      { timeout: 30_000, message: "the multi-file batch was never analysed" }).toBe(true);
    const staged2 = await multiItems();
    expect(staged2.length, "DOC-03: all three files were taken").toBe(3);
    expect(staged2.filter((i) => i.status === "Invalid").length, "DOC-10: only the broken one").toBe(1);
    expect(staged2.filter((i) => i.status === "Ready").length, "DOC-10: the valid two survive it").toBe(2);
    // DOC-07: every file gets a checksum, and two different files get two different ones.
    const sums = staged2.map((i) => i.checksum);
    expect(sums.every((s) => /^[0-9a-f]{64}$/.test(s)), "DOC-07: SHA-256 per file").toBe(true);
    expect(new Set(sums).size).toBe(3);
    await checkpoint(page, "FS-16_multifile_review");

    // Confirm through the button a user presses, then wait for the store job: like analysis, the
    // confirm response is the state at hand-off, not the finished batch.
    await page.getByRole("button", { name: /^Store \d+ documents?$/ }).click();
    await expect.poll(async () => {
      const resp = await page.request.get(`/api/documents/batches/${multiId}`,
        { headers: { Authorization: `Bearer ${token}` } });
      return (await resp.json()).status as string;
    }, { timeout: 30_000, message: "the batch never reached a terminal status" })
      .toMatch(/Partially Completed|Completed/);
    expect(dbCount("document"), "DOC-10: the two valid files are stored, the broken one is not")
      .toBe(documentsBefore + 2);
    await checkpoint(page, "FS-16_confirmed");

    // DOC-04 / DOC-18: a folder upload keeps its relative path. Posted the way the "Choose folder"
    // control posts (`source: "folder"` with the browser's `webkitRelativePath`), because
    // Playwright's `setInputFiles` cannot populate `webkitRelativePath` on a `webkitdirectory`
    // input — the limitation is the driver's, so this is the closest faithful call.
    const folderFile = unique("folder");
    const folderUpload = await page.request.post("/api/documents/batches", {
      headers: { Authorization: `Bearer ${token}` },
      multipart: {
        files: { name: "TOR.pdf", mimeType: "application/pdf", buffer: fs.readFileSync(folderFile) },
        paths: "Model_Governance/Commercial_Banking/M-0012/Governance/TOR.pdf", source: "folder",
      },
    });
    expect(folderUpload.status(), await folderUpload.text()).toBe(201);
    const folderBatch = await folderUpload.json();
    expect(folderBatch.source, "a folder upload is recorded as a folder batch").toBe("folder");
    expect(folderBatch.items[0].relative_path, "DOC-18: the folder path is retained")
      .toBe("Model_Governance/Commercial_Banking/M-0012/Governance/TOR.pdf");
    // DOC-06: the nested folders become folder records under their parents.
    await expect.poll(() => dbCount("document_folder",
      "relative_path = 'Model_Governance/Commercial_Banking/M-0012/Governance'"),
      { timeout: 30_000, message: "the nested folder was never created" }).toBeGreaterThan(0);
  });

test("FS-17 DOC-20 completeness on Model 360 changes after an upload", async ({ page }) => {
  await signInAs(page, "Admin");
  const token = await page.evaluate(() => localStorage.getItem("mrm.token"));
  type Completeness = { model_id: string; present: string[]; missing: string[]; score: number | null };

  // The model is *found*, not named. M-0042 has all five required documents on a complete seed, so
  // there was no gap to close and the scenario could never judge DOC-20 (harness defect H-04). The
  // first model the API reports with a missing required document is the right fixture, and it
  // cannot go stale when the seed changes.
  const all = (await apiAs(page, "/api/documents/completeness?missing_only=true")).body as Completeness[];
  const withGap = all.find((c) => c.missing.length > 0);
  expect(withGap, "the seed must have a model with a required document missing").toBeTruthy();
  const modelId = withGap!.model_id;
  const completeness = async () =>
    ((await apiAs(page, `/api/documents/completeness?model_id=${modelId}`)).body as Completeness[])[0];

  const before = await completeness();
  expect(before.missing.length, "the model should start with a gap to close").toBeGreaterThan(0);
  const target = before.missing[0];

  const resp = await page.request.post("/api/documents", {
    headers: { Authorization: `Bearer ${token}` },
    multipart: {
      file: { name: "FT_completeness.pdf", mimeType: "application/pdf",
              buffer: fs.readFileSync(path.join(INPUTS, "ft_completeness.pdf")) },
      model_id: modelId, document_type: target,
    },
  });
  expect(resp.status(), await resp.text()).toBe(201);

  const after = await completeness();
  expect(after.present, `${target} should now be present`).toContain(target);
  expect(after.missing).not.toContain(target);
  expect(Number(after.score), "DOC-20: the completeness score rises").toBeGreaterThan(Number(before.score));

  // The documentation component of the score follows it (§40).
  const comps = ((await apiAs(page, `/api/models/${modelId}`)).body as
    { score: { components: { key: string; score: string | null }[] } }).score.components;
  const documentation = comps.find((c) => c.key === "documentation");
  expect(documentation?.score, "the documentation component reflects completeness").not.toBeNull();

  await page.goto(`/models/${modelId}`);
  await page.getByRole("tab", { name: /^Documents/ }).click();
  await expect(page.getByText("FT_completeness.pdf")).toBeVisible({ timeout: 10_000 });
  await checkpoint(page, "FS-17_completeness");
  expect(dbCount("document", "model_id = ?", [modelId])).toBeGreaterThan(0);
});

test.fixme("FS-33 DOC-16 AI extraction proposals are confirmed or dropped", async () => {
  // Not built (Phase 5). document.extraction_status is still defaulted to "Not started".
});
