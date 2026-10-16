// FS-25 — the core Model Risk Report end to end (§12A REQ-REG-10A; REG-15, REG-16, REG-17).
import { expect, test } from "@playwright/test";
import {
  apiAs, checkpoint, containsIgnoringSpace, dbCount, dbQuery, openScreen, pdfText, signInAs,
} from "./helpers";

/** A distribution table on the report, as {label or key: count}. */
async function section(page: import("@playwright/test").Page, heading: RegExp) {
  const panel = page.locator("section.panel", { has: page.getByText(heading) }).first();
  await expect(panel).toBeVisible();
  return panel;
}

test("FS-25 REG-15 REG-16 REG-17 generate the core report, reconcile it, and read it as other roles",
  async ({ page }) => {
    // --- Generate as a Validator (one of the roles REQ-REG-10A names) ------------------------
    await signInAs(page, "Validator");
    const dash = (await apiAs(page, "/api/dashboard/summary")).body as {
      tiles: Record<string, number>; distributions: Record<string, { key: string; count: number }[]>;
    };
    const before = dbCount("model_risk_report");
    const auditBefore = dbCount("audit_event", "entity = 'model_risk_report' AND action = 'generate'");

    await openScreen(page, "Model Risk Report");
    await expect(page.getByRole("heading", { level: 1, name: "Model Risk Report" })).toBeVisible();
    await page.getByRole("button", { name: "Generate report" }).click();
    await expect(page.getByText(/Content hash/)).toBeVisible({ timeout: 30_000 });

    expect(dbCount("model_risk_report"), "REG-16: one generation stores one report").toBe(before + 1);
    await checkpoint(page, "FS-25_generated");

    // --- REG-15: the figures are the Command Center's ----------------------------------------
    const inventory = await section(page, /^Inventory —/);
    await expect(inventory).toContainText(`${dash.tiles.total_models} models`);
    for (const row of dash.distributions.tier) {
      await expect(inventory.locator("tr", { hasText: row.key }).first(),
        `tier ${row.key}`).toContainText(String(row.count));
    }
    // The displayed stage, not the raw lifecycle phase (LIF-02, the D12 amendment).
    await expect(inventory).toContainText("Stage (as displayed)");
    const revalidation = dash.distributions.stage.find((r) => r.key === "Revalidation");
    if (revalidation) {
      await expect(inventory.locator("tr", { hasText: "Revalidation" }).first())
        .toContainText(String(revalidation.count));
    }
    // Score bands read as labels, never as the internal keys.
    const score = await section(page, /^Governance score/);
    await expect(score).not.toContainText("below_warn");
    await expect(score).not.toContainText("warn_to_good");

    // --- REG-17: "changes since" compares against the seeded earlier report -------------------
    const changes = await section(page, /^Changes since the previous report/);
    await expect(changes).toContainText(/Compared against MRR-/);
    await expect(changes.locator("tr", { hasText: "Models added" })).toBeVisible();

    // --- REG-16: generating again from the same data gives the same content ------------------
    //
    // What makes this assertion worth anything is the *second* generation being observed. The first
    // version of this block polled `hashOf()` until it was not `""` — but a hash is on the screen
    // from the first generation onwards, so the poll returned on its first evaluation and the final
    // comparison was usually the first report's hash against itself. Against a product that
    // generated different content the second time — precisely what REG-16 forbids — it passed
    // (review finding TR-39; reproduced with a route handler that rewrote the second response's
    // hash: the old pattern passed, this one fails).
    //
    // So the second report is now identified three ways: the row count rises by one, the *displayed
    // report id* changes (which is the event the poll waits for, and it cannot already be true),
    // and only then are the hashes compared.
    const header = page.locator("section.panel", { has: page.getByText(/Content hash/) }).first();
    const idOf = async () => (await header.innerText()).match(/MRR-\d{8}-\d{3}/)?.[0] ?? "";
    const hashOf = async () => (await header.innerText()).match(/Content hash\s+(\S+)/)?.[1] ?? "";
    const firstId = await idOf();
    const firstHash = await hashOf();
    expect(firstId, "the generated report's id must be on screen").toMatch(/^MRR-/);
    expect(firstHash, "and its content hash").not.toBe("");

    await page.getByRole("button", { name: "Generate report" }).click();
    await expect.poll(idOf, { timeout: 30_000, message: "the second report never appeared" })
      .not.toBe(firstId);
    expect(dbCount("model_risk_report"), "REG-16: the second generation stores a second report")
      .toBe(before + 2);
    expect(await hashOf(), "REG-16: same data, same business date, same content").toBe(firstHash);
    // "Each generation writes one audit event" — the other half of REG-16, previously unchecked here.
    expect(dbCount("audit_event", "entity = 'model_risk_report' AND action = 'generate'"),
      "REG-16: one audit event per generation").toBe(auditBefore + 2);

    // --- REG-16: an Executive may read but not generate ---------------------------------------
    await signInAs(page, "Executive");
    await openScreen(page, "Model Risk Report");
    await expect(page.getByRole("button", { name: "Generate report" }),
      "SEC-02: a read-only role is offered no write action").toHaveCount(0);
    const refused = await page.request.post("/api/reports/model-risk", {
      headers: { Authorization: `Bearer ${await page.evaluate(() => localStorage.getItem("mrm.token"))}` },
    });
    expect(refused.status(), "and the API refuses it too, not just the UI").toBe(403);
    // A refusal is only proven when nothing was stored and nothing was audited either (REG-16).
    expect(dbCount("model_risk_report"), "REG-16: the refused generation stored nothing")
      .toBe(before + 2);
    expect(dbCount("audit_event", "entity = 'model_risk_report' AND action = 'generate'"),
      "REG-16: and wrote no audit event").toBe(auditBefore + 2);

    // --- REG-17: a read role reopens a stored report and downloads the PDF --------------------
    await page.getByRole("button", { name: "Open" }).first().click();
    await expect(page.getByText(/Content hash/)).toBeVisible({ timeout: 20_000 });
    const download = page.waitForEvent("download");
    await page.getByRole("button", { name: "Download PDF" }).click();
    expect((await download).suggestedFilename()).toMatch(/^MRR-[\d-]+\.pdf$/);
    await checkpoint(page, "FS-25_executive_reopened");

    // --- REG-17: and so can an Auditor, whom the criterion names explicitly -------------------
    await signInAs(page, "Auditor");
    await openScreen(page, "Model Risk Report");
    await expect(page.getByRole("button", { name: "PDF" }).first()).toBeVisible();
    const auditorDownload = page.waitForEvent("download");
    await page.getByRole("button", { name: "PDF" }).first().click();
    expect((await auditorDownload).suggestedFilename()).toMatch(/\.pdf$/);
    await checkpoint(page, "FS-25_auditor_download");
  });

// FS-25 (continued) — what changed after the 2026-10-08 Gate 1 run: D14's seeded-example disclosure on
// every surface, the PDF's reconciliation line (G1.31), and S13's "decisions since the previous report"
// moving into the changes section, out of the content hash (G1.29). A second test under the same ID so
// `-g "FS-25"` still runs the whole scenario. Runs after the first half, which stores generated reports.
test("FS-25 REG-16 REG-17 D14 S13 the seeded example discloses its dates everywhere; decisions sit in the changes section",
  async ({ page }) => {
    test.setTimeout(120_000);
    const token = async () => page.evaluate(() => localStorage.getItem("mrm.token"));
    const pdfOf = async (reportId: string) => {
      const resp = await page.request.get(`/api/reports/model-risk/${reportId}/pdf`,
        { headers: { Authorization: `Bearer ${await token()}` } });
      expect(resp.status(), `PDF of ${reportId}`).toBe(200);
      return pdfText(await resp.body());
    };
    type Header = { report_id: string; business_date: string; figures_as_of: string | null;
      is_seeded: boolean; seeded_label: string | null; generated_at: string; content_hash: string };
    type Detail = Header & { sections: Record<string, Record<string, unknown>> };

    // --- D14 on the list, as a read role -----------------------------------------------------
    await signInAs(page, "Auditor");
    const list = (await apiAs(page, "/api/reports/model-risk")).body as Header[];
    const seeded = list.filter((r) => r.is_seeded);
    expect(seeded.length, "a reset seeds exactly one example report (S11)").toBe(1);
    const ex = seeded[0];
    const generated = list.filter((r) => !r.is_seeded);
    expect(generated.length, "the first half of FS-25 stored generated reports").toBeGreaterThan(0);
    // D14 (clarified 2026-10-15): "<generation date>" is the business date the figures were computed
    // for — app.clock.today() at the reset — and the example keeps its earlier business date.
    const businessDate = generated[0].business_date;
    expect(ex.figures_as_of, "D14: the seeded figures are as of today's business date").toBe(businessDate);
    expect(ex.business_date < businessDate, "D14 option (b): the example keeps an earlier date").toBe(true);
    const label = `Seeded example: figures computed from current seed data on ${ex.figures_as_of}, ` +
      `dated ${ex.business_date} for illustration.`;
    expect(ex.seeded_label, "D14: the API words the disclosure exactly").toBe(label);
    for (const r of generated) {
      expect(r.seeded_label, `${r.report_id} is not seeded and carries no label`).toBeNull();
      expect(r.figures_as_of, "D14: a generated report's figures are as of its own business date")
        .toBe(r.business_date);
    }

    await openScreen(page, "Model Risk Report");
    const exRow = page.locator("tr", { hasText: ex.report_id });
    await expect(exRow, "D14: the list carries the pill").toContainText("Seeded example");
    await expect(exRow, "D14: and the full label").toContainText(label);
    await checkpoint(page, "FS-25_d14_list");

    // --- D14 on the reopened report ----------------------------------------------------------
    await exRow.getByRole("button", { name: "Open" }).click();
    const head = page.locator("section.panel", { has: page.getByText(/Content hash/) }).first();
    await expect(head).toContainText(ex.report_id, { timeout: 20_000 });
    await expect(head, "D14: the reopened report carries the label").toContainText(label);
    await expect(head, "S12: the reconciliation is stated in the past tense, about this report")
      .toContainText("Figures reconciled with the Command Center at generation");
    await checkpoint(page, "FS-25_d14_reopened");

    // --- D14: the PDF counts as a surface ----------------------------------------------------
    const reconciled = "Figures reconciled with the Command Center at generation,";
    const exPdf = await pdfOf(ex.report_id);
    expect(containsIgnoringSpace(exPdf, label), "D14: the seeded PDF carries the label").toBe(true);
    expect(containsIgnoringSpace(exPdf, reconciled), "D14: every PDF carries the reconciliation line")
      .toBe(true);
    const genPdf = await pdfOf(generated[0].report_id);
    expect(containsIgnoringSpace(genPdf, reconciled),
      "D14: a generated report's PDF carries the reconciliation line too").toBe(true);
    expect(containsIgnoringSpace(genPdf, "Seeded example"),
      "a generated report's PDF is not labelled as an example").toBe(false);

    // --- S13: a decision recorded between generations, through the UI ------------------------
    await signInAs(page, "MRC Member");
    const generate = async (): Promise<Detail> => {
      await openScreen(page, "Model Risk Report");
      const respP = page.waitForResponse((r) => r.url().endsWith("/api/reports/model-risk")
        && r.request().method() === "POST");
      await page.getByRole("button", { name: "Generate report" }).click();
      const resp = await respP;
      expect(resp.ok(), `generate: ${resp.status()}`).toBe(true);
      const body = await resp.json() as Detail;
      await expect(page.locator("section.panel", { has: page.getByText(/Content hash/) }).first())
        .toContainText(body.report_id, { timeout: 20_000 });
      return body;
    };
    await generate();

    const approvalIds = () => dbQuery("SELECT approval_id FROM approval").map((r) => String(r.approval_id));
    const before = new Set(approvalIds());
    const auditBefore = dbCount("audit_event", "entity = 'approval'");
    await page.goto("/models/M-0030");
    await page.getByRole("tab", { name: /^Approvals/ }).click();
    await page.getByRole("button", { name: "Record decision" }).click();
    const field = (name: string) => page.locator(
      `xpath=//form[contains(@class,"action-form")]//label[normalize-space(text())="${name}"]`)
      .locator("input, select, textarea");
    await field("Decision date").fill("2026-09-29");
    await field("Forum").selectOption({ index: 1 });
    await field("Decision type").selectOption({ index: 1 });
    await field("Decision").selectOption("Approved");
    await page.getByRole("button", { name: "Save decision" }).click();
    await expect.poll(() => approvalIds().length, { timeout: 15_000 }).toBe(before.size + 1);
    const newId = approvalIds().find((id) => !before.has(id)) ?? "";
    expect(dbCount("audit_event", "entity = 'approval'"), "AUD-01: the decision is audited once")
      .toBe(auditBefore + 1);

    const seesIt = await generate();
    const changes = page.locator("section.panel",
      { has: page.getByText(/^Changes since the previous report/) }).first();
    const decisionsRow = changes.locator("tr", { hasText: "Approval decisions recorded" });
    await expect(decisionsRow, "S13: the decision is listed in the changes section").toContainText(newId);
    const recorded = (seesIt.sections.changes_since.decisions_recorded as { approval_id: string }[])
      .map((d) => d.approval_id);
    expect(recorded, "S13: exactly the decision recorded since the previous report").toEqual([newId]);
    expect(Object.keys(seesIt.sections.approvals),
      "S13: nothing derived from the predecessor remains in Approvals").not.toContain("decisions_since_previous");
    await checkpoint(page, "FS-25_s13_changes");

    const afterIt = await generate();
    expect(afterIt.sections.changes_since.decisions_recorded, "nothing recorded in between").toEqual([]);
    expect(afterIt.content_hash,
      "REG-16 (CR-52, S13): same data, same business date, same hash — whatever the predecessor saw")
      .toBe(seesIt.content_hash);
  });
