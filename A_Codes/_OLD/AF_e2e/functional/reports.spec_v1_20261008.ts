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
    const hashOf = async () => (await page.getByText(/Content hash/).innerText()).replace(/\s+/g, " ");
    const first = await hashOf();
    await page.getByRole("button", { name: "Generate report" }).click();
    await expect.poll(hashOf, { timeout: 30_000 }).not.toBe("");
    expect(await hashOf(), "REG-16: same data, same business date, same content").toBe(first);

    // --- REG-16: an Executive may read but not generate ---------------------------------------
    await signInAs(page, "Executive");
    await openScreen(page, "Model Risk Report");
    await expect(page.getByRole("button", { name: "Generate report" }),
      "SEC-02: a read-only role is offered no write action").toHaveCount(0);
    const refused = await page.request.post("/api/reports/model-risk", {
      headers: { Authorization: `Bearer ${await page.evaluate(() => localStorage.getItem("mrm.token"))}` },
    });
    expect(refused.status(), "and the API refuses it too, not just the UI").toBe(403);

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
