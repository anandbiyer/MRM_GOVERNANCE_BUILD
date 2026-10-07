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
