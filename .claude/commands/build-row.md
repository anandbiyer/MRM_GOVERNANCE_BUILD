---
description: Build one or more plan activities end to end
argument-hint: "<plan ID or range, e.g. G3.2 or G3.2-G3.4>"
---
Build $ARGUMENTS from project_plan.md, one row at a time, one commit per row.
For each row:
1. Read the row, its criteria in CLAUDE.md, and any decision it cites (decision_log.md). If a needed
   decision is missing or the spec contradicts itself, stop and ask; do not guess.
2. Follow Part 0: snapshot before editing, writes only through services with audit in the same
   transaction, no business numbers in code (add T12 policy rows, bootstrap and seed paired),
   app.clock.today().
3. Write the tests first, citing the row's criterion IDs, and confirm they fail. Then build until
   they pass.
4. Run pytest and npm run build. Both must be green.
5. If the row is on the schema (R1) or risk (R2) checkpoint list, run /review-checkpoint for it.
6. Update the row's status and evidence, add a change-log line, then commit on the current gate branch.
7. If you discover anything new along the way, log it for /triage-review. Do not fix it in this row
   (scope freeze).
Stop after the last row in $ARGUMENTS, at a checkpoint with a Critical or High finding, or when blocked.
If the last row in the gate is now Done, say so and suggest /review-build gate <N>.
