# Test-outcome review: Gate 1 exit re-run (R3), core Model Risk Report (D12 holds)

- **Date:** 2026-10-15 (run 23:45 EDT; it finished early on 2026-10-16)
- **Branch / commit:** `gate-1-core-report` at **`a4f17ce`** (HEAD, clean). Merge base with `main` is `0f11fda`.
- **Scope for judgement:** this report re-grades eight criteria and recalculates the whole §76A.14 table over **152** criteria.
  - REG-15, REG-16, REG-17 (§76D)
  - GEN-04, GEN-05 (§76A.12, D16 wording)
  - PLT-01, PLT-02, PLT-03 (§76E)
- **Supersedes:** `20261015_gate1_exit.md` (`b8cc1f3`, Not ready on TR-87). The G1.33 and G1.34 checkpoint reports were checked against HEAD, not taken on trust.
- **Method:**
  - All four CI gates were run locally, and `backend` was run twice.
  - GitHub Actions was read for `a4f17ce` through the public API.
  - **49 product mutants** were run, applied in-process by an out-of-repo pytest plugin (`mutation/mut_g1y.py`). They are the 40 from the previous exit plus 9 new mutants for CR-67, D17 and D16.
  - **31 snapshot-checker mutants** were run against its own self-test at HEAD (`mutation/mut_plt3.py`), without `PYTHONUTF8`.
  - The PLT-01 probe was re-run.
  - Nothing outside `D_Reviews/DB_test_review/` was modified. The mutant copies and full outputs are in the session scratchpad. The kill lists are in `mutation/kills/`.
- **Raw output:** `D_Reviews/DB_test_review/20261015_gate1_exit_rerun/`

---

## 1. Gate results

| Gate | Command | Result | Duration |
|---|---|---|---|
| `backend` (run 1) | `.venv/Scripts/python -m pytest -q --junitxml=…/backend.xml` | **253 passed, 4 skipped, 0 failed** (257 collected) | 350 s |
| `backend` (run 2, CI env `MRM_DATABASE_URL=sqlite://`) | the same | **253 passed, 4 skipped**. All 257 outcomes are identical to run 1. | 374 s |
| `backend-postgres` | `alembic upgrade head` + `pytest tests/test_postgres.py` | **Not run locally; CI only** (`MRM_TEST_POSTGRES_URL` is unset). **Green on GitHub at `a4f17ce`**: "Apply migrations" and "Run PostgreSQL tests" both succeeded, and the job fails on any skip (`ci_jobs_a4f17ce.json`). | 42 s (CI) |
| `frontend` | `npm run build` (`tsc -b` + `vite build`) | **pass** | 4 s |
| `snapshots`: self-test | `python A_Codes/AZ_tools/test_check_snapshots.py` (no `PYTHONUTF8`) | **37/37 PASS**, exit 0 | 18 s |
| `snapshots`: check | `python A_Codes/AZ_tools/check_snapshots.py 0f11fda HEAD` | **exit 0.** 37 non-merge commits and 111 file edits checked. 8 gaps are reported, all in commits made before 2026-10-09. | 23 s |
| `snapshots`: `--ci`, as the workflow invokes it | push `c72bb97..a4f17ce`; first push (zero sha); `pull_request` (base `origin/main`); `workflow_dispatch` | All exit 0. The push checks 2 commits and 5 edits. First push, PR and dispatch all resolve to `0f11fda` and check 37 commits and 111 edits. | — |

**GitHub Actions run 38847052627 (push, `a4f17ce`): success on all four jobs.** The jobs are Backend tests (ubuntu-latest), Migrations and PostgreSQL integration, Snapshot convention (both steps), and Frontend typecheck and build.

The 4 local skips are exactly the four `test_postgres.py` cases (confirmed from `backend.xml`).

| | Local | CI | Difference |
|---|---|---|---|
| Python | 3.14.5 | 3.14 | none |
| Node | **v24.16.0** (npm 11.13.0) | 22 | carried, TR-23 |
| git | 2.54.0.windows.1, `core.autocrlf=true` | ubuntu default | no longer matters: the CRLF case now discriminates locally (P12 killed) |

**No flaky behaviour.** The two backend runs agree test for test.

---

## 2. Failures

**No test failed, errored or was xfailed in any gate.** The PLT-01 probe (`mutation/test_probe_plt01.py`, a reviewer probe that is not in the repo) fails as expected; see §4.

---

## 3. Verification of the history since `b8cc1f3`

| Item | State at `a4f17ce` | Evidence |
|---|---|---|
| **TR-87** (High; rename-and-rewrite passed the snapshot control) | **Closed** | Mutants P2, P2b, P3 and N13 are each killed by "PLT-02 rename + rewrite without a snapshot fails". Also confirmed end to end on the real branch: 111 edits are counted, where the old code counted 106. |
| TR-88 (PLT-03 unasserted) | Closed (G1.33) | P1, P7, P8, N4, N5, N6, N7, N9, N10 and N11 are killed. |
| TR-89 (CRLF case vacuous under autocrlf) | Closed | P12 is killed locally with `core.autocrlf=true`. |
| TR-90 (no PLT tag) | **Partly closed** | PLT-02 and PLT-03 are named per case in the self-test. No backend test names PLT-01 (TR-99, still open). |
| **TR-94** (self-test crashed on Windows) | **Closed** | The self-test passes 37/37 without `PYTHONUTF8`, and the whole mutant battery ran without it. |
| **TR-95** (rename-with-snapshot case vacuous) | **Closed** | N1 (destination lookup removed) and N2 (source lookup removed) are now each killed, and the "really checked" count assertion holds. |
| TR-96 (sub-threshold rename as delete+add) | Open (spec; D-pending) | Unchanged. P13 and P14 are still equivalent under the `MR` filter. |
| TR-97 (PLT-02 says "authored"; rename out of `A_Codes/` untested) | Open | CLAUDE.md §76E still says "Commits authored before 2026-10-09". N3 survives. |
| TR-98 (dispatch on the default branch is an empty range) | Open | N8 survives (near-equivalent). |
| **TR-84** (PDF reconciliation timestamp unasserted) | **Closed** | R27 is killed by `test_d17_…`, which asserts the whole line, timestamp included. |
| TR-83 (seeded reconciliation time is false; spec) | **Closed by D17 (a)** | D01 (restoring the shaped 09:00 time) is killed by `test_d17_…`. |
| TR-110 (lock check ordered before the permission check) | Open | C02 survives. |
| TR-111 (refusal after the store write orphans an object) | Open | C03 survives. |
| TR-112 (D17 window blind to naive local time on a UTC host) | Open | D02 is killed on this UTC−04:00 machine only, so the original reasoning stands for CI. |
| **TR-113** (CR-67 test tagged GEN-04) | **Closed** | The `test_cr_67_…` docstring now names REG-16 only. |
| TR-114 (CR-67 check-then-act) | Open (known limit, beside TR-73) | Unchanged. |
| TR-91, TR-92, TR-93 | Open (held) | R22, R29 and R10 survive, as at the exit. |
| TR-79…TR-82, TR-85, TR-86 | Unchanged | No code or tests in their scope changed. |
| BL.1–BL.39 | Unchanged | Re-confirmed by mutation: BL.7/TR-09 (R18 survives), BL.13/AUD-01 (R16 survives), BL.26/TR-47 (G11 survives), BL.31/PLT-01 (probe still fails). |

---

## 4. Criterion table: Gate 1 scope

| Criterion | Expected result (short) | Tests | Grade | Gap |
|---|---|---|---|---|
| **REG-15** | Every REQ-REG-10A section is present. Every figure equals the Command Center and its drill-down. The inventory is by displayed stage. The report is always for `app.clock.today()`. | `test_reg_15_*` (9), `test_s11_…`, `test_d14_the_seeded_example_…`; FS-25 | **Proven** | R06, R07, R08, R09, R11 and R12 are killed. Residuals are unchanged: TR-92 (R29), TR-93 (R10), TR-07. |
| **REG-16** | Same data and same date give the same hash, with `changes_since` excluded. One audit event per generation. Without `REPORT_GENERATE` the API returns 403, and nothing is stored and no audit event is written. | `test_reg_16_*` (10), `test_s13_…`, `test_cr_67_…` | **Proven** | R01–R05 and R13–R15 are killed. The CR-67 extension (a report refused during a reset) is guarded at the API: C01 is killed by `test_cr_67_…`. Residuals: TR-110 (C02), TR-111 (C03), TR-114, hash breadth (BL.30), and R16 (the AUD-01 class, BL.13). |
| **REG-17** | Stored reports are listed, reopened and downloaded as a PDF by read roles, including Executive and Auditor. Changes-since lists exactly the differences. | `test_reg_17_*` (6), `test_reg_16_read_roles_…`, `test_tr_61_…`, `test_d14_the_pdf_…`, `test_d17_…`; FS-25 | **Proven** | R17, R19–R21, R23, R25–R28 and D01 are killed, and R27 is now killed too (TR-84 closed). Residuals: TR-91 (R22) and TR-09 (R18). |
| REG-01…REG-14 | §12A proper | — | **Not built (Phase 2A, deferred D12)** | — |
| **GEN-04** (D16) | A second reset gets a 409 that names the batch **or says it is still being created**, and names the stage. Nothing is deleted, regenerated or submitted. A held lock is answered from a read. A locked claim is a 409, never a 500. A 403 beats the 409. | 12 GEN-04-tagged tests in `test_reset_lock.py` and `test_imports.py` | **Weak** (was Proven under the old wording) | Every clause is killed except one. Mutants G01 (batch), **G12 (stage, new)**, G02 (nothing regenerated or submitted), G03 (read-first), G04 (409, not 500) and G08 (403 first) are killed. **G15 survives**: dropping "(being created)" from the message passes all 82 reset and report tests. D16 added that clause precisely because "names the batch" cannot hold before the batch exists, and `test_g1_32_a_held_lock_is_answered_from_a_read_…`, which holds a lock with no batch, asserts only the status code (**TR-115**). |
| **GEN-05** (D16) | An explicit lock is held from the first step to the last, and status reads it, never a batch status. A failure at any stage releases the lock with the outcome and the stage. A lock left by a stopped application is released with a reason at startup. There is no release API. | `test_g1_32_after_every_commit_…`, the stage-parametrised test (×5), `…_analysis_failure_…`, `…_missing_baseline_…`, the two recovery tests, `test_reset_status_…`, `test_cr_57_…`, `test_ft_05_…` | **Proven** | G05, G06, G07, G09 and G10 are killed. The new startup clause is killed too: **G13** (no recovery) by both recovery tests, and **G14** (recovery without a reason) by `…_recovered_with_a_reason`. "No API to release it" holds by inspection of `app/api/admin.py`, but no test asserts it (**TR-116**, Low). Residuals held: TR-75 and TR-47 (G11). |
| **PLT-01** | Every API datetime is tz-aware UTC, including untyped nested sections. A new field is covered without editing a list. | `test_api_timestamps.py` (3; none tagged PLT-01) | **Failing** (known, BL.31) | The probe shows `sections.changes_since.previous_generated_at` is **naive** on `POST /api/reports/model-risk` and on the reopened report (now `2026-10-16T04:08:27`, the real D17 time, still with no offset). The sweep is still a hard-coded list that omits `/api/reports/*`. |
| **PLT-02** | For each non-merge commit, each hand-edited file it modifies (or renames and modifies) has its pre-change content in `_OLD/`. The criterion lists the exemptions and the grandfathering. | `A_Codes/AZ_tools/test_check_snapshots.py` (37 checks, PLT-02 named per case) | **Proven** (was Failing) | TR-87 is closed. P2, P2b, P3, P5, P6, P9, P10, P10b, P11, P12, P15, N1, N2, N12 and N13 are killed. P4, P13 and P14 are equivalent. Residuals: TR-96 (spec), TR-97 (N3; "authored" wording). |
| **PLT-03** | CI resolves a non-empty base on every trigger and uses the merge base for PRs. It fails rather than skipping. Non-ASCII and renamed paths are checked, and the count is reported. | the same self-test (CI resolution, non-ASCII, count and empty-base cases) | **Proven** (was Failing) | P1, P7, P8, N4–N7, N9, N10 and N11 are killed. The `--ci` simulation agrees on all four triggers, and the real CI step is green. Residual: TR-98 (N8). |

---

## 5. Findings

New IDs start at TR-115.

| ID | Severity | Criterion | Problem | Suggested test change |
|---|---|---|---|---|
| **TR-115** | Medium | GEN-04 | **The D16 clause "or says it is still being created" is unasserted.** Mutant G15 (`{lock.batch_id or ''}` instead of `'(being created)'`) survives all 82 tests in `test_reset_lock.py`, `test_imports.py` and `test_reports.py`. The only test that refuses a reset while the lock has no batch (`test_g1_32_a_held_lock_is_answered_from_a_read_without_claiming`) asserts `status_code == 409` and nothing about the message. This is the clause D16 added because the old "names the batch in flight" cannot hold in that window. | In that test, assert `"being created" in resp.json()["detail"]` and `"stage Starting" in resp.json()["detail"]`. That one test then covers the no-batch branch of both the batch clause and the stage clause. |
| **TR-116** | Low | GEN-05 | **"There is no API to release it" is true by inspection but unguarded.** No route in `app/api/` touches `reset_lock` other than `GET /api/admin/reset/status`. A future `POST /api/admin/reset/release` would pass the suite. | Add a route-table test: iterate `app.routes` and assert that no non-GET route under `/api/admin/reset` exists other than `POST /api/admin/reset`. Optionally assert that `POST /api/imports/batches/{seed_batch}/cancel` during a held lock leaves `reset_in_progress` unchanged. |

### Severity against the rules

- **No Critical or High is open in scope.** TR-87, the only High at the exit, is closed and verified by mutation.
- No SEC, AUD or APR criterion is in scope as Weak or Failing.
  - R16, the report committed before its audit event, is the known AUD-01 gap (BL.13).
  - REG-16's CR-67 residuals TR-110 and TR-111 are Low because REG-16's own wording is met. The 409 during a reset appears in no criterion text (TR-113 spec note).
- **PLT-01 stays Failing.** It is triaged to BL.31, and per D15 it was in this gate as a known Failing criterion rather than a new defect. It is not counted as a new finding.

---

## 6. Untraced tests and stale counts

- **257 collected, 217 test functions, 37 name no criterion.** The function count is +2 since `b8cc1f3` (`test_d17_…` and `test_cr_67_…`, both traced). The untraced tests by file:

  | File | Untraced |
  |---|---|
  | `test_seed_generator.py` | 12 |
  | `test_db_config.py` | 6 |
  | `test_documents.py` | 4 |
  | `test_api_timestamps.py` | 3 (PLT-01's tests, TR-99) |
  | `test_migrations.py` | 3 |
  | `test_postgres.py` | 2 |
  | `test_reports.py` | 2 (`test_s12_…`, `test_d14_a_generated_report_…`) |
  | `test_dashboard.py`, `test_imports.py`, `test_models_api.py`, `test_policy_and_audit.py`, `test_rules.py` | 1 each |
- **`test_check_snapshots.py`** has 37 checks, all traced to PLT-02 or PLT-03 by heading. It is not under pytest.
- **Part 0, `CLAUDE.md:25`** still reads "188 tests: 184 pass, 4 PostgreSQL skip". The actual figures are **257 collected, 253 pass, 4 skip**. This count is stale for the sixth time (BL.34).
- **§76A.14 is stale.**
  - It lists PLT-02 and PLT-03 under "Failing".
  - Its headline says 76 of 152.
  - Its "Tagging and spec gaps" still carries the 2026-10-07 bullet saying GEN-04 "stays **partly proven**". My previous §7.6 should have replaced that bullet and did not.
- **§76E PLT-02** still says "authored" (TR-97).

---

## 7. Proposed replacement text for §76A.14

Splice this text into §76A.14 as Part 0 directs, and **do not hand-adjust** it. Any subsection not listed below stays verbatim:
- the "Not proven: no test" table;
- the Partly-proven rows for INV-01, INV-02, INV-03, INV-06, LIF-01, VAL-03, VAL-06, SCR-05, AUD-01, GEN-01 and DOC-09;
- the "Correctly open" table.

### 7.1 Replace from "Coverage at the Gate 1 exit, 2026-10-15" through "…until that gate merges."

> Coverage at the Gate 1 exit re-run, 2026-10-15 (`test-outcome-reviewer`, commit `a4f17ce`): **77 of
> 152** criteria (§76A–§76E, §77, §78, §79) are *proven*. That is **77 of 94** once the 58 unbuilt
> criteria are excluded: 20 monitoring (§77), 13 Data Audit (§76B), 10 Copilot (§76C), 14 regulatory
> (§76D, deferred D12) and DOC-16 (Phase 5). A further **12** have a test that passes without
> asserting the whole expected result, **4** have no test, and **1** is failing: PLT-01. All CI gates
> were green on GitHub at `a4f17ce`, including `backend-postgres` (migrations through `0009`, the
> drift guard and the append-only trigger) and both steps of the `snapshots` job.
>
> By set:
> - §76A **46/60** Proven (11 Weak, 3 Untested)
> - §76B **0/13** (Phase 7)
> - §76C **0/10** (Phase 9)
> - §76D **3/17** Proven, 14 deferred (D12)
> - §76E **2/3** Proven, 1 Failing (PLT-01)
> - §77 **0/20** (Phase 6)
> - §78 **17/20** (1 Weak, 1 Untested, 1 Phase 5)
> - §79 **9/9**
>
> Gate 1's movement is **+5 Proven** over the Gate 0 exit figure of 72:
> - **REG-15**, **REG-16** and **REG-17**, the core Model Risk Report (G1.16–G1.18, G1.25–G1.27,
>   G1.29, G1.31, G1.34).
> - **PLT-02** and **PLT-03**, the snapshot control (G1.33). A rename-and-rewrite is now charged
>   (TR-87), and the CI base resolution is tested.
>
> **GEN-04** moved from Proven to **Weak** when D16 reworded it. Every clause has a killing mutant
> except the new "or says it is still being created" (TR-115). **GEN-05** is Proven under its D16
> wording, including the startup release with a reason. **PLT-01** is still Failing: the report's
> nested `previous_generated_at` is naive (BL.31).
>
> The §76D total is 17. REG-01 to REG-14 are deferred with the rest of Phase 2A (**D12**) and are
> reported as *Not built (Phase 2A, deferred D12)*, never as failures. REG-15 to REG-17, the core
> Model Risk Report, are built on `gate-1-core-report` and Proven. On `main` they stay *Not built*
> until that gate merges.

### 7.2 In "Partly proven", add this row after GEN-01

> | GEN-04 | The 409 names the batch and the stage, and both are killed by mutation. Nothing is deleted, regenerated or submitted on refusal. A held lock is answered from a read. A locked claim is a 409. The 403 comes first. | The no-batch branch: dropping "(being created)" from the message passes every test. The test that holds a lock with no batch asserts only the status code (TR-115). |

### 7.3 Replace the "Failing" table with

> | Criterion | What fails | Fix |
> |---|---|---|
> | PLT-01 | `sections.changes_since.previous_generated_at` is emitted naive on `POST /api/reports/model-risk` and on a reopened report, because `sections` is an untyped dict that `schemas.core.Utc` never reaches. The sweep walks a hard-coded list of endpoints and omits `/api/reports/*`. Re-confirmed by probe at `a4f17ce`. | BL.31: serialise `sections` through the same normaliser, sweep every GET route from the app's route table, and tag the tests PLT-01 (TR-99). |

### 7.4 Replace "Residual non-discrimination on otherwise-proven criteria" with

> - **APR-03.** Unchanged: no test covers an `Approved` decision that carries an `Open` condition status.
> - **GEN-01 / GEN-05 (FT-04).** The listener is Session-level (BL.26), and it anchors on the *last*
>   hand-off. An extra hand-off before the last write still passes all 82 reset tests (TR-47,
>   re-verified at `a4f17ce`).
> - **GEN-04.** Concurrent claim atomicity is shown on neither engine (TR-73, BL.38). SQLite write-lock
>   contention with no reset running is answered "a reset is already running" (TR-79). The
>   non-contention `OperationalError` branch is untested (TR-80).
> - **GEN-05.** If `runner.submit` raises, the lock stays held until restart (TR-75, BL.38). "There
>   is no API to release it" is true but has no guard test (TR-116).
> - **REG-15.** Four Command Center equalities are tautological (TR-07). The seeded example is
>   compared with a fresh report for `documentation` only (TR-92). The overdue-findings boundary on
>   the business date is unpinned (TR-93).
> - **REG-16.**
>   - Hash breadth: each content key can still be dropped from the digest individually (TR-38/TR-62,
>     BL.30).
>   - Audit coupling: committing the report before its audit event passes every report test, which
>     is AUD-01's per-service coupling (BL.13).
>   - CR-67, the report refused during a reset: guarded at the API.
>   - The service-level permission-before-lock order is unasserted (TR-110).
>   - An object stored before a late refusal is not checked (TR-111).
>   - The check is check-then-act (TR-114).
> - **REG-17.** Ordering by `generated_at` is unasserted (TR-09). A reopen that alters a stored figure
>   passes (TR-91). The seeded example's reconciliation line is asserted in full, timestamp included
>   (TR-84 closed, D17). The window check would not catch naive local time on a UTC host (TR-112).
> - **PLT-02.**
>   - A rename that git reports as delete plus add is uncharged, pending a decision on deletes
>     (TR-96).
>   - A rename out of `A_Codes/` with a rewrite is charged but untested (TR-97).
>   - The criterion still says "authored" where the code uses the committer date (TR-97).
> - **PLT-03.** A manual run on the default branch is an empty range that exits 0 (TR-98).

### 7.5 In "Tagging and spec gaps"

**Delete** the first bullet, "GEN-04 and GEN-05 tagging: fixed 2026-10-07 …". It still says GEN-04 "stays partly proven" for a reason that has since been closed, and the current GEN-04 gap is in §7.2.

**Replace** the untraced-tests bullet and the PLT bullet with:

> - **Untraced tests are 37 of 217 test functions** (257 collected). Two new tests arrived since the
>   Gate 1 exit, `test_d17_…` and `test_cr_67_…`, and both are traced. Still structural: §64, §65, the
>   seed generator's file safety, and migrations (`test_migrations.py`, BL.35) have no criteria.
> - **PLT-01 is named by no backend test** (TR-99). The three `test_bl_28_*` tests are PLT-01's.
>   PLT-02 and PLT-03 are named per case in `A_Codes/AZ_tools/test_check_snapshots.py` (37 checks).
> - **CR-67** (no report while a reset holds the lock) belongs to no criterion's wording. Its test is
>   tagged REG-16 only (TR-113, closed). Decide whether REG-16 should state it.

### 7.6 Replace the closing paragraph

> The four untested criteria and twelve partly proven ones are real gaps in built functionality.
> **PLT-01** (BL.31) comes first, because it is the only built criterion that fails outright. Then
> **AUD-01's per-service coupling** (observed in `report_service` as well) and **GEN-01's row-count
> comparison**, before Phase 6 adds more surface area. GEN-04's TR-115 is a one-assertion fix.

---

## 8. Mutation battery: full result

**Product: 49 mutants (`mutation/mut_g1y.py`, `mutation/mut_g1y_summary.txt`, `mutation/kills/`). 40 killed, 9 survived.**
- R mutants run against `test_reports.py` and `test_api_timestamps.py` (38 tests).
- C and D mutants run against `test_reports.py` and `test_reset_lock.py` (52 tests).
- G mutants run against `test_reset_lock.py`, `test_imports.py` and `test_reports.py` (82 tests).

| Mutant | Result | Note |
|---|---|---|
| R01–R09, R11–R15, R17, R19–R21, R23–R26, R28 | killed | as at the exit |
| **R27** PDF reconciliation without its timestamp | **killed** (newly) | `test_d17_…`; TR-84 closed |
| R10 overdue includes due-today | survived | TR-93 |
| R16 report committed before audit | survived | BL.13 |
| R18 list ordered by id only | survived | TR-09 |
| R22 reopen alters a stored figure | survived | TR-91 |
| R29 seeded example shapes a figure | survived | TR-92 |
| C01 no lock check in `generate` | killed | `test_cr_67_…` |
| C02 lock check before the permission check | survived | TR-110 |
| C03 lock check after `store.put` | survived | TR-111 |
| D01 seeded `generated_at` shaped to 09:00 | killed | `test_d17_…` |
| D02 seeded `generated_at` naive local | killed **on this UTC−04:00 host only** | TR-112 |
| G01–G10 | killed | as at the exit |
| G11 extra hand-off before the last write | survived | TR-47 |
| G12 409 omits the stage | killed | 2 tests |
| G13 no startup recovery | killed | both recovery tests |
| G14 recovery without a reason | killed | `…_recovered_with_a_reason` |
| **G15 409 omits "(being created)"** | **survived** | **TR-115** |

**Snapshot control: 31 mutants (`mutation/mut_plt3.py`, `mutation/mut_plt3_out.txt`), run without `PYTHONUTF8`. 25 killed, 6 survived.**
- Killed: P1, P2, P2b, P3, P5–P12, P10b, P15, N1, N2, N4–N7, N9–N13.
- P0 is the identity mutant, and it passes as it should.
- P4, P13 and P14 are equivalent.
- N3 survives (TR-97).
- N8 survives (TR-98, near-equivalent).

---

## 9. Verdict on this agent's scope

**Ready on test outcomes: 0 Critical, 0 High open.**
- All four CI gates are green: locally (two agreeing backend runs, no flakiness) and on GitHub at `a4f17ce`.
- **TR-87 is closed** and verified by mutation. PLT-02 and PLT-03 move from Failing to Proven.
- REG-15, REG-16, REG-17 and GEN-05 are Proven.
- GEN-04 drops to Weak under its D16 wording, on one unasserted clause (TR-115, Medium).
- PLT-01 remains Failing, as already triaged (BL.31).

New findings: **Medium 1** (TR-115), **Low 1** (TR-116).

**77 of 152 criteria proven (77 of 94 built).**
