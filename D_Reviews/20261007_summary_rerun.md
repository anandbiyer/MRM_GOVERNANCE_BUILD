# Gate 0 exit review (R3), re-run — 2026-10-07

**Verdict: Ready.** No open Critical or High finding; all three CI gates green; the functional suite
passes end to end; 0 Missing and 0 Partial parity items. §84's bar is met and **Gate 0 closes.**

The run did find one new High — **CR-29**, a missing `_OLD/` snapshot in G0.23 — and it is **closed in
`c8deaaf`**, by the same remedy the triage directed for CR-22: recover the pre-edit content from git.
Nothing else new is above Medium.

| | |
|---|---|
| Branch / commit | `review-agents` @ `779e3de`; the two testers ran at `c8deaaf`, which is product-identical (`git diff 779e3de c8deaaf` over backend, frontend, seed and `B_Inputs` is empty — verified by the parity agent) |
| Scope | Gate 0, rows G0.1–G0.26 (`E_ProjectPlan/project_plan.md` §3) |
| Agents | all four |
| Previous run | 2026-10-07 @ `f89ef6a` — **Not ready**, 1 Critical + 6 High ([`20261007_summary.md`](20261007_summary.md)) |
| CI gates | backend **184 pass / 4 skip**; PostgreSQL **4 / 4**; frontend build **green** |
| Criteria proven | **72 of 118** (72 of 88 built) — §76A 46/60 · §76D 0/17 · §77 0/12 · §78 17/20 · §79 9/9 |
| Functional | **25 pass · 0 fail · 0 flaky** · 6 not built (was 18 pass / 6 fail) |
| Parity | **23 Match · 0 Partial · 0 Missing** · 5 accepted · 10 not built (38 IDs) |

## The previous run's Critical and High findings

All seven closed, each confirmed by the agent that raised it rather than by the author.

| ID | Sev | Closed by | How it was confirmed |
|---|---|---|---|
| **FT-04** | Critical | G0.22 `df49c3f` | **Verified.** Eleven resets by three entry points, all in thread mode, every one loading **1,116** documents and ending `Completed`; 0 lock errors, 0 tracebacks, 0 HTTP 500s across the run. Completeness back to 63.6% / 92 models with gaps, against 0% while the defect was live |
| **FT-05** | High | G0.23 `e126a12` | **Verified live, not read:** a 400-file batch still `Validating` cancelled with **HTTP 200** where it previously returned 409. The crash-recording path is wired into all three jobs and driven by three backend tests; inducing a real crash needs a product edit the tester correctly did not make, so that half is Confirmed as code and Likely at runtime |
| **MP-10 / FT-06** | High | G0.24 `2c7d4b9` | **Verified on a UTC−4 host**, independently of the new FS-26. Lede "as of 9/30/2026"; M-0012 4/16/2026, 4/16/2027, 8/9/2024 — the API values exactly. The cross-screen half: M-0188 now reads `7/5/2026` on **both** the timeline and Model 360. Cross-checked arithmetically — the printed date and the printed day count agree, where before they contradicted each other by one |
| **CR-21** | High | G0.25 `2564c4a` | **Closed, and the reviewer judges the generalisation better than its own suggested fix.** It also confirms its earlier note was wrong: only `monitoring_phase` was in `CONTEXT_KEYS`, so following the suggestion literally would have left four settings unguarded |
| **CR-22** | High | triage `02b3ccf` | **Closed, diff-verified byte for byte** — each recovered snapshot matches the commit state it claims to record |
| **TR-25** | High | G0.26 `aeb31be` | **Closed, re-derived with the reviewer's own mutations:** 4 of 6 now fail, including two I did not try |
| **TR-26** | High | G0.26 `aeb31be` | **Closed decisively: 6 of 6 fail**, including the original CR-05 defect |

**TR-24 withdrawn by the agent that raised it.** A bare `db.commit()` before `audit.record` in
`create_model` fails **8** tests, not the suite-green it reported, because it breaks the import
engine's per-row SAVEPOINTs. The coverage gap underneath does reproduce with a narrower one-line
variant that spares every importer, so AUD-01 stays **Weak** and Medium (BL.13) — the oldest open
test finding in the project.

## New Critical and High

| ID | Source | Sev | Criterion | Problem | Status |
|---|---|---|---|---|---|
| **CR-29** | requirements | High | Part 0 convention | G0.23 edited `app/documents/batch.py` and `app/services/reset_service.py` with no fresh `_OLD/` snapshot. The copies taken during G0.22 record the **pre-G0.22** state, so the FT-04 ordering fix as first written existed only in git. Diff-verified by the reviewer: no `_OLD/` copy matched `e126a12^`. CR-22's own failure mode, inside the commits convened to close CR-22 | **Closed `c8deaaf`.** Both recovered from `e126a12^` and confirmed identical to the G0.22 content. Not systemic — two of the commit's four files *were* snapshotted and `snapshot.sh` increments correctly; the author applied a stricter rule to the test files than to these two |

Nothing else new is Critical or High, in any of the four reports.

## Where the author's own claims were wrong

Recorded because each would otherwise stand in the plan or in CLAUDE.md as fact.

| Claim | Reality | Finding |
|---|---|---|
| G0.25's commit and plan row: the `effective_weight` assertion is what catches the score rising | **It is not.** Restoring the literal-phase defect fails four assertions earlier, at `required == required_before`. The score and weight assertions are correct belt-and-braces for a *rescaling* defect but never fire for CR-21 itself | TR-35, Low |
| §76A.14: GEN-04 is carried by the reset tests "from G0.23 onwards" | **No test names GEN-04 at all** — the four tests credited carry GEN-02. GEN-04 is the only Gate 0 criterion whose ID appears nowhere, which defeats the grep contract the section is built on | TR-31, Medium |
| FS-21 was renamed to claim `GEN-04` and `GEN-05` | The scenario **never exercised** the concurrent-reset refusal. The functional tester added the real probe: a mid-reset second `POST /api/admin/reset` must return 409, name the batch, and create no batch row | fixed in the run |
| FT-04's regression test asserts "no write after the submit" | It listens on SQLAlchemy's **Session** `after_commit`, so it proves no *Session* commit. An Engine-level post-submit write, or an uncommitted transaction still open at submit time, races the job identically and leaves the suite green | TR-34, Low |
| `mockup-parity.md` MUP-04: the app shows all of §10's list | **It does not.** Owner, Last validation and Latest outcome are on no revalidation view — only on Model 360, one model at a time — although `/api/dashboard/summary` already returns all three on every timeline row. §10 is a BRD requirement, so this cannot be an accepted difference | MP-17, Medium, **explicitly not new** |

**MP-17 needs a decision, not triage.** The 2026-10-07 triage accepted MP-08 as "no BRD requirement";
that is true of the frequency column and the distribution chart, and false of §10's owner/last
validation/latest outcome. The parity agent corrected the entry and split the live part out. The fix is
three columns in the UI and no backend change.

## Spec issues

| ID | Issue | Status |
|---|---|---|
| **S9** (new) | **SEC-07 asserts more than the code does.** Its last clause — "no value fetched under the previous identity is presented under the new one" — is not met: `resetCachesAndIdentity` only invalidates, so inactive queries serve previous-identity values on next mount. Either the criterion loses the clause or the behaviour is fixed | needs a decision |
| **S7** | The three Gate 0 behaviours had no criterion | **closed** by SEC-07, GEN-04, GEN-05 (`779e3de`) |
| S3 | T04 still has no `evidence` column | open, unchanged |
| S5 | Part 0's "the only place that writes" overstates it | open, and now load-bearing: the verdict on `record_job_failure` rests on it |
| S8 | `breach_severity_rules` ships `High`, a severity no vocabulary contains | open — D3 / D7, Phase 6 |
| S1, S2, S4, S6 | — | closed |

## Medium and Low

**Medium 5:** CR-30 (cancel on a running batch is audited then overwritten — nothing reads
`"Cancelled"`), CR-31 (the failure wrapper misses `_reset_job`'s own first stage and the status
restore, so a reset can still leave a non-terminal batch), CR-32 (= S9), TR-31 (GEN-04 untagged and
its "nothing deleted / no second job" clause unasserted), MP-17 (not new; see above).

**Low 14:** CR-33…CR-39, TR-32…TR-36, MP-15 (the app shows two different calendar days for events
minutes apart, because the API serialises `score.calculated_at` zone-aware and four other timestamps
naive — *not* a G0.24 regression, but a latent trap that becomes live the moment the backend is made
consistent), MP-16 (`retention_start`/`retention_end` print raw ISO in the very `<dl>` G0.24 fixed).

**Carried and already triaged:** 18 requirements findings (BL.10–BL.23), TR-23, TR-24, TR-27–TR-30,
FT-07, FT-08, MP-13, MP-14.

## Reports

- `D_Reviews/DA_code_review/20261007_gate0_rerun.md` — requirements (0 Critical, 1 High, 3 Medium, 7 Low)
- `D_Reviews/DB_test_review/20261007_gate0_rerun.md` — tests, raw gate output under `20261007/*_rerun.*`
- `D_Reviews/DD_functional_test/20261007_gate0_rerun.md` — functional (0 new, 25/25 pass)
- `D_Reviews/DC_mockup_review/20261007_gate0_rerun.md` — parity, 72 screenshots under `20261007/`

## What the gate confirmed as sound

- **Every one of the previous run's seven Critical and High findings is closed**, and each was
  re-verified by the agent that raised it, with its own mutations or its own measurements rather than
  by reading the fix.
- **No regressions.** No test that passed at `f89ef6a` fails now; no criterion moved down; parity
  Missing stayed at 0 across 38 IDs.
- **The five fixes were measured in the mode the defects live in**, not only in the one CI can see:
  FT-04 and FT-05 in thread mode against file-backed databases, MP-10 on a host behind UTC.
- **Thirteen criteria moved from "confirmed by hand" to proven by the functional suite**, including
  DOC-07, DOC-13 and DOC-18, which no scenario had asserted before.
- **Nine harness defects fixed by the functional tester** and two more it found itself (H-15, H-16),
  one of which would otherwise have been reported as an audit defect that did not exist.
- **`B_Inputs` clean after all eleven resets** — G0.15's normalisation holds under real use.
- The demo database was untouched by every agent; both testers stopped the servers they started.

## Two things not to lose in the Backlog

Both agents volunteered these, and they are right to.

1. **GEN-04 is the only Gate 0 criterion whose ID appears in no test** (TR-31). It is a one-line
   change per test and it should go with the §76A.14 update, because the section's own prose currently
   contradicts its tables.
2. **AUD-01's rollback half still covers one service of seven** (TR-24, BL.13). The evidence for it
   changed this run; the gap did not.

## The merge hook cannot be satisfied as written

Recording a Ready verdict necessarily creates a commit after the one reviewed, and
`.claude/hooks/review_gate.py:123` requires `entry["head"] == HEAD` exactly. So the sequence is: merge
refused → run the review → the review's own summary commit moves HEAD → merge refused again. This has
never shown before because no gate had reached Ready.

`head` below is recorded as **`c8deaaf`**, the tree the testers ran against. The merge to `main` will
be refused until the rule is relaxed — the obvious form being "the recorded head is an ancestor of
HEAD and nothing under `A_Codes/` or `B_Inputs/` has changed since", which keeps the guarantee that
matters (no unreviewed product change reaches `main`) while allowing the review to record itself.
**Not changed here:** the hook is the control, and loosening a control is the user's call, not the
reviewed party's.
