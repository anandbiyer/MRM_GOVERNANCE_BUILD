# MRM/MIS — Project Plan

**Status as at:** 2026-10-03 · **Branch:** `review-agents`

*(No commit hash here on purpose: a hash written into a tracked file is stale the moment it is
committed. Evidence columns cite test names and settings, which stay valid.)*

This is the live plan from the current build to a demonstrable product. It is the tracking document:
statuses here are maintained as work lands, and every activity carries a stable ID so it can be
referenced in commits and reviews.

## How to use this file

- **Stable IDs.** `G0.1`, `G1.4` and so on never change meaning or get renumbered. New work gets the
  next free number in its gate; cancelled work is marked `Dropped`, not deleted.
- **Status vocabulary:** `Done` · `In progress` · `Blocked` · `Not started` · `Dropped`.
  `Blocked` always names what it waits on.
- **Evidence.** A `Done` row cites what proves it — a commit, a test, a report path. A row without
  evidence is not `Done`.
- **Update rule.** Update this file in the same change that moves the work, not afterwards. Add a line
  to the change log at the bottom. Keep the "Status as at" line current.
- Findings referenced as `CR-nn` / `TR-nn` / `MP-nn` come from `D_Reviews/20261002_summary.md` and the
  three reports beneath it. `D1`–`D11` are the §81A decisions in `CLAUDE.md`.

---

## 1. Where the project stands

| Dimension | Built | Remaining |
|---|---|---|
| BRD phases (§81) | 1, 2, 3, 4 + core of 8 | 2A, 5, 6, 7, 9, 10 |
| Screens (§55) | 7 of 11 | 2 placeholders (Monitoring, Data Audit) + 2 absent (Model Risk Report, Copilot) |
| Database tables | 21 | ~17 — monitoring (6), CDE/DQ (4), KPI/performance (3), `document_extraction`, §12A (3) |
| Import templates | 8 of 21 — T01–T05, T12, T17, T18 | 10 registered but disabled (T06–T11, T13–T16) + T19–T21 not registered |
| API groups (§54) | ~11 | 8 — monitoring (5), cde, dq, copilot |
| Acceptance criteria | 69 of 112 proven | 16 open in built scope (3 untested, 13 partly proven) + 27 unbuilt |
| Mock-up parity | 24 of 35 items Match | 10 not built, 1 flaky harness |
| Roles / permissions | 10 × 15, enforced server-side | `REG_CLASSIFY`, `OVERLAY_APPROVE` (Phase 2A) |

**The shape of it:** the governance spine is complete — recording and governing a model works end to
end. The measurement half is absent — nothing observes a model over time. That is why 69 of 112
criteria are proven while only about 55% of the data model exists.

### Two demo bars

| Bar | Scope | State |
|---|---|---|
| **A — what exists** | Inventory, tiering, validation, findings, approvals, score, structured import, documents, Command Center, Operations Board, Model 360, Admin, Audit Trail | Near ready; Gate 0 closes it out |
| **B — what the customer saw** | All 35 mock-up items, including monitoring, backtesting, CDE/DQ, the MRC report and the Copilot | Needs Gates 1–6 |

**Recommended target:** Gate 0 → 1 → 2 → 3. That is the shortest credible customer demo: the full
governance lifecycle, the SR 26-2 regulatory story, the model risk report and monitoring. Data Audit,
AI extraction and the Copilot are self-contained and nothing depends on them, so they can be presented
as roadmap.

---

## 2. Completed to date

| ID | Activity | Status | Evidence |
|---|---|---|---|
| GR.1 | §76A acceptance criteria for the governance core (57 criteria) ported from the superseded `design.md` §12, with a traceability map | Done | `claude.md` §76A, commit `83afa1f` |
| GR.2 | Tests tagged with criterion IDs — 104 of 111 functions | Done | commit `83afa1f` |
| GR.3 | CI workflow: backend pytest, migrations + PostgreSQL, frontend build | Done | `.github/workflows/ci.yml`, commit `83afa1f` |
| GR.4 | Three review agents + `/review-build` + `D_Reviews/` | Done | `.claude/`, commit `7ecb31c`. **Caveat:** agents register only after a Claude Code restart |
| GR.5 | Playwright mock-up parity harness, 35-item checklist | Done | `A_Codes/AF_e2e/`, commit `7ecb31c`. `mockup` project 35/35 |
| GR.6 | `setup_first_time.ps1` requires Python 3.14 and installs the harness | Done | commit `7ecb31c` |
| GR.7 | First full review run — 1 Critical, 7 High | Done | `D_Reviews/20261002_summary.md` |
| GR.8 | **MP-01** — stale seed T12 dropped two policy settings, so Reset to seed left the Command Center returning 500 | Done | commit `f87f130`; seed 60→62 keys; reset now fails loudly on an incomplete baseline |
| GR.9 | **MP-02** — four tests covering the committed seed, each confirmed to fail before the fix | Done | commit `f87f130`; suite 143 tests, 139 pass |
| GR.10 | CLAUDE.md corrections from the review applied | Done | commit `ee6c7eb` |

---

## 3. Gate 0 — close out the review (unblocks Bar A)

Small, high value, no dependencies. Everything here is an open finding from the first review.

| ID | Activity | Finding | Status | Note |
|---|---|---|---|---|
| G0.1 | Resolve the lifecycle phase from policy; guard the unchecked `.index("Monitoring")` | CR-02 (High) | **Done** | New T12 setting `monitoring_phase`; `revalidation.displayed_columns()` is now the single source of the column order (was duplicated in `dashboard_service` and `api/models`) and degrades instead of raising; `displayed_column()` lost its `"Monitoring"` default; paired policy validation refuses breaking either side on the interactive path. Tests: `test_cr_02_renaming_the_monitoring_phase_does_not_break_the_dashboard`, `test_lif_02_monitoring_phase_comes_from_policy`, `test_displayed_columns_*`. Regression confirmed: restoring the old line fails with `ValueError: list.index(x): x not in list` |
| G0.2 | Move governance score bands 60 / 80 into `policy_setting` | CR-01 (High) | **Done** | New T12 settings `score_band_warn_min` / `score_band_good_min`, with ordering and 0–100 validation. Classification lives in `rules.score.band_of/band_labels`; band keys renamed to `below_warn` / `warn_to_good` / `good_plus` and flags to `scored_*` so no key restates a boundary. `/api/models/meta` returns the boundaries and labels, and all three frontend sites (`Pills.ScoreValue`, `CommandCenter`, `OperationsBoard`) derive from it. Test: `test_cr_01_score_bands_come_from_policy` |
| G0.3 | Enforce `Permission.DOCUMENT_REVIEW` on the review actions | CR-04 (Med) | **Done** | `batch._require` split into `_require_upload` (create_batch) and `_require_review` (update_items, start_confirm, cancel). Frontend `DocumentBatchReview` now gates on `document:review`. Test: `test_cr_04_reviewing_a_batch_needs_document_review_not_upload`; reverting the gate makes a Model Developer's remap return 200 instead of 403 |
| G0.4 | "Open findings" tile must drill into findings, not models; severity bars must filter | CR-05 (Med) | **Done** | Tile relabelled "Models with open findings" and valued in models (new tiles `models_with_open_findings`, `models_with_overdue_findings`, `models_with_critical_overdue`); findings totals kept in the sub-line, where each link's number matches the list it opens. New `finding_severity` filter on `/api/models` and the Operations Board, so each severity bar drills to its own models. Tests: `test_cr_05_each_severity_bar_drills_to_its_own_models`, extended `test_tiles_tie_out_to_lists`. Recorded as an accepted difference from the mock-up in `mockup-parity.md` |
| G0.5 | Invalidate the Command Center query on mutation | CR-06 (Med) | **Done** | `invalidateGovernance()` / `invalidatePolicy()` in `api/queries.ts` own the list of derived reads (`dashboard`, `models`, `completeness`, `audit`); all seven governance-mutation sites call them instead of hand-listing keys. Verified by static call-graph check, **not** by an automated test — there is no frontend test harness (see G7.5) |
| G0.6 | Add `model_version` to documents | CR-07 (Med) | **Done** | Migration `0005_document_model_version`: nullable `model_version` on `document` and `document_upload_item`, with a composite FK over `(model_id, model_version)`. Validated in `store_version` with a message naming the known versions; carried through the single-upload form, T17 and the batch review path. Spec issue **S4** resolved in §48 in favour of §24/§27. Test: `test_cr_07_evidence_records_the_model_version_it_is_about`. Migration **executed and verified** against PostgreSQL 16: full `alembic upgrade head` from an empty database, drift guard passing, composite FK present in `\d document` |
| G0.7 | Prove AUD-01: a refused write leaves no audit event; a failed audit rolls the change back | TR-01 (High) | Not started | Seven tests currently prove only that an event exists |
| G0.8 | Prove APR-03 (outstanding until conditions close) and APR-04 (ordering by date) | TR-02, TR-03 (High) | Not started | |
| G0.9 | Prove SEC-05 for role removal, not just deactivation | TR-04 (High) | Not started | Distinct code path |
| G0.10 | Record decisions **D10** and **D5** | S1, S2 | Not started | D10 already implemented with a blank decision; D5's proposed key names clash with shipped T12 |
| G0.11 | Fix the `127.0.0.1:5173` address in `.claude/agents/mockup-parity-tester.md`, or set `server.host` in `vite.config.ts` | MP-04 | Not started | The agent waits on an address that never answers |
| G0.12 | Make `generate_seed.py`'s `shutil.rmtree` safe in a OneDrive-synced copy | new | Not started | A partial failure deletes committed evidence PDFs; hit once this session |
| G0.13 | Stabilise the flaky MUP-34 cross-screen count check | MP-03 (Low) | Not started | Passes alone, intermittently reads 0 rows in a full run |
| G0.14 | Migration/ORM drift: `validation.report_document_id` and `approval.supporting_document_id` were `VARCHAR(40)` in migration 0002 but `String(20)` in the ORM | new, found 2026-10-04 | **Done** | Migration `0006_document_fk_widths` narrows both to match the referenced `document.document_id`. Found only once PostgreSQL was available; the drift guard had never run. Also closes **TR-05**, which flagged that drift and the append-only trigger were unverifiable |

## 4. Gate 1 — Phase 2A, Regulatory alignment (SR 26-2)

First in the Part 0 build order. **Needs no §81A decision**, so it can start immediately and in
parallel with Gate 2.

| ID | Activity | Criteria | Status |
|---|---|---|---|
| G1.1 | Migration: §12A `model` columns, `model_dependency`, `effective_challenge`, `model_limitation` | — | Not started |
| G1.2 | Inventory classification (Model / Tool / AI system) with reason, audit and exclusion from model counts | REG-01, REG-02 | Not started |
| G1.3 | Exposure fields; materiality suggestion from `materiality_exposure_bands` that never overwrites the user's answer; `tier_rationale` | REG-03, REG-05 | Not started |
| G1.4 | Proportionate revalidation defaults from `reval_frequency_by_tier` + deviation reason | REG-06 | Not started |
| G1.5 | Vendor model fields and `vendor_required_documents` in completeness | REG-07 | Not started |
| G1.6 | Effective challenge log; independence check; "Finding raised" creates the finding in the same transaction | REG-08 | Not started |
| G1.7 | Limitations / overlays / use exceptions with approver rules, expiry insights and the Critical in-use insight | REG-09, REG-10 | Not started |
| G1.8 | Model dependencies: self- and cycle-refusal, upstream-issue propagation | REG-11 | Not started |
| G1.9 | Permissions `REG_CLASSIFY`, `OVERLAY_APPROVE` | — | Not started |
| G1.10 | Templates T19–T21 and optional T02 columns — existing T02 files must still load | REG-14 | Not started |
| G1.11 | Command Center aggregate model risk view with drill-down | REG-09, REG-12 | Not started |
| G1.12 | **Model Risk Report** (§55.10) — generate, preview, download, audited, reproducible | REG-10, REG-13 | Not started |
| G1.13 | Model 360 sections: classification, exposure, vendor, limitations, challenges, dependencies | — | Not started |
| G1.14 | Auditor read-all + evidence package download | REG-11 | Not started |
| G1.15 | Seed additions (§12A.4) and REG-01…REG-14 tests | — | Not started |

**Delivers mock-up items MUP-29, MUP-30.**

## 5. Gate 2 — record decisions D1–D7 ⛔ blocks Gate 3

Not an engineering task. Can and should run in parallel with Gate 1.

| ID | Decision | Subject | Status |
|---|---|---|---|
| G2.1 | **D1** | KPI vs monitoring tables — which is the system of record | Not started |
| G2.2 | **D2** | Bounds for the "within range" direction | Not started |
| G2.3 | **D3** | Rules-created breaches vs T16 import | Not started |
| G2.4 | **D4** | Backtests as a `monitoring_run` type | Not started |
| G2.5 | **D5** | Escalation / repeated-breach policy keys (see G0.10) | Not started |
| G2.6 | **D6** | What feeds the Monitoring score component; treatment of Not Available | Not started |
| G2.7 | **D7** | Missing MON criteria for §21–§24 and T13–T16 validation | Not started |

## 6. Gate 3 — Phase 6, Monitoring (largest block)

Blocked by Gate 2. Also requires G0.6.

| ID | Activity | Criteria | Status |
|---|---|---|---|
| G3.1 | Migration: `monitoring_plan`, `monitoring_metric`, `monitoring_run`, `monitoring_result`, `monitoring_breach`, `monitoring_evidence` with effective dating | — | Blocked (G2) |
| G3.2 | Monitoring plans, versioned, with owner/reviewer and review calendar | — | Blocked (G2) |
| G3.3 | Configurable metrics and thresholds; direction incl. within-range (D2) | MON-01 | Blocked (G2) |
| G3.4 | Runs and results; **threshold snapshot onto each result** so history never changes | MON-01, MON-05 | Blocked (G2) |
| G3.5 | Breach creation, severity rules, escalation, repeated-breach detection (D3, D5) | MON-02, MON-03, MON-08 | Blocked (G2) |
| G3.6 | Run completeness check before sign-off | MON-04 | Blocked (G2) |
| G3.7 | Backtesting as a run type (D4) | — | Blocked (G2) |
| G3.8 | Trends: ≥4 periods, chart drill-down to the result | MON-06, MON-07 | Blocked (G2) |
| G3.9 | Evidence attachment to runs and metrics | MON-10 | Blocked (G2) |
| G3.10 | Breach → finding conversion by authorised action only | MON-09 | Blocked (G2) |
| G3.11 | Monitoring Dashboard screen (§25), replacing the placeholder | MON-11 | Blocked (G2) |
| G3.12 | Model 360 Monitoring tab (§26) | — | Blocked (G2) |
| G3.13 | Monitoring score component (D6) | MON-12 | Blocked (G2) |
| G3.14 | Templates T13–T16 and T07–T09 | — | Blocked (G2) |
| G3.15 | MON-01…MON-12 plus whatever D7 adds | — | Blocked (G2) |

**Delivers MUP-18, MUP-19.** Note: every model's governance score shifts when this lands — the 15%
monitoring weight stops being rescaled away. Expect the seeded portfolio figures to change.

## 7. Gate 4 — Phase 7, Data Audit

Blocked by **D8** (write DQ criteria as §76B).

| ID | Activity | Status |
|---|---|---|
| G4.1 | Migration: `cde`, `dq_rule`, `dq_result`, `dq_issue` | Blocked (D8) |
| G4.2 | CDE registry, DQ rules and thresholds, results by run, issue log | Blocked (D8) |
| G4.3 | Templates T06 and T10 | Blocked (D8) |
| G4.4 | Data Audit screen (§55.5), replacing the placeholder | Blocked (D8) |
| G4.5 | Model 360 CDE/DQ tab | Blocked (D8) |
| G4.6 | §76B criteria and tests | Blocked (D8) |

**Delivers MUP-20, MUP-27, MUP-28.**

## 8. Gate 5 — Phase 5, AI extraction

| ID | Activity | Status |
|---|---|---|
| G5.1 | Migration: `document_extraction` with the §60 provenance fields (provider, model, prompt version, reviewer) | Not started |
| G5.2 | PDF/DOCX text extraction | Not started |
| G5.3 | Document classification and per-type extraction (ToR, MDD, Validation Report, Monitoring Report) | Not started |
| G5.4 | Review queue; **nothing persists without human confirmation**; every AI step audited | Not started |
| G5.5 | DOC-16 and MDD section completeness in the documentation score | Not started |

**Delivers MUP-26.**

## 9. Gate 6 — Phase 9, Audit Copilot

Blocked by **D11** (write COP criteria as §76C).

| ID | Activity | Status |
|---|---|---|
| G6.1 | Read-only query tools over governed data | Blocked (D11) |
| G6.2 | Answers cite model IDs and underlying records; refuse to act | Blocked (D11) |
| G6.3 | Suggested questions; Copilot screen and route | Blocked (D11) |
| G6.4 | §76C criteria and tests | Blocked (D11) |

**Delivers MUP-31, MUP-32.**

## 10. Gate 7 — Phase 10, hardening (before any external demo)

| ID | Activity | Status |
|---|---|---|
| G7.1 | OIDC / enterprise identity, replacing the no-password dev role picker | Not started |
| G7.2 | Malware scanning on upload (`scan_status` is a stub today) | Not started |
| G7.3 | Celery/RQ workers instead of the in-process thread executor | Not started |
| G7.4 | Performance: <2s Command Center and Model 360 at scale | Not started |
| G7.5 | **Frontend tests — none exist.** `tsc -b` is the only frontend gate | Not started |
| G7.6 | E2E in CI (the parity harness is deliberately outside it) | Not started |
| G7.7 | Backup / restore, health checks, deployment | Not started |

---

## 11. Critical path and risks

1. **Gate 2 is a decision bottleneck, not an engineering one.** It gates the largest block of work
   (Gate 3). Start it now, in parallel with Gate 1. If it slips, Gate 3 slips with it.
2. **G0.6 must precede Gate 3.** Adding `model_version` to documents after monitoring evidence is
   attached means migrating live associations.
3. **Scores move when Gate 3 lands.** Anything quoting today's governance scores — seed expectations,
   demo scripts, GEN-01's documented figures — needs revisiting then.
4. **The review agents need a Claude Code restart** before `/review-build` works as intended (GR.4).
5. **No deadline estimates appear in this plan deliberately.** There is no velocity data for this team;
   sequencing and dependencies are stated instead, so dates can be attached once capacity is known.

---

## 12. Change log

| Date | Change |
|---|---|
| 2026-10-03 | Plan created. Records GR.1–GR.10 as Done from the current session; Gates 0–7 opened with all activities `Not started` or `Blocked`. |
| 2026-10-04 | **G0.6 verified, and G0.14 found and fixed.** With Docker available, PostgreSQL 16 was brought up and `alembic upgrade head` run from an empty database. The drift guard then **failed** — not on the new migration, which was clean, but on a pre-existing disagreement from migration 0002 (two document foreign keys declared `VARCHAR(40)` against an ORM `String(20)`). Fixed forward in `0006_document_fk_widths`; all four PostgreSQL tests now pass, so the `backend-postgres` CI job is green rather than red. G0.6's provisional caveat is removed. This also resolves **TR-05**: the append-only audit trigger and the absence of drift are now confirmed rather than unverifiable. Worth noting the sequence — the drift had existed since Phase 2 and was invisible because the gate that checks it had never been run. |
| 2026-10-04 | **G0.6 Done** (CR-07). Suite 151 tests / 147 pass; frontend build green. The Gate 3 prerequisite is now cleared. Also resolved spec issue **S4** by recording the decision in §48 rather than leaving the BRD contradicting itself. **Verification gap:** the migration was never executed. Docker's daemon is not running locally and the launcher uses `create_all`, so Alembic only ever runs against PostgreSQL; it was checked by `alembic upgrade --sql` offline render, which produced the expected DDL with the composite FK. The `backend-postgres` CI job runs the real upgrade and the ORM/migration drift guard — **treat this item as provisional until that job has passed once.** |
| 2026-10-04 | **G0.5 Done** (CR-06). Frontend build green; backend suite unchanged at 150 / 146 (no backend files touched). Fixed by centralising rather than by the finding's suggestion of adding `["dashboard"]` to nine call sites — hand-listed keys are what produced the bug, and nine more hand-edits would be forgotten the next time a screen is added. `["audit"]` was added to the derived set too: every material write produces an audit event, so the Audit Trail had the same staleness. **Verification gap:** no automated test covers this, because the frontend has no test harness at all (G7.5); it was checked by static call-graph analysis only. |
| 2026-10-04 | **G0.4 Done** (CR-05). Suite 150 tests / 146 pass; frontend build green; parity `mockup` project still 35/35. Chose to count the tile in models rather than build a findings-list screen — the alternative reading of CC-01 — because every tile on the Command Center opens a model list. That makes the tile label diverge from the mock-up, so it is recorded as the first **accepted difference** in `mockup-parity.md` and MUP-01's assertion was updated. The severity bars now have a real drill-down, which `/api/models` previously could not express at all. |
| 2026-10-04 | **G0.3 Done** (CR-04). Suite 149 tests / 145 pass; frontend build green. `DOCUMENT_REVIEW` had been declared and granted to four roles but checked nowhere, so Model Developer and Data Owner — who hold upload but not review — could reclassify and commit a staged batch. Noted while testing: the record-level check (SEC-03) still rejected the *items* downstream, which is why the hole had not surfaced in practice; it only bit on a model the uploader was assigned to. |
| 2026-10-03 | **G0.2 Done** (CR-01). Suite 148 tests / 144 pass; frontend build green. Policy count 63 → 65. **Contract change:** the `score_band` distribution keys and the `?flag=scored_*` values were renamed to drop the embedded numbers, so any saved Operations Board link using `scored_below_60` no longer resolves. Not re-run: the mock-up parity `app` project — the change is label-level and the harness asserts structure, so the backend tests, typecheck and build were taken as sufficient. Noted for later: `Pills.ScoreValue` now calls `useModelMeta()` per cell, so a 256-row board holds that many subscriptions to one cached query; fine today, worth passing as a prop if the board grows. |
| 2026-10-03 | **G0.1 Done** (CR-02). Suite 147 tests / 143 pass. Policy count 62 → 63 (`monitoring_phase`), so `AA_bootstrap/T12` and `AC_seed/T12` were both updated — the GR.9 baseline test enforces that pairing. Noted during the work: `document_rules.py:113` hard-codes `"Implementation"` the same way, but is guarded, so it belongs to CR-08 rather than here. |
