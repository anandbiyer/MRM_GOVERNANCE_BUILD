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
