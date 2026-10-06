---
description: Gate exit review (R3) — run the agents that gate needs and write one consolidated summary
argument-hint: "gate <N> | [phase N | §section | criterion prefix] [--github]  (empty = everything built)"
---

Review the build. Scope: $ARGUMENTS (if empty, everything Part 0 lists as implemented).

This is the **R3 gate exit** review. It is not run per commit or per activity — see CLAUDE.md Part 0,
"When reviews run — and when they do not".

1. **Resolve the scope.**
   - `gate <N>`: take the agents to run from the R3 table in CLAUDE.md Part 0 ("Which agents run at a
     gate exit"). For **gate 1**, use the *core Model Risk Report* row while **D12** holds — that is
     G1.16–G1.18, FS-25 and MUP-29 (MUP-30 partial) — and the *rest of Phase 2A* row only once D12 is
     lifted. **Gate 2 has no review**: say so and stop.
   - Scope `requirements-reviewer` and `test-outcome-reviewer` to that gate's activities and criteria.
     Run the CI gates and the functional suite **in full**, so a regression elsewhere is still caught
     without re-reviewing finished work line by line.
   - Anything else (`phase N`, `§25`, a criterion prefix) scopes all four agents as before.
2. **Skip rule.** Read `D_Reviews/review_state.json`. If the latest entry for this gate has verdict
   `Ready` and its `head` equals the current commit (`git rev-parse HEAD`), say
   "No change since <date>; citing <summary>" and stop. Nothing is re-run.
3. **Run the agents** the table names, and no others:
   - `requirements-reviewer` and `test-outcome-reviewer` **in parallel**.
   - Then `functional-tester` and then `mockup-parity-tester`, **one after the other, never
     overlapping** — both start the application and reset the data, so running them together would
     have each pull the ground from under the other. Pass `--github` to `functional-tester` only if
     $ARGUMENTS contains it.
4. **Write `D_Reviews/<YYYYMMDD>_summary.md`** containing:
   - Overall verdict: **Ready** (no open Critical or High finding, all gates green) or **Not ready**.
   - The gate reviewed, and Proven / total criteria.
   - All Critical and High findings from the agents that ran, in one table:
     `ID | Source | Severity | Criterion / MUP | Problem | Suggested fix`, deduplicated where two
     agents found the same thing. Include the `functional-tester`'s Critical and High issues (FT-nn)
     and link each issue file under `D_Reviews/DD_functional_test/<YYYYMMDD>/issues/`.
   - Spec issues and the §81A decisions they touch.
   - Counts of Medium and Low findings, with links to each report.
5. **Record the result** in `D_Reviews/review_state.json` under `gates.<N>`: `date`, `verdict`,
   `summary` path, and `head` = the commit reviewed. If the gate has an exit row in the plan, put the
   verdict and the summary path in that row's Evidence column. The gate closes only on **Ready**.
6. Do not fix anything. Show me the summary table, then run `/triage-review` on this summary.
