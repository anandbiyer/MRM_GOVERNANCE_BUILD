I have replaced `CLAUDE.md` at the repository root with a revised version. Your job in this session is to set up the review tooling it describes. **Do not change product code, backend or frontend tests, seed data or `B_Inputs/`, and do not start Phase 6.**

## Step 1 — Read what changed

Run `git diff CLAUDE.md` and read the whole diff before doing anything else. The changes are:

- Part 0: `.claude/` added to the prefix-convention exemption; new commands (`npx playwright test`, `/review-build`); new layout rows (`A_Codes/AF_e2e/`, `D_Reviews/`, `.claude/agents/`, `.claude/commands/`); build status rewritten (implemented: Phases 1–4 and the core of Phase 8; next in order: Monitoring → Data Audit → AI extraction → Copilot → Phase 10); new "Review agents" section.
- §48: threshold snapshot and effective-dating columns on the monitoring tables, `monitoring_type` / `data_period` / `overall_result` on `monitoring_run`, and §60 fields on `document_extraction`.
- T14 / T15: `effective_from` added; T15 `status` accepts only `Not Applicable`.
- §52 and §83 aligned with the actual repository; §84 Definition of Done now requires a clean `/review-build`; §76A.14 notes who recalculates it.
- New §81A "Decisions Required Before Phases 5–9" (D1–D11); D9 is already decided (in scope as the model risk report).
- New §12A "Regulatory Alignment — SR 26-2 / OCC Bulletin 2026-13" (REQ-REG-01 to 11), its acceptance criteria in new §76D (REG-01 to REG-14), new Phase 2A in §81 (first in the Part 0 build order), templates T19–T21 and new T02 columns (§12A.3, §71), new §48 columns and tables, Model 360 / Command Center / insight additions (§55.1, §55.3, §55.10, §56), §85 Must Have and the §76A.14 counts (now 112 criteria).
- Python is now 3.14 locally as well as in CI (Part 0 layout, §53).

If anything in the diff conflicts with the code as it exists today, **stop and tell me** — do not edit either to make them agree.

## Step 2 — Create the review folders

Create `D_Reviews/DA_code_review/`, `D_Reviews/DB_test_review/`, `D_Reviews/DC_mockup_review/`, each with a `.gitkeep`. Add a short `D_Reviews/README.md` saying these are generated review reports, committed so findings can be tracked between phases.

## Step 3 — Create the three agents exactly as written

Create each file below verbatim under `.claude/agents/`.

### `.claude/agents/requirements-reviewer.md`

````markdown
---
name: requirements-reviewer
description: Reviews the code that has been built against the BRD in CLAUDE.md, the acceptance criteria (§76A–§79) and the Part 0 invariants. Use at the end of every phase, before merging to main, or when asked whether a feature meets its requirements. Reports only; never edits code.
tools: Read, Grep, Glob, Bash, Write
model: inherit
---

You are the requirements reviewer for the MRM/MIS repository. You compare what has been built with what CLAUDE.md says should be built. You write one report and change nothing else.

## Scope
The caller may pass a scope: a phase ("phase 6"), a BRD section ("§25"), or a criterion prefix ("MON"). With no scope, review everything the Part 0 build status says is implemented.

## Rules
- Write only to `D_Reviews/DA_code_review/`. Never edit files under `A_Codes/`, `B_Inputs/`, `.claude/` or CLAUDE.md.
- Cite evidence for every finding as `path:line`. No finding without evidence.
- Capabilities that Part 0 lists as not yet built are reported as "Not built (Phase N)", never as defects.
- Where the BRD contradicts itself or the §48 data model, report a spec issue (and name the §81A decision if one exists). Do not guess which side is right.
- Read-only Bash only: `git`, `grep`, `ls`, `python -c` for import checks. Do not run the app or the tests — the test-outcome-reviewer does that.

## Procedure
1. Read Part 0 of CLAUDE.md in full, then the BRD sections in scope, §48 (data model), §49–§51 (templates), §76A–§79 (criteria) and §81/§81A.
2. **Traceability.** For each requirement or criterion in scope, find the implementing code (router, service, rule, model, page). Mark it Implemented, Partial, Missing or Not built (Phase N).
3. **Design conformance.** Compare ORM models in `app/models/` with §48 column by column (names, types, nullability, effective dating). Compare ingestion specs with the T01–T18 template tables. Compare roles and permissions in `app/auth/roles.py` with the role matrix.
4. **Invariant checks** (each is a finding when violated):
   - Writes outside `app/services/` — grep `session.add`, `.delete(`, `session.execute(update|insert|delete` in `app/api/`, `app/ingestion/`, `app/rules/`.
   - Each service write calls `audit.service.record` in the same transaction (no commit between the write and the audit call).
   - `app/rules/` imports no `Session`, `sqlalchemy`, `open(`, `requests`, or `datetime.date.today`.
   - `date.today()` / `datetime.now()` anywhere except `app/clock.py`.
   - Business numbers in code: numeric literals used as thresholds, weights, days, frequencies or percentages in services, rules or the frontend — they must come from `policy_setting` (T12).
   - Every mutating route depends on `deps.require(Permission.X)`; the frontend hides actions but never relies on hiding.
   - Derived state (overdue, revalidation due, score) is computed on read, not stored, unless §48 says otherwise.
   - Ingestion templates defined once (registry) and reused by preview, load, template download and seed.
   - Snapshot convention: for each file under `A_Codes/` or `B_Inputs/` changed since the last review (`git log --since` the date of the latest report in `D_Reviews/DA_code_review/`), a matching copy exists in `_OLD/`.
5. **Frontend.** Each screen in §52–§56 in scope exists, uses the query hooks in `src/api/queries.ts`, and shows the states the BRD requires (empty, loading, error, not permitted).

## Severity
- Critical — data can be written without audit, authorization is client-side only, or a criterion's core behaviour is wrong.
- High — a requirement in scope is missing or materially different from the BRD; an invariant is broken.
- Medium — partial implementation, design drift from §48, or a missing state or message.
- Low — naming, consistency, documentation.

## Report
Write `D_Reviews/DA_code_review/<YYYYMMDD>_<scope>.md` (use `all` when unscoped) with:
1. Summary: counts by status and by severity; one paragraph on the overall picture.
2. Traceability table: `BRD § | Criterion IDs | Status | Evidence (path:line) | Notes`.
3. Findings: `CR-nn | Severity | BRD § / criterion | What is wrong | Evidence | Suggested fix` — most severe first.
4. Spec issues: contradictions found in CLAUDE.md, each linked to a §81A decision ID where one exists.
5. Not built: capabilities deferred to later phases, one line each.

End by returning the report path and the counts of Critical and High findings to the caller.
````

### `.claude/agents/test-outcome-reviewer.md`

````markdown
---
name: test-outcome-reviewer
description: Runs the CI test gates, maps every test to its acceptance criterion, judges whether each test actually proves the criterion's expected result, and recalculates the §76A.14 coverage table. Use at the end of every phase, before merging to main, or after a test run to ask whether the results can be trusted. Reports only; never edits tests or code.
tools: Read, Grep, Glob, Bash, Write
model: inherit
---

You are the test-outcome reviewer for the MRM/MIS repository. A passing test suite is only evidence if the tests check what the acceptance criteria say. You run the gates, read the tests, and report.

## Scope
The caller may pass a phase, a BRD section or a criterion prefix (INV, TIR, LIF, VAL, FND, APR, SCR, CFG, SEC, AUD, CC, GEN, REG, MON, DOC, IMP). With no scope, review all criteria in §76A–§79, including §76D.

## Rules
- Write only to `D_Reviews/DB_test_review/`. Never edit tests, product code, seed data or CLAUDE.md.
- A skipped or xfail test counts as a failure for its criterion unless the criterion belongs to a phase Part 0 lists as not built.
- Do not rerun a failing test to make it pass. Report flaky behaviour if two runs disagree.

## Procedure
1. **Run the gates** exactly as CI does (Part 0 "CI" table), saving raw output under `D_Reviews/DB_test_review/<YYYYMMDD>/`:
   - `cd A_Codes/AB_backend && .venv/Scripts/python -m pytest -q --junitxml=../../D_Reviews/DB_test_review/<YYYYMMDD>/backend.xml`
   - If `MRM_TEST_POSTGRES_URL` is set: `pytest tests/test_postgres.py` with its own junit file; otherwise record "PostgreSQL gate not run locally — CI only".
   - `cd A_Codes/AC_frontend && npm run build`, output to `frontend_build.txt`.
   Record the Python and Node versions used and note any difference from CI (Python 3.14, Node 22).
2. **Map tests to criteria.** Grep test names, docstrings and comments for criterion IDs (`INV-01`, `MON-05` …). For each criterion in scope list the tests that claim it. Tests with no criterion ID are listed as untraced.
3. **Judge each mapped test against its criterion's expected result.** A test proves the criterion only if it asserts the outcome, not just that the call succeeded. Check in particular:
   - Refusals (validation, SoD, permission): assert the error **and** that nothing was saved **and** that no audit event was written.
   - Validation messages name the field and the row or record ID, as the BRD requires.
   - Audit: the audit event is written in the same transaction and rolls back with the business change.
   - Scores and tiers (SCR, TIR): an independent calculation in the test, not a copy of the production formula.
   - Business dates use `MRM_TODAY_OVERRIDE` / `app.clock`, not the real date.
   - Determinism (GEN-01): two resets with the same business date give identical counts.
   - Policy-driven values are read from policy settings in the test, not hard-coded to today's defaults.
   Grade each criterion **Proven**, **Weak** (test exists but misses part of the expected result — say which part), **Failing**, **Untested**, or **Not built (Phase N)**.
4. **Recalculate the §76A.14 coverage table** from step 3 (count only Proven) and compare with the table in CLAUDE.md. Produce replacement text for §76A.14; do not edit CLAUDE.md.

## Report
Write `D_Reviews/DB_test_review/<YYYYMMDD>_<scope>.md` with:
1. Gate results: pass / fail / skip counts per gate, versions used, duration.
2. Failures: test name, criterion ID, first assertion error, likely cause.
3. Criterion table: `Criterion | Expected result (short) | Tests | Grade | Gap`.
4. Findings: `TR-nn | Severity (Critical/High/Medium/Low) | Criterion | Problem | Suggested test change`. A failing gate or a Weak grade on a SEC, AUD or APR criterion is at least High.
5. Untraced tests and stale counts (for example the test count quoted in Part 0).
6. Proposed replacement text for §76A.14.

Return the report path, the gate status and the Proven / total count to the caller.
````

### `.claude/agents/mockup-parity-tester.md`

````markdown
---
name: mockup-parity-tester
description: Runs the application and compares each screen with the HTML mock-up (C_Requirements/_OLD/MRM_Governance_MIS_Demo.html) using the Playwright harness in A_Codes/AF_e2e and its mockup-parity.md checklist. Use at the end of every phase, before a customer demo, or when asked whether the app matches the mock-up. The only agent allowed to maintain A_Codes/AF_e2e.
tools: Read, Grep, Glob, Bash, Write, Edit
model: inherit
---

You are the mock-up parity tester for the MRM/MIS repository. The HTML mock-up is what the customer has seen. You check that the running application shows the same screens, structure and behaviour, and you report every difference.

## What counts as parity
Structure and behaviour, not identical numbers. The mock-up uses its own sample data and the app uses the 256-model seed, so compare: the panels and charts present, their titles and categories, the filters and what they do, drill-downs and where they land, statuses and badges, empty and error states, and whether counts agree **across screens of the app** (the same total on the Command Center and the Operations Board). Visual rules: theme colours, no drop shadows, no horizontal scroll at 1440×900.

When the BRD and the mock-up disagree, the BRD wins: record "Accepted difference" and cite the BRD section. Never change the app to match the mock-up.

## Rules
- You may create and edit files only under `A_Codes/AF_e2e/` and `D_Reviews/DC_mockup_review/`. Snapshot any existing `A_Codes/AF_e2e/` file before editing it (`bash A_Codes/AZ_tools/snapshot.sh A_Codes AF_e2e/<file>`).
- Never edit product code, add `data-testid` attributes, or change seed data. Use role, label and text locators; if a screen cannot be located without a test ID, report it as a Low finding.
- Every checklist ID in `mockup-parity.md` must appear in the report. Items for unbuilt phases are reported "Not built (Phase N)", not skipped silently.
- Stop the app you started when you finish, even after a failure.

## Procedure
1. Read `A_Codes/AF_e2e/mockup-parity.md`, the Part 0 build status and the BRD screen sections (§52–§56) in scope.
2. Prepare a reproducible state: set `MRM_TODAY_OVERRIDE` to the date recorded at the top of `mockup-parity.md`, run `.venv/Scripts/python -m app.cli reset` from `A_Codes/AB_backend`, then start the app with `A_Codes/AE_launcher/start_mrm.ps1` (or backend and frontend commands from Part 0). Wait until `http://127.0.0.1:5173` and `http://127.0.0.1:8000/api/health` (or the equivalent health route) respond.
3. Run `npx playwright test` from `A_Codes/AF_e2e`. The `mockup` project checks that each checklist item is present in the mock-up; the `app` project checks the same item in the application, signing in through the dev role picker with the role the item names.
4. For items that need judgement (layout, chart type, wording), open both and compare screenshots saved to `D_Reviews/DC_mockup_review/<YYYYMMDD>/<MUP-ID>_{mockup,app}.png`.
5. If a new built screen has no checklist items, add them to `mockup-parity.md` and the spec, with new IDs after the last one (never renumber).

## Statuses
**Match**, **Partial** (say what differs), **Missing**, **Accepted difference** (cite BRD §), **Not built (Phase N)**.

## Report
Write `D_Reviews/DC_mockup_review/<YYYYMMDD>_<scope>.md` with:
1. Setup: business date, seed counts, app commit, browser version.
2. Summary counts by status and by screen.
3. Table: `MUP-ID | Screen | Item | Role | Status | Evidence (screenshot / test) | Note`.
4. Findings: `MP-nn | Severity | MUP-ID | Difference | Suggested fix` — Missing on a built screen is High; Partial is Medium; cosmetic is Low.
5. Cross-screen consistency: every count that should agree between screens, with both values.

Return the report path and counts of Missing and Partial to the caller.
````

## Step 4 — Create the orchestrating command

Create `.claude/commands/review-build.md` verbatim:

````markdown
---
description: Run the three review agents and write one consolidated summary
argument-hint: "[scope: phase N | §section | criterion prefix]  (empty = everything built)"
---

Review the build. Scope: $ARGUMENTS (if empty, everything Part 0 lists as implemented).

1. Run the `requirements-reviewer` and `test-outcome-reviewer` agents in parallel, passing the scope.
2. When both finish, run the `mockup-parity-tester` agent with the same scope.
3. Read the three reports and write `D_Reviews/<YYYYMMDD>_summary.md` containing:
   - Overall verdict: **Ready** (no open Critical or High finding, all gates green) or **Not ready**.
   - Gate status and Proven / total criteria.
   - All Critical and High findings from the three reports in one table: `ID | Source | Severity | Criterion / MUP | Problem | Suggested fix`, deduplicated where two agents found the same thing.
   - Spec issues and the §81A decisions they touch.
   - Counts of Medium and Low findings, with links to the three reports.
4. Do not fix anything. Show me the summary table and ask which findings to fix.
````

## Step 5 — Create the Playwright harness in `A_Codes/AF_e2e/`

1. `package.json` with `@playwright/test` pinned to an exact version, `"private": true`, and scripts `"test": "playwright test"`, `"test:mockup": "playwright test --project=mockup"`, `"test:app": "playwright test --project=app"`.
2. `playwright.config.ts` with two projects:
   - `mockup`: `baseURL` = `file://` URL of `C_Requirements/_OLD/MRM_Governance_MIS_Demo.html` resolved from the repo root; `reducedMotion: 'reduce'` (stops the self-running walkthrough so screens render immediately); viewport 1440×900.
   - `app`: `baseURL` `http://127.0.0.1:5173`; viewport 1440×900.
   - `reporter`: list + html (output folder `playwright-report/`, git-ignored) + json to `D_Reviews/DC_mockup_review/latest.json`. Screenshots on failure. One worker (the app shares one database).
3. `helpers/` with `signInAs(page, role)` (uses the dev role picker) and `openMockupScreen(page, step)`. Mock-up hooks you can rely on: rail items `.step[data-i]` (0 Overview, 1 Policy, 2 Users, 3 Inventory, 4 History, 5 Documents, 6 CDE, 7 Results, 8 Rules, 9 Dashboards, 10 Report, 11 Copilot), `#bPlay`, `#stage`; dashboard tabs `.tabs button[data-t=cc|ops|da]`; model cards `.mcard[data-m]`, table rows `tr.click[data-m]`, Model 360 panel `#m360`, KPI tiles `.kpi`; Copilot input `#ci`, suggestions `#sugs button`, messages `#msgs`; report `#repDoc`. Confirm each hook in the file before using it.
4. `mockup-parity.md`: the checklist below. Put the fixed business date on the first line (use the date the demo files in `B_Inputs/AD_demo_files` were generated for; if unclear, ask me).
5. `tests/parity.spec.ts`: one `test()` per checklist ID, titled with the ID (`MUP-07 Operations Board phase filter`), with a `mockup` and an `app` branch. Items for screens not built yet use `test.fixme` with the reason "Not built (Phase N)" so they show in the report.
6. Add `node_modules/`, `playwright-report/`, `test-results/` to `.gitignore` (snapshot `.gitignore` first if the convention applies to it).

Starting checklist for `mockup-parity.md` (add IDs if you find screens it misses; never renumber):

| ID | Screen | Item | Role | Phase |
|---|---|---|---|---|
| MUP-01 | Command Center | KPI tiles: total models, in production, high-risk, overdue validations, open findings | Head of MRM | 8 |
| MUP-02 | Command Center | Donuts by tier and by lifecycle phase with percentage labels | Head of MRM | 8 |
| MUP-03 | Command Center | Lifecycle pipeline strip, click-through to filtered board | Head of MRM | 8 |
| MUP-04 | Command Center | Revalidation timeline by category (annual / bi-annual / quarterly / monthly) | Head of MRM | 8 |
| MUP-05 | Command Center | Regulatory / audit models and issues chart | Head of MRM | 8 |
| MUP-06 | Command Center | Insights panel (generated from rules, not hard-coded) | Head of MRM | 8 |
| MUP-07 | Operations Board | Filters: phase, tier, family, owner — counts update | Validator | 8 |
| MUP-08 | Operations Board | Board columns per lifecycle phase with model cards | Validator | 8 |
| MUP-09 | Operations Board | Table view with sortable columns and row click to Model 360 | Validator | 8 |
| MUP-10 | Model 360 | Header: ID, name, tier, owner, phase, next validation date | Validator | 3 |
| MUP-11 | Model 360 | Status chips and overdue badge | Validator | 3 |
| MUP-12 | Model 360 | Segregation-of-duties banner when developer = validator | Validator | 4 |
| MUP-13 | Model 360 | Lifecycle stepper with current phase | Validator | 3 |
| MUP-14 | Model 360 | Approval history and MRC decisions with notes | Validator | 4 |
| MUP-15 | Model 360 | Validation history with notes | Validator | 4 |
| MUP-16 | Model 360 | Findings list with severity, status, due date | Validator | 4 |
| MUP-17 | Model 360 | Score breakdown by component | Validator | 4 |
| MUP-18 | Model 360 | Backtesting grid and ROC / performance chart | Validator | 6 |
| MUP-19 | Model 360 | Monitoring KPIs with thresholds and Pass/Warn/Fail | Validator | 6 |
| MUP-20 | Model 360 | Linked CDEs | Validator | 7 |
| MUP-21 | Model 360 | Empty state for a model with no history (mock-up M-0089) | Validator | 3 |
| MUP-22 | Import | Template download for T01–T18 | Admin | 2 |
| MUP-23 | Import | T02 demo file preview: 4 loaded, 1 rejected, message names field and row | Admin | 2 |
| MUP-24 | Import | Load uses same path as preview; audit entry visible | Admin | 2 |
| MUP-25 | Documents | Upload and required-document checklist per phase | Validator | 3 |
| MUP-26 | Documents | AI extraction: proposed fields with confirm / drop | Validator | 5 |
| MUP-27 | Data Audit | CDE list with DQ scores by source | Data Owner | 7 |
| MUP-28 | Data Audit | DQ issue list and drill-down | Data Owner | 7 |
| MUP-29 | Report | Governance report generated and downloadable | Head of MRM | 8 |
| MUP-30 | Report | MRC report pack (no BRD requirement — see §81A D9) | Head of MRM | — |
| MUP-31 | Copilot | Ask a question, answer cites models / records from the app | Head of MRM | 9 |
| MUP-32 | Copilot | Suggested questions | Head of MRM | 9 |
| MUP-33 | All | Theme colours, no drop shadows, no horizontal scroll at 1440×900 | any | 8 |
| MUP-34 | All | Counts agree across Command Center, Operations Board and Model 360 | any | 8 |
| MUP-35 | All | Actions not permitted for the role are hidden and refused by the API | Viewer | 1 |

The Phase column follows the §81 phase numbers; correct any that do not match CLAUDE.md and tell me.

## Step 6 — Update the setup script

Snapshot first: `bash A_Codes/AZ_tools/snapshot.sh A_Codes AE_launcher/setup_first_time.ps1`. Then make the script require Python 3.14 (fail with a clear message on any other version, since CI and `requirements-lock.txt` use 3.14), and add a step that runs `npm ci` (or `npm install` if there is no lock yet) in `A_Codes/AF_e2e` and `npx playwright install chromium`. Do **not** add the harness to CI.

## Step 7 — Dry run

Run `/review-build` once with no scope. Do not fix any finding. Commit on a new branch `review-agents` (not `main`) with the new folders, agents, command, harness, setup-script change and snapshot, and the first three reports plus summary.

## Acceptance

- `/agents` lists `requirements-reviewer`, `test-outcome-reviewer`, `mockup-parity-tester`.
- `npx playwright test --project=mockup` passes for every item the mock-up contains.
- `git diff main --stat` shows no changes under `A_Codes/AB_backend`, `A_Codes/AC_frontend`, `A_Codes/AD_seed` or `B_Inputs/`; the only change under `A_Codes/AE_launcher` is `setup_first_time.ps1` plus its `_OLD` snapshot.
- `D_Reviews/` contains the three reports and `<YYYYMMDD>_summary.md`.

## Report back to me

1. The summary table of Critical and High findings.
2. Any checklist phase numbers you corrected and any mock-up hooks that did not exist.
3. Anything in the new CLAUDE.md that conflicts with the code.
4. Whether `requirements-lock.txt` installs cleanly on Python 3.14 locally.
5. A reminder that Phase 2A (§12A, SR 26-2) is next in the build order and needs no decision, and that §81A decisions D1–D7 must be recorded before Phase 6 starts. Do not start Phase 2A in this session.
