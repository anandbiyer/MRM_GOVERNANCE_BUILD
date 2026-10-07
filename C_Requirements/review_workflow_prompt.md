Make the review agents run at a few defined points in the plan, not continuously and not only when I remember to ask. Today they run only when someone asks. The last full review was on 2 October, and fourteen Gate 0 items have landed since then.

The aim is to **review at the points where a missed problem is expensive, and nowhere else.** Ordinary activities are finished with the normal tests (pytest, `npm run build`) and need no review agent.

**Do not change product code, tests, seed data or `B_Inputs/`. Snapshot any existing file under `A_Codes/` before editing it. Work on the current branch.**

Run this after `C_Requirements/phase2a_deferral_prompt.md`. That prompt deferred Phase 2A (decision D12), except a core Model Risk Report in rows G1.16–G1.18. Use the row IDs it actually assigned; the IDs below assume G1.16–G1.18.

The functional tester (G0.16) exists. Its first run (`D_Reviews/DD_functional_test/20261005_all.md`) has already been triaged by hand into G0.17, G0.18, G0.19 and harness defects H-01 to H-10, and it found **0 product defects**. Gate 0 has been growing, because each fix turns up the next edge case and every finding lands in Gate 0. So this session also **freezes Gate 0's scope** (Step 6). It does not run the Gate 0 exit review.

## The review points

There are four review points, and nothing runs outside them.

| # | Review point | When | Agents | Needs the app? | Why here |
|---|---|---|---|---|---|
| R1 | **Schema checkpoint** | Right after a gate's migration activity is done, before the services are built on it (Gate 1: after G1.16, the core report migration; Gate 3: after G3.1; Gate 4: after G4.1; Gate 5: after G5.1. G1.1 gets one too if Phase 2A resumes) | `requirements-reviewer` only, scoped to the new tables against §48 and the gate's templates | No | A wrong column or key is cheap to fix now and expensive once services, imports and seed data depend on it |
| R2 | **Risk checkpoint** | When an activity changes permissions, audit, or the score or tier calculation: its criteria include SEC, AUD, SCR or TIR, or its text names a permission or "same transaction" | `test-outcome-reviewer` only, scoped to that activity's criteria | No | These are the areas where a green test that proves nothing does real harm. Each one is a few minutes and runs no app |
| R3 | **Gate exit** | When the last activity of a gate is `Done` | `/review-build`, scoped to the gate. Which agents run depends on the gate (table below) | Only if a tester runs | Confirms the gate as a whole before the next one builds on it |
| R4 | **Before merging to `main` or a customer demo** | On request, or when a merge or push to `main` is attempted | Nothing new if the last R3 is Ready **and** reviewed the same commit. Otherwise the R3 set for the current gate | Only if a tester runs | The only point the hook enforces |

Nothing runs per commit, per file or per ordinary activity. The schema and risk checkpoints use only the static reviewers, which never start the app. The testers that start the app (`functional-tester`, `mockup-parity-tester`) run only at gate exit and before a demo.

### Which agents run at each gate exit (R3)

| Gate | `requirements-reviewer` | `test-outcome-reviewer` | `functional-tester` | `mockup-parity-tester` |
|---|---|---|---|---|
| 0 — close the review | ✓ | ✓ | ✓ | ✓ (first run since G0.4 changed MUP-01) |
| 1 — core Model Risk Report (while D12 holds) | ✓ | ✓ | ✓ (FS-25) | ✓ (MUP-29; MUP-30 partial) |
| 1 — rest of Phase 2A (when D12 is lifted) | ✓ | ✓ | ✓ | ✓ (MUP-30) |
| 2 — decisions D1–D7 | — | — | — | — |
| 3 — Monitoring | ✓ | ✓ | ✓ | ✓ (MUP-18, MUP-19) |
| 4 — Data Audit | ✓ | ✓ | ✓ | ✓ (MUP-20, 27, 28) |
| 5 — AI extraction | ✓ | ✓ | ✓ | ✓ (MUP-26) |
| 6 — Copilot | ✓ | ✓ | ✓ | ✓ (MUP-31, MUP-32) |
| 7 — hardening | ✓ | ✓ | ✓ | ✓ |

Gate 2 is decisions only, so it has no review. At each exit, `requirements-reviewer` and `test-outcome-reviewer` are scoped to the gate's own criteria, while the CI gates and the functional suite run in full. That catches regressions elsewhere without re-reviewing finished work line by line.

**Skip rule:** if a review point's scope has not changed since its last review — the same `git write-tree` for the files in scope — the review is skipped, and the earlier report is cited.

## Step 1 — Add the review points to CLAUDE.md Part 0

In the "Review agents" section, replace the rule "Run `/review-build` at the end of every phase and before merging to `main`" with:

```
### When reviews run — and when they do not

Reviews run only at four points. Ordinary activities finish with the normal tests and no review agent.

- **R1 Schema checkpoint.** Right after a gate's migration activity (G1.16 for the core report, G3.1,
  G4.1, G5.1; G1.1 if Phase 2A resumes), run
  `/review-checkpoint schema <ID>` before building services on the new tables.
- **R2 Risk checkpoint.** When an activity's criteria include SEC, AUD, SCR or TIR, or it changes a
  permission or what is written in the same transaction as an audit event, run
  `/review-checkpoint risk <ID>` before marking it `Done`.
- **R3 Gate exit.** When the last activity of a gate is `Done`, run `/review-build gate <N>` and record
  the verdict in the gate's exit row. The gate closes only on **Ready**.
- **R4 Merge to main or customer demo.** Needs a Ready gate review of the same commit. The hook in
  `.claude/settings.json` enforces this; if it blocks you, run the review it names.

Do not run review agents at any other time unless I ask. A checkpoint whose scope has not changed since
its last review is skipped, and the earlier report is cited.
```

Also correct the restart note. Claude Code picks up new and edited agent files within a few seconds. A restart is needed only when the first file is created in a new `.claude/agents/` folder, which is what happened in GR.4. Update the note in the "Review agents" section to say so.

## Step 2 — Tie the agents' descriptions to the review points

Claude Code decides when to hand work to an agent from the agent's `description:` field. Broad wording such as "use proactively after code changes" would make reviews run continuously, which is exactly what we want to avoid. In each file under `.claude/agents/`, replace the "Use at / Use when …" sentence of the `description:` line with the wording below, and change nothing else in the file.

- `requirements-reviewer`: "Use only at a schema checkpoint (right after a gate's migration activity), at a gate exit, or when explicitly asked. Do not use after ordinary code changes."
- `test-outcome-reviewer`: "Use only at a risk checkpoint (an activity touching SEC, AUD, SCR or TIR criteria), at a gate exit, or when explicitly asked. Do not use after ordinary code changes."
- `mockup-parity-tester`: "Use only at a gate exit, before a customer demo, or when explicitly asked."
- `functional-tester` (if present): "Use only at a gate exit, before merging to main, before a customer demo, or when explicitly asked."

## Step 3 — Commands

### 3a. New `.claude/commands/review-checkpoint.md`

````markdown
---
description: Schema or risk checkpoint for one plan activity (R1 or R2)
argument-hint: "schema <plan ID> | risk <plan ID>"
---

Checkpoint: $ARGUMENTS

1. Find the plan ID's row in `project_plan.md`. If it cannot be found, stop and say so.
2. Work out the scope:
   - **schema**: the tables and columns the activity's migration adds, the §48 entries for them, and the templates of the same gate that will load them.
   - **risk**: the activity's criteria IDs. If the row names a finding instead (CR-, TR-, MP-), use the criteria that finding cites.
3. Skip check: compute `git write-tree` over the files in scope. If `D_Reviews/review_state.json` already holds a checkpoint for this ID with the same tree, say "No change since <date>; citing <report>" and stop.
4. Run one agent: `requirements-reviewer` for schema, `test-outcome-reviewer` for risk. Name the report `<YYYYMMDD>_<ID>_<schema|risk>.md`.
5. Report the findings for this activity in one table: `ID | Severity | Criterion / table | Problem | Suggested fix`. Findings outside the scope are listed under it, but are not this activity's to fix.
6. With no open Critical or High finding, add the report path to the row's Evidence column. Otherwise list what must be fixed first, and leave the plan unchanged.
7. Record the checkpoint in `D_Reviews/review_state.json`. Do not fix anything.
````

### 3b. Edit `.claude/commands/review-build.md` (snapshot first)

- Accept `gate <N>` as a scope. Take the agents for that gate from the R3 table in CLAUDE.md. Scope `requirements-reviewer` and `test-outcome-reviewer` to the gate's activities and criteria, and run the CI gates and the functional suite in full.
- Run the two static reviewers in parallel. Then run `functional-tester` and `mockup-parity-tester` one after the other: both start the app and reset data, so they must not overlap.
- Apply the skip rule. If the last Ready gate review has the same `head` as the current commit, say so and stop.
- After writing the summary, record the gate result in `D_Reviews/review_state.json` (verdict, summary path, `head` = the commit reviewed). If the gate has an exit row in the plan, put the verdict and summary path in its Evidence column.
- Replace the last step ("Show me the summary table and ask which findings to fix") with: "Show me the summary table, then run `/triage-review` on this summary."
- Do the same at the end of `/review-checkpoint`: if it found anything, finish with `/triage-review` on its report.

### 3c. New `.claude/commands/triage-review.md` — turning findings into plan work

Every review ends in triage. Reports never feed development directly; triage decides what each finding becomes, and **I approve that before the plan changes**.

````markdown
---
description: Turn the findings of the latest review into plan rows, decisions or closures
argument-hint: "[summary or report path]  (empty = the latest D_Reviews summary or checkpoint report)"
---

Triage: $ARGUMENTS

1. Findings discovered while fixing something else go through triage too; they are not added to the gate directly. Collect every finding that is not yet triaged from the report(s): CR-, TR-, MP- and FT- IDs, harness defects (H-) and any items a report raises "for a decision" or as "Unspecified behaviour". For FT issues, read each `issues/FT-nn.md`, including its root cause and its regression-test suggestion. Merge duplicates (the same root cause found by two agents) into one item that lists all the IDs.
2. Propose one disposition per item, using these rules:
   | Finding | Disposition |
   |---|---|
   | Critical or High, in a built area or the current gate, that affects data integrity, security or what a demo shows | **Fix now**: a new row in the current gate. It blocks that gate's exit |
   | Regression (a `Done` row's behaviour is back) | **Fix now**, in the current gate, citing the original row |
   | Medium or Low, in a built area, or anything that only a test harness, a polling client or an edge case of a dev-only operation would hit | **Backlog**: a row in the plan's Backlog section (`BL.n`), naming the gate or activity that should pick it up. Never added to the current gate |
   | Belongs to a capability not built yet | **Attach** to the existing row of the gate that builds it (Note column); no new row |
   | Spec issue or "Unspecified behaviour" | **Decision**: a new §81A decision (next D number) and a `decision_log.md` entry marked Open. Fixed only after it is decided |
   | Works as specified | **Not a defect**: closed with the reason |
   | Harness defect (H-) or a test-environment problem | **Harness**: listed under the row that owns that harness (G0.16 for the functional suite, G0.13 for the parity harness). No new row unless the fix needs a decision |
3. Show me the proposal in one table: `Item | Source IDs | Severity | Root cause (layer, confidence) | Proposed disposition | Plan row or decision`. Ask me to approve it, change it, or reject items. Change nothing until I answer.
4. When I approve, apply it:
   - Add plan rows with the next free IDs. Activity: the fix in one line. Finding: the source IDs. Status: `Not started`. Note: the issue path and, for FT items, "Regression test: <criterion> — <assertion>" taken from the issue.
   - Set the `Status:` line of each FT issue file to `Planned (<row ID>)`, `Decision (<D-ID>)` or `Not a defect — <reason>`. For CR, TR and MP findings, add the disposition to the summary's triage section instead.
   - Add a change-log line to the plan.
5. Do not fix anything.
````

**How a planned fix is done and closed.** This goes in CLAUDE.md Part 0, under the review points.

```
### Fixing review findings

- A finding is fixed through its plan row, like any other activity.
- **Scope freeze.** Something new you discover while fixing a row is not fixed on the spot and not added
  to the current gate. Log it, finish the row, and let `/triage-review` place it. Only Critical or High
  issues that affect data integrity, security or the demo enter the current gate; the rest go to the
  Backlog.
- Write the regression test the issue names first, cite the criterion ID, and confirm it fails. Then fix
  the code, and confirm the test passes.
- For FT issues, rerun only the affected scenario: `npx playwright test --project=functional -g "FS-nn"`.
  If it passes, set the issue's Status to `Fixed (<commit>)`. Do not rerun the whole suite or call a
  review agent for this.
- If the fix touches permissions, audit, score or tier, it also gets a risk checkpoint (R2).
- At the next gate exit, the functional tester reruns everything and moves `Fixed` issues to `Verified`,
  or reopens them as `Regression`. The plan row becomes `Done` only once the issue is `Verified`, or
  for CR, TR and MP findings, once the gate review no longer reports it.
```

**Issue statuses.** In `.claude/agents/functional-tester.md`, change only the issue format's `Status:` line and the rule about previous runs, so that the lifecycle is: `New` → `Planned (<row>)` / `Decision (<D-ID>)` / `Not a defect` → `Fixed (<commit>)` → `Verified`, or back to `Regression`. On each run the agent:
- moves `Fixed` issues whose scenario now passes to `Verified`;
- marks a `Fixed` or `Verified` issue whose scenario fails again as `Regression`;
- never changes `Planned`, `Decision` or `Not a defect`, which triage owns.

### 3d. `D_Reviews/review_state.json`

```json
{
  "checkpoints": { "G1.16": { "kind": "schema", "date": "...", "report": "...", "tree": "...", "open_critical_high": 0 } },
  "gates": { "1": { "date": "...", "verdict": "Ready", "summary": "...", "head": "<commit reviewed>" } }
}
```

## Step 4 — Add the review points to the project plan

Following the plan's own rules (stable IDs, next free number, change-log line), add these rows. If a number is taken, use the next free one and tell me.

| Gate | New rows |
|---|---|
| Gate 0 | **G0.20** (G0.17–G0.19 are taken) Gate 0 exit review (R3): all four agents, verdict Ready. Status `Blocked (G0.16)`. Note: "No full review since 2026-10-02; this confirms G0.1–G0.18 together." |
| Gate 1 | **G1.19** Schema checkpoint after G1.16 (R1) · **G1.20** Core report exit review (R3), covering G1.16–G1.18 · **G1.21** Gate 1 exit review for the rest of Phase 2A (R3), status `Blocked (D12)` |
| Gate 3 | **G3.16** Schema checkpoint after G3.1 (R1) · **G3.17** Gate 3 exit review (R3) |
| Gate 4 | **G4.7** Schema checkpoint after G4.1 (R1) · **G4.8** Gate 4 exit review (R3) |
| Gate 5 | **G5.6** Schema checkpoint after G5.1 (R1) · **G5.7** Gate 5 exit review (R3) |
| Gate 6 | **G6.5** Gate 6 exit review (R3) |
| Gate 7 | **G7.8** Gate 7 exit review (R3) |

Risk checkpoints (R2) get no rows of their own. They are cited in the Evidence of the activity they review. In the current plan, the activities that need one are G1.16 (new permission `REPORT_GENERATE`, audited generation), G3.4, G3.10 and G3.13, plus G1.2, G1.6, G1.7, G1.9 and G1.14 when Phase 2A resumes; list these in the Reviews bullet below so they are not missed.

In "How to use this file", add one bullet:

> **Findings.** Every review ends with `/triage-review`. Approved findings become rows in the current gate (Critical, High and regressions block its exit), attach to a later gate's row, become a §81A decision, or are closed as not a defect. A finding's row is `Done` when the issue is `Verified` at a gate exit. IDs: `CR-nn` / `TR-nn` / `MP-nn` / `FT-nn`, from the reports under `D_Reviews/`.

> **Reviews.** Review agents run at four points only (CLAUDE.md Part 0, "When reviews run"): a schema checkpoint after each gate's migration, a risk checkpoint for activities touching permissions, audit, score or tier (currently G1.16, G3.4, G3.10, G3.13; G1.2, G1.6, G1.7, G1.9 and G1.14 when Phase 2A resumes), a gate exit review, and before merging to `main` or a demo. Other activities need no review agent to be `Done`.

In §11, replace risk 4 (the restart caveat) with:

> **Reviews run at four fixed points, not continuously.** A merge or push to `main` without a Ready gate review of that commit is blocked by a hook; nothing else is.

Do not change any other row. Rows already `Done` keep their status; G0.20 reviews them together. Also add a **Backlog** section after Gate 7 (IDs `BL.1`, `BL.2`, …; columns: ID, Item, Source, Pick up with, Status).

## Step 5 — One hook, at the merge to `main`

Only the R4 point is enforced. Commits are never blocked, so ordinary development is never slowed by reviews.

1. Write `.claude/hooks/review_gate.py`, a short Python script using only the standard library, and register it in `.claude/settings.json`:
   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Bash",
           "hooks": [
             { "type": "command", "if": "Bash(git merge *)", "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/hooks/review_gate.py\" merge" },
             { "type": "command", "if": "Bash(git push *)",  "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/hooks/review_gate.py\" push" }
           ]
         }
       ]
     }
   }
   ```
   Use the Python on the PATH that Claude Code's hook shell sees on this machine. Check it with a dry run, and change the `command` if needed.
2. Behaviour:
   - If the merge or push does not target `main`, allow it with no output.
   - If it targets `main`, the latest gate entry in `review_state.json` must have verdict `Ready` and `head` equal to the commit being merged or pushed. Otherwise deny, with the reason "Merging to main needs a Ready gate review of this commit. Run /review-build gate <N>."
   - Deny by printing the `hookSpecificOutput` JSON with `permissionDecision: "deny"` and `permissionDecisionReason`, and exit 0.
   - If the script itself fails, deny with the error, so that a broken hook is noticed rather than silently skipped.
3. Test it on a scratch branch without touching product code. A push of the scratch branch passes. A simulated merge into `main` with no Ready entry is denied. With a Ready entry for that exact commit, it is allowed (test this with a temporary copy of `review_state.json`, then restore it). Then delete the scratch branch and confirm `git status` is clean.

## Step 6 — Freeze Gate 0's scope and finish it

Since 2026-10-05, every Gate 0 fix has turned up another edge case: G0.6 led to G0.14, G0.12 to G0.15, FT-01 to G0.17, G0.17 to G0.18, and G0.18 to G0.19. None was a product defect a user would meet in a demo. Apply these decisions of mine to the plan, adding a change-log line:

1. **G0.19 (authentication gap during a reset):** set to `Dropped` with the note "Moved to BL.1". Add **BL.1**: "A reset deletes and reloads `app_user`, so for a second or two tokens 401 and login fails. Decide whether the reset keeps the acting Admin, or clients re-authenticate — pick up with DOC-11 (progress display) or G7.7." In the functional harness, re-signing in after a 401 during a reset becomes part of H-10 under G0.16.
2. **G0.16 closes on a narrower bar.** Change its Note's closing condition to: "Done when the defects that can produce a false result are fixed — H-05 (capped audit counts), H-07 (role switch not confirmed) and H-10 (polls the wrong batch / re-auth during reset) — and FS-07, FS-18, FS-22, FS-23 and FS-24 pass together in one run." Move the other harness defects (H-01 to H-04, H-06, H-08, H-09) to **BL.2**, "Functional harness hardening — pick up with G7.6 (E2E in CI)". Set G0.16's status to `In progress` ("Built, suite not yet green" is not in the status vocabulary).
3. **The two items the first run raised for a decision** (`ImportCentre.tsx:205` default tab from an asynchronously loaded permission; `/api/audit` capping results without a `total`): add them as **BL.3** and **BL.4**, unless you judge either to be High under the triage rules. In that case, show me why and stop.
4. **Gate 0 is now closed to new rows.** Its remaining work is G0.16 (on the narrower bar) and then the exit review G0.20. Anything else found goes through triage to the Backlog or to a later gate.

Do not run `/review-build gate 0` in this session. Show me the plan diff and stop.

## Acceptance

- `/review-checkpoint risk G0.9` runs only `test-outcome-reviewer`, scoped to SEC-05. Run a second time, it reports "No change since …" and runs nothing.
- `.claude/commands/review-build.md` maps `gate 0` and `gate 1` to the agents in the R3 table, with the core-report row used while D12 holds. Check this by reading the file, not by running it.
- No agent description contains "proactively".
- The plan shows G0.19 `Dropped`, G0.16 `In progress` with the narrower closing condition, BL.1–BL.4 in a new Backlog section, and G0.20 `Blocked (G0.16)`.
- No `/review-build` ran in this session.
- The hook tests in Step 5.3 behave as described, and `git commit` is never blocked.
- CLAUDE.md Part 0 has the "When reviews run — and when they do not" section and the corrected restart note. The plan has the new rows, the Reviews bullet, the replaced risk 4 and a change-log line. No other plan rows changed.
- `git diff --stat` shows no changes under `A_Codes/AB_backend`, `A_Codes/AC_frontend`, `A_Codes/AD_seed` or `B_Inputs/`.

## Report back to me

1. The plan diff for Step 6, and anything from Step 6.3 you judged High.
2. The command the hook actually uses to run Python on this machine.
3. Any plan IDs you had to renumber (including the G1.19–G1.21 review rows), and any activity you think belongs on, or off, the risk checkpoint list.
