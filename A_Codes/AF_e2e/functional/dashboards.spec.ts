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


// FS-26 — date-only values must not shift, and must agree between screens (MP-10 / FT-06).
//
// Pinned to a timezone west of UTC on purpose. `new Date("2026-09-30")` parses as UTC midnight, so
// `toLocaleDateString()` renders the *previous* day anywhere behind UTC: the Command Center lede
// read "as of 9/29/2026" for business date 2026-09-30. It is invisible in UTC, which is why CI and
// the rest of this suite never saw it. The cross-screen half matters more than the offset: the
// revalidation timeline printed the raw ISO string while Model 360 formatted it, so the same model
// showed two different due dates depending on where you looked.
test.describe("FS-26 date-only rendering", () => {
  test.use({ timezoneId: "America/Los_Angeles" });

  /** The numbers in a rendered date, order- and locale-independent: {2026, 9, 30}. */
  const parts = (text: string) => new Set((text.match(/\d+/g) ?? []).map(Number));
  const isoParts = (iso: string) => new Set(iso.split("-").map(Number));

  test("CC-01 LIF-02 a date-only value renders its own calendar day, west of UTC", async ({ page }) => {
    await signInAs(page, "Executive");
    const summary = (await apiAs(page, "/api/dashboard/summary")).body as {
      as_of: string;
      revalidation_timeline: { model_id: string; next_due: string | null }[];
    };

    await openScreen(page, "Command Center");
    const lede = await page.locator("p.lede").first().innerText();
    const asOf = /as of ([^.]+)\./.exec(lede);
    expect(asOf, `the lede does not state a business date: ${lede}`).not.toBeNull();
    expect(parts(asOf![1]), `lede "${asOf![1]}" must be business date ${summary.as_of}`)
      .toEqual(isoParts(summary.as_of));
    await checkpoint(page, "FS-26_command_center_as_of");

    // The same due date on two screens. Taken from the timeline the Command Center actually renders,
    // so this compares what a user sees, not what the API returns twice.
    const row = summary.revalidation_timeline.find((r) => r.next_due);
    expect(row, "the seed must have at least one model with a due date").toBeTruthy();
    // The column is found by its header, not by index. This read `.nth(2)` until BL.24 inserted
    // Owner and Last validation ahead of Due, and a positional locator then silently compared the
    // wrong cell — it failed loudly here, but only by luck of the values differing.
    const timeline = page.locator("section.panel",
      { has: page.getByRole("heading", { name: /Revalidation timeline/ }) });
    const dueHeader = timeline.getByRole("columnheader", { name: "Due", exact: true });
    await expect(dueHeader, "the timeline must have a Due column").toHaveCount(1);
    const dueColumn = await dueHeader.evaluate((el) => (el as HTMLTableCellElement).cellIndex);
    const timelineCell = timeline
      .locator("tbody tr", { has: page.getByRole("link", { name: row!.model_id, exact: true }) })
      .locator("td").nth(dueColumn);
    const onTimeline = (await timelineCell.innerText()).trim();
    expect(parts(onTimeline), `timeline due "${onTimeline}" must be ${row!.next_due}`)
      .toEqual(isoParts(row!.next_due!));

    // Model 360 renders its profile as a <dl className="kv"> of <dt>/<dd> pairs.
    const kv = (label: string) => page.locator("dl.kv > div")
      .filter({ has: page.locator("dt", { hasText: new RegExp(`^${label}$`) }) }).locator("dd");

    await page.goto(`/models/${row!.model_id}`);
    const onModel360 = (await kv("Next due").first().innerText()).trim();
    expect(onModel360, "the same due date must read the same on both screens").toBe(onTimeline);
    await checkpoint(page, "FS-26_model360_next_due");

    // And the model's own stored date, which is where the one-day shift was first seen (M-0012's
    // last validation 2026-04-16 displayed as 4/15/2026).
    const detail = (await apiAs(page, "/api/models/M-0012")).body as {
      model: { last_validation_date: string | null };
    };
    await page.goto("/models/M-0012");
    const lastVal = (await kv("Last validation").first().innerText()).trim();
    expect(parts(lastVal), `last validation "${lastVal}" must be ${detail.model.last_validation_date}`)
      .toEqual(isoParts(detail.model.last_validation_date!));
  });
});


test("FS-28 CC-03 §10 the revalidation timeline is the Revalidation column, with §10's full list",
     async ({ page }) => {
  // BRD §10 requires the revalidation view to display next due date, days remaining, days overdue,
  // risk tier, **owner**, **last validation** and **latest outcome**. Three of those seven were on
  // no revalidation view at all — not here, not behind the Operations Board's revalidation filter —
  // only on Model 360, one model at a time, so "show me A. Williams' models due for revalidation"
  // could not be answered from any list (review finding MP-17, plan BL.24).
  //
  // `GET /api/dashboard/summary` has returned `owner_id`, `last_validation_date` and
  // `latest_decision` on every timeline row all along; the screen discarded them.
  await signInAs(page, "Executive");
  const summary = (await apiAs(page, "/api/dashboard/summary")).body as {
    revalidation_timeline: {
      model_id: string; tier: string; owner_id: string | null;
      next_due: string | null; days_to_due: number | null; status: string | null;
      last_validation_date: string | null; latest_decision: string | null;
    }[];
  };
  const rows = summary.revalidation_timeline;
  expect(rows.length, "the seed must have models in the Revalidation column").toBeGreaterThan(0);

  // CC-03 itself: "the revalidation timeline contains exactly the models in the Revalidation
  // column". The scenario carried the CC-03 tag while asserting only §10's columns, so `grep CC-03`
  // reported coverage it did not provide (review finding TR-41's neighbour, TR-42). Set equality
  // against the displayed stage — which is LIF-02's computed column, not the raw lifecycle phase —
  // is what the criterion says, so it is asserted here rather than only in the backend tests.
  const all = (await apiAs(page, "/api/models")).body as {
    model_id: string; state: { displayed_column: string | null };
  }[];
  const inColumn = new Set(all.filter((m) => m.state.displayed_column === "Revalidation")
                              .map((m) => m.model_id));
  expect(new Set(rows.map((r) => r.model_id)),
         "CC-03: the timeline is exactly the Revalidation column").toEqual(inColumn);

  await openScreen(page, "Command Center");
  const panel = page.locator("section.panel", {
    has: page.getByRole("heading", { name: /Revalidation timeline/ }),
  });

  // Every column §10 names is present as a header.
  for (const header of ["Model", "Tier", "Owner", "Last validation", "Due", "Days", "Outcome", "Status"]) {
    await expect(panel.getByRole("columnheader", { name: new RegExp(`^${header}$`, "i") }),
                 `§10 column "${header}"`).toHaveCount(1);
  }

  // And the values are that model's own, not a neighbour's. Checked on a row with all three present,
  // so an empty-cell fallback cannot pass for a value.
  const row = rows.find((r) => r.owner_id && r.last_validation_date && r.latest_decision);
  expect(row, "the seed must have a timeline row with owner, last validation and outcome").toBeTruthy();
  const cells = panel.locator("tbody tr", {
    has: page.getByRole("link", { name: row!.model_id, exact: true }),
  });
  await expect(cells).toHaveCount(1);
  const text = await cells.innerText();
  expect(text, `owner of ${row!.model_id}`).toContain(row!.owner_id!);
  expect(text, `latest outcome of ${row!.model_id}`).toContain(row!.latest_decision!);
  // Date-only, so it must go through the formatter rather than printing ISO (G0.24).
  const [y, m, d] = row!.last_validation_date!.split("-").map(Number);
  const shown = new Date(y, m - 1, d).toLocaleDateString();
  expect(text, `last validation of ${row!.model_id} as ${shown}`).toContain(shown);

  await checkpoint(page, "FS-28_revalidation_timeline");
});


// FS-29 — one date per event, west of UTC (MP-15 / MP-16, plan BL.28).
//
// Model 360 showed two different calendar days for events minutes apart: the Score tab read
// "calculated 10/7/2026, 9:07 PM" while the History tab and the lifecycle line read 10/8/2026.
// `score.calculated_at` is built in Python as `datetime.now(UTC)` and serialised with a `Z`;
// `changed_at`, `recorded_at`, `occurred_at` and `uploaded_at` came from the database default and
// were serialised naive, which the browser reads as *local* — so a UTC wall-clock was rendered as
// local and landed on the adjacent day. Three datetime fields were also passed to `formatDate`,
// whose contract is date-only.
//
// This asserts the screen agrees with the instant the API actually sent, which is the property that
// was broken; comparing two on-screen dates to each other would pass if both were wrong the same way.
test.describe("FS-29 one date per event", () => {
  test.use({ timezoneId: "America/Los_Angeles" });

  test("§67 a timestamp renders the day of the instant the API sent", async ({ page }) => {
    await signInAs(page, "Admin");
    const model = (await apiAs(page, "/api/models/M-0012")).body as {
      score: { calculated_at: string };
      phase_history: { changed_at: string }[];
    };

    // Every timestamp must carry an offset, or the browser is guessing.
    expect(model.score.calculated_at, "score.calculated_at").toMatch(/(Z|[+-]\d\d:\d\d)$/);
    expect(model.phase_history.length, "M-0012 must have phase history").toBeGreaterThan(0);
    for (const h of model.phase_history) {
      expect(h.changed_at, "phase_history.changed_at").toMatch(/(Z|[+-]\d\d:\d\d)$/);
    }

    // The day each instant falls on *in the browser's timezone*, computed in the page so it is the
    // same clock the application renders with.
    //
    // Note what carries the proof here, because it is not this. If the API went back to sending
    // naive timestamps, `new Date(...)` below would misread them exactly as the page does, the two
    // would agree, and this check would pass while the screen was wrong — the same "test that
    // cannot fail" that TR-25 and TR-26 were. The discriminating assertions are the offset checks
    // above (they failed against the real defect: 14 of 16 API timestamps had no zone) and the
    // time-of-day check below, which fails if a datetime is sent through the date-only formatter.
    const localDay = (iso: string) =>
      page.evaluate((s) => new Date(s).toLocaleDateString(), iso);
    const HAS_TIME = /\d{1,2}:\d{2}/;

    await page.goto("/models/M-0012");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

    // Both panels live behind their own tab, so each is opened before it is read.
    await page.getByRole("tab", { name: "Score" }).click();
    const scoreHeading = page.getByRole("heading", { name: /Governance score/ });
    await expect(scoreHeading).toBeVisible();
    // Scoped to the heading that renders `calculated_at`, for the reason given below (TR-41).
    const calculated = await scoreHeading.innerText();
    expect(calculated, "the Score tab must show the day of its own calculated_at")
      .toContain(await localDay(model.score.calculated_at));
    expect(calculated, "and a time, since calculated_at is an instant").toMatch(HAS_TIME);

    // The phase history is on Overview (the lifecycle list), not on the History tab — which is the
    // *audit* trail. MP-15 compared the two, so the scenario reads the one that carries changed_at.
    //
    // Both time-of-day assertions below are scoped to the panel that renders the field, not to
    // `main`. Scoped to `main` they could be satisfied by a *neighbour's* timestamp and so could
    // pass while the field under test went through the date-only formatter (review finding TR-41):
    // the Overview tab also renders tier overrides with `formatDateTime`
    // (`Model360Page.tsx:85`) — which FS-08 creates on this very model, M-0012 — and the History
    // tab always renders the Versions list the same way (`:187`), so the audit half of the check
    // was vacuous on every run, not only after FS-08.
    await page.getByRole("tab", { name: "Overview" }).click();
    const lifecycle = page.locator("section.panel", {
      has: page.getByRole("heading", { name: "Lifecycle" }),
    });
    const lifecycleEntries = lifecycle.locator("ul.checklist > li");
    await expect(lifecycleEntries.first()).toBeVisible();
    const lifecycleText = await lifecycleEntries.first().innerText();
    expect(lifecycleText, "the lifecycle history must show the day of its own changed_at")
      .toContain(await localDay(model.phase_history[0].changed_at));
    // `changed_at` is an instant, so it must come through `formatDateTime` and carry a time.
    // Passing it to `formatDate` — which is what MP-15 found — drops the time silently.
    expect(lifecycleText, "a lifecycle entry must show a time, not just a date").toMatch(HAS_TIME);

    // And the audit trail on the History tab, which is the other half of the disagreement.
    const audit = (await apiAs(page, "/api/audit?model_id=M-0012")).body as { occurred_at: string }[];
    expect(audit.length, "M-0012 must have audit events").toBeGreaterThan(0);
    expect(audit[0].occurred_at, "audit occurred_at").toMatch(/(Z|[+-]\d\d:\d\d)$/);
    await page.getByRole("tab", { name: "History" }).click();
    const auditPanel = page.locator("section.panel", {
      has: page.getByRole("heading", { name: "Audit history" }),
    });
    await expect(auditPanel.locator("tbody tr").first()).toBeVisible();
    const whenCell = await auditPanel.locator("tbody tr").first().locator("td").first().innerText();
    expect(whenCell, "the audit table must show the day of its own occurred_at")
      .toContain(await localDay(audit[0].occurred_at));
    expect(whenCell, "an audit entry must show a time, not just a date").toMatch(HAS_TIME);

    await checkpoint(page, "FS-29_one_date_per_event");
  });
});
