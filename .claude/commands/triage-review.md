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
