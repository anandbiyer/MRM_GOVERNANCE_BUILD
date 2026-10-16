Business date: **2026-09-30** (`MRM_TODAY_OVERRIDE=2026-09-30`) — the committed seed's date, same as `mockup-parity.md`
Expected seed counts: models **256** · users **65** · validations **415** · findings **206** · approvals **383** · documents **1116** · policy settings **72**

# Functional scenario catalogue

Owned by the `functional-tester` agent (review agent 4). Each scenario drives the running application
through the browser with real input files and checks the result against a BRD acceptance criterion.

The counts above are read from the committed seed, not from a prompt — a reset that does not reproduce
them means the reset did not take, and the run must stop. The policy count has moved repeatedly (60 →
62 → 63 → 65 → 67 → 70 → 72, the last two added by Gate 1's `regulatory_framework` and its
companion); re-read it rather than trusting any document.

## Conventions

- **Stable IDs.** `FS-nn` never changes meaning. New scenarios take the next free number; gaps are
  deliberate — the reserved block FS-25…FS-29 is now fully used, so the next built scenario takes a
  number above FS-40 rather than disturbing the unbuilt block at FS-30+.
  FS-25 took the first reserved number for the core Model Risk Report (D12), FS-26 the second for
  date-only rendering (G0.24), FS-27 the third for the role-switch identity refresh (SEC-07), and
  FS-28 and FS-29 the last two for BL.24 and BL.28.
- Scenarios for phases Part 0 lists as unbuilt use `test.fixme` with "Not built (Phase N)" and appear
  in the report as *Not built*, never as failures.
- Every expectation is quoted from CLAUDE.md or `decision_log.md`. Where neither says what should
  happen, the scenario records **Unspecified behaviour** instead of inventing an expectation.
- A refusal is only proven when the response status, the absence of the record **and** the absence of
  an audit event are all checked.

## Catalogue

| ID | Journey | Criteria | Role | Inputs | Phase |
|---|---|---|---|---|---|
| FS-01 | Sign in as each role; read-only roles see no write actions and the API refuses their writes | SEC-01…SEC-04 | each | — | 1 |
| FS-02 | Download every enabled template (T01–T05, T12, T17, T18); columns equal the registry; disabled templates (T06–T11, T13–T16) cannot be downloaded or loaded | IMP-02, IMP-03 | Admin | — | 3 |
| FS-03 | Preview the T02 demo file: loaded and rejected counts, each message names field and row; then load; audit entries appear | IMP-01, IMP-05, IMP-08, INV-03 | Admin | `AD_demo_files` T02 | 3 |
| FS-04 | Preview and load give the same result for the same file; loading the same file again does not duplicate models | IMP-01, IMP-07 | Admin | sample T02 | 3 |
| FS-05 | Load T03, T04 and T05; validations, findings and approvals appear on the right models | VAL-01, FND-01, APR-01 | Admin | sample T03–T05 | 3 |
| FS-06 | A segregation-of-duties breach is refused, both when created in the UI and when imported | INV-03 | Admin | generated T02 | 2 |
| FS-07 | Create a model in the UI, edit it, and see before and after values in the audit trail. The Command Center, Operations Board and Audit Trail show the change without a page reload — the first runtime proof of G0.5 (CR-06), previously verified by static analysis only | INV-01, INV-02, AUD-01, CC-01 | Model Owner | — | 2 |
| FS-08 | Answer the tiering questions; the tier follows policy thresholds; an override needs a reason and keeps the calculated tier | TIR-01, TIR-04, TIR-05 | Validator | — | 2 |
| FS-09 | A lifecycle move without required evidence is refused; with the evidence uploaded it is allowed | LIF-01, INV-05 | Model Owner | seed PDF | 2 |
| FS-10 | Revalidation status (Scheduled, Due Soon, Overdue) is correct for the fixed business date | VAL-02, VAL-04 | Validator | — | 2 |
| FS-11 | Raise a finding, move it through its statuses, and see overdue counts change on the Command Center | FND-02, FND-04, CC-01 | Validator | — | 2 |
| FS-12 | A conditional approval stays visible until all its conditions are closed | APR-03 | MRC Member | — | 2 |
| FS-13 | The governance score breakdown for three sample models matches an independent calculation | SCR-01, SCR-05 | Validator | — | 2 |
| FS-14 | Changing a policy setting changes the tier thresholds and keeps the setting's history | CFG-02, CFG-03, TIR-03 | Admin | T12 | 2 |
| FS-15 | Upload a single document, upload version 2, and upload a duplicate; check classification, versioning and duplicate detection | DOC-01, DOC-08, DOC-17 | Model Owner | seed PDFs | 4 |
| FS-16 | ZIP package with a T17 manifest, then a multi-file upload through the Document Centre control, then a folder-source upload; documents map to models; failures are reported per file | DOC-03…DOC-07, DOC-10, DOC-13, DOC-15, DOC-18 | Admin | generated ZIP + per-run PDFs | 4 |
| FS-17 | Document completeness on Model 360 changes after an upload | DOC-20, §40 | Model Owner | seed PDF | 4 |
| FS-18 | Each Command Center tile drills down to a list whose count equals the tile and the Operations Board filter. "Models with open findings" counts models, and each findings link in its sub-line opens a list of that size. Each severity bar filters by `finding_severity`. Score-band links use the `scored_*` flags (G0.2, G0.4). The tile label differs from the mock-up as an accepted difference | CC-01, CC-02 | Executive | — | 8 |
| FS-19 | Each insight links to its source record | CC-04 | Executive | — | 8 |
| FS-20 | Audit trail filters by user, model, entity, action, date, batch and document | AUD-03 | Auditor | — | 8 |
| FS-21 | Resetting to the seed twice with the same business date gives the same counts **and reloads the 1,116 evidence documents** (FT-04); a reset started while one is running is refused with a conflict naming the batch and submits no second job (FT-02) — never a 500 (TR-70); the in-flight signal is the `reset_lock` row (G1.32), and an idle `reset/status` reports `last_outcome` Completed with the lock free and the seeded example report written; **report generation while the lock is held answers 409, writes no `generate` audit event, and the idle portfolio holds only the seeded report (CR-67, G1.34)**; `B_Inputs` content is unchanged (timestamp-only churn is G0.15) | GEN-01, GEN-04, GEN-05 | Admin | — | 2 |
| FS-22 | A Model Developer and a Data Owner can upload a document batch but cannot remap, confirm or cancel it in review; the API returns 403 and nothing changes. A role with `document:review` can (CR-04, G0.3) | SEC-02, DOC-03 | Model Developer, Data Owner | seed PDFs | 4 |
| FS-23 | Removing one role from a user by re-importing T01 (there is no role-edit screen or API yet, CR-19) invalidates that role's session at once, in the UI and the API. The user's other roles keep working (TR-04, G0.9) | SEC-05 | Admin | generated T01 | 1 |
| FS-24 | Refused writes through the UI leave no audit event: an SoD breach, a tier override without a reason, and an action without permission. A permitted write adds exactly one event (TR-01, G0.7) | AUD-01 | Admin | — | 2 |
| FS-29 | **One date per event, west of UTC** (`timezoneId: America/Los_Angeles`): every timestamp the API sends carries an offset, the Score tab shows the day of its own `calculated_at`, the lifecycle list the day of its own `changed_at` and the History tab the day of its own `occurred_at` — each also showing a **time**, which is what catches a datetime sent through the date-only formatter. The offset and time checks carry the proof; the local-day comparison alone could not fail, and the scenario says so | §67, BL.28 (MP-15/MP-16) | Admin | — | 8 |
| FS-28 | The revalidation timeline **is exactly the Revalidation column** (set equality against each model's displayed stage) and shows **§10's full list** — Model, Tier, Owner, Last validation, Due, Days, Outcome, Status — each value being that row's own model's, checked on a row where owner, last validation and outcome are all non-empty | CC-03, §10, BL.24 (MP-17) | Executive | — | 8 |
| FS-27 | A role switch takes effect **without a page reload**: as Executive the audit-gated nav item is absent and `GET /api/audit` is 403; after switching to `U-001|Admin` through the picker — no navigation — the nav item appears, `/api/auth/me` is the new identity and the same call returns 200. A `window` marker is checked at the end, because a reload would make the scenario vacuous. The FT-03 / G0.21 regression test, and the only named guard for SEC-07 at any level | SEC-07 | Executive → Admin | — | 1 |
| FS-26 | Date-only values render their own calendar day and agree between screens, in a timezone **west of UTC** (`timezoneId: America/Los_Angeles`): the Command Center lede states the business date, and the revalidation timeline's due date is character-for-character what Model 360 shows for the same model (MP-10 / FT-06) | CC-01, LIF-02 | Executive | — | 8 |
| FS-25 | Generate the core Model Risk Report as a Validator; its figures equal the Command Center; the score bands read as labels, not keys; generating again gives the same content; "changes since" compares against the report the reset seeds; an Executive can view and download but not generate, and is refused by the API as well as the UI; an Auditor can download. **Second test (2026-10-15):** the seeded example carries D14's label, worded exactly from its `business_date` and `figures_as_of`, on the list, the reopened report and its PDF; every PDF carries "Figures reconciled with the Command Center at generation, …"; an MRC Member records a decision through Model 360 between generations, and it is listed under "Approval decisions recorded" in the changes section (S13), not in Approvals, while the next generation gives the same content hash (REG-16, CR-52); **D17 (G1.34): the seeded example's `generated_at` is a real instant inside the last reset's lock window, never 09:00 on its illustrative date, and the reopened report and the PDF print that same instant in the reconciliation line** | REG-15…17, D14, S13 | Validator, Executive, Auditor | — | 2A-core (**built**, G1.16–G1.18) |
| FS-30 | Monitoring plan, metrics and results load; Pass/Warn/Fail is calculated; a breach is created | MON-01…MON-03 | Monitoring Analyst | T13–T16 | 6 |
| FS-31 | Inventory classes, vendor models, challenges, overlays and dependencies. When Phase 2A resumes, split into one scenario per REG criterion as FS-40 onwards. The report itself is FS-25, built ahead of this (D12) | REG-01…REG-14 | various | T19–T21 | 2A (deferred, D12) |
| FS-32 | CDE and DQ results load and appear on Data Audit | §76B (D8, undecided) | Data Owner | T06, T10 | 7 |
| FS-33 | AI extraction proposals are confirmed or dropped, and nothing is saved before confirmation | DOC-16 | Validator | seed PDF | 5 |
| FS-34 | Copilot answers cite records from the app | §76C (D11, undecided) | Executive | — | 9 |

## Criterion IDs corrected from the starting catalogue

The starting catalogue cited criterion *families* (`IMP`, `DOC`, `SEC`) where CLAUDE.md numbers
individual criteria. Families cannot be traced, so each row now names the criteria it actually
exercises. Specific corrections:

| ID | Was | Now | Why |
|---|---|---|---|
| FS-01 | `SEC-01…04` | `SEC-01…SEC-04` | Range written out; all four exist in §76A.9 |
| FS-02 | `IMP` | `IMP-02, IMP-03` | IMP-02 is the registry/template contract; IMP-03 is isolation of an unloadable file |
| FS-03 | `IMP, INV` | `IMP-01, IMP-05, IMP-08, INV-03` | The demo file's rejected row *is* the SoD case, so INV-03 is exercised too |
| FS-05 | `VAL, FND, APR` | `VAL-01, FND-01, APR-01` | The loaded records' validation rules |
| FS-09 | `LIF` | `LIF-01, INV-05` | Required-evidence refusal is INV-05; the transition record is LIF-01 |
| FS-13 | `SCR` | `SCR-01, SCR-05` | SCR-01 is the calculation, SCR-05 the explainability |
| FS-14 | `CFG` | `CFG-02, CFG-03, TIR-03` | Tier thresholds moving is TIR-03 |
| FS-18 | `CC-01` | `CC-01, CC-02` | The severity bars are a distribution (CC-02) |
| FS-19 | `CC` | `CC-04` | Insights are CC-04 |
| FS-22 | `SEC, DOC` | `SEC-02, DOC-03` | — |
| FS-32 | `DQ (§76B)` | `§76B (D8, undecided)` | §76B does not exist yet; D8 is unrecorded, so there is no criterion to cite |
| FS-34 | `COP (§76C)` | `§76C (D11, undecided)` | Same — D11 is unrecorded |

No scenarios were renumbered and none removed. No scenarios were added: the starting catalogue
already covers every §76A family with at least one scenario, and the four Gate 0 runtime-proof
scenarios (FS-07, FS-18, FS-22, FS-23, FS-24) were already present.

## Harness defects closed in the 2026-10-07 re-run and the 2026-10-08 Gate 1 run

Recorded here so the next run can tell a harness change from a product change. H-17 to H-19
were closed in the Gate 1 run, from findings the test reviewer raised against these files. All of these produced
a *false negative* — a scenario that failed, or passed, on itself rather than on the application.

| ID | Scenario | Was | Now |
|---|---|---|---|
| H-02 | FS-11, FS-12 | Looked for `Raise finding` / `Record decision` on the Overview tab; they live behind the Findings and Approvals tabs. FS-11 also named U-003 as M-0012's owner, which the seed has not been true of for some time, so the write would have been refused 403 and read as a product defect | Clicks the tab; reads the owner from the model. Both scenarios also use `actionField()` — XPath on the label's direct `text()`, because `ActionForm` wraps its control in the `<label>` and `getByLabel(..., {exact:true})` therefore matches "Severity" plus every option |
| H-03 | FS-16 | Asserted the final item status on the `POST /api/documents/batches` response, but analysis is a background job: items read `Uploaded` there and `Ready` a second later | Polls `GET /api/documents/batches/{id}` until no item is `Uploaded`, then asserts. The same applies after Confirm, which is also asynchronous |
| H-04 | FS-17 | Hard-coded M-0042, which has all five required documents on a complete seed, so there was no gap to close and DOC-20 could never be judged | Finds a model from `/api/documents/completeness?missing_only=true` |
| H-09 (part) | FS-12, FS-16 | Not re-runnable: FS-12 closed only the *first* open condition, so a second run left the model outstanding; FS-16's ZIP files are exact duplicates on a second run, so the Store path was never reached | FS-12 closes every open condition, which is what APR-03 actually says; FS-16 keeps the ZIP for DOC-05/DOC-06 and uploads per-run unique bytes for the Store path |
| H-11 | FS-06 | Named U-003 as both Owner and Validator, but the Validator `<select>` lists only Validator-role users, so the option could never exist | Queries the seed for a user holding **both** roles (U-101) and fails loudly if there is none |
| H-12 | FS-21 | Default 30 s test timeout against its own 300 s poll | `test.setTimeout(900_000)` |
| H-13 | FS-23 | Removed U-040's MRC Member role and never restored it; U-040 is the seed's only MRC Member, so FS-12 could not sign in on any later run | Restores it in a `finally` from `T01_role_restored.csv`, and proves it by signing in |
| H-14 | FS-20 | Checkpoint screenshot taken while the table still read "Loading…" | Waits for the first row |
| **H-15** | FS-07 | Asserted `= 1` `create` audit event for the model id it was given. A reset reloads the seed but **keeps the audit trail**, so the next free model id is handed out again and the trail already holds a `create` for it — the scenario failed on a second run while the product was correct | Counts only events newer than the scenario's own starting `event_id` |
| **H-16** | FS-21 | Screenshotted the Command Center without reloading it, so the evidence showed the pre-reset portfolio (260 models) after a reset that had restored 256 | Reloads, and asserts the tile equals the stored count |
| **H-17** | FS-25 | The REG-16 determinism check could not fail: `expect.poll(hashOf).not.toBe("")` returned on its first evaluation, because a hash is on screen from the first generation onwards, so the final comparison was the first report's hash against itself — and nothing observed the second generation at all. Reproduced with a route handler that rewrote the second response's hash: the old pattern passed (review finding **TR-39**) | Waits for the **displayed report id** to change, asserts the row count rises by one, and only then compares hashes. The same defect now fails the scenario. REG-16's audit half (one event per generation) and its refusal half (nothing stored, nothing audited) are asserted too |
| **H-18** | FS-29 | Both time-of-day assertions were scoped to `main`, so a *neighbour's* timestamp satisfied them. The Overview tab also renders tier overrides through `formatDateTime`, and FS-08 creates one on M-0012; the History tab always renders the Versions list the same way, so the audit half was vacuous on every run, not only after FS-08 (review finding **TR-41**) | Each assertion is scoped to the element that renders the field under test: the Lifecycle panel's first `<li>`, the Audit history table's first `When` cell, and the Governance score heading (which also gains the missing time check) |
| **H-20** | FS-21 | Asserted `policy === 70` against a bootstrap that Gate 1 took to **72**, so the scenario failed on its own stale constant while the reset was correct. A false negative of the most expensive kind on this scenario: GEN-01 is the check that tells the whole run whether the reset took | Pinned to 72, with a comment saying the figure is edited deliberately rather than read from the database it is checking. The catalogue header carries the same number |
| **H-19** | FS-28 | Titled `CC-03` while asserting only §10's columns, so `grep CC-03` reported coverage the scenario did not provide (review finding **TR-42**) | Retitled, and CC-03's actual claim is now asserted: the timeline's model ids equal the set of models whose displayed stage is Revalidation |
| **H-21** | FS-21 | Read "a reset is running" from batch statuses, the inference G1.32 removed from the product. Both reset batches are terminal while the seeded example report is written, so the GEN-04 probe could stop early and fail on "the reset finished before a second one could be attempted"; and a 500 from the refused reset was retried as if it were a 401, so TR-70's defect could not fail the scenario | Reads the `reset_lock` row (`holder IS NOT NULL`); a 5xx ends the probe as a failure; after each reset asserts GEN-05's `last_outcome` Completed, the lock free and exactly one seeded report |
| **H-22** | FS-25 | Asserted nothing about D14, G1.31 or S13, which all landed after the 2026-10-08 run | Second FS-25 test; `pdfText` helper (ASCII85 + Flate, no new dependency) reads the PDF. Shown to discriminate on 2026-10-15 with two temporary route-rewrite probes, both deleted: blanking `seeded_label` on the list fails "D14: and the full label", and rewriting the third generation's hash fails the REG-16 comparison |
| **H-23** | FS-21, FS-25 | Asserted nothing about G1.34: the seeded example's real generation time (D17) and the 409 for a report generated while a reset holds the lock (CR-67) | FS-25's second test checks D17 against the reset lock's `acquired_at`/`released_at` on the list, the reopened report and the PDF; FS-21's second reset carries a report-during-reset probe. Shown to discriminate on 2026-10-16 by running both scenarios against a backend built from `b8cc1f3` (the only product difference is `report_service.py`): the CR-67 probe failed (the old code answered 500), and the D17 check failed on `2026-08-31T09:00` |

Still open and deliberately not fixed: **H-08** (`openScreen` does not wait for the destination —
latent, no scenario fails on it), and the rest of **H-09** (FS-15 and FS-24 leave state behind; both
are idempotent enough to pass twice, and FS-21's reset clears them mid-suite).

One ordering effect worth knowing rather than fixing: FS-24's control write sets `reval_lead_days`
to 90 and does not put it back, so the scenarios between it and FS-21's reset see a 90-day
revalidation lead time. Every assertion in that window is internally consistent (each tile is
compared with its own drill-down), but two screenshots of the Command Center in the same run can
legitimately show different revalidation-queue counts.
