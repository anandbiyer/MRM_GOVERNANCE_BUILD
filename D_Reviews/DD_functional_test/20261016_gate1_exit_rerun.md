# Functional test: Gate 1 exit re-run (R3), limited to the owner's scope

Run by `functional-tester` (review agent 4) on 2026-10-16, branch `gate-1-core-report`, commit `a4f17ce`.

**Scope, set by the owner:** FS-25 (both tests) and the reset scenarios. I checked the catalogue for scenarios that run a reset or touch the reset lock. Only **FS-21** does. FS-07 only tolerates an earlier reset (H-15), and FS-25 reads the example report that FS-21's reset seeds, so it was in scope anyway. The previous full run, at `b8cc1f3`, passed 29 of 29 (`20261015_gate1_exit.md`).

**What changed since `b8cc1f3`:** the only product change is in `app/services/report_service.py` (G1.34):
- **D17:** the seeded example's `generated_at` is now the real time the example was computed.
- **CR-67:** `POST /api/reports/model-risk` answers 409 while a reset holds the lock.

G1.33 changed only the snapshot CI tool, so it has no effect on the product.

---

## 1. Setup

| | |
|---|---|
| Commit under test | `a4f17ce`. The working tree's only changes are other agents' untracked reports and my harness files |
| Business date | **2026-09-30** (`MRM_TODAY_OVERRIDE`, line 1 of `functional-scenarios.md`) |
| Test database | `D_Reviews/DD_functional_test/20261016/env/functional.db` (SQLite). Built from empty with `create_all` + `add_missing_columns`, then `app.cli reset`. The earlier `env/` folder (20261015) was deleted first; its screenshots were kept |
| Object store | `20261016/env/object_store` (`MRM_STORAGE_BACKEND=local`) |
| App | uvicorn `127.0.0.1:8000` and Vite `http://localhost:5173`, both started with the test environment. Readiness was checked on `/api/health/live` |
| Browser | Chromium (Playwright 1.63.0, chromium-1243), 1440 × 900 |
| Demo app | **Not running** when I started, so nothing was stopped. Every process I started has been stopped, and ports 8000 and 5173 are free |

**Seed counts all match line 2 of the catalogue** (models 256 · users 65 · validations 415 · findings 206 · approvals 383 · documents 1116 · policy settings 72). After the reset the database also held:
- the reset lock, free, with `last_outcome` Completed;
- one seeded example report, `MRR-20260831-001`.

**`B_Inputs`:** `git status --porcelain B_Inputs` was clean after both CLI resets and after FS-21's four API resets. Every file was reported "unchanged", so not even the known G0.15 timestamp churn appeared.

---

## 2. Summary

| | |
|---|---|
| Scenarios in scope | **2** (FS-21; FS-25, which has 2 tests): 3 Playwright tests |
| Pass | **2** (3 of 3 tests), on two separate runs at `a4f17ce` |
| Fail | 0 |
| Flaky | 0 (one retry was allowed; none was used) |
| Not built | — (out of scope this run) |

**New issues: 0 Critical · 0 High · 0 Medium · 0 Low.** Two known Low findings were seen again in passing screenshots (§4).

**Verdict on this scope: Ready.** End to end in the browser and API:
- **D17 holds.** The seeded example's generation time is real, and the list, the reopened report and the PDF all show the same instant.
- **CR-67 holds.** Generating a report while a reset runs is refused with 409. Nothing is stored and nothing is audited.
- **REG-15, REG-16, REG-17, D14, S13, GEN-01, GEN-04 and GEN-05 still pass.**

### Harness extended (H-23), and shown to fail on the old code

**FS-25, second test (D17).** The test now checks that the seeded example's `generated_at`:
- does not start with `<business_date>T09:00`;
- falls inside the last reset's lock window (`acquired_at`…`released_at` from `/api/admin/reset/status`, with the start floored to the second);
- is no later than the generated reports' times.

It also checks that the reopened report shows `Figures reconciled with the Command Center at generation, <the same instant, formatted by the browser>.` Finally, the PDF must contain `… at generation, <YYYY-MM-DD HH:MM:SS>` and must not contain `<business_date> 09:00`.

**FS-21, second reset (CR-67).** While `reset_lock.holder` is set, the test calls `POST /api/reports/model-risk` as Admin, who holds `REPORT_GENERATE`. It retries on 401/403 (BL.1), and any 2xx or 5xx fails the test. It then asserts:
- the response is 409, and its body says a reset is running;
- no new `model_risk_report`/`generate` audit event was written;
- once the reset is idle, `model_risk_report` holds exactly one row, the seeded example. This proves nothing was stored.

**Discrimination test.** I ran both scenarios against a backend built from `b8cc1f3`'s `app/` package; `report_service.py` is the only product difference. I used the same test database, then deleted the copy afterwards.
- FS-21 failed: *"CR-67: report generation during a reset must be refused with a conflict — received 'report generation during a reset answered 500'"*. The old code also answered **500** rather than 201 mid-reset. That is moot now, but it means CR-67 also closed a 500 path.
- FS-25's second test failed on *"D17: generated_at is no longer shaped to 09:00"*, because the old row held `2026-08-31 09:00:00`.

Then I reset again at `a4f17ce` and re-ran: 3 of 3 passed. The backend log shows `POST /api/admin/reset 409` (GEN-04) and `POST /api/reports/model-risk 409` (CR-67) on both runs, and no 5xx.

I took a snapshot of each file before editing it:
- `_OLD/AF_e2e/functional/reports.spec_v3_20261016.ts`
- `_OLD/AF_e2e/functional/import.spec_v8_20261016.ts`
- `_OLD/AF_e2e/functional-scenarios_v9_20261016.md`

The catalogue's FS-21 and FS-25 rows now name CR-67 and D17, and H-23 records the change.

---

## 3. Scenario table

| FS-ID | Journey | Criteria | Role | Result | Issues |
|---|---|---|---|---|---|
| **FS-21** | Two resets give the same counts and reload 1,116 documents. A concurrent reset is refused 409 and names the batch. **A report generated during a reset is refused 409 and nothing is stored or audited (CR-67)**. Idle status means the lock is free, the outcome is Completed and exactly one seeded report exists | GEN-01, GEN-04, GEN-05; CR-67 (REG-16 refusal clause) | Admin | **Pass** (23.7 s, 23.1 s) | FT-11 re-observed (Known, BL.32) |
| **FS-25** test 1 | Generate as Validator. The figures equal the Command Center, and generating again gives the same hash with one audit event per generation. The Executive is refused in both the UI and the API, with nothing stored or audited. The Executive and Auditor can download | REG-15, REG-16, REG-17 | Validator, Executive, Auditor | **Pass** | FT-10 re-observed (Known, BL.29) |
| **FS-25** test 2 | D14's label appears on the list, the reopened report and the PDF. **The D17 real generation time appears on all three**. With S13, a decision recorded in the UI lands in the changes section, and the next hash is unchanged | REG-16, REG-17, D14, **D17**, S13 | Auditor, MRC Member | **Pass** | — |

REG-01…REG-14: *Not built (Phase 2A, deferred D12)*. They are not exercised by this scope.

---

## 4. Issue index

No new FT issues. No status changes: no issue in scope was `Fixed`, and FT-09 stays Verified.

Known findings seen again:

| ID | Severity | Title | Layer | Status | Evidence this run |
|---|---|---|---|---|---|
| FT-10 | Low | The report prints internal keys (`validation_currency`, `documentation`) and lists without separators (`Model Development Document,Model Approval/MRC Paper`) | Frontend | Still open, Planned (BL.29) | `20261016/screens/FS-25_d14_reopened.png`: the Lowest-scoring and Documentation tables |
| FT-11 / MP-20 | Low | The revalidation timeline clips the Outcome and Status columns at 1440 px | Frontend | Still open, Planned (BL.32) | `20261016/screens/FS-21_after_two_resets.png`, where the OUTCOME header is cut at the panel edge |

BL.1 (users get 401 for a few seconds mid-reset) was seen again and handled by re-authenticating. It is not a finding.

Checks on the passing screenshots: the screens showed no blank panels, raw errors, "undefined" or "NaN". The Command Center after two resets shows 256 models, 89 High and 31 in the revalidation queue, matching the reopened report's Inventory and Stage tables. On the list, the seeded example's time (10/16/2026, 12:48:18 AM) is earlier than the two generated reports' times, and the reopened header shows the same instant.

---

## 5. Unspecified behaviour

None found in this scope.

---

## 6. Inputs used

None uploaded. FS-21 and FS-25 use no input files. The seed came from the committed `B_Inputs/AC_seed` through `app.cli reset` and the Admin reset API, and its content was unchanged.

---

**Counts:** Pass 2 scenarios (3 of 3 tests) · Fail 0 · Flaky 0. **Open Critical/High from this run: 0.**
