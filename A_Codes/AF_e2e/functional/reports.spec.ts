// FS-25 — the core Model Risk Report end to end (§12A REQ-REG-10A; REG-15, REG-16, REG-17).
import { expect, test } from "@playwright/test";
import { apiAs, checkpoint, dbCount, openScreen, signInAs } from "./helpers";

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
