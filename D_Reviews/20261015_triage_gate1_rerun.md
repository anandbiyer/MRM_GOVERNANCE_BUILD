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

## Addendum — the G1.29 and G1.30 risk checkpoints (2026-10-15)

Approved by the owner after the G1.30 checkpoint returned a High.

| Item | Source IDs | Severity | Disposition | Where |
|---|---|---|---|---|
| The seed batch is committed `Completed` by `engine.run` before `_reset_job` re-holds it, so for milliseconds a second reset is accepted | TR-65 | High | **Fix now, structurally**: an explicit reset lock replaces the status inference | **G1.32** |
| A crash in the job's final status restore latches the batch | TR-67 | Medium | Folded into G1.32 (the lock is always released, with the reason) | **G1.32** |
| Analysis-failure path untested; stage not asserted; no 409 asserted during the report write | TR-66, TR-68, TR-69 | Medium, Low | Folded into G1.32's tests | **G1.32** |
| The S13 test compares two reports whose "since" lists are empty, so it cannot fail | TR-60 | Medium | **Fix now** in G1.29 | **G1.29** (reopened in part) |
| Reports stored before S13 reopen showing 0 decisions | TR-61 | Medium | **Decided**: option (a), fall back to the stored old key | **G1.29** (reopened in part) |
| Hash moves on only one composite probe; `SECTIONS` omits `baseline` | TR-62, TR-63 | Medium, Low | Backlog | **BL.30** |
| A non-raising total evidence failure still writes the example and reads Completed | OS-1 | Low | Backlog | **BL.37** |
| Stray `test_zz_*.pyc` files | OS-2 | — | Not a defect: untracked and ignored, left by earlier probes | — |

## Addendum 2 — the G1.32 checkpoints (2026-10-15)

Approved by the owner after the G1.32 risk checkpoint returned a High introduced by the row itself.

| Item | Source IDs | Severity | Disposition | Where |
|---|---|---|---|---|
| A refused second reset gets HTTP 500 "database is locked" instead of 409 in thread mode | TR-70 | High | **Fix within G1.32**: read the lock first; a claim meeting a database lock answers 409 | **G1.32** |
| Two releases (baseline path, pre-submit failure) unguarded by tests | TR-72 | Medium | Folded into G1.32 | **G1.32** |
| GEN-04's "nothing deleted, no second job submitted" unasserted | TR-74 | Medium | Folded into G1.32 | **G1.32** |
| The 409-during-report test recurses instead of failing when the lock is not held | TR-76 | Low | Folded into G1.32 | **G1.32** |
| Stated reason for no FK on `batch_id` wrong | CR-59 | Low | Folded into G1.32 | **G1.32** |
| Claim atomicity unshown on either engine; `submit` raising; one-commit allowance; holder check untested | TR-73, TR-75, TR-77, TR-78 | Medium, Low | Backlog | **BL.38** |
| Users 401 for ~3 s during every reset | TR-71 | Medium | Backlog | **BL.1** |
| Singleton constraint; PostgreSQL row assertion; `uvicorn`-only dev DB lacks the table | CR-60, CR-61, CR-62 | Low | Backlog | **BL.39** |
