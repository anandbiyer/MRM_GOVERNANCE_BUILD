Business date: **2026-09-30** (`MRM_TODAY_OVERRIDE=2026-09-30`)

That is the date the committed seed and demo files in `B_Inputs/` were generated for — the T04 demo
file raises findings on 2026-09-20, ten days before it — so resetting with this date reproduces the
overdue and revalidation states the checklist expects. Change it only by regenerating the seed.

# Mock-up parity checklist

Owned by the `mockup-parity-tester` agent. The HTML mock-up
(`C_Requirements/_OLD/MRM_Governance_MIS_Demo.html`) is what the customer has seen; this checklist is
the list of things the running application must show too.

Parity means **structure and behaviour, not identical numbers**: the mock-up carries its own sample
data and the app carries the 256-model seed. When the BRD and the mock-up disagree, the BRD wins and
the difference is recorded as an *Accepted difference* with its BRD section — the app is never changed
to match the mock-up.

## Mock-up hooks (all confirmed present)

| Hook | Where | Note |
|---|---|---|
| `.step[data-i]` | rail step buttons, indices 0–11 | **Rendered by script**, not in the raw file — wait for it |
| `#bPlay`, `#stage` | run bar, stage canvas | Static |
| `.tabs button[data-t=cc\|ops\|da]` | dashboard tabs | Static |
| `.mcard[data-m]`, `tr.click[data-m]`, `.idlink[data-m]` | model cards, table rows, inline model links | Script-rendered |
| `#m360` | Model 360 panel | Appears after a model is opened |
| `.kpi` (inside `.kpis`) | KPI tiles | Script-rendered |
| `#ci`, `#sugs button`, `#msgs` | Copilot input, suggestions, messages | Script-rendered |
| `#repDoc` | generated report | Script-rendered |

The mock-up reads `prefers-reduced-motion` (its `REDUCED` constant) and renders each step instantly
instead of running the timed walkthrough, so `reducedMotion: 'reduce'` in the `mockup` project makes
screens stable to assert on. Rail step indices: 0 Overview, 1 Policy, 2 Users, 3 Inventory,
4 History, 5 Documents, 6 CDE, 7 Results, 8 Rules, 9 Dashboards, 10 Report, 11 Copilot.

## Role mapping

The mock-up names personas; the app has the §5 role model. The Role column below uses **app roles**,
because the harness signs in with them. The personas map as:

| Mock-up persona | App role | Why |
|---|---|---|
| Head of MRM | Executive | Read-only management information (§5) |
| Viewer | Executive | No `Viewer` role exists in §5; Executive is the read-only equivalent |
| Validator, Admin, Data Owner | same | Exist unchanged in §5 |

## Phase numbers

The Phase column follows the §81 phase identifiers, which are **not** the build order (Part 0).
Built today: 1, 2, 3, 4 and the core of 8. Items on any other phase are reported
"Not built (Phase N)", never as failures.

## Checklist

| ID | Screen | Item | Role | Phase |
|---|---|---|---|---|
| MUP-01 | Command Center | KPI tiles: total models, in production, high-risk, overdue validations, open findings | Executive | 8 |
| MUP-02 | Command Center | Donuts by tier and by lifecycle phase with percentage labels | Executive | 8 |
| MUP-03 | Command Center | Lifecycle pipeline strip, click-through to filtered board | Executive | 8 |
| MUP-04 | Command Center | Revalidation timeline by category (annual / bi-annual / quarterly / monthly) | Executive | 8 |
| MUP-05 | Command Center | Regulatory / audit models and issues chart | Executive | 8 |
| MUP-06 | Command Center | Insights panel (generated from rules, not hard-coded) | Executive | 8 |
| MUP-07 | Operations Board | Filters: phase, tier, family, owner — counts update | Validator | 8 |
| MUP-08 | Operations Board | Board columns per lifecycle phase with model cards | Validator | 8 |
| MUP-09 | Operations Board | Table view with sortable columns and row click to Model 360 | Validator | 8 |
| MUP-10 | Model 360 | Header: ID, name, tier, owner, phase, next validation date | Validator | 8 |
| MUP-11 | Model 360 | Status chips and overdue badge | Validator | 8 |
| MUP-12 | Model 360 | Segregation-of-duties banner when developer = validator | Validator | 8 |
| MUP-13 | Model 360 | Lifecycle stepper with current phase | Validator | 8 |
| MUP-14 | Model 360 | Approval history and MRC decisions with notes | Validator | 8 |
| MUP-15 | Model 360 | Validation history with notes | Validator | 8 |
| MUP-16 | Model 360 | Findings list with severity, status, due date | Validator | 8 |
| MUP-17 | Model 360 | Score breakdown by component | Validator | 8 |
| MUP-18 | Model 360 | Backtesting grid and ROC / performance chart | Validator | 6 |
| MUP-19 | Model 360 | Monitoring KPIs with thresholds and Pass/Warn/Fail | Validator | 6 |
| MUP-20 | Model 360 | Linked CDEs | Validator | 7 |
| MUP-21 | Model 360 | Empty state for a model with no history (mock-up M-0089) | Validator | 8 |
| MUP-22 | Import | Template download for T01–T18 | Admin | 3 |
| MUP-23 | Import | T02 demo file preview: 4 loaded, 1 rejected, message names field and row | Admin | 3 |
| MUP-24 | Import | Load uses same path as preview; audit entry visible | Admin | 3 |
| MUP-25 | Documents | Upload and required-document checklist per phase | Validator | 4 |
| MUP-26 | Documents | AI extraction: proposed fields with confirm / drop | Validator | 5 |
| MUP-27 | Data Audit | CDE list with DQ scores by source | Data Owner | 7 |
| MUP-28 | Data Audit | DQ issue list and drill-down | Data Owner | 7 |
| MUP-29 | Report | Governance report generated and downloadable | Executive | G1.16–G1.18 (core report) |
| MUP-30 | Report | MRC report pack (in scope as the model risk report — §12A REQ-REG-10, §81A D9) | Executive | Partial after the core report; full with Phase 2A (D12) |
| MUP-31 | Copilot | Ask a question, answer cites models / records from the app | Executive | 9 |
| MUP-32 | Copilot | Suggested questions | Executive | 9 |
| MUP-33 | All | Theme colours, no drop shadows, no horizontal scroll at 1440×900 | any | 8 |
| MUP-34 | All | Counts agree across Command Center, Operations Board and Model 360 | any | 8 |
| MUP-35 | All | Actions not permitted for the role are hidden and refused by the API | Executive | 1 |

### Accepted differences from the mock-up

Where the BRD and the mock-up disagree, the BRD wins and the difference is recorded here rather than
fixed in the app.

| ID | Mock-up shows | App shows | BRD basis |
|---|---|---|---|
| MUP-01 | A KPI tile labelled "Open findings", valued as a count of findings | "**Models with open findings**", valued in models, with the findings total in the sub-line | §76A CC-01 — a tile must equal the count returned by its own drill-down, and this tile opens a list of models. Review finding CR-05 |

### Phase numbers corrected from the original list

Never renumber an ID; the Phase column is corrected against §81 where the original was wrong.

| ID | Was | Now | Reason |
|---|---|---|---|
| MUP-10, 11, 13, 21 | 3 | 8 | Model 360 is the Phase 8 screen; Phase 3 is the Import Engine |
| MUP-12, 14, 15, 16, 17 | 4 | 8 | The rules are Phase 2, but these are Model 360 panels (Phase 8); Phase 4 is the Document Centre |
| MUP-22, 23, 24 | 2 | 3 | The import engine is Phase 3; Phase 2 is the governance core |
| MUP-25 | 3 | 4 | The Document Centre is Phase 4 |
| MUP-29 | 8 | G1.16–G1.18 | The report is required by §12A, not Phase 8. **D12** builds the core report (REQ-REG-10A, REG-15…17) ahead of the rest of Phase 2A, so this item lands with G1.17 |
| MUP-30 | — | Partial, then 2A | §81A D9 is **decided**: the MRC report pack is in scope as the model risk report (REQ-REG-10, REG-13). **D12** defers the §12A sections, so this is *partial* once the core report lands and full only when Phase 2A resumes |

MUP-35's role was "Viewer", which does not exist in §5; it now reads Executive.
