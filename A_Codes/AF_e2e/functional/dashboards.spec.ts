// FS-18, FS-19 — Command Center tiles, drill-downs and insights (CC-01, CC-02, CC-04).
// FS-34 is Phase 9 and appears as fixme.
import { expect, test } from "@playwright/test";
import { apiAs, checkpoint, highlight, openScreen, signInAs } from "./helpers";

test("FS-18 CC-01 CC-02 every tile and bar drills to a list of its own size", async ({ page }) => {
  await signInAs(page, "Executive");
  const summary = (await apiAs(page, "/api/dashboard/summary")).body as {
    tiles: Record<string, number | null>;
    distributions: Record<string, { key: string; count: number }[]>;
  };
  const t = summary.tiles;
  const count = async (query: string) => ((await apiAs(page, `/api/models${query}`)).body as unknown[]).length;

  // CC-01: each tile equals the count returned by its own drill-down.
  expect(await count(""), "Total models").toBe(t.total_models);
  expect(await count("?tier=High"), "High risk").toBe(t.high_tier);
  expect(await count("?column=Revalidation"), "Revalidation queue").toBe(t.revalidation_queue);
  expect(await count("?flag=in_production"), "In production").toBe(t.in_production);
  expect(await count("?flag=doc_gaps"), "Document gaps").toBe(t.models_with_document_gaps);
  expect(await count("?flag=open_conditions"), "Open MRC conditions").toBe(t.models_with_open_conditions);

  // G0.4 (CR-05): the findings tile counts models, and each sub-line link opens a list of its size.
  expect(await count("?flag=open_findings"), "Models with open findings").toBe(t.models_with_open_findings);
  expect(await count("?flag=overdue_findings"), "models overdue").toBe(t.models_with_overdue_findings);
  expect(await count("?flag=critical_overdue"), "critical overdue").toBe(t.models_with_critical_overdue);

  // G0.4: each severity bar filters by finding_severity, not one shared flag.
  const severities = summary.distributions.open_findings_by_severity;
  const perSeverity: Record<string, number> = {};
  for (const bar of severities) {
    perSeverity[bar.key] = await count(`?finding_severity=${encodeURIComponent(bar.key)}`);
    expect(perSeverity[bar.key], `${bar.key} models cannot exceed its findings`)
      .toBeLessThanOrEqual(bar.count);
  }
  expect(new Set(Object.values(perSeverity)).size, "the bars must not all open the same list")
    .toBeGreaterThan(1);

  // G0.2: score-band links use the scored_* flags and carry no numbers.
  for (const band of summary.distributions.score_band) {
    expect(band.key, "band keys carry no numbers").not.toMatch(/\d/);
    expect(await count(`?flag=scored_${band.key}`), `scored_${band.key}`).toBe(band.count);
  }

  // The screen agrees with the API, and the label is the accepted difference from the mock-up.
  await openScreen(page, "Command Center");
  const tile = page.locator(".tile", { hasText: "Models with open findings" }).first();
  await expect(tile).toBeVisible();
  await expect(tile.locator("b")).toHaveText(String(t.models_with_open_findings));
  await highlight(tile);
  await checkpoint(page, "FS-18_tiles");

  // And the Operations Board filter lands with the same count.
  await tile.click();
  await expect(page).toHaveURL(/\/operations\?.*flag=open_findings/);
  await expect.poll(async () => page.locator("div.tablewrap tbody tr").count(), { timeout: 15_000 })
    .toBe(t.models_with_open_findings);
  await checkpoint(page, "FS-18_board_filtered");
});

test("FS-19 CC-04 every insight links to its source record", async ({ page }) => {
  await signInAs(page, "Executive");
  const summary = (await apiAs(page, "/api/dashboard/summary")).body as {
    insights: { rule: string; message: string; model_id: string | null; link: string }[];
    insight_counts_by_rule: Record<string, number>;
  };
  expect(summary.insights.length, "the seed should produce insights").toBeGreaterThan(0);

  const models = new Set(((await apiAs(page, "/api/models")).body as { model_id: string }[])
    .map((m) => m.model_id));
  for (const insight of summary.insights) {
    expect(insight.model_id, `insight ${insight.rule} must name a model`).not.toBeNull();
    expect(models.has(insight.model_id!), `${insight.model_id} must exist`).toBe(true);
    expect(insight.link).toBe(`/models/${insight.model_id}`);
  }

  await openScreen(page, "Command Center");
  const first = page.getByRole("link", { name: new RegExp(summary.insights[0].model_id!) }).first();
  await checkpoint(page, "FS-19_insights");
  if (await first.count()) {
    await first.click();
    await expect(page).toHaveURL(new RegExp(`/models/${summary.insights[0].model_id}`));
    await checkpoint(page, "FS-19_insight_target");
  }
});

test.fixme("FS-34 Copilot answers cite records from the app", async () => {
  // Not built (Phase 9); criteria set §76C does not exist yet (decision D11 unrecorded).
});
