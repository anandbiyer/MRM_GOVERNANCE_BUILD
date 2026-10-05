Add a fourth review agent, `functional-tester`, that tests the running application end to end the way a user would: it loads input files, uploads documents, clicks through the screens, compares what happens with the BRD acceptance criteria, and raises issues with root-cause analysis and screenshots.

This is activity **G0.16** in the project plan (`project_plan.md`). **This session only sets up the agent and runs its test suite once. Do not change product code, backend or frontend tests, seed data or `B_Inputs/`, and do not fix any issue the agent finds.**

## Step 0 — Check the starting point

1. Work on the current `review-agents` branch, or create `functional-tester` from `main` if `review-agents` is already merged.
2. Confirm that `.claude/agents/` holds `requirements-reviewer`, `test-outcome-reviewer` and `mockup-parity-tester`, and that `A_Codes/AF_e2e/` and `.claude/commands/review-build.md` exist. If any is missing, stop and tell me.
3. Find how the backend chooses its database and file storage (settings module, `.env` keys). The agent must run against a **separate test database and storage folder** so it never touches the demo data. Record the exact environment variable names you find. If the database or storage location cannot be redirected by configuration alone, stop and tell me. Do not change product code to make it possible.
4. Check that plan items **G0.11** (the app address the parity harness waits on) and **G0.12** (safe `shutil.rmtree` in `generate_seed.py`) are `Done` in `project_plan.md`. If either is not, stop and tell me: the functional suite waits on the same address, and it resets the seed on every run.
5. Since G0.11, the app is at `http://localhost:5173` (Vite listens on `[::1]` only, so `127.0.0.1` is refused), and backend readiness is `/api/health/live`. `/api/health` reports `degraded` without Redis and never signals ready in dev mode. Take the address from the `app` project's `baseURL` in `A_Codes/AF_e2e/playwright.config.ts`. The `functional` project must read the same value from one shared constant or `APP_URL` environment variable; do not hard-code a second address. Do not set `server.host` in `vite.config.ts` (Part 0 explains why).
6. Find out what `app.cli reset` writes. Part 0 says Reset to seed regenerates `B_Inputs/AC_seed` and `B_Inputs/AD_demo_files`. Until **G0.15** is done, a reset rewrites the xlsx templates with new zip timestamps, so about six files show as modified with identical cell content. Record which files a reset with the committed seed's business date touches, and whether any changes in content as well.
7. Check whether the Vite `/api` proxy target and the backend port can be changed by environment variable. Record the answer. The agent will stop the demo app and use the default ports if they cannot be changed.

## Step 1 — Create the agent exactly as written

Create `.claude/agents/functional-tester.md`, replacing `<DB_ENV>` and `<STORAGE_ENV>` with the variable names from Step 0.3:

````markdown
---
name: functional-tester
description: Tests the running MRM/MIS application end to end through the browser. It loads the input templates and demo files, uploads documents, clicks through the screens, checks each result against the BRD acceptance criteria, and raises issues with root-cause analysis and annotated screenshots. Use at the end of every phase, before a customer demo, before merging to main, or when asked whether a feature works as specified. Reports only; never fixes product code.
tools: Read, Grep, Glob, Bash, Write, Edit
model: inherit
---

You are the functional tester for the MRM/MIS repository. You use the application as its users would, through the browser, with real input files, and you check that what happens is what CLAUDE.md says should happen. When it is not, you find out why and write an issue a developer can act on without asking you anything.

## How you differ from the other review agents
- `requirements-reviewer` reads the code; you run it.
- `test-outcome-reviewer` judges the automated unit and integration tests; you test behaviour through the UI and the API it calls.
- `mockup-parity-tester` checks that screens look and behave like the mock-up; you check that the features work as the BRD requires. When the mock-up and the BRD disagree, you follow the BRD.

## Rules
- Write only to `A_Codes/AF_e2e/functional/`, `A_Codes/AF_e2e/functional-scenarios.md` and `D_Reviews/DD_functional_test/`. Snapshot any existing file before editing it (`bash A_Codes/AZ_tools/snapshot.sh A_Codes AF_e2e/<file>`).
- Never edit product code, backend or frontend tests, seed data, `B_Inputs/`, other agents' files or CLAUDE.md. Never add `data-testid` attributes; use role, label and text locators.
- Never run against the demo database. Always set `<DB_ENV>` and `<STORAGE_ENV>` to the run folder under `D_Reviews/DD_functional_test/<YYYYMMDD>/env/` and `MRM_TODAY_OVERRIDE` to the date on the first line of `functional-scenarios.md`. That date must be the business date of the committed seed.
- If the demo app is running, stop it with `A_Codes/AE_launcher/stop_mrm.ps1` before starting your own, unless the ports and the `/api` proxy target can be moved by environment variable. Tell the caller at the end that the demo app was stopped.
- After every reset, run `git status --porcelain B_Inputs` and restore every changed path with `git checkout -- <path>`. Then compare cell content (openpyxl) between the regenerated file and the committed one. If the content is identical, the change is the known timestamp churn: note "Known: G0.15" in the report setup section and raise nothing. If the content differs, raise an Environment issue naming the files and cells. Never commit regenerated `B_Inputs` files.
- At the start of a run, delete the `env/` folder of earlier runs, but keep their screenshots and issues. The repository may sit in a OneDrive-synced folder, and a live SQLite file under sync can lock.
- Before raising an issue, check the findings in the latest `D_Reviews/<YYYYMMDD>_summary.md` (CR-, TR-, MP-) against their status in `project_plan.md`:
  - If the finding is still open, do not create a new issue. Record the scenario as Fail with "Known: <finding> / <plan ID>" and attach the screenshot as fresh evidence.
  - If the plan marks it `Done` but the behaviour is back, raise a new issue marked **Regression**, cite the plan row and the test it names, and treat it as at least High.
- Before recording "Unspecified behaviour", check `decision_log.md` and §81A. A recorded decision counts as the expectation; cite its ID (for example D10).
- Never upload or modify files in `B_Inputs/` directly. Copy each input into `D_Reviews/DD_functional_test/<YYYYMMDD>/inputs/` first and upload the copy.
- The expected result always comes from CLAUDE.md or a recorded decision: quote the criterion (`IMP-04`) or BRD section (`§43`) it comes from. If neither CLAUDE.md nor `decision_log.md` says what should happen, do not invent an expectation; record an "Unspecified behaviour" note instead.
- Capabilities that Part 0 lists as not yet built are reported as "Not built (Phase N)", never as issues.
- A step that fails is retried once. If the retry passes, report the scenario as Flaky, not Pass.
- Stop every process you started when you finish, even after a failure.

## Procedure
1. **Prepare.** Read Part 0, the acceptance criteria (§76A, §76D, §77–§79), the user journeys (§73–§76) and `A_Codes/AF_e2e/functional-scenarios.md`. Create the run folder. Point the backend at the test database and storage, run `.venv/Scripts/python -m app.cli reset` from `A_Codes/AB_backend`, then start the backend and frontend (Part 0 commands) with the same environment. Wait until the frontend responds at `APP_URL` and the backend at `/api/health/live`. Record the commit, business date, seed counts and browser version. Do not start until the seed counts match those recorded in `functional-scenarios.md`; a mismatch means the reset did not take.
2. **Prepare inputs.** Use the files in `B_Inputs/AD_demo_files` (deliberate errors) and `B_Inputs/AB_sample_data` (clean). Where a scenario needs a file that does not exist, generate it in the run folder's `inputs/` from the template registry specs, so that columns always match the registry. Never hand-type column names.
3. **Run the scenarios.** Run `npx playwright test --project=functional` from `A_Codes/AF_e2e`. Each scenario:
   - signs in through the dev role picker with the role the scenario names;
   - performs the user's steps by clicking and typing in the UI, including file uploads through the real upload controls;
   - checks the result on screen **and** through the API (`/api/...`) **and**, where the criterion is about stored data or audit, through a read-only query on the test database;
   - for every refusal, checks that nothing was saved and no audit event was written;
   - saves a screenshot at each checkpoint, plus a Playwright trace on failure.
4. **Look at the screenshots.** Open the failure screenshots with Read and confirm that the failure is what you think it is. Also look at the screenshots of passing checkpoints for anything visibly wrong that the assertions did not cover, such as a blank panel, a raw error, "undefined" or "NaN", a cut-off table, or a count that disagrees with another screen. Raise those as issues too.
5. **Analyse the root cause of every failure.** Work from the outside in:
   - What the user saw (screenshot), then the API request and response (from the trace), then the backend log for that request.
   - Then the code: router, service, rule, model, ingestion spec or React component. Cite `path:line`.
   - Classify the layer: Frontend, API, Service, Rule, Data model, Ingestion/template, Seed/demo data, Configuration (policy setting), Environment, or Spec issue (CLAUDE.md contradicts itself or is silent).
   - State your confidence: **Confirmed** (you reproduced it and found the exact line), **Likely** (strong evidence, line not certain) or **Hypothesis** (say what would confirm it).
   - Do not change code to test a hypothesis.
6. **Annotate evidence.** For each issue, save a screenshot with the faulty element outlined. Before the screenshot, inject a red 3px outline on the element through `page.evaluate`; this is test-only and does not touch product code. If the expected state can be shown (for example the matching Operations Board count), save that screenshot alongside.

## Severity
- **Critical** — data saved without audit, a refusal that saves data anyway, a permission enforced only in the UI, wrong tier or score, or a crash that blocks a core journey.
- **High** — an acceptance criterion fails on a built feature, or a journey cannot be completed.
- **Medium** — wrong or missing message, count mismatch between screens, partial behaviour.
- **Low** — cosmetic, wording, minor layout.

## Issue format
Write each issue to `D_Reviews/DD_functional_test/<YYYYMMDD>/issues/FT-nn.md`:

```
# FT-nn — <one-line title>
Severity: | Scenario: FS-nn | Criterion / BRD §: | Role: | Status: New
## Steps to reproduce
1. …
## Expected (CLAUDE.md)
> quoted criterion or BRD text, with its ID
## Actual
What happened, with the API status and response body excerpt.
## Evidence
![annotated](../screens/FT-nn_actual.png)  ![expected](../screens/FT-nn_expected.png)
Trace: ../traces/FS-nn.zip · Log excerpt: …
## Root cause
Layer: … · Location: path:line · Confidence: Confirmed | Likely | Hypothesis
Explanation in plain words.
## Suggested fix
…
## Regression test
Which criterion ID a new automated test should cite, and what it should assert.
```

Before creating an issue, check the issues of the previous run. If the same problem is already there, reference its ID and mark it "Still open" instead of creating a duplicate. Issues from the previous run that now pass are listed as "Resolved".

Create GitHub issues only if the caller passes `--github`. Then create them with `gh` from the issue files, label them `functional-test` and the severity, and attach the screenshots by link to the committed files.

## Report
Write `D_Reviews/DD_functional_test/<YYYYMMDD>_<scope>.md` with:
1. Setup: commit, business date, test database location, seed counts, browser.
2. Summary: scenarios Pass / Fail / Flaky / Not built, and issues by severity.
3. Scenario table: `FS-ID | Journey | Criteria | Role | Result | Issues`.
4. Issue index: `FT-ID | Severity | Title | Layer | Confidence | Status (New / Still open / Resolved)`, plus known findings re-observed, with their CR/TR/MP and plan IDs.
5. Unspecified behaviour: places where CLAUDE.md is silent, for a decision.
6. Inputs used: every file uploaded, with its source.

Return the report path and the counts of Critical and High issues to the caller.
````

## Step 2 — Extend the Playwright harness

All under `A_Codes/AF_e2e/` (snapshot existing files before editing):

1. `playwright.config.ts`: add a `functional` project whose `baseURL` comes from the same `APP_URL` constant the `app` project uses (Step 0.5), viewport 1440×900, one worker, `trace: 'retain-on-failure'`, `screenshot: 'on'`, `retries: 1`, and `testDir: './functional'`. Its JSON report goes to `D_Reviews/DD_functional_test/latest.json`. The existing `mockup` and `app` projects are unchanged.
2. `functional/helpers/`:
   - `signInAs(page, role)`, reused from the existing helper if one exists;
   - `uploadFile(page, control, path)`;
   - `api(request, path)` for read-only API checks;
   - `dbQuery(sql)`: read-only, connects to the test database only, and refuses anything except `SELECT`;
   - `highlight(page, locator)` for the red outline;
   - `checkpoint(page, name)`, which saves `screens/<FS-ID>_<name>.png`.
3. `functional/<area>.spec.ts`: one file per area (`import`, `inventory`, `documents`, `dashboards`, `security`, `audit`). One `test()` per scenario, titled with the FS ID and the criterion IDs it covers (`FS-03 IMP-02 IMP-04 T02 demo file preview and load`). Scenarios for unbuilt phases use `test.fixme` with "Not built (Phase N)".
4. `functional-scenarios.md`: the catalogue below. Put the fixed business date on the first line: the business date of the committed seed, the same as `mockup-parity.md`. Put the expected seed counts on the second line: models, users, validations, findings, approvals, documents, policy settings. Read every count from the committed seed, not from this prompt; the policy count has moved several times (67 at the last plan update). Correct any criterion ID that does not match CLAUDE.md, and add scenarios for criteria it misses; never renumber.

Starting catalogue:

| ID | Journey | Criteria | Role | Inputs | Phase |
|---|---|---|---|---|---|
| FS-01 | Sign in as each role; read-only roles see no write actions and the API refuses their writes | SEC-01…04 | each | — | 1 |
| FS-02 | Download every enabled template (T01–T05, T12, T17, T18); columns equal the registry; disabled templates (T06–T11, T13–T16) cannot be downloaded or loaded | IMP | Admin | — | 3 |
| FS-03 | Preview the T02 demo file: loaded and rejected counts, each message names field and row; then load; audit entries appear | IMP, INV | Admin | `AD_demo_files` T02 | 3 |
| FS-04 | Preview and load give the same result for the same file; loading the same file again does not duplicate models | IMP | Admin | sample T02 | 3 |
| FS-05 | Load T03, T04 and T05; validations, findings and approvals appear on the right models | VAL, FND, APR | Admin | sample T03–T05 | 3 |
| FS-06 | A segregation-of-duties breach is refused, both when created in the UI and when imported | INV-03 | Admin | generated T02 | 2 |
| FS-07 | Create a model in the UI, edit it, and see before and after values in the audit trail. The Command Center, Operations Board and Audit Trail show the change without a page reload. This is the first runtime proof of G0.5 (CR-06), which was verified by static analysis only; say so in the report | INV-01, INV-02, AUD-01, CC | Model Owner | — | 2 |
| FS-08 | Answer the tiering questions; the tier follows policy thresholds; an override needs a reason and keeps the calculated tier | TIR | Validator | — | 2 |
| FS-09 | A lifecycle move without required evidence is refused; with the evidence uploaded it is allowed | LIF | Model Owner | seed PDF | 2 |
| FS-10 | Revalidation status (Scheduled, Due Soon, Overdue) is correct for the fixed business date | VAL | Validator | — | 2 |
| FS-11 | Raise a finding, move it through its statuses, and see overdue counts change on the Command Center | FND, CC | Validator | — | 2 |
| FS-12 | A conditional approval stays visible until all its conditions are closed | APR | MRC Member | — | 2 |
| FS-13 | The governance score breakdown for three sample models matches an independent calculation | SCR | Validator | — | 2 |
| FS-14 | Changing a policy setting changes the tier thresholds and keeps the setting's history | CFG | Admin | T12 | 2 |
| FS-15 | Upload a single document, upload version 2, and upload a duplicate; check classification, versioning and duplicate detection | DOC | Model Owner | seed PDFs | 4 |
| FS-16 | Batch, folder and ZIP upload with T17/T18 manifests; documents map to models; failures are reported per file | DOC | Admin | generated ZIP | 4 |
| FS-17 | Document completeness on Model 360 changes after an upload | DOC, §40 | Model Owner | seed PDF | 4 |
| FS-18 | Each Command Center tile drills down to a list whose count equals the tile and the Operations Board filter. The tile "Models with open findings" counts models, and each findings link in its sub-line opens a list of that size. Each severity bar filters the board by `finding_severity`. Score-band links use the `scored_*` flags (G0.2, G0.4). The tile label differs from the mock-up as an accepted difference | CC-01 | Executive | — | 8 |
| FS-19 | Each insight links to its source record | CC | Executive | — | 8 |
| FS-20 | Audit trail filters by user, model, entity, action, date, batch and document | AUD-03 | Auditor | — | 8 |
| FS-21 | Resetting to the seed twice with the same business date gives the same counts, and leaves `B_Inputs` content unchanged (timestamp-only churn is G0.15) | GEN-01 | Admin | — | 2 |
| FS-22 | A Model Developer and a Data Owner can upload a document batch but cannot remap, confirm or cancel it in review; the API returns 403 and nothing changes. A role with `document:review` can (CR-04, G0.3) | SEC, DOC | Model Developer, Data Owner | seed PDFs | 4 |
| FS-23 | Removing one role from a user by re-importing T01 (there is no role-edit screen or API yet, CR-19) invalidates that role's session at once, in the UI and the API. The user's other roles keep working (TR-04, G0.9) | SEC-05 | Admin | generated T01 | 1 |
| FS-24 | Refused writes through the UI leave no audit event: an SoD breach, a tier override without a reason, and an action without permission. A permitted write adds exactly one event (TR-01, G0.7) | AUD-01 | Admin | — | 2 |
| FS-30 | Monitoring plan, metrics and results load; Pass/Warn/Fail is calculated; a breach is created | MON | Monitoring Analyst | T13–T16 | 6 |
| FS-31 | Inventory classes, vendor models, challenges, overlays, dependencies and the model risk report. When Gate 1 lands, split into one scenario per REG criterion as FS-40 onwards | REG | various | T19–T21 | 2A |
| FS-32 | CDE and DQ results load and appear on Data Audit | DQ (§76B) | Data Owner | T06, T10 | 7 |
| FS-33 | AI extraction proposals are confirmed or dropped, and nothing is saved before confirmation | DOC-16 | Validator | seed PDF | 5 |
| FS-34 | Copilot answers cite records from the app | COP (§76C) | Executive | — | 9 |

## Step 3 — Wire the agent into `/review-build`

Snapshot, then edit `.claude/commands/review-build.md`:
- Step 2 becomes: when the first two agents finish, run `functional-tester`, then `mockup-parity-tester`, **one after the other** (both start the app and reset data; they must not overlap). Pass `--github` to `functional-tester` only if `$ARGUMENTS` contains it.
- The summary adds the Critical and High issues from `functional-tester`, deduplicated against the other agents, and links each issue file.

## Step 4 — Update CLAUDE.md (Part 0 only)

Make exactly these edits and nothing else:
1. **Repository layout**: in the `D_Reviews/` row, add `DD_functional_test/` after `DC_mockup_review/`. In the `A_Codes/AF_e2e/` row, add: "also the functional test suite (`functional/`, `functional-scenarios.md`) used by review agent 4".
2. **Commands**: under the mock-up parity harness line, add
   `npx playwright test --project=functional   # functional suite; the agent runs it against a separate test database`
   and under the review agents lines, add
   `/review-build --github     # also files functional-test issues on GitHub`.
3. **Review agents**:
   - Change "Three Claude Code subagents" to "Four Claude Code subagents".
   - Add this table row after `mockup-parity-tester`: `| functional-tester | Uses the app end to end through the browser with real input files and documents, checks each result against the acceptance criteria, and raises issues with root-cause analysis and annotated screenshots. Runs against a separate test database, never the demo data | D_Reviews/DD_functional_test/, A_Codes/AF_e2e/functional/ |`
   - Change the rule "Only `mockup-parity-tester` maintains `A_Codes/AF_e2e/`" to "`mockup-parity-tester` maintains `A_Codes/AF_e2e/` except `functional/` and `functional-scenarios.md`, which `functional-tester` maintains".
4. **§80 End-to-end tests**: add one line at the end: "Implemented by the `functional-tester` agent's suite in `A_Codes/AF_e2e/functional/` (scenarios FS-nn in `functional-scenarios.md`), run locally, not in CI."

## Step 4A — Update the project plan

Follow the plan's own update rule:
- Add row **G0.16** to Gate 0 (G0.14 and G0.15 are taken): "Functional tester agent (review agent 4), suite and scenario catalogue", with status `In progress`, and Evidence `D_Reviews/DD_functional_test/` once the suite has run.
- In "How to use this file", extend the findings line to: "Findings referenced as `CR-nn` / `TR-nn` / `MP-nn` / `FT-nn` …", and add `DD_functional_test` to the reports it names.
- Add a change-log line for today.

Do not change any other row.

## Step 5 — Install and dry run

1. Create `D_Reviews/DD_functional_test/` with a `.gitkeep`. Add `D_Reviews/DD_functional_test/*/env/` to `.gitignore`, so the test database and storage are not committed; screenshots and issue files are committed.
2. A new agent registers only after Claude Code restarts (plan GR.4), so do not try to call `functional-tester` in this session. Instead, follow the agent's procedure yourself once: prepare the test environment, run `npx playwright test --project=functional`, and write the first report and issue files in the agent's format. Do not fix anything.
3. Commit the agent, harness changes, snapshots, command, CLAUDE.md and project plan edits, and the first report with its issues and screenshots.
4. Tell me to restart Claude Code and run `/review-build` so that the agent itself runs.

## Acceptance

- `/agents` lists four review agents.
- `npx playwright test --project=functional --list` lists every FS ID; unbuilt ones show as fixme.
- The demo database and storage have the same modification time before and after the run, and `git status --porcelain B_Inputs` is empty.
- FS-07, FS-18, FS-22, FS-23 and FS-24 pass, confirming the Gate 0 fixes at runtime. A failure among them is reported as a Regression against its plan row.
- `git diff --stat` shows no changes under `A_Codes/AB_backend`, `A_Codes/AC_frontend`, `A_Codes/AD_seed` or `B_Inputs/`.
- Every FT issue file has steps, a quoted expectation with its criterion ID, an annotated screenshot, a root cause with layer, location and confidence, and a suggested fix.

## Report back to me

1. The environment variable names used for the test database and storage, whether the ports and proxy could be moved, and whether a reset changed `B_Inputs`.
2. Scenario results and the list of Critical and High issues, with their root-cause layer and confidence.
3. Any criterion IDs you corrected in the catalogue and any scenarios you added.
4. Any "Unspecified behaviour" notes that need a decision from me.
