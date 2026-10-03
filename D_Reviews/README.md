# D_Reviews — generated review reports

These are reports written by the three review agents in `.claude/agents/`, run together by
`/review-build` (see CLAUDE.md Part 0 → Review agents).

| Folder | Written by | Contains |
|---|---|---|
| `DA_code_review/` | `requirements-reviewer` | Code against the BRD, the acceptance criteria and the Part 0 invariants |
| `DB_test_review/` | `test-outcome-reviewer` | Gate results, test-to-criterion mapping, recalculated §76A.14 coverage |
| `DC_mockup_review/` | `mockup-parity-tester` | Screen-by-screen parity with the HTML mock-up, plus screenshots |
| `<YYYYMMDD>_summary.md` | `/review-build` | One consolidated verdict across the three reports |

They are **generated**, but they are committed on purpose: a finding raised at the end of one phase
has to be traceable at the start of the next, and the dated reports are the record of what was open,
what was fixed and what was accepted as a difference. Treat them like the `_OLD/` snapshots — history
to keep, not clutter to clean up.

Reports are never edited by hand. The agents rewrite them; findings are fixed in the main session.
