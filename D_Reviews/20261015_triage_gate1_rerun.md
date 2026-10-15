# Triage — Gate 1 static re-run (2026-10-09) and the G3.0 risk checkpoint

| | |
|---|---|
| Date | 2026-10-15 |
| Sources | `DA_code_review/20261009_gate1_rerun.md` (requirements-reviewer, Not ready), `DB_test_review/20261009_gate1_rerun.md` (test-outcome-reviewer, Ready), `DB_test_review/20261009_G3.0_risk.md` (R2 checkpoint of G3.0) |
| Approved by | Anand, with changes to items 1, 7, 9 and 10 of the proposal |
| Branch | `gate-1-core-report`, after `main` was merged in (`4b0e4e3`) |

There was no consolidated summary for this re-run (only the two static reviewers ran), so the
dispositions for CR and TR findings are recorded here rather than in a `<date>_summary.md`.

## Dispositions

| Item | Source IDs | Severity | Disposition | Where |
|---|---|---|---|---|
| A predecessor-derived figure, `approvals.decisions_since_previous`, is still inside the content hash | CR-52 | High | **Fix now** — every predecessor-derived figure moves into the changes section (owner's choice over an allowlist) | **G1.29**; **S13** in the D12 addendum |
| The reset reports itself finished while the example report is still being written (regression of G0.18 from G1.26) | CR-53 | High | **Fix now** | **G1.30** |
| A failure writing the example report leaves no trace | CR-57 | Low | **Fix now**, folded into G1.30 by the owner (same function, same `finally`) | **G1.30** |
| Snapshot convention broken (three pre-edit states) | CR-54 | High | **Closed** — recovered in `ff6f498`; the CI control now enforces it. A further instance (`fa33e47`) was caught by that control on its first GitHub run and recovered in `de484c2` | Re-verify at the Gate 1 exit |
| G3.0 checkpoint: control could not go green, could not see CR-54, had no tests, passed vacuously on manual runs, skipped two file classes silently, wrong PR base, false failure on mode-only change | TR-49, TR-50, TR-51, TR-52, TR-53, TR-54, TR-55 | 3 High, 4 Medium | **Closed** — fixed in `fa33e47`; CI job green on GitHub, 20 checker tests pass | Re-verify at the Gate 1 exit |
| G3.0 validation not reproducible at HEAD; Part 0 silent on the CI check | TR-57 | Low | **Closed** — `fa33e47` replaced the hand validation with tests and updated Part 0; the reproducibility note is in the G3.0 row | G3.0 row |
| Migration FK naming guard checks a character class, not the convention | TR-46, CR-58 | Medium, Low | **Backlog** | **BL.35**, before G3.1 |
| FT-04 test anchors on the last hand-off, not the first | TR-47 | Low | **Backlog** | **BL.26** |
| Seeded example states a business date its figures do not belong to, undisclosed; the PDF carries no S12 disclosure | TR-48, CR-55 | Medium | **Decision → decided**: D14 option (b); the PDF is a surface. Built in this gate | **D14**, **G1.31** |
| Page lede still asserts a present-tense reconciliation | CR-56 | Low | **Backlog** | **BL.29** |
| No acceptance criteria for build controls | TR-56 | Medium | **Decision → decided**: §76E PLT-01…PLT-03; total 152 | **D15** |
| `_v<N>` no longer chronological; npm lock files covered by the check | TR-58, TR-59 (lock files) | Low | **Backlog** | **BL.36** |
| Part 0's test count stale | TR-59 (count) | Low | **Backlog** | **BL.34** |
| Decision log named G1.21–G1.23 for work that landed as G1.25–G1.28 | CR report §7 note | — | Corrected in `decision_log.md` | — |

Carried findings re-verified as unchanged by both reviewers (BL.7, BL.8, BL.13, BL.26, BL.29–BL.31,
BL.33, BL.34, TR-23) need no new disposition.

## What Gate 1 needs now

G1.29, G1.30 and G1.31, each followed by an R2 risk checkpoint, then one full `/review-build gate 1`
with all four agents. Gate 1 closes on that run unless it finds a new Critical or High; new Medium or
Low findings go to the Backlog.
