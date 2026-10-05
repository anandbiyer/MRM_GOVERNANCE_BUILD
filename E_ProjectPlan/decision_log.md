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

*Recorded retrospectively: this decision was already written into §81A and §12A before this log
existed.*

---

## D10 — Are the additional finding statuses required?

| | |
|---|---|
| **Status** | `Proposed` — awaiting sign-off |
| **Sections** | §11, criterion FND-03 |
| **Needed before** | Any |
| **Decided on** | — |
| **Decided by** | — |

**Proposed decision.** Required. All six statuses stand: `Open`, `In Progress`, `Deferred`, `Closed`,
`Accepted Risk`, `Rejected`. Of these, `Open`, `In Progress` and `Deferred` count as open for ageing
and the issue-remediation score; `Closed`, `Accepted Risk` and `Rejected` do not.

**Why.** §11 lists the three extra statuses as "additional recommended", but the build already treats
them as required and has since Phase 2 — `B_Inputs/AA_bootstrap/T12_policy_settings.csv` ships all six
in `finding_statuses`, and `finding_open_statuses` ships the three that count as open. Monitoring also
needs `Accepted Risk` independently: §20 gives breaches that status, and MON-09 lets a breach become a
finding, so a finding must be able to carry it. Ratifying what ships is therefore the lower-risk
option; the alternative would mean removing shipped configuration.

**The substantive point to confirm.** It is not the list, it is the classification. **`Accepted Risk`
does not count as open**, so a model with a formally accepted critical finding scores as though it had
been remediated and drops out of the overdue-findings tile and insight. That is defensible — the risk
was accepted, so no remediation is outstanding — but it is a governance judgement, and a supervisor may
expect accepted risks to stay visible. Changing it is one value in T12 (`finding_open_statuses`), not a
code change. **Please confirm the classification explicitly, not just the list.**

**Consequences if accepted as proposed.** No code or configuration changes. Spec issue S1 closes.
§11's "additional recommended" wording should be amended to "required" so the BRD stops contradicting
the build.

---

## D5 — Repeated-breach and escalation policy keys

| | |
|---|---|
| **Status** | `Proposed` — awaiting sign-off |
| **Sections** | §21, §22, §69 |
| **Needed before** | Phase 6 (Gate 3) |
| **Decided on** | — |
| **Decided by** | — |

**Proposed decision.** Keep the three keys already shipped and drop §81A's proposed renames. Add the
two that are genuinely missing, named to match the shipped convention.

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

**Still open, and worth deciding with this.** `breach_severity_rules` is typed as a list, but its item
grammar is undefined. §69 requires the rules to be configurable and §21's examples are conditional
("high-risk model + failed critical KPI = Critical"), which a flat list cannot express without a
convention. `revalidation_frequencies` set the precedent with `Name=months` items validated in
`policy_values.check_key_specific`. A grammar is needed before Phase 6 writes against the key —
otherwise the first implementation invents one by accident. **This is the part most likely to cause
rework if left until the build.**

**Consequences if accepted as proposed.** Two T12 rows added to `B_Inputs/AA_bootstrap`, the seed
regenerated so the baseline test stays green, and `check_key_specific` extended once the grammar is
agreed. Spec issue S2 closes. Gate 2's G2.5 can be marked Decided; Gate 3 stays blocked on D1–D4, D6
and D7.

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
