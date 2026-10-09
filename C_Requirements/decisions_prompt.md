Record my open decisions so that every remaining gate can be built. This is a documentation-only session on branch `decisions-d1-d7`: **no changes to product code, tests, seed data, `B_Inputs/` or the T12 policy files.**

Work in **three stages** and **STOP at the end of each one** for my approval. Do not merge until I approve stage 3.

| Stage | Decisions | Status today |
|---|---|---|
| 1 | D1, D2, D3, D4, D6, D7 (monitoring) | My decisions are written below; record them |
| 2 | D8 (Data Audit criteria), D11 (Copilot criteria) | You draft them; I approve |
| 3 | D13 (AI provider for Gates 5 and 6) | New; I choose |

D5, D9, D10 and D12 are already decided and are not changed here.

---

## Stage 1 — D1, D2, D3, D4, D6, D7

Record each one as **Decided 2026-10-09** in `decision_log.md` (decision, reason, consequences, affected sections) and in the §81A Decision column. New policy keys named below are added during Gate 3, not now.

### My decisions


#### D1 — KPI and monitoring tables
`monitoring_metric` and `monitoring_result` are the only system of record. `kpi` and `kpi_result` are **not created**. T07 (KPI Definitions) and T08 (KPI Results) stay as import aliases that write through the same services as T14 and T15, so older files still load. T09 (Performance Curves) loads into `performance_point`, which gains a `monitoring_run_id` foreign key, so every curve belongs to a run.
*Reason:* one source of truth for thresholds and history; avoids two Pass/Warn/Fail calculations disagreeing.

#### D2 — Bounds for "within range"
`monitoring_metric` gains `range_lower` and `range_upper`, used only when `direction` = within range, and both are required in that case. Inside the bounds (inclusive) gives Pass; outside gives Fail. Warn is not used for within-range metrics in this release. Following MON-05, the bounds are copied onto each result as `range_lower_applied` and `range_upper_applied` when the result is evaluated.
*Reason:* the smallest rule that is unambiguous. A warning band can be added later without changing history, because the applied bounds are stored on each result.

#### D3 — Rule-created breaches versus T16
- Breaches are created **only by the rules**: on a Fail, and on a Warn escalated under D5's `warning_escalation_periods`.
- A T16 row must match an existing breach on `monitoring_run_id` + `metric_id`. It may update status, owner, due date, root cause, impact, management response and resolution. It never creates a breach and never changes severity.
- An unmatched T16 row is rejected, with a message naming the row and the two keys.
- Breach severity gets its own vocabulary, policy key `breach_severities` = Low, Medium, High, Critical. This is separate from `finding_severities`, which closes the gap noted under D5. When a breach becomes a finding (MON-09), its severity is mapped by policy key `breach_to_finding_severity`.
- Breach statuses follow §20. As with findings under D10, Accepted Risk and Closed count as not open.

*Reason:* one place creates breaches, so counts and escalation are reproducible; imports carry the human part of the work.

#### D4 — Backtesting
A backtest is a `monitoring_run` with `monitoring_type` = Backtest. Its methodology and sample period are recorded on the run (`methodology`, `data_period`), and its results are `monitoring_result` rows against metrics whose category is Backtest. Screens show backtests separately from routine monitoring. The Model 360 backtesting grid (MUP-18) reads from these runs. Backtest runs do not feed the monitoring score (D6).
*Reason:* reuses runs, results, thresholds, evidence and breaches unchanged; no new table.

#### D6 — Monitoring score component
- **Models in the Monitoring phase.** The component is the share of the model's active metrics whose latest result, in the latest signed-off non-backtest run, is Pass. Not Applicable results are excluded from both numerator and denominator. Not Available results are excluded too, and listed under the score's "Missing information".
- **Monitoring-phase model with no active monitoring plan:** the component is 0, with "No active monitoring plan" as missing information.
- **Models in any other phase:** the component is excluded and the remaining weights are rescaled, as today.

*Reason:* simple, explainable (§57), and it makes a missing plan visible instead of rewarding it.

#### D7 — Missing monitoring criteria
Add criteria **MON-13 to MON-20** to §77, worded as below. You may tighten the wording, but not change the meaning; show me any changed wording in the diff.

- **MON-13 Escalation.** When a metric is Warn for `warning_escalation_periods` consecutive non-backtest runs, a breach is created for the latest run. Fewer consecutive Warns create none.
- **MON-14 Breach severity.** A breach's severity comes from `breach_severity_rules` (D5's `Condition=Severity` format). The allowed conditions are exactly `Fail`, `Warn_escalated`, `Repeat` and `Tier_High_Fail`. When several apply, the highest severity wins. Policy validation refuses an unknown condition or a severity outside `breach_severities`; this replaces D5's provisional shape-only check.
- **MON-15 Repeated breach.** A breach is marked Repeat when the metric has Failed in `repeat_breach_consecutive` consecutive runs, or in `repeat_breach_count` of the last `repeat_breach_window` runs. A Repeat raises an insight and applies the `Repeat` severity rule.
- **MON-16 Backtest separation.** Backtest runs and results appear only in backtest views and the MUP-18 grid. They never appear in monitoring trends, completion figures or the monitoring score.
- **MON-17 Evidence before sign-off.** A run cannot be signed off without the evidence §24 requires. The refusal names the run and the missing evidence. Nothing is saved, and no audit event is written.
- **MON-18 Template validation (T13–T16).** Rows load through the same services as the UI. An unknown model, plan, metric or run rejects the row with a message naming the field and the row. T15 accepts a `status` of Not Applicable only. T16 rows follow D3. The thresholds and bounds applied are copied onto each result when it is evaluated.
- **MON-19 Alias templates (D1).** Loading equivalent data through T07/T08 or through T14/T15 produces identical metrics and results. No `kpi` or `kpi_result` table exists.
- **MON-20 Within range (D2).** A within-range metric without both bounds is refused. A value inside the bounds (inclusive) is Pass, and outside is Fail. A later change to the bounds does not change earlier results.

### Where to write them

**CLAUDE.md**
- §81A: fill the Decision column for D1, D2, D3, D4, D6 and D7 with a one-line summary, and "see decision_log.md".
- §48: mark `kpi` and `kpi_result` "not created (D1)"; add `monitoring_run_id` to `performance_point`. Add `range_lower` and `range_upper` to `monitoring_metric`, and `range_lower_applied` and `range_upper_applied` to `monitoring_result` (D2). Add `methodology` to `monitoring_run` if it is not already there (D4).
- §16, §20, §21, §23, §57: add a one-line reference to the decision that now governs each section. Do not rewrite them.
- §71 / §72: note that T07 and T08 are aliases of T14 and T15 (D1), and the T16 matching rule (D3).
- §77: add MON-13 to MON-20.
- §76A.14: add 8 to the criteria total. MON-13 to MON-20 are "Not built (Phase 6)".
- Part 0 build status: remove "needs D1–D7" from the Monitoring step.

**project_plan.md** (follow its rules: stable IDs, change-log line)
- G2.1, G2.2, G2.3, G2.4, G2.6 and G2.7: set to **Decided 2026-10-09**, with "decision_log.md" as Evidence.
- Gate 2's heading: drop "⛔ blocks Gate 3", and add "Closed 2026-10-09".
- G3.1–G3.15: change `Blocked (G2)` to `Not started`. G3.15's criteria become "MON-01…MON-20".
- Under Gate 3, add one note: "New policy keys to add in Gate 3 (T12 bootstrap and seed, paired): `breach_severities`, `breach_to_finding_severity`; and tighten `breach_severity_rules` validation to the MON-14 conditions."
- §11, risk 1: replace it with "Gate 2 closed 2026-10-09. Gate 3 is the largest remaining block, and nothing now blocks it."

### Acceptance (stage 1)

- `decision_log.md` has six new Decided entries, and §81A has no blank Decision cell for D1–D7.
- §77 has MON-13 to MON-20. §48 shows the D1, D2 and D4 changes. The §76A.14 count went up by 8.
- In the plan, Gate 2 is closed, Gate 3's rows are `Not started`, and there is a change-log line.
- `git diff --stat` shows no changes under `A_Codes/`, `B_Inputs/` or the T12 files.

### Report back at the end of stage 1

1. Any place where my decisions conflict with existing BRD text, the code, or D5 / D10. Do not resolve a conflict yourself; list it.
2. Any MON-13 to MON-20 wording you changed, and why.
3. The §20 breach statuses, quoted, so that I can confirm D3's "not open" rule fits them.

**Then STOP.** Show me the stage 1 diff, any conflicts, and the §20 breach statuses. Commit only after I approve.

---

## Stage 2 — D8 and D11: draft the missing acceptance criteria

**D8 — Data Audit (§76B).** Draft criteria DQ-01 onwards from §55.5, the `cde`, `dq_rule`, `dq_result` and `dq_issue` tables in §48, and templates T06 and T10, in the same style as §77. They must cover at least:
- CDE registry: a CDE links to models; an unknown model is refused.
- DQ rules and thresholds come from the template or the screen, never from code.
- DQ results by run: each result is evaluated against the threshold in force at the time, and that threshold is stored on the result, as MON-05 does for monitoring.
- DQ issues: raised from failing results, with owner, due date and status; the statuses follow the D10 pattern.
- T06 and T10 validation through the same service path as the UI, with messages naming the field and the row.
- The Data Audit screen (§55.5) and the Model 360 CDE/DQ tab show the same counts.

**D11 — Audit Copilot (§76C).** Draft criteria COP-01 onwards from §61 and Principle 10. They must cover at least:
- The Copilot is read-only: it never creates, changes or deletes a record, and asking it to do so is refused.
- Every answer cites the model IDs and records it used, and each citation opens that record.
- It never states a figure that is not in the governed data; when the data does not answer the question, it says so.
- It respects the user's role: it cannot reveal records the user could not open on screen.
- Every question and answer is audited.
- Suggested questions are offered.

Mark D8 and D11 **Proposed** in §81A and `decision_log.md`, add the criteria to CLAUDE.md as §76B and §76C, and update the §76A.14 total.

**Then STOP.** Show me both criteria lists in full. When I approve, mark D8 and D11 Decided, set Gate 4 and Gate 6 rows in `project_plan.md` from `Blocked (D8)` / `Blocked (D11)` to `Not started`, add a change-log line, and commit.

---

## Stage 3 — D13: AI provider for Gates 5 and 6

Add **D13 — AI provider for AI extraction (Gate 5) and the Copilot (Gate 6)** to §81A and `decision_log.md`, with these options and the Decision blank:
1. Claude API, with the key in `.env` (never committed).
2. An offline stub that returns deterministic canned results, for demos and tests.
3. Both, switchable by a setting (`ai_provider`), with the stub as the default when no key is present.

Note under it that §60's provenance fields (`provider`, `model_used`, `prompt_version`) record which one produced each result.

**Then STOP** for my choice. When I choose, mark D13 Decided, note the choice under Gates 5 and 6 in the plan, commit, then switch this worktree to `main` and merge `decisions-d1-d7` into it.

---

## Overall acceptance

- `decision_log.md` has D1–D4, D6, D7, D8, D11 and D13 as Decided, and §81A has no blank Decision cell.
- CLAUDE.md has MON-13 to MON-20 in §77, §76B and §76C, and the §76A.14 total updated.
- In the plan, Gate 2 is closed, and Gates 3, 4 and 6 are `Not started` (Gate 6 is still subject to D13 for its provider).
- `git diff --stat main` shows no changes under `A_Codes/`, `B_Inputs/` or the T12 files.
