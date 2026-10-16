# Gate 1 exit re-run (R3): core Model Risk Report, requirements

**Scope:** Gate 1 while **D12** holds. This is a re-run scoped by the owner after the triage of
`20261015_gate1_exit.md`. Criteria in scope:
- REQ-REG-10A, including **S13**, **D14** (with `figures_as_of`) and **D17**.
- **REG-15, REG-16, REG-17** (§76D).
- **GEN-04, GEN-05** as reworded by **D16** (§76A.12).
- **PLT-01…PLT-03** (§76E).
- The Part 0 invariants and the snapshot convention over the commits since `b8cc1f3`.
- Confirmation that CR-67, CR-68, CR-69, CR-70 and SI-1 are closed in code or spec.

Date 2026-10-15 · branch `gate-1-core-report` · commit **`a4f17ce`** · agent `requirements-reviewer`.
Commits reviewed since the last run: `4c927e4`, `c72bb97`, `3994f43`, `a4f17ce`. REG-01…REG-14 are
*Not built (Phase 2A, deferred D12)*.

Paths are relative to `A_Codes/AB_backend/` unless they start with `A_Codes/`, `claude.md`,
`.github/`, `E_ProjectPlan/` or `D_Reviews/`.

---

## 1. Summary

| Criteria in scope | Count | IDs |
|---|---:|---|
| Implemented | 8 | REG-15, REG-16, REG-17, GEN-04, GEN-05, **PLT-02**, **PLT-03** (both were Partial), REQ-REG-10A (S13, D14, D17) |
| Partial | 1 | PLT-01 (BL.31, carried, unchanged) |
| Missing | 0 | — |
| Not built (Phase 2A, deferred D12) | 14 | REG-01…REG-14 |

| Severity | New | Closed since last run |
|---|---:|---|
| Critical | 0 | — |
| High | 0 | CR-68 (= TR-87, the High that held the gate) |
| Medium | 0 | CR-67 |
| Low | 2 (CR-71, CR-72) | CR-69 in code; CR-70 for PLT-02/03 (PLT-01 half held as TR-99) |

Every item the triage put into G1.33 and G1.34 is in the code, and I checked each one at the line
where it lives.

**The snapshot control (G1.33).**
- `diff-tree` now runs with `-M`.
- For a rename, the pre-change content is read at the **source** path in the parent.
- A snapshot named for either end of the rename is accepted.
- The count line reports file edits, not only commits.
- The grandfather cut-off reads the committer date.
- The CI base is resolved in a `--ci` mode that has tests, instead of in untested shell.
- PLT-02 and PLT-03 are named in the self-test.

**The report (G1.34).**
- `report_service.generate` refuses with 409 while the reset lock is held. It checks after the
  permission check and before any read or write.
- The seeded example no longer shapes `generated_at`, so D17 (a) is built.

**D16.** GEN-04 and GEN-05 now describe the reset lock, and the code matches the new wording.

**Snapshot convention.** My own content-hash walk of all four commits found 12 hand edits and
0 missing snapshots.

Two new Lows:
- **CR-71.** The CR-67 guard is a check-then-act. A reset that claims the lock *after* the check, while
  a generation is still computing, can still race it. The window is narrow.
- **CR-72.** One sentence of the D14 text in REQ-REG-10A still says the seeded `generated_at` is set
  to the illustrative date. Two lines below, D17 says it is not.

**Verdict on this agent's scope: Ready. 0 Critical, 0 High open.**

---

## 2. Traceability

### 2.1 Criteria

| BRD § | Criterion | Status | Evidence (path:line) | Notes |
|---|---|---|---|---|
| §12A.2 REQ-REG-10A, §76D | **REG-15** | **Implemented** | `sections` `app/services/report_service.py:307`; always `today()`, no date parameter (`generate` `:358`, `on = today()` follows the guard); `app/api/reports.py:16-28` | Unchanged since `b8cc1f3` apart from the CR-67 guard, which comes before any figure is computed. |
| §12A.2, §76D | **REG-16** | **Implemented** | hash excludes only `changes_since` `report_service.py:55`; permission then **CR-67 409** `:365-377`; one audit event in the same transaction as the row `:402-407`; test `tests/test_reports.py:950` | A refused generation happens before `get_store().put`, `db.add` and `audit.record`. So a 409 stores no blob, no row and no event. The test asserts the row count and the audit count before and after. |
| §12A.2, §76D | **REG-17** | **Implemented** | list/reopen/PDF `app/api/reports.py:31-51`; reconciliation line `app/reports/pdf.py:71-81`; test `tests/test_reports.py:922` | **D17:** the seeded row no longer passes `generated_at` (`report_service.py:470-473`), so the column's `server_default=func.now()` applies (`app/models/reports.py:26`). The test checks the full PDF line, including the timestamp, against a window around the real reset. |
| REQ-REG-10A S11/S12, **D14**, **D17** | (header) | **Implemented** | seeded `figures_as_of=today()` `report_service.py:478`; generated `figures_as_of=on` `:392`; D17 text `claude.md:994-996`; decision `E_ProjectPlan/decision_log.md:740` | **TR-83 and TR-84 closed** in code. Nothing in `app/` or `src/` still renders a shaped time: the only remaining `09:00` is the explanatory comment at `report_service.py:470`. `latest()` (`:286-291`) orders by `generated_at`. The seeded example's time is now real and earlier than any report a user generates after the reset, so the predecessor chain is unchanged. The spec still contains one stale sentence about this (CR-72). |
| §76A.12 | **GEN-04** (D16) | **Implemented** | 403 first `app/services/reset_service.py:273-276`; read-first `:288-290`; claim, with a database-lock refusal mapped to 409 `:291-300`; claim before `regenerate_seed` and deletes `:301-311`; message naming the batch or "(being created)" and the stage `:250-260`; `runner.submit` only after the claim `:318` | Matches the D16 wording clause by clause (`claude.md:3447-3453`). TR-79 (unrelated contention reported as "already running") and TR-80…TR-82 are in BL.38 and unchanged. |
| §76A.12 | **GEN-05** (D16) | **Implemented** | lock held from the claim to the `finally` release `reset_service.py:396-412`; outcome and stage recorded on every failure `:312-315`, `:405-410`; status endpoint reads only the lock `app/api/admin.py:38-53`; startup release `app/main.py:17-34` → `reset_service.py:215-237` | Matches the D16 wording (`claude.md:3455-3462`), including "there is no API to release it". **SI-1 closed.** |
| §76E | **PLT-01** | **Partial** (carried, BL.31) | `report_service.py:278` (`previous_generated_at` naive inside the untyped `sections`); `tests/test_api_timestamps.py:1-4` | Unchanged. D17 adds one more naive value that reaches `sections`: the seeded example's `generated_at` is now the server default. It is serialised through the same unnormalised path as every user report's, so this is not a new class of defect. |
| §76E | **PLT-02** | **Implemented** (was Partial) | `-M` `A_Codes/AZ_tools/check_snapshots.py:128`; source and destination paths kept `:136-142`; `before` read at the source `:151`; pure rename skipped `:155-156`; candidates for either name `:161`; tests `A_Codes/AZ_tools/test_check_snapshots.py:245-277` | **CR-68 / TR-87 closed.** Residual held items: TR-96 (renames below the similarity threshold are reported as delete+add, see §5) and TR-97 (the wording still says "authored"). |
| §76E | **PLT-03** | **Implemented** (was Partial) | `--ci` base resolution `check_snapshots.py:173-194`, `:201-206`; empty base refused `:209-212`; `-z` and `core.quotePath=false` `:74`, `:128`; count of file edits `:242-243`; committer date `:226`; CI `.github/workflows/ci.yml:146-158` (`fetch-depth: 0` `:130-131`); tests `test_check_snapshots.py:279-336` | **CR-69 closed in code.** TR-98 is held: a manual run on the default branch is an empty range and exits 0. |
| §76D | REG-01…REG-14 | **Not built (Phase 2A, deferred D12)** | — | §7 |

### 2.2 Rows in scope

| Row | Plan | Verified in code | Notes |
|---|---|---|---|
| **G1.33** (TR-87 = CR-68, TR-88, TR-89, CR-69, TR-90 = CR-70) | Done | **Yes** | See PLT-02 and PLT-03 above. TR-90/CR-70 is closed for PLT-02 and PLT-03 only. The PLT-01 half is held as TR-99: `tests/test_api_timestamps.py:3` still says "No acceptance criterion covers this". |
| **G1.34** (TR-83, TR-84, CR-67) | Done | **Yes** | See REG-16, REG-17 and the header row above. |
| G1.16–G1.32, G3.0 | Done | Unchanged since `b8cc1f3` | `git diff b8cc1f3..a4f17ce -- A_Codes/AB_backend` touches only `report_service.py` and `test_reports.py`. No migration, model or schema changed, so §48 conformance (`model_risk_report`, `reset_lock`) stands as reported at the last run. |

---

## 3. Findings

Both findings are new and both are Low.

| ID | Severity | BRD § / criterion | What is wrong | Evidence | Suggested fix |
|---|---|---|---|---|---|
| **CR-71** | Low | REQ-REG-10A (S11), REG-16; §64 Reliability | **The CR-67 guard is check-then-act, so a reset that starts during a generation still races it.** `generate` reads the lock once (`:372`), then computes every section, puts the JSON in the store and commits (`:379-407`). `start_reset` does not consult in-flight generations. It claims the lock and deletes `ModelRiskReport` first (`reset_service.py:58`). Two outcomes are possible. On **SQLite WAL**, the generation's read snapshot is stale by the time it writes, so the insert fails as an `OperationalError` (500) and leaves an orphan blob in the store. On **PostgreSQL** under READ COMMITTED (the BRD's system of record), the insert either violates the self-FK on a deleted predecessor (500), or, with no predecessor, succeeds over a half-cleared portfolio. The second is exactly what CR-67 set out to prevent. The window is the few seconds of the reset's first stages, so this is Low. | `app/services/report_service.py:369-377` (single read), `:379-386` (store put before commit), `:403-407`; `app/services/reset_service.py:58`, `:288-300` | Serialise the two against the lock row instead of reading it. In `generate`, read the lock row `FOR SHARE` in the same transaction that inserts the report (a no-op on SQLite, where the single writer already serialises). On PostgreSQL, the reset's conditional `UPDATE` then waits for the generation to commit, and a generation that starts after the claim sees the holder. Alternatively, re-read the lock immediately before `db.add` and treat an `OperationalError` there as the same 409. Backlog, with BL.38. |
| **CR-72** | Low | REQ-REG-10A D14 / D17; spec consistency | **REQ-REG-10A contradicts itself about the seeded `generated_at`.** The D14 paragraph says `figures_as_of` is "not `generated_at`, which on the seeded example is itself set to the earlier illustrative date". The D17 sentence a few lines later says the seeded `generated_at` "is the real time it was computed — not shaped to its illustrative date". The code follows D17. | `claude.md:988-989` (stale) vs `claude.md:994-996` (D17); code `app/services/report_service.py:470-473` | Edit the D14 sentence to end at "…and not `generated_at`, which records when the report was computed (D17)". Documentation only. See §4, SI-2. |

---

## 4. Spec issues

- **SI-1 (previous run): closed** by **D16**. The new GEN-04/GEN-05 wording (`claude.md:3447-3466`)
  describes the lock, the startup release and the absence of an API release, and the code matches it
  (§2.1).
- **SI-2 (new): the seeded `generated_at` is described two ways in REQ-REG-10A.** See CR-72. This is
  decided by **D17**; only the text needs to catch up.
- **TR-96: decision pending for the owner. My comment, not a ruling.** A file moved and heavily
  rewritten (below git's 50% similarity), or moved when a decoy copy of the source exists, appears as
  delete plus add. PLT-02 exempts both deletes and adds (`claude.md:3885-3889`), so the change is not
  charged.
  - Part 0's convention 1 is "Never delete or silently rewrite code" (`claude.md`, Part 0 →
    "Two repository conventions"). PLT-02's delete exemption is therefore narrower than the
    convention it enforces, which is a genuine contradiction and not a code defect.
  - Option (a) in TR-96 charges deletions of covered files. That is consistent with Part 0's
    wording. It also has no retroactive cost: `git log --no-merges --diff-filter=D` shows **no**
    deletion of a covered hand-edited file (outside `_OLD/` and the generated seed folders) anywhere
    in history, so it would not turn the job red.
  - Option (b) amends PLT-02 to declare the limit. It is cheaper, but it keeps an evasion path for
    exactly the "silently rewrite" case in a control that, by its own docstring, fails open when it
    is defective.
  - Either way, a self-test case should make the chosen behaviour visible.
- **TR-97 (held), status update.** The word "authored" survives in three places, while the code uses
  the committer date (`A_Codes/AZ_tools/check_snapshots.py:226`; its own docstring `:37-39` is
  already correct):
  - PLT-02 (`claude.md:3889`);
  - Part 0 (`claude.md:135`, "commits authored before 2026-10-09");
  - the `ENFORCED_FROM` comment (`A_Codes/AZ_tools/check_snapshots.py:68`).

  This is the same item, with one more location than TR-97 named.
- **§76A.14** still lists §76E as "0/3 (3 Failing)" (`claude.md:3526`, `:3537-3539`). PLT-02 and PLT-03
  are now Proven by the G1.33 checkpoint. As Part 0 requires, the test-outcome reviewer recalculates
  the table; I only note the stale figure.

---

## 5. Invariants (Part 0), over `b8cc1f3..a4f17ce`

| Invariant | Result |
|---|---|
| **Writes only in services** | **Holds.** The only product-code change is inside `app/services/report_service.py`. Nothing changed under `app/api/`, `app/ingestion/` or `app/rules/`. |
| **Audit in the same transaction** | **Holds.** The 409 is raised before any write. The success path is still add → `audit.record` → commit (`report_service.py:402-407`), and the seeded path is still add → `audit.record` → commit (`:467-482`). |
| **`app/rules/` is pure** | **Holds.** Untouched. |
| **`app.clock.today()`** | **Holds.** No new `date.today()` or `datetime.now(` in `app/`. Removing `datetime.combine(on, time(9, 0))` removes one hand-made timestamp. The remaining `datetime.now(UTC)` sites are the wall-clock class already carried (CR-14). |
| **No business number in code** | **Holds.** Nothing new. The seed-shaping constants are unchanged (CR-45, BL.33). |
| **Mutating routes behind `deps.require`** | **Holds.** No route changed. `POST /api/reports/model-risk` stays behind `REPORT_GENERATE` (`app/api/reports.py:19`). The 409 message points to `GET /api/admin/reset/status`, which every signed-in principal can read (`app/api/admin.py:38-39`), so the advice it gives can be followed. The page shows the message (`A_Codes/AC_frontend/src/pages/ModelRiskReportPage.tsx:201`, `:236`). |
| **Derived state on read** | **Holds.** Unchanged. |
| **Templates defined once** | Not applicable. |
| **Snapshot convention** | **Holds: 12 of 12.** I compared each modified file's parent content, CRLF-normalised and SHA-256 hashed, against every `_OLD/` file at HEAD with a matching stem. `4c927e4`: 7 `AF_e2e` files → `functional-scenarios_v8`, `index_v2`, `import.spec_v7`, `reports.spec_v2`, `mockup-parity_v7`, `screens_v3`, `parity.spec_v8`. `3994f43`: `check_snapshots_v2`, `test_check_snapshots_v1`. `a4f17ce`: `report_service_v10`, `test_reports_v10`, `test_check_snapshots_v2`. `c72bb97` touches no covered file. `.github/workflows/ci.yml` changed. It is outside the convention's roots, but under the hook's protected set, so this re-run is the review it needs. |

---

## 6. Carried and held findings: changes in status only

| ID | Status now | Evidence |
|---|---|---|
| **CR-67** (Medium) | **Closed** (residual race: CR-71) | `report_service.py:367-377`; `tests/test_reports.py:950` |
| **CR-68 = TR-87** (High) | **Closed** | `check_snapshots.py:128`, `:151`, `:161`; `test_check_snapshots.py:245-277` |
| **CR-69** (Low) | **Closed in code**; wording is TR-97 | `check_snapshots.py:226`; `test_check_snapshots.py:303-309` |
| **CR-70 = TR-90** (Low) | **Closed for PLT-02/PLT-03**; PLT-01 half is TR-99 (held) | `test_check_snapshots.py:245-336`; `tests/test_api_timestamps.py:3` |
| **TR-83, TR-84** | **Closed** by D17 / G1.34 | `report_service.py:470-473`; `tests/test_reports.py:922` |
| **SI-1** | **Closed** by D16 | `claude.md:3447-3466` |
| CR-46 / PLT-01 (BL.31) | Unchanged | `report_service.py:278` |
| TR-79…TR-82 (BL.38), CR-63…CR-65 (BL.39), CR-43/CR-56 (BL.29), CR-44/45/48–51 (BL.33), CR-58 (BL.35), CR-60…CR-62 (BL.39) | Unchanged; the code at the cited lines did not move except by the 11-line shift in `report_service.py` after `:366` | — |
| TR-94, TR-95 | Fixed in-row per the plan (`E_ProjectPlan/project_plan.md:177`) | — |
| TR-96…TR-99, TR-110…TR-114 | Held; no code change since their checkpoints | §4 |

---

## 7. Not built

- **REG-01…REG-14**, templates T19–T21, §12A columns on T02: **Not built (Phase 2A, deferred D12).**
- **MON-01…MON-20**, T13–T16, T07–T09: Not built (Phase 6).
- **DQ** criteria (§76B), T06, T10: Not built (Phase 7).
- **DOC-16**, AI extraction: Not built (Phase 5).
- **COP** criteria (§76C), Audit Copilot: Not built (Phase 9).
- AI commentary on the report: Phase 9, under REQ-REG-10A. The report is complete without it.

---

## 8. Verdict

**Ready on this agent's scope: 0 Critical, 0 High open.**

The one High that held Gate 1 (CR-68 = TR-87) is closed in the code and covered by named PLT-02 cases.
CR-67 and D17 are built as decided, and D16 brings GEN-04/GEN-05 into line with the code. Every
Part 0 invariant holds over the four commits, and the snapshot convention holds 12 of 12.

The two new Lows (CR-71, CR-72) and the pending TR-96 decision belong in the Backlog or the decision
register under the scope-freeze rule. None of them affects data integrity, security or the demo enough
to enter the gate.
