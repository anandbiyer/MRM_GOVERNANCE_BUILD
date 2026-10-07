---
description: Schema or risk checkpoint for one plan activity (R1 or R2)
argument-hint: "schema <plan ID> | risk <plan ID>"
---

Checkpoint: $ARGUMENTS

1. Find the plan ID's row in `project_plan.md`. If it cannot be found, stop and say so.
2. Work out the scope:
   - **schema**: the tables and columns the activity's migration adds, the §48 entries for them, and the templates of the same gate that will load them.
   - **risk**: the activity's criteria IDs. If the row names a finding instead (CR-, TR-, MP-), use the criteria that finding cites.
3. Skip check: take a digest of the scoped files with
   `git ls-files -s -- <paths> | git hash-object --stdin`, which hashes their blob ids and so changes
   only when their content does. (`git write-tree` cannot be used: it digests the whole index, so it
   would be identical for every scope and the rule would never skip anything.) If
   `D_Reviews/review_state.json` already holds a checkpoint for this ID with the same `tree`, say
   "No change since <date>; citing <report>" and stop.
4. Run one agent: `requirements-reviewer` for schema, `test-outcome-reviewer` for risk. Name the report `<YYYYMMDD>_<ID>_<schema|risk>.md`.
5. Report the findings for this activity in one table: `ID | Severity | Criterion / table | Problem | Suggested fix`. Findings outside the scope are listed under it, but are not this activity's to fix.
6. With no open Critical or High finding, add the report path to the row's Evidence column. Otherwise list what must be fixed first, and leave the plan unchanged.
7. Record the checkpoint in `D_Reviews/review_state.json`, keyed `<ID>` for a schema checkpoint and
   `<ID>:risk` for a risk one. A row can need both — G1.16 did — so a single key per plan ID would let
   the second checkpoint overwrite the first and make the skip rule cite the wrong report. Do not fix
   anything.
8. If the checkpoint found anything, finish by running `/triage-review` on its report. A finding is not
   added to the plan from here — triage places it, and only after the user approves.
