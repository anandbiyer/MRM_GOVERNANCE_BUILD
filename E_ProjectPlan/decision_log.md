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
