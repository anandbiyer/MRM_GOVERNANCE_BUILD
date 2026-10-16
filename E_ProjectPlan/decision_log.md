# Decision log — §81A decisions

The §81A table in `CLAUDE.md` lists the decisions that must be recorded before Phases 5–9, with a
one-line outcome in its Decision column. That column has no room for reasoning, so the reasoning
lives here: one entry per decision ID, in ID order.

## How to record a decision

1. Find the entry below (or add one using the template at the bottom).
2. Change **Status** from `Proposed` to `Decided`, and fill in **Decided on** and **Decided by**.
3. Copy the one-line outcome into the Decision column of §81A in `CLAUDE.md`, as D9 already shows.
4. Note it in the change log of `project_plan.md`, and unblock the gate entries that cite it.

A `Proposed` entry is a recommendation, not a decision: §81A's own rule is that Claude Code shall not
implement an item until its Decision column is filled in. Entries are never deleted — a decision that
is later reversed gets a **Superseded by** line and a new entry.

---

## D9 — Is the mock-up's MRC report in scope?

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §55, §12A |
| **Needed before** | Any |

**Decision.** In scope, as the model risk report: §12A REQ-REG-10 with criteria REG-13. AI commentary
waits for Phase 9.

**Why.** The mock-up generates an MRC governance report, but no BRD section required one, so the
screen had no specification behind it. SR 26-2 independently requires reporting of aggregate model
risk to senior management and the board, so the requirement was written there rather than inventing a
separate one.

**Consequences.** Delivered by Gate 1 (Phase 2A), not Phase 8. Mock-up items MUP-29 and MUP-30 moved
to Phase 2A, and MUP-30 is no longer "no BRD requirement".

*Met first by REQ-REG-10A (core report); full report deferred with **D12**. MUP-29 is delivered by the
core report; MUP-30 stays partial until Phase 2A resumes.*

*Recorded retrospectively: this decision was already written into §81A and §12A before this log
existed.*

---

## D10 — Are the additional finding statuses required?

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §11, criterion FND-03 |
| **Needed before** | Any |
| **Decided on** | 2026-10-05 |
| **Decided by** | Anand |

**Decision.** Required. All six statuses stand: `Open`, `In Progress`, `Deferred`, `Closed`,
`Accepted Risk`, `Rejected`. Of these, `Open`, `In Progress` and `Deferred` count as open for ageing
and the issue-remediation score; `Closed`, `Accepted Risk` and `Rejected` do not.

**Why.** §11 lists the three extra statuses as "additional recommended", but the build already treats
them as required and has since Phase 2 — `B_Inputs/AA_bootstrap/T12_policy_settings.csv` ships all six
in `finding_statuses`, and `finding_open_statuses` ships the three that count as open. Monitoring also
needs `Accepted Risk` independently: §20 gives breaches that status, and MON-09 lets a breach become a
finding, so a finding must be able to carry it. Ratifying what ships is therefore the lower-risk
option; the alternative would mean removing shipped configuration.

**The classification, confirmed deliberately.** The substantive part of this decision is not the list
but which statuses count as open. **`Accepted Risk` does not count as open**, so a model with a
formally accepted critical finding scores as though it had been remediated and drops out of the
overdue-findings tile and insight. That is the intended behaviour: the risk was accepted, so no
remediation is outstanding. It was confirmed explicitly rather than inherited.

If a supervisor later expects accepted risks to stay visible, the change is one value in
`finding_open_statuses` in T12 — no code — and should be recorded here as a superseding entry.

**Consequences.** No code or configuration changes; the build already matched. §11's wording changed
from "Additional recommended status" to "Also required", with the open/closed split stated there.
Spec issue **S1 closes**. Covered by `test_d5_and_d10_decided_keys_are_configured`, which asserts the
six statuses and that `Accepted Risk` is absent from the open list — so the decision cannot be
silently reversed by a configuration edit.

---

## D1 — KPI tables versus monitoring tables: which is the system of record?

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §48, §71, §72; criterion MON-19 |
| **Needed before** | Phase 6 (Gate 3) |
| **Decided on** | 2026-10-09 |
| **Decided by** | Anand |

**Decision.** `monitoring_metric` and `monitoring_result` are the only system of record. `kpi` and
`kpi_result` are **not created**. T07 (KPI Definitions) and T08 (KPI Results) stay as import aliases
that write through the same services as T14 and T15, so older files still load. T09 (Performance
Curves) loads into `performance_point`, which gains a `monitoring_run_id` foreign key, so every curve
belongs to a run.

**Why.** One source of truth for thresholds and history; two tables would mean two Pass/Warn/Fail
calculations that could disagree.

**Consequences.** §48 marks `kpi` and `kpi_result` "not created (D1)" and adds `monitoring_run_id` to
`performance_point`; §71 records T07/T08 as aliases. The registry's T07/T08 entries (today stubs
targeting `kpi`/`kpi_result`) are repointed in Gate 3. Criterion **MON-19** proves the aliases are
equivalent and that neither KPI table exists.

**Amended 2026-10-09 (stage 1 review) — the aliases are dropped.** The review found the aliases
underspecified: the old T07 shape has no plan ID and a `warn_tolerance_pct`, the old T08 has no run ID
and an `is_backtest` flag, and no T07 or T08 file exists in the repository to keep loading. So:

- **T07 and T08 are retired from the registry** (G3.14). They are not offered, and an upload naming
  them is refused. Metrics load through T14 and results through T15.
- **T09 gains `monitoring_run_id`**, and every T09 row requires an existing run.
- **MON-19** is reworded to "T07/T08 are not offered; T09 rows require a run; no `kpi` or `kpi_result`
  table exists".
- The template total falls from 21 to 19 (§71, plan §1). The registry change is product code, so it is
  made in Gate 3, not on this branch.

The first two sentences of the Decision above still stand; the sentence about aliases does not.

---

## D2 — Bounds for the "within range" direction

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §16, §48, T14; criterion MON-20 |
| **Needed before** | Phase 6 (Gate 3) |
| **Decided on** | 2026-10-09 |
| **Decided by** | Anand |

**Decision.** `monitoring_metric` gains `range_lower` and `range_upper`, used only when `direction` =
within range, and both are required in that case. Inside the bounds (inclusive) is Pass; outside is
Fail. Warn is not used for within-range metrics in this release. Following MON-05, the bounds are copied
onto each result as `range_lower_applied` and `range_upper_applied` when the result is evaluated.

**Why.** The smallest rule that is unambiguous. A warning band can be added later without changing
history, because the applied bounds are stored on each result.

**Consequences.** Two columns on `monitoring_metric` and two on `monitoring_result` (§48); T14 gains the
two bounds in Gate 3. Criterion **MON-20**.

---

## D3 — Rule-created breaches versus T16 imports

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §20, §21, §72 (T16); criteria MON-02, MON-09, MON-14, MON-18 |
| **Needed before** | Phase 6 (Gate 3) |
| **Decided on** | 2026-10-09 |
| **Decided by** | Anand |

**Decision.**

- Breaches are created **only by the rules**: on a Fail, and on a Warn escalated under D5's
  `warning_escalation_periods`.
- A T16 row must match an existing breach on `monitoring_run_id` + `metric_id`. It may update status,
  owner, due date, root cause, impact, management response and resolution. It never creates a breach
  and never changes severity.
- An unmatched T16 row is rejected, with a message naming the row and the two keys.
- Breach severity has its own vocabulary, policy key `breach_severities` = Low, Medium, High, Critical,
  separate from `finding_severities` — closing the gap recorded under D5. When a breach becomes a
  finding (MON-09), its severity is mapped by policy key `breach_to_finding_severity`.
- Breach statuses follow §20. As with findings under D10, `Accepted Risk` and `Closed` count as not
  open.

**Why.** One place creates breaches, so counts and escalation are reproducible; imports carry the human
part of the work.

**Consequences.** §20 and §72 cite D3. Two new T12 keys, `breach_severities` and
`breach_to_finding_severity`, are added in Gate 3 (bootstrap and seed paired), not now. D5's
`check_key_specific` shape check is tightened to validate severities against `breach_severities`
(MON-14).

**Amended 2026-10-09 (stage 1 review).**

- **Every Fail creates a breach.** MON-02 said "a failed *critical* KPI", but nothing defines a
  critical metric, so D3 wins and MON-02 now reads "Any Fail result creates a monitoring breach".
- **Severity conditions.** Exactly `metric_fail`, `warn_escalated`, `repeated_breach`,
  `high_tier_metric_fail` and `regulatory_metric_fail`, with default severities Medium, Low, High, High
  and High. `data_quality_fail` is reserved for Gate 4, when §21's data-quality example returns.
  `metric_warn` is dropped, because a plain Warn never creates a breach. Critical is not a default but
  stays available through policy. When several conditions apply, **the highest severity wins**
  (MON-14). The precedence change also amends D5.
- **T16 matching.** `breach_id` wins when given, and a row whose `breach_id` disagrees with its
  `monitoring_run_id` + `metric_id` is rejected. Without a `breach_id`, the row matches on run + metric.
  A supplied `severity` is **ignored, with a warning naming the row**. T16 gains a `resolution` column
  (§72), because D3 lets an import update the resolution.
- **Status vocabulary, following the D10 pattern.** New policy keys `breach_statuses` (the six §20
  statuses) and `breach_open_statuses` (New, Acknowledged, Under Investigation, Action Required), added
  in Gate 3.

---

## D4 — Backtesting

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §23, §26, §48, §71; criterion MON-16 |
| **Needed before** | Phase 6 (Gate 3) |
| **Decided on** | 2026-10-09 |
| **Decided by** | Anand |

**Decision.** A backtest is a `monitoring_run` with `monitoring_type` = Backtest. Its methodology and
sample period are recorded on the run (`methodology`, `data_period`), and its results are
`monitoring_result` rows against metrics whose category is Backtest. Screens show backtests separately
from routine monitoring. The Model 360 backtesting grid (MUP-18) reads from these runs. Backtest runs do
not feed the monitoring score (D6).

**Why.** Reuses runs, results, thresholds, evidence and breaches unchanged; no new table.

**Consequences.** `monitoring_run` gains `methodology` in §48 (it was not there). Criterion **MON-16**
keeps backtests out of trends, completion figures and the score; MON-13 and MON-15 count non-backtest
runs only.

**Amended 2026-10-09 (stage 1 review).** §15 has no Backtest category and no policy list of categories,
so a new policy key `metric_categories` (the §15 categories plus **Backtest**) is added in Gate 3.

---

## D6 — What feeds the Monitoring score component

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §57; criterion MON-12 |
| **Needed before** | Phase 6 (Gate 3) |
| **Decided on** | 2026-10-09 |
| **Decided by** | Anand |

**Decision.**

- **Models in the Monitoring phase.** The component is the share of the model's active metrics whose
  latest result, in the latest signed-off non-backtest run, is Pass. Not Applicable results are
  excluded from numerator and denominator. Not Available results are excluded too, and listed under the
  score's "Missing information".
- **A Monitoring-phase model with no active monitoring plan** scores 0 on the component, with "No active
  monitoring plan" as missing information.
- **Models in any other phase:** the component is excluded and the remaining weights are rescaled, as
  today (SCR-02).

**Why.** Simple, explainable (§57), and it makes a missing plan visible instead of rewarding it.

**Consequences.** §57 cites D6. Every Monitoring-phase model's score moves when Gate 3 lands, because
the 15% weight stops being rescaled away — already recorded in the plan as risk 4.

**Amended 2026-10-09 (stage 1 review): the edge cases.**

| Case | Component |
|---|---|
| "Signed-off" | A run whose status is **Approved** and whose `signoff_date` is set |
| Active plan, but no signed-off non-backtest run | **0**, missing information "No signed-off monitoring run" |
| Every result in the latest signed-off run is Not Applicable | **Excluded**; the remaining weights are rescaled |
| No usable result because the rest are Not Available | **0**, with the Not Available metrics listed as missing information |

---

## D7 — Missing monitoring acceptance criteria

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §21–§24, §72, §77 |
| **Needed before** | Phase 6 (Gate 3) |
| **Decided on** | 2026-10-09 |
| **Decided by** | Anand |

**Decision.** Add **MON-13 to MON-20** to §77: escalation (MON-13), breach severity (MON-14), repeated
breach (MON-15), backtest separation (MON-16), evidence before sign-off (MON-17), T13–T16 template
validation (MON-18), retired KPI templates (MON-19, from D1) and within range (MON-20, from D2).

**Why.** §77 had no criteria for §21–§24 or for T13–T16 import validation, so those parts of Phase 6
could not be tested or reviewed.

**Consequences.** §77 grows 12 → 20 and the §76A.14 total 118 → 126; MON-13…MON-20 are *Not built
(Phase 6)*. MON-14 fixes the rule conditions as exactly `Fail`, `Warn_escalated`, `Repeat` and
`Tier_High_Fail`, which supersedes the provisional condition names in D5's seeded default. MON-15 cites
D5's shipped key names rather than the names in the original prompt, so D5 stands unchanged.

**Amended 2026-10-09 (stage 1 review).**

- **MON-15** keeps D5's shipped key names (`repeated_breach_consecutive_periods`,
  `repeated_breach_window_fails`, `repeated_breach_window_periods`), confirmed. It applies the
  `repeated_breach` severity rule.
- **MON-14**'s conditions are those in the D3 amendment (`metric_fail`, `warn_escalated`,
  `repeated_breach`, `high_tier_metric_fail`, `regulatory_metric_fail`), not the four first written.
- **MON-17** reads a new policy key, `monitoring_required_evidence`: the document types each run needs
  before sign-off, default Monitoring Report. Sign-off is refused while any of them is missing. §24
  gives only examples, so without the key the criterion had nothing to test against.
- **MON-02** reworded per the D3 amendment; **MON-19** reworded per the D1 amendment.

---

## D5 — Repeated-breach and escalation policy keys

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §21, §22, §69 |
| **Needed before** | Phase 6 (Gate 3) |
| **Decided on** | 2026-10-05 |
| **Decided by** | Anand |

**Decision.** Keep the three keys already shipped and drop §81A's proposed renames. Add the two that
are genuinely missing, named to match the shipped convention.

| Key | Status | Value | Meaning |
|---|---|---|---|
| `repeated_breach_consecutive_periods` | ships today | 2 | Same KPI failing this many consecutive periods is a repeated breach (§22) |
| `repeated_breach_window_fails` | ships today | 3 | Failures within the window that count as repeated (§22) |
| `repeated_breach_window_periods` | ships today | 4 | Window length in periods (§22) |
| `warning_escalation_periods` | **to add** | 3 | Consecutive warnings before a metric escalates (§21) |
| `breach_severity_rules` | **to add** | *(list)* | Configurable severity/escalation rules (§21) |

§81A had proposed `repeat_breach_consecutive`, `repeat_breach_count`, `repeat_breach_window` and
`warn_escalation_periods`.

**Why.** The three existing keys are already in the bootstrap file, the seed generator and the
committed seed, and are covered by the GR.9 baseline test that fails if bootstrap and seed diverge.
Renaming them would churn configuration in circulation for no behavioural gain, and the shipped names
are the clearer ones — `repeated_breach_window_fails` says what it counts, where `repeat_breach_count`
does not. The two additions are real gaps: §21 requires configurable escalation and neither key exists,
so Phase 6 would otherwise hard-code them, which Part 0 forbids.

**Rule grammar, decided with this.** `breach_severity_rules` items are **`Condition=Severity`**,
separated by `;` — deliberately the same shape as `revalidation_frequencies`' `Name=months`, so the
file has one convention for keyed lists rather than two. Seeded default:

```
metric_warn=Low; metric_fail=Medium; data_quality_fail=High;
regulatory_metric_fail=High; repeated_breach=High; high_tier_critical_metric_fail=Critical
```

`policy_values.check_key_specific` enforces the **shape only** — both sides present and non-empty. It
deliberately does not yet validate the names, because neither vocabulary exists:

- The **condition** names above are provisional. The set of conditions a rule can test is part of the
  Phase 6 rules engine (§21, §22) and belongs with **D7**.
- There is no **breach severity** vocabulary. §21's examples use `High`, which `finding_severities`
  (Critical; Medium; Low) does not contain, so breach severities are a separate list that Phase 6 must
  add — likely a `breach_severities` T12 key, settled with **D3**.

When those land, `check_key_specific` should validate both sides against them instead of accepting any
names. Recorded here so Phase 6 tightens an existing check rather than discovering the gap.

**Consequences.** Two T12 rows added to `B_Inputs/AA_bootstrap` and the seed regenerated, so the GR.9
baseline test stays green (65 → 67 settings). `check_key_specific` extended with the shape rule.
Spec issue **S2 closes**; G2.5 is Decided. Gate 3 stays blocked on D1–D4, D6 and D7.

**Amended 2026-10-09 (stage 1 review of D1–D7).** The key names and the `Condition=Severity` grammar
stand. Two things change:

- **Conditions.** The provisional names in the seeded default are replaced by MON-14's set. The seeded
  value becomes `metric_fail=Medium; warn_escalated=Low; repeated_breach=High; high_tier_metric_fail=High;
  regulatory_metric_fail=High`. `data_quality_fail` is reserved for Gate 4, and `metric_warn` is dropped.
- **Precedence.** When several conditions apply, **the highest severity wins**, not "first match from the
  most specific", which is what the T12 description says today. That description is corrected along with
  the value.

Both are changes to `B_Inputs/` (bootstrap and seed, paired) and to `check_key_specific`, so they are made
in Gate 3 and listed in the plan's Gate 3 note, not on the documentation-only `decisions-d1-d7` branch.

---

## D8 — Data Audit acceptance criteria

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §48 (`cde`, `cde_model`, `dq_rule`, `dq_result`, `dq_issue`), §55.5, §71 (T06, T10), §76B |
| **Needed before** | Phase 7 (Gate 4) |
| **Decided on** | 2026-10-09 |
| **Decided by** | Anand |

**Decision.** Adopt §76B, criteria **DQ-01 to DQ-13**, drafted 2026-10-09 from §55.5, the four DQ
tables, T06 and T10, and the superseded `design.md` (REQ-CDE-01…03, REQ-DA-01/02, rule R7 and test
conditions TC-CDE-*, TC-DA-*). They cover the CDE registry and its model links, thresholds from data with
`dq_default_pass_pct`/`dq_default_warn_pct` as the fallback, result status with a boundary example, the
threshold in force copied onto each result (the MON-05 pattern), result validation, issues raised from
failing results without duplicates, D10-pattern issue statuses, T06/T10 through the service path,
audit, `dq:manage` authorization, Data Audit and Model 360 agreeing, the screen's filters and ordering,
and the Critical DQ issue insight.

**Why.** Data Audit had no acceptance criteria (§76A.13 left `TC-CDE-*` and `TC-DA-*` unported), so
Gate 4 could not be tested or reviewed.

**Settled at approval (2026-10-09).**

- **One CDE may feed several models.** §48 gains a `cde_model` link table, and `cde` carries no
  `model_id` of its own. The superseded `design.md` gave each CDE a single model.
- **`dq_result` stores the thresholds applied**: `pass_threshold_applied` and `warn_threshold_applied`,
  added to §48 now (DQ-04).
- **Policy keys for Gate 4** (in the plan's Gate 4 note): `dq_issue_statuses` and
  `dq_issue_open_statuses` (the D10 pattern); `dq_issue_severity_rules` (Critical when the CDE feeds a
  High-tier model, otherwise Medium); `dq_issue_due_days`. `dq_default_pass_pct` and
  `dq_default_warn_pct` already ship and are kept.
- **No new permissions**: writes need the existing `dq:manage`.

**Consequences.** §76A.14 total 126 → 139 (149 with D11). Gate 4 rows G4.1–G4.6 go from `Blocked (D8)`
to `Not started`.

---

## D11 — Audit Copilot acceptance criteria

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §60, §61, §76C, Principle 10 |
| **Needed before** | Phase 9 (Gate 6) |
| **Decided on** | 2026-10-09 |
| **Decided by** | Anand |

**Decision.** Adopt §76C, criteria **COP-01 to COP-10**, drafted 2026-10-09 from §60, §61, Principle 10
and the superseded `design.md` (REQ-COP-01…03, TC-COP-*). They cover the following: read-only and
refusing to act; citations that exist, open their record and meet the question; no figure outside the
governed data; the user's role and record-level access respected; every question and answer audited
with §60 provenance; suggested questions from policy; who may ask; embedded text treated as data, not
instruction; and provider failure shown, not hidden.

**Why.** The Copilot had no acceptance criteria (§76A.13 left `TC-COP-*` unported), so Gate 6 could not
be tested or reviewed.

**Settled at approval (2026-10-09).** COP-09 (embedded text is data, not instruction) and COP-10
(provider failure is shown) are kept, although they go beyond the minimum asked for. There is no new
permission: asking needs `read`.

**Consequences.** §76A.14 total 139 → 149. Gate 6 rows G6.1–G6.4 go from `Blocked (D11)` to
`Not started`; the provider remains D13. Gate 6 adds a policy key for the suggested questions.

---

## D12 — Is Phase 2A built now?

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §12A, §55.10, §76D, §81A, §85, Part 0 |
| **Needed before** | Gate 1 |
| **Decided on** | 2026-10-05 |
| **Decided by** | Anand |

**Decision.** Phase 2A deferred, except the core Model Risk Report. Gate 1 (§12A, REQ-REG-01 to 11) is
not built until I say so. Exception: **REQ-REG-10A**, a core Model Risk Report built from existing data,
is built now (§12A.2). When Phase 2A resumes, G1.12 extends that report with the §12A sections instead
of creating a second one. **D9** (the mock-up's MRC report is in scope as the model risk report) stands,
and is met first by the core report.

**Why.** Phase 2A is the largest unbuilt block that nothing else depends on: it adds columns, three
templates, six new record types and two screens before producing anything a customer sees. The report
is the opposite — it is the one piece of §12A that is visible, that the mock-up already promises
(MUP-29, MUP-30), and that needs no new data: tier, phase, revalidation status, findings, approvals,
score and document completeness are all already computed on read by `governance_view`.

**Consequences.**

- Gate 1 rows G1.1–G1.15 become `Blocked (D12)`. G1.12 is marked as extending the core report rather
  than being replaced by it, so resuming Phase 2A does not produce a second report.
- Three new plan rows (G1.16–G1.18) carry the core report: backend, screen, then seed and tests.
- Criteria **REG-15, REG-16, REG-17** are added for the core report; **REG-01 to REG-14** become
  "deferred, D12" and the review agents report them as *Not built (Phase 2A, deferred D12)*, never as
  defects. The §76A.14 total goes 112 → 115.
- The policy key `regulatory_framework` arrives early, with the core report rather than with §12A.
- **Gate 2 becomes the critical path.** Once the core report is done, nothing but Gate 5 (AI
  extraction) can be built until D1–D7 are recorded. That risk is recorded in the plan's §11.
- `model_risk_report` is added to §48 now; the rest of §12A's tables stay deferred.

**Amendments, 2026-10-06** (before G1.16 was built; both tighten REQ-REG-10A and REG-15).

1. **The report is always for the current business date.** "For a chosen business date" is removed.
   `app.clock.today()`, which `MRM_TODAY_OVERRIDE` fixes, is the only date; history is the stored
   copies, which are listed and reopened. *Why:* derived governance state is recomputed on read
   (Part 0, `governance_view`), so a past date would have to be threaded through `dashboard_service`
   and `governance_view` — and even then it would reconstruct today's records as they would have been
   judged on that date, not the portfolio as it actually stood. That is a different and much larger
   thing than a report. The stored report is the record of the past; **no date parameters are added to
   `dashboard_service` or `governance_view`**.
2. **"Models by lifecycle phase" becomes "models by stage, the column the Command Center displays"
   (LIF-02).** *Why:* REQ-REG-10A also requires every figure to equal the Command Center, and the
   Command Center's distribution is the *displayed* column — a model in Monitoring whose next due date
   falls inside the lead time appears in Revalidation. The two requirements could not both hold as
   written; this was raised as an ambiguity when the core report was specified and is now settled in
   favour of agreeing with the screen.

Also decided with these: `reportlab` is added to `requirements.txt` and `requirements-lock.txt` as part
of **G1.16**. It was checked beforehand — it installs as a pure-Python wheel and renders a styled PDF on
Python 3.14.5 under Windows — so REQ-REG-10A's "stop and ask if no PDF library installs cleanly" branch
does not apply.

---

## D12 addendum — the content hash, and what a stored report may claim

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §12A REQ-REG-10A, criteria REG-16 and REG-17, §76A.14 |
| **Needed before** | Gate 1 merging to `main` |
| **Decided on** | 2026-10-09 |
| **Decided by** | Anand |

Three spec issues raised by the Gate 1 exit review (`D_Reviews/20261008_summary.md`), decided
together because they are one question seen from three sides: what is a stored report a statement
*about*?

**S10 — the predecessor is not part of "the same data".** `changes_since` is excluded from the content
hash, and REG-16 is reworded to say so: *"Generating twice from the same data and business date gives
the same content hash over the report's figures; the changes-since section is excluded from the
hash."*

*Why.* The old wording could not be satisfied once any predecessor existed. The first generation of a
day diffs the previous stored report; the second diffs the first. The change lists therefore differ by
construction, so a hash covering them differs too — review finding **FT-09**, which failed REG-16 in
production terms, not only in a demo. The code already held the right principle and then contradicted
it four lines later: it excluded `previous_report_id` and `previous_generated_at` as "provenance, not
content" while keeping the lists derived *solely* from that predecessor. If the predecessor's identity
is provenance, so is everything computed from it.

*What the hash still covers.* Every figure about the portfolio: inventory by tier and stage,
revalidation, findings, approvals, score, documentation, and the baseline. So two reports that say
different things about the portfolio still hash differently; two reports that say the same thing about
it no longer differ because one happened to be second.

**S11 — a stored report never holds a figure that was not real.** Every stored report is produced by
the report service from the portfolio as it stood at generation, and no figure is shaped by hand. The
seeded example is generated the same way and **after the seed evidence is loaded**, so its figures are
a real portfolio state. Its baseline stays shaped — that is diff input, not a reported figure, and it
is what gives the next report a non-empty "changes since".

*Why.* The seeded report was being generated before the evidence loaded, so `completeness` returned
`score=0` rather than `None` and the 25%-weight documentation component scored zero for every model.
On screen that read as **0% documentation, 250 of 256 models missing documents, portfolio score 64.5**
against today's 92.9, with every other section showing today's numbers — a credible-looking governance
collapse that "recovered" with nothing in the section whose job is to explain it (**CR-41**, **MP-18**).

**S12 — a reopened report states what was true at generation.** The footer reads *"Figures reconciled
with the Command Center at generation, &lt;timestamp&gt;"*, and the seeded example is labelled
**"Seeded example"** wherever reports are listed or reopened.

*Why.* The footer was rendered at page level, outside the report view, so it asserted
*"Figures reconcile with the Command Center for the same business date"* over whichever report was
open. For a historical report that is false, and **unverifiable by construction**: the Command Center
has no as-of control and always renders `app.clock.today()`, so no Command Center for an earlier
business date can be produced at all. A governance tool asserting a reconciliation it cannot
demonstrate is worse than one saying nothing.

**Consequences.** Plan rows **G1.25** (S10) and **G1.26** (S11, S12). REG-16's rewording is in
§76D; REQ-REG-10A carries the stored-report rules. REG-17 is unaffected in wording but needed
**G1.27** to reach Proven. The §76A.14 note that REG-16 is *Failing* is replaced by the Gate 1 re-run.
*(Corrected 2026-10-15: this paragraph first named G1.21–G1.23, the IDs proposed before the rows were
renumbered; the work landed as G1.25–G1.28, as the plan's 2026-10-09 change log records.)*

**S13 — every predecessor-derived figure lives in the changes section** (decided 2026-10-15, review
finding **CR-52**). G1.25 excluded `changes_since` from the hash, but one more figure derived solely
from the previous report, `approvals.decisions_since_previous`, sat in the `approvals` section and so
stayed inside it: record one approval, generate twice, and identical data gives two hashes. Two fixes
were on the table — hash an explicit allowlist of figure keys, or move every "since the previous
report" figure into the changes section. **The second is chosen**: the decisions recorded since the
previous report become part of `changes_since`, the approvals section keeps only conditional approvals
with open conditions, and the single rule "the changes section is out of the hash" stays the whole rule.

*Why.* S10's principle is "if the predecessor's identity is provenance, so is everything computed from
it". An allowlist would enforce that in the hash function while leaving predecessor-derived figures
scattered across sections; moving them puts the principle in the report's *shape*, where a reader can
see it, and makes the next such figure's correct home obvious. REQ-REG-10A now says so in its section
list. Plan row **G1.29**; regression test: record an approval between two generations and assert the
hashes agree while the changes section differs.

*Recorded as an addendum to **D12** rather than a new ID, because all four sit inside the core
report D12 scoped.*

---

## D13 — AI provider for AI extraction (Gate 5) and the Copilot (Gate 6)

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §37, §51, §60, §61, §76C |
| **Needed before** | Gate 5 (the first gate that calls a model) |
| **Decided on** | 2026-10-09 |
| **Decided by** | Anand |

**Options.**

1. **Claude API**, with the key in `.env` (never committed).
2. **An offline stub** that returns deterministic canned results, for demos and tests.
3. **Both**, switchable by a policy setting `ai_provider`, with the stub as the default when no key is
   present.

**Decision.** Option 3: both providers, switchable.

- The switch is an **environment setting**, `MRM_AI_PROVIDER` (`stub` | `claude`), in `app/config.py`,
  with `MRM_AI_MODEL` for the model name. It is **not a T12 row**: whether an API key is present is a
  fact about the deployment, not a governance policy, and Part 0 already keeps infrastructure settings
  in `app/config.py` (as with `MRM_SQLITE_BUSY_TIMEOUT_MS`).
- **Default:** `stub` when no API key is present.
- **`MRM_AI_PROVIDER=claude` with no key: the application refuses to start**, with a clear message. It
  never falls back to the stub silently, because a stub answer presented as a real one would be a false
  governance record.
- The §60 provenance fields record which provider and model produced each result.

**Why.** Tests and CI run offline with no key, so they need deterministic stub results. A customer demo
needs the real model. Only option 3 serves both. Refusing to start, rather than falling back, keeps a
misconfiguration from being mistaken for a working system.

**Consequences.** Gate 5 builds the provider seam (`app/config.py` settings, a startup check, the stub
and the Claude client behind one interface) before any extraction. Gate 6 reuses it. The stub is what
the tests for DOC-16 and COP-01…COP-10 run against. `.env` holds the key and is never committed. No T12
row and no `B_Inputs/` change.

**Note.** §60's provenance fields (`provider`, `model_used`, `prompt_version`) record which provider
produced each result, whichever option is chosen. Those fields sit on `document_extraction` (§48) for
Gate 5, and in the Copilot's audit event (COP-06) for Gate 6.

---

## D14 — What the seeded example report discloses, and whether the PDF must carry it

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §12A REQ-REG-10A, REG-15, REG-17; extends S11 and S12 (D12 addendum) |
| **Needed before** | Gate 1 merging to `main` |
| **Decided on** | 2026-10-15 |
| **Decided by** | Anand |

**Question.** The seeded example is stored with a business date one month before the seed's
(`SEED_REPORT_AGE_DAYS`), while S11 requires its figures to be computed from the portfolio as it is —
so it reads "Business date 2026-08-31" over 2026-09-30 figures, and nothing says so (**TR-48**). And
S12's disclosures are on the screen only: the downloaded PDF carries neither the "Seeded example" label
nor the reconciliation line, although it is the artefact that leaves the system (**CR-55**).

**Options.** (a) Date the seeded report on its generation date and move the "a month earlier" framing
into the label. (b) Keep the earlier business date and disclose both dates.

**Decision.** Option (b). The seeded example keeps its earlier business date and is labelled
*"Seeded example: figures computed from current seed data on &lt;generation date&gt;, dated
&lt;business date&gt; for illustration."* **The PDF counts as a surface**: it carries that label on the
seeded report, and the line *"Figures reconciled with the Command Center at generation,
&lt;timestamp&gt;"* on every report.

**Why.** The earlier date is what makes the seeded example useful — the first real report shows a month
of "changes since" — so (a) would remove the reason the example exists. What was wrong was the silence,
not the date. The PDF is the copy a board reader holds; a disclosure that stops at the screen does not
reach the person S12 was written for.

**Consequences.** Plan row **G1.31**: the label on the screen, in the list and in the PDF, with the
reconciliation line in the PDF header; tests assert the label's two dates and the PDF's text.
REQ-REG-10A carries the wording.

**Clarified 2026-10-15 (owner), before G1.31 was built.** The wording left "&lt;generation date&gt;"
open between the wall-clock date the reset ran, `generated_at` (which on the seeded example is itself
set to the earlier illustrative date), and the business date the figures belong to. **It is the business
date the figures were computed for**, stored as a new column `model_risk_report.figures_as_of`
(migration 0009) rather than derived from the seeding offset, so changing that offset can never misdate
a report already stored. For every report a user generates it equals `business_date`; only the seeded
example differs. Recorded here after the G1.31 schema checkpoint found the clarification written
nowhere (CR-66).

---

## D15 — Acceptance criteria for platform and build controls

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | Part 0 (snapshot convention), §64, §76A.14; new §76E |
| **Needed before** | Any |
| **Decided on** | 2026-10-15 |
| **Decided by** | Anand |

**Question.** The snapshot control (G3.0), the merge hook and the UTC-timestamp invariant (BL.31) have
no acceptance criteria, so they appear in no §76A.14 row and their coverage has no signal that can go
stale (**TR-56**). The snapshot convention was broken and found by eye at five consecutive reviews for
exactly that reason.

**Decision.** Add **§76E "Platform and build controls"** with **PLT-01** (every API timestamp is UTC,
from BL.31), **PLT-02** (every hand-edited file's pre-change content is recoverable from `_OLD/`) and
**PLT-03** (the snapshot control cannot pass vacuously). §76A.14's total goes 149 → **152**.

**Consequences.** BL.31 cites PLT-01. The tests in `A_Codes/AZ_tools/test_check_snapshots.py` are
tagged PLT-02/PLT-03 when that file is next edited, and the Gate 1 exit review grades all three. The
merge hook is not given a criterion here; it can join §76E when it next changes.

---

## D16 — GEN-04 and GEN-05 describe the reset lock

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §76A.12 GEN-04, GEN-05; §48 `reset_lock` |
| **Needed before** | Gate 1 merging to `main` |
| **Decided on** | 2026-10-15 |
| **Decided by** | Anand |

**Question.** Spec issue SI-1 (Gate 1 exit, requirements-reviewer): both criteria still described the
batch-status mechanism plan G1.32 replaced with an explicit reset lock. GEN-05's escape hatch — cancel
a batch left non-terminal through the API — no longer frees anything, and GEN-04's "names the batch in
flight" cannot hold before the batch exists.

**Decision.** Reword both to the lock. GEN-04: the 409 names the running reset's batch (or says it is
being created) and its stage; nothing is deleted, regenerated or submitted; a held lock is answered
from a read and a locked claim is the same 409, never a 500. GEN-05: the status signal is the lock
alone; any failing stage releases it with the outcome and stage; a lock left by an application that
stopped mid-reset is released, with the reason, when it next starts — confirmed in code
(`app/main.py` startup → `reset_service.recover_interrupted_reset`, test
`test_g1_32_starting_the_application_releases_an_interrupted_lock`) — and there is no API release.

**Consequences.** §76A.12 reworded; no code change, because the behaviour already exists.

---

## D17 — The seeded example's reconciliation time

| | |
|---|---|
| **Status** | **Decided** |
| **Sections** | §12A REQ-REG-10A, S12, D14 |
| **Needed before** | Gate 1 merging to `main` |
| **Decided on** | 2026-10-15 |
| **Decided by** | Anand |

**Question.** TR-83 (G1.31 risk checkpoint, re-observed by all three runtime agents at the Gate 1
exit): the seeded example's reconciliation line reads "at generation, 2026-08-31 09:00" — its shaped
`generated_at` — one line above "figures computed … on 2026-09-30". TR-48's silent date disagreement,
moved one line down.

**Options.** (a) The real time the seeded example was computed. (b) `figures_as_of`. (c) Omit the line
on the seeded example.

**Decision.** Option (a). The seeded example's `generated_at` becomes the real time it was computed,
no longer shaped to its illustrative date, so both its reconciliation line and its "generated at" are
true statements. Its `business_date` keeps the illustrative earlier date and its label (D14) says so.

**Consequences.** Plan row **G1.34**, which also refuses report generation with 409 while the reset
lock is held (CR-67). Tests assert the seeded reconciliation timestamp in full (closing TR-84 for the
seeded case).

---

## Template

```
## D<n> — <question in one line>

| | |
|---|---|
| **Status** | `Proposed` / **Decided** / `Superseded by D<n>` |
| **Sections** | |
| **Needed before** | |
| **Decided on** | |
| **Decided by** | |

**Decision.**

**Why.**

**Consequences.**
```
