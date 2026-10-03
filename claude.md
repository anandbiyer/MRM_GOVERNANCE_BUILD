# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> This file is both the repository guide (Part 0) and the Business Requirements Document (from §1 onwards).
> The BRD is the business specification; Part 0 describes how the code that implements it is organised and run.
> Section references like "BRD §57" throughout the codebase point at the numbered sections below.

---

# Part 0 — Working in this repository

## Commands

All paths are relative to the repository root. PowerShell is the primary shell.

```powershell
# Run the whole app (dev mode: SQLite + local file storage, no Docker)
A_Codes\AE_launcher\start_mrm.ps1        # backend :8000 + frontend :5173, seeds on first run
A_Codes\AE_launcher\stop_mrm.ps1
A_Codes\AE_launcher\setup_first_time.ps1 # new machine: venv, npm install, .env, shortcuts

# Backend (from A_Codes\AB_backend)
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
.venv\Scripts\python -m pytest                              # 147 tests: 143 pass, 4 PostgreSQL skip
.venv\Scripts\python -m pytest tests/test_rules.py -k tiering -x
$env:MRM_TEST_POSTGRES_URL="postgresql+psycopg://mrm:mrm_dev_password@localhost:5432/mrm"
.venv\Scripts\python -m pytest tests/test_postgres.py       # migrations, schema drift, audit immutability
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m alembic revision --autogenerate -m "0005_monitoring"

# Backend CLI (from A_Codes\AB_backend) — same service path as the UI
.venv\Scripts\python -m app.cli bootstrap        # policy settings + users only
.venv\Scripts\python -m app.cli reset            # regenerate + load the 256-model seed; keeps the audit trail
.venv\Scripts\python -m app.cli import FILE ...  # validate and load files as one batch

# Frontend (from A_Codes\AC_frontend)
npm run dev          # localhost:5173 (not 127.0.0.1 — see below), proxies /api to 127.0.0.1:8000
npm run typecheck    # tsc -b
npm run build        # typecheck + build — the only lint/type gate in the repo

# Mock-up parity harness (from A_Codes\AF_e2e) — needs the app running on :5173
npx playwright test

# Review agents (inside Claude Code, from the repository root) — reports go to D_Reviews\
/review-build              # all three review agents, one consolidated summary
/review-build phase 6      # scope to a phase, a BRD section (§25) or a criterion prefix (MON)

# Infra (optional; only needed for PostgreSQL/MinIO/Redis)
docker compose -f A_Codes/AA_infra/docker-compose.yml --env-file A_Codes/AA_infra/.env up -d
```

The dev server answers on **`http://localhost:5173`, not `http://127.0.0.1:5173`**:
`AC_frontend/vite.config.ts` sets no `host`, so Vite binds to localhost only, which resolves to `::1`
first on Windows — `127.0.0.1` refuses the connection. Anything scripted against the frontend (the
`A_Codes/AF_e2e` harness, a health probe, a wait loop) must use `localhost`. The backend is the other
way round: uvicorn binds `127.0.0.1:8000`, which is what the Vite proxy targets.

There is no linter or formatter configured. `npm run build` and `pytest` are the gates, and
`.github/workflows/ci.yml` runs them on every push to `main` and every pull request in three jobs:

| Job | What it runs |
|---|---|
| `backend` | `pytest -q` on Python 3.14 against `requirements-lock.txt`, SQLite, no infrastructure |
| `backend-postgres` | `alembic upgrade head` then `pytest tests/test_postgres.py` against a `postgres:16` service — the only coverage for migrations, schema drift and the append-only audit trigger |
| `frontend` | `npm ci` then `npm run build` (`tsc -b` + `vite build`) on Node 22 |

CI installs the **lock** with no fallback to `requirements.txt`, unlike `setup_first_time.ps1`: a lock
that no longer installs is a failure worth seeing. The PostgreSQL job treats a *skipped* test as a
failure, because `tests/test_postgres.py` self-skips when `MRM_TEST_POSTGRES_URL` is unset and would
otherwise report green while asserting nothing.

`.github/workflows/` and `.claude/` (review agents and commands) are the only paths exempt from the
`A_`/`B_`/`C_`/`D_` prefix convention — GitHub and Claude Code require those exact locations.

## Repository layout

Top-level folders and the folders inside `A_Codes/` carry a letter prefix in build/run order.

| Path | Contents |
|---|---|
| `A_Codes/AA_infra/` | docker-compose: PostgreSQL 16, MinIO, Redis |
| `A_Codes/AB_backend/` | FastAPI + SQLAlchemy 2.0 + Alembic (Python 3.14, the same as CI; `.venv` in-folder) |
| `A_Codes/AC_frontend/` | React 19 + TypeScript + Vite + TanStack Query + React Router |
| `A_Codes/AD_seed/` | `generate_seed.py` — deterministic 256-model seed + ~1,100 synthetic evidence PDFs |
| `A_Codes/AE_launcher/` | One-click start/stop/setup PowerShell scripts and shortcuts |
| `A_Codes/AF_e2e/` | Playwright harness and the `mockup-parity.md` checklist; drives the app and the HTML mock-up side by side (review agent 3). Not in CI: it needs a running app |
| `A_Codes/AZ_tools/snapshot.sh` | Copies a file into `_OLD/` before it is edited |
| `B_Inputs/` | Input data: `AA_bootstrap` (policy + core users), `AB_sample_data`, `AC_seed`, `AD_demo_files` (deliberate errors for demos) |
| `C_Requirements/_OLD/` | Earlier requirements and the original HTML prototype (visual reference) |
| `D_Reviews/` | Review agent reports: `DA_code_review/`, `DB_test_review/`, `DC_mockup_review/`, plus a dated consolidated summary. Committed history, like `_OLD/` |
| `E_ProjectPlan/` | `project_plan.md` — the live plan from today's build to a demonstrable product. Stable activity IDs (`G0.1`, `G1.4`), status per activity, decision register and change log. **Update it in the same change that moves the work**, not afterwards |
| `.claude/agents/`, `.claude/commands/` | The three review agents and the `/review-build` command (see Review agents below) |

## Two repository conventions that override normal practice

1. **Never delete or silently rewrite code.** Before editing any existing file under `A_Codes/` or
   `B_Inputs/`, snapshot it first:
   `bash A_Codes/AZ_tools/snapshot.sh A_Codes AB_backend/app/main.py`
   This copies it to `A_Codes/_OLD/<same relative path>/<name>_v<N>_<YYYYMMDD>.<ext>`. The `_OLD/`
   trees are intentionally committed history; never clean them up.
2. **Do not create files outside the repository folder** (no desktop shortcuts, no system temp output
   the user is expected to find).

`Reset to seed` regenerates `B_Inputs/AC_seed` and `B_Inputs/AD_demo_files` for the current business
date, so git will show those as modified after any reset. That is expected.

## Backend architecture — the layering that matters

Request flow, and the rule that no layer may be skipped:

```
app/api/*          FastAPI routers. Auth via deps.require(Permission.X). No business logic.
app/services/*     The only place that writes. Validates, applies rules, writes audit, commits.
app/rules/*        Pure functions. No Session, no I/O. Tiering, revalidation, score, insights, doc rules.
app/models/*       SQLAlchemy ORM (source of truth for metadata).
app/schemas/*      Pydantic request/response models — deliberately separate from ORM models.
app/storage.py     Object store for bytes only (MinioStore | LocalStore behind one Protocol).
```

Key invariants, all enforced in code and covered by tests:

- **Every material write goes through a service**, which calls
  `app.audit.service.record(...)` **in the same transaction** — business change and audit event commit
  or roll back together. Importers and document batches use the same services (`app/ingestion/adapters.py`
  deliberately never touches tables directly), so a CLI import and a UI edit produce identical audit trails.
- **No business number in code.** Thresholds, weights, frequencies, lifecycle phases, required documents
  and keyword lists all live in the `policy_setting` table, read through `app/services/policy_access.Policy`
  (`policy.int("reval_lead_days")`, `policy.score_weights()`, `policy.phase_requirements`). `Policy` is
  cached per `Session` in `session.info` and invalidated on write and on any rollback. If you need a new
  constant, add a policy setting and a `T12` bootstrap row — do not hard-code it.
- **Authorization is two-layered.** `app/auth/roles.py` holds the role→permission matrix ("what may this
  role do"); `app/services/access.py` holds record-level checks ("on which models"). The frontend's
  `navigation.ts` permissions are display-only.
- **The business date is `app.clock.today()`**, never `date.today()` — `MRM_TODAY_OVERRIDE` fixes it for
  demos and tests so seeded overdue/revalidation states are reproducible.
- **Derived governance state is computed on read**, not stored: `app/services/governance_view.py`
  recomputes revalidation status, finding ageing, MRC status and the explainable score from the database
  each time, so a policy change shows up immediately.
- **Background jobs** go through `app/workers/runner.submit`. Job functions take a *session factory* plus
  IDs (never a live `Session`) so they can move to Celery/RQ unchanged. `MRM_JOB_MODE=inline` runs them
  synchronously; tests always use `inline`.

## Ingestion engine

`app/ingestion/registry.py` is the single source of truth for structured templates (T01–T18): blank
template downloads, import validation and the seed generator all read the same `Template`/`Column` specs.
Allowed values that are configurable point at `"policy:<key>"` rather than being listed in the registry.

`app/ingestion/engine.py` runs **the same code path for preview and load** — preview is a full run that is
always rolled back; load re-validates and never trusts the preview. Files in a batch are processed in
template `order` inside one transaction (so T02 models created in a batch satisfy T04 finding references
in the same batch), and **every row runs in its own SAVEPOINT** so a bad row is reported while valid rows
load (partial acceptance). Upserts are idempotent, so a crashed load can simply be re-run.

Because SQLite is used for dev and tests, `app/db.configure_sqlite` is required for SAVEPOINTs and
foreign keys to behave — don't create engines without it.

## Documents

`app/documents/batch.py` handles single/multi/folder/ZIP uploads:
upload → stage bytes → analyse in background (checksum, detect model from `M-0012`-style paths, guess type
from policy `document_type_keywords`, find duplicates/versions) → user reviews and corrects the mapping →
Confirm → store in background. **Nothing becomes a governance document before Confirm.** A failing file
never stops the others. Every stored file is an immutable `DocumentVersion`; an exact SHA-256 re-upload is
refused unless the caller explicitly asks for a new version; documents are archived, never deleted.
A `T17` manifest in the upload overrides all heuristics.

## Frontend

Routes in `src/App.tsx`, sidebar in `src/navigation.ts`, API access via `src/api/client.ts` (`api<T>()`
attaches the bearer token and turns FastAPI error bodies into readable messages) and TanStack Query hooks
in `src/api/queries.ts`. Dev auth is a no-password user+role picker (`SignInPage`, `RoleSwitcher`).
Visual language: dark-first, flat cards, thin borders, no shadows, dense tables, status pills — all in the
single stylesheet `src/styles/app.css`. `C_Requirements/_OLD/MRM_Governance_MIS_Demo.html` is the visual
reference only, not an architectural one.

## Build status by phase

Phase numbers in §81 are identifiers, not the build order.

Implemented: Phases 1–4 and the core of Phase 8 — foundation/RBAC, governance core (inventory, tiering, lifecycle,
validation, findings, approvals, score), the import engine (T12, T01–T05), the Document Centre
(single/batch/folder/ZIP, versioning, completeness), Command Center, Operations Board, Model 360, Import
Centre, Admin, Audit Trail.

Not yet built, in build order. The "seam already exists" column says what is actually in place — it is
not uniform, so check it before assuming there is a placeholder to replace:

| # | Capability | Phase | Seam already exists |
|---|---|---|---|
| 1 | **Regulatory alignment (SR 26-2)** — §12A, templates T19–T21. Extends the built inventory, tiering, validation and Command Center; needs no §81A decision. REG-07 waits for Phase 6 | 2A | **Nothing yet** — no registry entries for T19–T21, no tables, no route |
| 2 | **Monitoring** — templates T13–T16 and T07–T09 | 6 | Registry entries (`available=False`), the Monitoring Dashboard `PlannedPage`, the Model 360 Monitoring tab, and the score's not-available component |
| 3 | **Data Audit / CDE-DQ** — templates T06 and T10 | 7 | Registry entries (`available=False`), the Data Audit `PlannedPage`, the Model 360 CDE/DQ tab |
| 4 | **AI extraction** | 5 | `document.extraction_status` defaults to "Not started"; the documentation score names the dependency |
| 5 | **Audit Copilot**, then hardening (Phase 10) | 9 | **Nothing yet** — no route, nav entry or placeholder |

**Do not start Phase 6 until decisions D1–D7 in §81A are recorded.** Phase 7 also needs D8, and Phase 9
needs D11. When adding these, follow the existing seams: new `app/monitoring/` service package,
new rules modules, new Alembic revision, new registry templates, replace the `PlannedPage` route.

## Review agents

Three Claude Code subagents in `.claude/agents/` check the build. `/review-build` runs them and writes one
consolidated summary to `D_Reviews/<YYYYMMDD>_summary.md`.

| Agent | Checks | Writes |
|---|---|---|
| `requirements-reviewer` | Code against the BRD, the acceptance criteria and the Part 0 invariants: traceability per BRD section, layering, audit in the same transaction, no business numbers in code, server-side authorization, `app.clock.today()`, the snapshot convention | `D_Reviews/DA_code_review/` |
| `test-outcome-reviewer` | Runs the CI gates, maps every test to its criterion ID, judges whether each assertion proves the criterion's expected result, and recalculates the §76A.14 coverage table | `D_Reviews/DB_test_review/` |
| `mockup-parity-tester` | Resets the seed with a fixed business date, runs the app and compares each screen with the HTML mock-up through the `A_Codes/AF_e2e` harness and its `mockup-parity.md` checklist | `D_Reviews/DC_mockup_review/`, `A_Codes/AF_e2e/` |

Rules for the agents:

- They report; they never edit product code, backend or frontend tests, seed data, `B_Inputs/` or this
  file. Only `mockup-parity-tester` maintains `A_Codes/AF_e2e/` (snapshot convention applies).
  Findings are fixed afterwards in the main session.
- Run `/review-build` at the end of every phase and before merging to `main`.
- When the BRD and the mock-up disagree, the BRD wins; the difference is recorded, not fixed.
- Capabilities not yet built are reported as "Not built (Phase N)", never as failures.
- Where the BRD contradicts itself, the agent reports a spec issue for a decision instead of guessing.

---

# Model Governance Management Information System (MRM/MIS)
## Business Requirements Document (BRD) — Development Specification

**Version:** 1.0  
**Date:** 30 September 2026  
**Purpose:** Development specification for Claude Code  
**Status:** Proposed / Development Baseline  
**Source documents:** Existing Model Governance MIS requirements/design, input templates, and HTML prototype.

---

# 1. Executive Summary

The objective is to develop a **Model Governance Management Information System (MRM/MIS)** that provides a central, auditable view of the model inventory, model lifecycle, validation, findings, approvals/MRC decisions, model documentation, monitoring results, critical data elements, data-quality results, governance scores and management information.

The system shall support both:

1. **Structured data ingestion** through Excel/CSV templates, and
2. **Unstructured evidence ingestion** through individual documents, multiple documents, and complete folder structures.

The existing requirements already define a strong initial capability: template-driven onboarding, model inventory, validation history, findings, approvals, CDE/DQ information, KPI results, performance curves, governance scoring, Model 360, Command Center, Operations Board, Data Audit, Audit Copilot, document extraction and audit trail.

This BRD extends that design in four important areas:

- **Model Monitoring:** ongoing monitoring plans, monitoring runs, KPI/threshold evaluation, performance deterioration, drift/stability, backtesting, data-quality monitoring, breaches, alerts, issues and evidence.
- **Document Management:** individual and batch document uploads, document classification, versioning, metadata, duplicate detection, extraction, review/confirmation and traceability.
- **Batch Upload:** users can upload multiple files in one operation, including mixed document types and structured data files.
- **Folder/Package Upload:** users can upload a folder structure or ZIP package while preserving the hierarchy and establishing relationships between folders, documents, models, monitoring periods and governance records.

The target architecture proposed in this BRD is:

**React + TypeScript frontend → Python/FastAPI backend → PostgreSQL → MinIO/S3-compatible object storage → Redis + Celery/RQ for asynchronous jobs → optional pgvector for semantic document search → Claude/other LLM through a server-side AI service.**

The system shall be designed as a reusable enterprise-style platform rather than a demo hard-coded around the existing seed data.

---

# 2. Business Objectives

## 2.1 Primary objectives

The system shall:

1. Maintain a complete and authoritative model inventory.
2. Provide a single source of truth for model governance information.
3. Track the full model lifecycle from initiation through retirement.
4. Track validation activities and validation outcomes.
5. Track findings, remediation and overdue issues.
6. Track MRC/approval decisions and conditions.
7. Maintain model documentation and supporting evidence.
8. Monitor model performance and model risk indicators.
9. Track KPI thresholds, breaches and trends.
10. Track data-quality rules and CDE health.
11. Calculate configurable model governance scores.
12. Provide management dashboards and operational work queues.
13. Provide an auditable history of all material changes.
14. Support individual, batch and folder-based data/document ingestion.
15. Reduce manual effort in onboarding and maintaining model governance records.
16. Provide controlled AI-assisted document extraction and governance querying.
17. Preserve evidence and lineage so users can answer:
   - What happened?
   - When did it happen?
   - Who changed it?
   - What evidence supports it?
   - Which model does it relate to?
   - Which monitoring/validation run produced it?

---

# 3. Scope

## 3.1 In scope

### Model inventory
- Model registration.
- Model metadata.
- Model owners/developers/validators.
- Lifecycle phase.
- Model version.
- Business line.
- Model type/subtype.
- Risk tier.
- Tiering questionnaire.
- Tier override.
- Revalidation frequency.
- Last validation date.
- Next validation due date.
- Model relationships and successor models.

### Governance
- Validation history.
- Findings.
- Remediation status.
- Approvals.
- MRC decisions.
- Conditions.
- Governance score.
- Governance insights.
- Segregation of duties.

### Monitoring
- Monitoring plans.
- Monitoring frequency.
- Monitoring KPIs.
- Thresholds.
- Warning bands.
- Monitoring runs.
- Monitoring results.
- Historical trends.
- Performance metrics.
- Backtesting.
- Drift/stability indicators.
- Data-quality monitoring.
- Breaches.
- Alerts.
- Monitoring issues.
- Evidence.
- Monitoring sign-off/review.

### Documents
- Individual upload.
- Multi-file upload.
- Folder upload.
- ZIP/package upload.
- Folder hierarchy preservation.
- Document metadata.
- Document versioning.
- Document classification.
- Document-to-model association.
- Document-to-validation association.
- Document-to-monitoring-run association.
- Document extraction.
- Human confirmation.
- Document completeness assessment.
- Document search.
- Download/view evidence.
- Document audit trail.

### Structured ingestion
- Excel.
- CSV.
- Batch Excel/CSV upload.
- Validation.
- Preview.
- Partial acceptance.
- Error reports.
- Import history.
- Re-import/update.
- Idempotency.
- Load dependencies.

### Management information
- Command Center.
- Operations Board.
- Model 360.
- Monitoring Dashboard.
- Data Audit.
- Import Center.
- Document Centre.
- Admin.
- Audit Trail.
- Audit Copilot.

---

# 4. Out of Scope for Initial Release

Unless explicitly enabled as a later phase:

- Direct integration with enterprise GRC platforms.
- Automatic regulatory submission.
- Automatic model changes.
- Automatic approval of findings.
- Automatic approval of extracted document content.
- Automatic lifecycle phase changes based solely on monitoring.
- Production model execution.
- Direct access to model source code repositories.
- Real-time trading/model execution systems.
- Automated regulatory interpretation.
- Automated replacement of human validation judgement.

The system may identify, calculate, flag and recommend workflow actions, but governance decisions remain human-controlled.

---

# 5. User Roles

The initial role model shall include:

| Role | Core responsibility |
|---|---|
| Admin | Configuration, users, policies, imports, system administration |
| Model Owner | Own model governance, documents, monitoring and remediation |
| Model Developer | Maintain development-related information and evidence |
| Validator | Perform/record independent validation and upload validation evidence |
| MRC Member | Review approvals, decisions and conditions |
| Auditor | Read-only governance and evidence access |
| Executive | Read-only management information |
| Monitoring Analyst | Maintain monitoring definitions/results and investigate breaches |
| Data Owner | Maintain CDE/data-quality information |
| Platform Administrator | Technical administration, storage and processing configuration |

A user may have one or more functional roles in the production version.

---

# 6. Functional Requirements

## 6.1 Model Inventory

### REQ-INV-01 — Model registration
The system shall allow an authorised user to create a model record.

Mandatory information shall include:
- Model ID
- Model name
- Model type
- Model subtype
- Purpose
- Business line
- Owner
- Developer
- Validator where applicable
- Lifecycle phase
- Version
- Go-live date where applicable
- Revalidation frequency
- Last validation date where applicable
- Tiering answers

### REQ-INV-02 — Model editing
Authorised users shall be able to edit model metadata.

Every edit shall generate an audit event containing:
- User
- Role
- Timestamp
- Entity
- Entity ID
- Before value
- After value

### REQ-INV-03 — Segregation of duties
The system shall prevent a validator from being the same person as the model owner or developer.

The check shall operate:
- During manual model creation.
- During manual editing.
- During structured import.
- During batch import.

### REQ-INV-04 — Model version
Model version shall be tracked independently from the model ID.

The system shall support multiple versions where required.

### REQ-INV-05 — Model relationships
The system shall support:
- Successor model.
- Predecessor model.
- Related model.
- Parent/child model.
- Model family/group.

---

# 7. Risk Tiering

The initial design contains four tiering questions:

1. Materiality.
2. Complexity.
3. Reliance.
4. Regulatory use.

Each is scored 1–3.

The system shall calculate:

**Tier Score = Materiality + Complexity + Reliance + Regulatory Use**

Initial policy thresholds:

- High: >= 10
- Medium: 7–9
- Low: <= 6

These values must be configuration-driven.

The system shall support an authorised tier override with:
- Override tier.
- Reason.
- User.
- Timestamp.
- Previous calculated tier.
- New tier.

The system shall never delete the calculated tier when an override is applied.

---

# 8. Model Lifecycle

The system shall support:

1. Initiation
2. Development
3. Validation
4. Implementation
5. Monitoring
6. Reg/Audit
7. Retirement

Revalidation shall be represented as a governance work state and not necessarily as a separate lifecycle phase.

The system shall display:
- Current phase.
- Previous phase.
- Phase transition date.
- User who performed the transition.
- Optional transition reason.
- Required evidence for the transition.

---

# 9. Validation Management

The system shall maintain validation exercises including:

- Validation ID.
- Model.
- Validation type.
- Validator.
- Start date.
- Completion date.
- Outcome.
- Validation report.
- Findings.
- Recommendations.

Validation types:
- Initial.
- Periodic.
- Targeted.
- Change.

Outcomes:
- Approved.
- Conditional.
- Rejected.
- In Progress.

The system shall calculate validation currency against the configured revalidation frequency.

---

# 10. Revalidation Management

The system shall calculate:

**Next Validation Date = Last Validation Date + Revalidation Frequency**

Supported frequencies:
- Monthly
- Quarterly
- Semi-annual
- Annual
- Biennial

The system shall classify a model as:
- Scheduled
- Due Soon
- Overdue

The lead-time and due-soon thresholds shall be configurable.

The system shall display:
- Next due date.
- Days remaining.
- Days overdue.
- Risk tier.
- Owner.
- Last validation.
- Latest outcome.

---

# 11. Findings and Remediation

Each finding shall contain:

- Finding ID
- Model
- Validation
- Title
- Description
- Severity
- Category
- Status
- Owner
- Raised date
- Due date
- Closed date
- Source
- Evidence
- Root cause
- Management response
- Remediation action

Initial severity:
- Critical
- Medium
- Low

Initial status:
- Open
- In Progress
- Closed

Additional recommended status:
- Accepted Risk
- Deferred
- Rejected

The system shall calculate:
- Days open.
- Days overdue.
- Number of overdue findings.
- Critical overdue findings.
- Finding ageing.

---

# 12. MRC and Approval Management

The system shall maintain:

- Approval ID.
- Model.
- Decision date.
- Forum.
- Decision type.
- Decision.
- Conditions.
- Condition due date.
- Condition status.
- Supporting document.

Decisions:
- Approved
- Conditional
- Rejected

Conditional decisions shall remain visible until all conditions are closed.

---

# 12A. Regulatory Alignment — SR 26-2 / OCC Bulletin 2026-13

Numbered 12A so no existing section shifts.

## 12A.1 Basis

On 17 April 2026 the Federal Reserve and the OCC issued revised interagency guidance on model risk
management (SR 26-2 / OCC Bulletin 2026-13). It replaces SR 11-7 (2011) and SR 21-8 (2021, BSA/AML
models). It is aimed mainly at banking organisations with more than $30 billion in assets, and applies
to smaller ones in proportion to their model risk. The main points this system must support:

- **Model definition.** Simple arithmetic calculations (for example in spreadsheets) are not models;
  tools that forecast or estimate still are.
- **Materiality and proportionality.** Practices are tailored to the number and complexity of models and
  to each model's materiality — its exposure and its purpose.
- **Development, validation, monitoring and governance** remain the core elements, with effective
  challenge by qualified, independent people with the standing to require change.
- **Third-party models.** The bank stays fully responsible, must understand the model conceptually, and
  relies on outcomes analysis and monitoring where the vendor's code is not available.
- **Aggregate model risk.** Risk from dependencies and shared assumptions across models is assessed and
  reported to senior management and the board, not only model by model.
- **Generative and agentic AI** are not addressed by SR 26-2; the agencies expect to issue separate
  guidance. Models that such systems call remain in scope.

This section turns those points into system requirements. It does not make the system interpret
regulation (§4): every threshold, list and label below is a policy setting (T12), so each bank sets its
own framework. The label shown on screens and reports is the policy key `regulatory_framework`, seeded
as "SR 26-2 / OCC Bulletin 2026-13".

## 12A.2 Requirements

### REQ-REG-01 — Inventory classification
Every inventory record shall carry an `inventory_class`:
- **Model** — in full MRM scope.
- **Tool** — a calculation that is not a model under the bank's definition (for example simple arithmetic
  or deterministic business rules). Tracked with owner, purpose and business line; not tiered, validated
  or scored.
- **AI system** — a generative or agentic AI system. Tracked with owner, purpose, provider and the models
  it uses; governed outside formal MRM until the bank's AI policy says otherwise.

Tool and AI system records require a `classification_reason`. Only a user with the `REG_CLASSIFY`
permission (Validator and Admin by default) may change the class; every change is audited with the
reason. Tools and AI systems are excluded from model counts, tiering, revalidation, the governance score
and the Operations Board unless a class filter asks for them.

### REQ-REG-02 — AI systems that use models
An AI system may be linked to the models it calls. The linked models stay in full scope, and each shows
"Used by AI system" on Model 360.

### REQ-REG-03 — Materiality: exposure and purpose
The model record shall hold `exposure_amount`, `exposure_currency` and `exposure_basis` (for example
portfolio balance, P&L at risk, capital impact). Where an exposure amount is given, the tiering screen
shall suggest a Materiality answer from the policy bands `materiality_exposure_bands`; the user's answer
is kept and the suggestion never overwrites it. Purpose is covered by the existing Reliance and
Regulatory use answers. The tier formula in §7 is unchanged.

A `tier_rationale` is required when the tier is High and when a tier override is applied.

### REQ-REG-04 — Proportionate revalidation
The default revalidation frequency for a new model comes from the policy map `reval_frequency_by_tier`.
A frequency longer than the tier default requires a `frequency_deviation_reason`. Changing the policy
does not rewrite existing models; models now longer than their tier default are listed as an insight.

### REQ-REG-05 — Third-party (vendor) models
The model record shall hold `is_vendor`, `vendor_name`, `vendor_product`, `vendor_version` and
`vendor_customisation` (customisations, settings or overlays applied by the bank). A vendor model
requires vendor name and product. The documents in the policy list `vendor_required_documents` (by
default: vendor methodology document, conceptual soundness review, outcomes analysis) count towards
document completeness (§40) for vendor models only.

A vendor model in the Monitoring phase with no outcomes-analysis or backtest run within
`vendor_outcomes_max_age_days` raises an insight. This part needs Phase 6.

### REQ-REG-06 — Effective challenge log
Each validation may hold challenge records: what the validator challenged, to whom, the owner's or
developer's response, and the resolution (Accepted, Response accepted, Escalated, Finding raised).
"Finding raised" creates the linked finding in the same transaction. A challenge cannot be raised by the
model's owner or developer (the independence check of REQ-INV-03). A challenge still open after its due
date raises an insight.

### REQ-REG-07 — Limitations, overlays and use exceptions
Each model may hold records of type:
- **Limitation** — a known weakness or condition of use.
- **Overlay** — a management adjustment to model output, with amount or description.
- **Use exception** — approval to keep using a model whose validation is overdue or whose latest outcome
  is Rejected.

Overlays and use exceptions require a rationale, an approver, an approval date and an expiry date; the
approver cannot be the model's owner or developer, and the `OVERLAY_APPROVE` permission (MRC Member by
default) is required. Expired overlays and exceptions raise an insight and show a badge on Model 360. A
model in Implementation or Monitoring whose latest validation outcome is Rejected, or whose revalidation
is Overdue, without an active use exception raises a Critical insight.

### REQ-REG-08 — Model dependencies
REQ-INV-05 relationships shall add a **Uses output of** dependency, with an optional `shared_component`
(for example "macroeconomic scenario generator"). A model cannot depend on itself, and a dependency that
would create a cycle is refused. When an upstream model has an open Critical finding, a Critical
monitoring breach, a Rejected latest outcome or an overdue revalidation, every downstream model shows
"Upstream issue" and an insight is raised.

### REQ-REG-09 — Aggregate model risk view
The Command Center shall show aggregate model risk alongside the existing portfolio view:
- Models by tier and by validation status (a tier × status grid).
- Share of High-tier models with overdue validation, open Critical findings, active overlays or active
  use exceptions.
- Vendor model share and vendor models without recent outcomes analysis.
- Dependency concentration: upstream models ranked by number of dependent models, with their own status.
- Tools and AI systems count, shown separately from models.

Every figure drills down to the list of models behind it and agrees with the Operations Board and
Model 360.

### REQ-REG-10 — Model risk report for senior management and the board
The system shall generate a model risk report for a chosen business date containing: inventory summary
by class and tier; validation status and overdue validations; open and overdue findings; active overlays,
limitations and use exceptions; vendor models; dependency concentration; open effective challenges; and
changes since the previous report. Figures equal the Command Center on the same business date. Report
generation is audited. The report may later include AI commentary (Phase 9), which is labelled as such
and needs human confirmation (Principle 10); the report is complete without it. This is the BRD basis for
the MRC report shown in the mock-up (§81A D9).

### REQ-REG-11 — Internal audit access
The Auditor role can read every record in this section and download the model risk report and a model's
evidence (documents, validations, challenges, findings, overlays, audit trail) as one package. Every write
by the Auditor role is refused on the server.

## 12A.3 Templates

Registered in the template registry like T01–T18 (§71):

- **T02 Model Inventory** gains optional columns `inventory_class` (default Model),
  `classification_reason`, `exposure_amount`, `exposure_currency`, `exposure_basis`, `tier_rationale`,
  `is_vendor`, `vendor_name`, `vendor_product`, `vendor_version`, `vendor_customisation`,
  `frequency_deviation_reason`. Existing T02 files without them still load.
- **T19 Effective Challenge** — challenge_id, validation_id, model_id, raised_by, raised_to, raised_date,
  due_date, topic, challenge, response, response_date, resolution, finding_id.
- **T20 Limitations, Overlays and Exceptions** — record_id, model_id, record_type, description,
  amount, rationale, approver, approval_date, effective_from, expiry_date, status.
- **T21 Model Dependencies** — model_id, depends_on_model_id, dependency_type, shared_component, note.

## 12A.4 Seed

The seed adds, deterministically: vendor models among the existing 256; a small set of Tool and AI
system records **in addition to** the 256 models, so existing model counts and tests do not change;
dependencies around at least one shared upstream model (a macroeconomic scenario model used by credit,
provisioning and stress-testing models); overlays, limitations and use exceptions including expired
ones; and challenge records on recent validations. Seed targets are documented with the §70 targets.

---

# 13. MODEL MONITORING — NEW CORE REQUIREMENT

## 13.1 Monitoring objective

The Model Monitoring capability shall provide an ongoing mechanism to determine whether a model remains within approved performance, stability, data-quality and governance boundaries after implementation.

Monitoring shall be evidence-based and time-series oriented.

The system shall distinguish:

- Monitoring definition.
- Monitoring run.
- Monitoring result.
- Threshold.
- Breach.
- Alert.
- Investigation.
- Finding/issue.
- Resolution.
- Evidence.

---

# 14. Monitoring Plan

Each production/monitoring model shall have a Monitoring Plan.

A Monitoring Plan shall contain:

- Monitoring plan ID.
- Model ID.
- Model version.
- Effective date.
- Monitoring owner.
- Reviewer.
- Monitoring frequency.
- Monitoring methodology.
- Required KPIs.
- Thresholds.
- Warning thresholds.
- Escalation thresholds.
- Required data sources.
- Required CDEs.
- Required monitoring reports.
- Review calendar.
- Approval status.
- Last review date.
- Next review date.

The monitoring plan shall be versioned.

Example:

| Attribute | Example |
|---|---|
| Model | M-0012 |
| Frequency | Quarterly |
| Owner | Model Owner |
| Reviewer | Validator |
| KPI | Gini |
| Target | >= 0.65 |
| Warning | 0.6175–0.65 |
| Breach | < 0.6175 |
| Data quality | >= 98% |
| Drift | PSI <= 0.10 |
| Review | Quarterly |

---

# 15. Monitoring Metrics

The system shall support configurable monitoring metrics rather than hard-coding a fixed list.

Metric categories shall include:

### 15.1 Discrimination/performance
Examples:
- Gini.
- AUC.
- KS.
- Accuracy.
- Precision.
- Recall.
- F1.
- Brier score.

### 15.2 Calibration
Examples:
- Calibration error.
- Observed vs predicted default rate.
- Predicted vs actual.
- Calibration slope/intercept.

### 15.3 Stability/drift
Examples:
- PSI.
- CSI.
- Population distribution change.
- Characteristic drift.
- Feature distribution drift.

### 15.4 Forecast/error metrics
Examples:
- MAE.
- MAPE.
- RMSE.
- Forecast bias.

### 15.5 Data quality
Examples:
- Completeness.
- Accuracy.
- Validity.
- Timeliness.
- Uniqueness.
- Referential integrity.

### 15.6 Business outcome monitoring
Examples:
- Actual loss vs predicted loss.
- Actual delinquency vs predicted PD.
- Exposure movement.
- Utilisation.
- Portfolio mix.

---

# 16. Monitoring Thresholds

Each monitoring metric shall support:

- Target/threshold.
- Warning threshold.
- Breach threshold.
- Direction:
  - Higher is better.
  - Lower is better.
  - Within range.
- Unit.
- Frequency.
- Applicable model types.
- Effective date.

Threshold changes shall be versioned and audited.

Historical results shall continue to use the threshold applicable at the time of the monitoring run.

---

# 17. Monitoring Run

A Monitoring Run represents one execution/review cycle.

Example:

**M-0012 / 2026-Q3 Monitoring Run**

A run shall contain:

- Run ID.
- Model.
- Model version.
- Period.
- Run date.
- Monitoring type.
- Data period.
- Status.
- Reviewer.
- Sign-off.
- Evidence package.
- Overall result.

Run status:
- Not Started
- In Progress
- Completed
- Under Review
- Approved
- Rejected

---

# 18. Monitoring Result

Every metric evaluated in a run shall create a Monitoring Result.

Fields:

- Monitoring result ID.
- Run ID.
- Metric ID.
- Actual value.
- Expected value.
- Threshold.
- Warning threshold.
- Status.
- Previous value.
- Change percentage.
- Evidence.
- Comment.
- Reviewer.
- Review status.

Status:
- Pass
- Warn
- Fail
- Not Available
- Not Applicable

---

# 19. Monitoring Trend Analysis

The system shall display historical monitoring results.

For each metric:
- Current value.
- Previous value.
- 4-period trend where available.
- 8-period trend where available.
- Target.
- Warning band.
- Breach band.

The system shall support charts such as:

- Metric trend.
- Actual vs threshold.
- Predicted vs actual.
- PSI trend.
- Gini/AUC trend.
- DQ trend.
- Breach history.

The user shall be able to drill from a trend point to the underlying monitoring run.

---

# 20. Monitoring Breach Management

A monitoring breach shall be created when a metric violates its configured threshold.

A breach shall contain:

- Breach ID.
- Model.
- Model version.
- Monitoring run.
- Metric.
- Actual value.
- Threshold.
- Severity.
- Detected date.
- Owner.
- Due date.
- Status.
- Root cause.
- Impact assessment.
- Management response.
- Resolution.
- Evidence.

The system shall support:

- New.
- Acknowledged.
- Under Investigation.
- Action Required.
- Closed.
- Accepted Risk.

A monitoring breach may optionally generate a formal model-risk finding.

---

# 21. Monitoring Escalation

Severity may be determined by configurable rules such as:

- High-risk model + failed critical KPI = Critical.
- Repeated warning for N periods = Escalation.
- Repeated failure = Critical/High.
- Material data-quality failure = High.
- Regulatory KPI failure = High/Critical.

These rules must be configurable rather than hard-coded.

The system shall record the rule that generated the escalation.

---

# 22. Repeated Breach Detection

The system shall identify repeated failures.

Examples:

- Same KPI fails for 2 consecutive periods.
- Same KPI fails for 3 of the last 4 periods.
- PSI remains above threshold for multiple periods.
- Data-quality rule fails repeatedly.
- Performance declines continuously.

The system shall present these as governance insights.

The system shall not automatically change the model lifecycle phase unless such automation is explicitly configured by policy.

---

# 23. Backtesting

The system shall support backtesting results as a monitoring category.

Each backtest shall contain:

- Backtest ID.
- Model.
- Model version.
- Methodology.
- Test period.
- Metric.
- Expected value.
- Actual value.
- Result.
- Threshold.
- Outcome.
- Supporting evidence.

Backtesting shall be shown separately from routine monitoring.

---

# 24. Monitoring Evidence

A monitoring run shall support multiple evidence files.

Examples:
- Monitoring report.
- KPI output.
- Data-quality report.
- Backtesting report.
- Drift report.
- Management commentary.
- Approval/sign-off.

Every evidence document shall be linked to:
- Model.
- Model version.
- Monitoring run.
- Metric where applicable.

---

# 25. Monitoring Dashboard

Add a dedicated **Monitoring Dashboard**.

The dashboard shall contain:

### Portfolio monitoring tiles
- Models monitored this period.
- Monitoring runs completed.
- Monitoring runs overdue.
- Models with KPI failures.
- Models with warnings.
- Models with critical breaches.
- Models with repeated breaches.
- Models with data-quality failures.
- Models requiring review.

### Charts
- Pass/Warn/Fail distribution.
- Breaches by severity.
- Breaches by model type.
- Breaches by business line.
- KPI trend.
- Performance trend.
- Drift trend.
- DQ trend.
- Monitoring completion trend.

### Work queue
- Overdue monitoring.
- Failed KPI.
- Critical breach.
- Repeated breach.
- Evidence missing.
- Review/sign-off pending.

---

# 26. Model 360 — Monitoring Section

Model 360 shall contain a dedicated Monitoring tab.

Sections:

1. Monitoring Plan.
2. Current monitoring status.
3. Latest monitoring run.
4. KPI scorecard.
5. Performance trend.
6. Stability/drift.
7. Data quality.
8. Backtesting.
9. Breaches.
10. Monitoring findings.
11. Monitoring evidence.
12. Historical runs.

The user shall be able to drill from:
**Model → Monitoring Run → Metric → Result → Evidence/Breach.**

---

# 27. DOCUMENT MANAGEMENT — NEW CORE REQUIREMENT

The document capability shall be treated as a document management subsystem rather than only a document upload field.

A document shall have:

- Document ID.
- File name.
- File type.
- MIME type.
- Size.
- Hash.
- Model ID.
- Model version.
- Document type.
- Document subtype.
- Version.
- Effective date.
- Uploaded date.
- Uploaded by.
- Source.
- Folder ID.
- Parent folder.
- Extraction status.
- Review status.
- Classification status.
- Storage location.
- Retention metadata.
- Confidentiality classification where required.

---

# 28. Document Types

Initial document types:

- Terms of Reference.
- Model Development Document.
- Validation Report.
- Monitoring Report.
- Backtesting Report.
- Model Approval/MRC Paper.
- Model Change Document.
- Data Quality Report.
- Regulatory/Audit Evidence.
- Model Inventory Evidence.
- Other.

The list shall be configurable.

---

# 29. Individual Document Upload

Users shall be able to upload one document.

Workflow:

**Select Model → Select Document Type → Select Version → Upload → Validate → Extract → Review → Confirm → Store**

The user shall see:
- File name.
- Size.
- File type.
- Model.
- Document type.
- Version.
- Upload progress.
- Processing status.
- Extraction status.
- Review status.

---

# 30. Batch Document Upload

Users shall be able to upload multiple files in a single operation.

Example:

```
M-0012/
    TOR.pdf
    MDD.pdf
    Validation_Report_2026.pdf
    Monitoring_Report_Q2_2026.pdf
    Backtesting_Q2_2026.xlsx
```

The user shall be able to upload all files together.

The system shall:
1. Detect every file.
2. Validate file type.
3. Calculate checksum.
4. Detect duplicates.
5. Determine folder path.
6. Identify candidate model.
7. Identify candidate document type.
8. Extract metadata where possible.
9. Queue processing.
10. Show progress.
11. Produce a batch summary.

---

# 31. Folder Upload

The user shall be able to select a local folder and upload it.

The system shall preserve:

- Folder name.
- Nested folders.
- Relative file path.
- File name.
- Folder hierarchy.

Example:

```
Model_Governance/
├── Credit_Risk/
│   ├── M-0012/
│   │   ├── Governance/
│   │   │   ├── TOR.pdf
│   │   │   └── MDD.pdf
│   │   ├── Validation/
│   │   │   └── Validation_Report.pdf
│   │   └── Monitoring/
│   │       ├── 2026_Q1/
│   │       └── 2026_Q2/
│   └── M-0042/
└── Forecasting/
    └── M-0076/
```

The system shall preserve this logical structure.

---

# 32. ZIP Package Upload

Because browser folder upload support varies, the system shall also support ZIP package upload.

The system shall:
- Accept ZIP.
- Scan contents.
- Reject unsupported file types.
- Prevent path traversal.
- Preserve relative paths.
- Extract files into controlled storage.
- Create folder records.
- Process each document asynchronously.
- Provide a package-level processing report.

---

# 33. Folder-to-Model Mapping

The system shall support multiple mapping methods.

### Method A — Folder naming convention

Example:

`/M-0012/Validation/`

The system identifies:
- Model = M-0012
- Area = Validation

### Method B — User mapping

The system presents:

| Folder | Candidate model | User action |
|---|---|---|
| M-0012 | M-0012 Wholesale PD | Confirm |
| M-0042 | M-0042 ALM | Confirm |

### Method C — Metadata extraction

The system extracts model IDs/model names from documents.

### Method D — Manifest file

The user may provide:

`manifest.xlsx`

containing:
- File path.
- Model ID.
- Document type.
- Version.
- Effective date.

The manifest shall override heuristic classification.

---

# 34. Document Classification

Classification may use:

1. Folder name.
2. File name.
3. Manifest.
4. Document content.
5. AI extraction.

Classification shall produce:
- Document type.
- Confidence.
- Reason.

AI classification shall never silently commit governance data without human confirmation where the classification affects material governance records.

---

# 35. Duplicate Documents

The system shall calculate a SHA-256 checksum.

Duplicate logic shall identify:
- Exact file duplicate.
- Same document with different filename.
- Same document version.
- Potential duplicate requiring user review.

The system shall not create duplicate records for exact re-upload unless the user explicitly chooses to create a new version.

---

# 36. Document Versioning

Documents shall support versions:

`1.0 → 1.1 → 2.0`

The system shall maintain:
- Current version.
- Previous versions.
- Uploaded date.
- Uploaded by.
- Change reason.

Historical versions must remain available.

---

# 37. Document Extraction

Existing extraction requirements shall be retained.

Supported initial extraction:

### ToR
- Model name.
- Purpose.
- Scope.
- Intended use.
- Planned dates.

### MDD
- Required section presence.
- Assumptions.
- Limitations.

### Validation Report
- Outcome.
- Findings.
- Severity.
- Category.
- Description.
- Recommended due date.

### Monitoring Report
Additional extraction:
- Monitoring period.
- Overall monitoring conclusion.
- KPI results.
- Failed metrics.
- Warning metrics.
- Breaches.
- Management commentary.
- Recommended actions.

AI output shall be:
**Extracted → Validated → Human Reviewed → Confirmed → Persisted.**

---

# 38. Document Review Queue

The Document Centre shall contain a Review Queue.

Columns:
- Document.
- Model.
- Document type.
- Version.
- Extraction status.
- Classification confidence.
- Review status.
- Uploaded by.
- Uploaded date.

Review actions:
- Confirm.
- Edit.
- Reject.
- Reclassify.
- Re-run extraction.
- Download original.

---

# 39. Folder-Level Governance View

The system shall provide a package/folder view.

Example:

**M-0012 Governance Evidence**

```
Governance
 ├── ToR                    ✓
 ├── MDD                    ✓
 ├── Approval Paper         ✓
Validation
 └── Validation Report      ✓
Monitoring
 ├── 2026 Q1                ✓
 ├── 2026 Q2                ⚠
 └── 2026 Q3                ✕
```

The system shall highlight missing expected evidence.

---

# 40. DOCUMENT COMPLETENESS

Document completeness shall be calculated based on:

- Lifecycle phase.
- Required document policy.
- Model type where applicable.
- Model risk tier where applicable.
- Monitoring requirements.

Example:

Development:
- ToR
- MDD

Validation:
- ToR
- MDD
- Validation Report

Production:
- ToR
- MDD
- Validation Report
- Approval evidence
- Monitoring plan

The required-document policy shall be configurable.

---

# 41. DATA INGESTION FRAMEWORK

The ingestion framework shall support:

### Structured
- XLSX.
- CSV.
- JSON where enabled.
- API payloads in future.

### Unstructured
- PDF.
- DOCX.
- XLSX evidence.
- PPTX where enabled.
- ZIP packages.

### Modes
- Individual upload.
- Batch upload.
- Folder upload.
- ZIP package.
- Manifest-driven upload.

---

# 42. IMPORT BATCH

Every ingestion operation shall create an Import Batch.

Fields:

- Batch ID.
- Batch type.
- Uploaded by.
- Start time.
- End time.
- Source.
- Number of files.
- Number of records.
- Successful records.
- Failed records.
- Warnings.
- Status.
- Error report.

Status:
- Uploaded
- Validating
- Validation Failed
- Ready
- Processing
- Partially Completed
- Completed
- Failed
- Cancelled

---

# 43. Import Preview

Before committing structured data, users shall see:

- File name.
- Template.
- Number of rows.
- Valid rows.
- Invalid rows.
- Warnings.
- New records.
- Existing records.
- Records to update.

The user shall explicitly choose **Load** before data is persisted.

---

# 44. Partial Acceptance

The system shall support valid-row loading.

Example:

100 rows uploaded:
- 94 valid.
- 6 invalid.

User sees:

**94 rows will be loaded; 6 rows will be rejected.**

The error report shall contain:
- File.
- Sheet.
- Row.
- Column.
- Error type.
- Error message.
- Original value.

---

# 45. Batch Processing

Large uploads shall be processed asynchronously.

The browser shall not wait for the entire operation to complete.

The UI shall display:
- Files processed.
- Files remaining.
- Records processed.
- Errors.
- Current status.

The user may navigate away and return to the batch history.

---

# 46. Data Lineage

Every important governance record shall have lineage to its source.

For example:

**Finding F-1023**
→ extracted from Validation Report
→ uploaded in Batch B-20260930-001
→ file `M-0012/Validation/Validation_Report.pdf`
→ uploaded by user U-014
→ extracted by AI
→ confirmed by U-003
→ created on 30-Sep-2026.

This lineage shall be accessible from the record.

---

# 47. Import History

Import Center shall show:

- Batch ID.
- Date.
- User.
- Type.
- Files.
- Records.
- Status.
- Errors.
- Warnings.

Clicking a batch opens:
- Files.
- Rows.
- Errors.
- Changes.
- Audit events.

---

# 48. Data Model — Extended

The existing 16-table design shall be extended.

Core existing tables:

- policy_setting
- app_user
- model
- tiering_answer
- validation
- finding
- approval
- document
- cde
- dq_rule
- dq_result
- dq_issue
- kpi
- kpi_result
- performance_point
- audit_event

Additional tables recommended:

### monitoring_plan
- monitoring_plan_id
- model_id
- model_version
- effective_from
- effective_to
- owner_id
- reviewer_id
- frequency
- methodology
- status
- approval_id

### monitoring_metric
- metric_id
- monitoring_plan_id
- metric_name
- metric_category
- direction
- threshold
- warning_threshold
- breach_threshold
- unit
- frequency
- active
- effective_from
- effective_to

### monitoring_run
- monitoring_run_id
- model_id
- monitoring_plan_id
- model_version
- monitoring_type
- period
- data_period
- run_date
- status
- overall_result
- reviewer_id
- signoff_date

### monitoring_result
- monitoring_result_id
- monitoring_run_id
- metric_id
- actual_value
- expected_value
- previous_value
- change_pct
- threshold_applied
- warning_threshold_applied
- breach_threshold_applied
- direction_applied
- status
- commentary

The thresholds in force on the run date are copied onto each result when it is evaluated, so a later
threshold change never alters a historical outcome (§16, MON-05, Principle 5).

### monitoring_breach
- breach_id
- monitoring_result_id
- severity
- detected_date
- owner_id
- due_date
- status
- root_cause
- impact
- management_response
- resolution

### monitoring_evidence
- monitoring_run_id
- document_id

### document_folder
- folder_id
- parent_folder_id
- folder_name
- relative_path
- model_id

### document_version
- document_id
- version
- checksum
- storage_path
- uploaded_by
- uploaded_at
- change_reason

### import_batch
- batch_id
- batch_type
- uploaded_by
- started_at
- completed_at
- status
- total_files
- successful_files
- failed_files

### import_file
- import_file_id
- batch_id
- file_name
- relative_path
- checksum
- file_type
- status
- error_count
- warning_count

### document_extraction
- extraction_id
- document_id
- document_version_id
- extraction_type
- provider
- model_used
- prompt_version
- status
- extracted_json
- confidence
- created_at
- reviewed_by
- reviewed_at

### model — columns added by §12A
- inventory_class
- classification_reason
- exposure_amount
- exposure_currency
- exposure_basis
- tier_rationale
- frequency_deviation_reason
- is_vendor
- vendor_name
- vendor_product
- vendor_version
- vendor_customisation

### model_dependency
Extends the REQ-INV-05 relationship store; if relationships already live in one table, add the
dependency type there rather than a second table.
- model_id
- depends_on_model_id
- dependency_type
- shared_component
- note

### effective_challenge
- challenge_id
- validation_id
- model_id
- raised_by
- raised_to
- raised_date
- due_date
- topic
- challenge
- response
- response_date
- resolution
- finding_id

### model_limitation
- record_id
- model_id
- record_type (Limitation, Overlay, Use exception)
- description
- amount
- rationale
- approver_id
- approval_date
- effective_from
- expiry_date
- status

### document_link
Generic many-to-many association between documents and:
- models
- validations
- findings
- approvals
- monitoring runs
- monitoring results
- DQ issues.

---

# 49. Database Requirements

PostgreSQL shall be the system of record.

Requirements:
- Referential integrity.
- Foreign keys.
- Unique constraints.
- Transactional writes.
- Database migrations.
- Soft delete where appropriate.
- Created/updated timestamps.
- Optimistic concurrency for material records.
- Indexes on model ID, status, lifecycle phase, tier, dates and monitoring periods.
- Full audit history.

Optional:
- pgvector for semantic document search.
- PostgreSQL full-text search for document metadata/content.

---

# 50. Document Storage

Use an S3-compatible object store.

Preferred open-source option:

**MinIO**

Object storage shall not store governance metadata as the only source of truth.

PostgreSQL stores metadata.

Object storage stores binary content.

Example:

```
bucket/
  models/
    M-0012/
      governance/
      validation/
      monitoring/
        2026/
          Q1/
          Q2/
```

The logical folder hierarchy shall also be represented in PostgreSQL.

---

# 51. Application Architecture

Recommended architecture:

```text
React + TypeScript
        |
        | REST / JSON
        v
Python FastAPI
        |
        +--------------------+
        |                    |
        v                    v
 PostgreSQL              Redis
        |                    |
        |                    v
        |                 Celery/RQ
        |                    |
        |             Background jobs
        |                    |
        v                    v
    MinIO <------------ Document processor
        |
        v
 PDF/DOCX/XLSX extraction
        |
        v
 AI extraction service
```

---

# 52. Frontend

Recommended:

- React.
- TypeScript.
- Vite or equivalent.
- React Router.
- TanStack Query.
- Recharts.
- Component library such as MUI or shadcn/ui. *(Not adopted: the build uses the single stylesheet
  `src/styles/app.css`, see Part 0.)*

The existing HTML prototype's visual language shall be preserved:

- Dark-first theme.
- Flat cards.
- Thin borders.
- No unnecessary drop shadows.
- Compact enterprise dashboard.
- Clear status pills.
- Dense data tables.
- Strong filtering and drill-down.

The existing prototype should be treated as the visual reference, not as the application architecture.

---

# 53. Backend

Recommended:

- Python 3.14 (the version CI uses; local setup must match).
- FastAPI.
- SQLAlchemy.
- Alembic.
- Pydantic.
- Pandas/OpenPyXL for structured ingestion.
- PyMuPDF/pdfplumber for PDF processing.
- python-docx for DOCX.
- Celery or RQ for asynchronous jobs.
- Redis for job state/caching where required.

---

# 54. API Requirements

API groups:

```text
/api/auth
/api/users
/api/models
/api/validations
/api/findings
/api/approvals
/api/documents
/api/folders
/api/imports
/api/monitoring/plans
/api/monitoring/metrics
/api/monitoring/runs
/api/monitoring/results
/api/monitoring/breaches
/api/cde
/api/dq
/api/dashboard
/api/copilot
/api/audit
/api/admin
```

All write APIs shall:
1. Validate authorization.
2. Validate payload.
3. Execute business rules.
4. Write transactionally.
5. Generate audit event.
6. Return the persisted record.

---

# 55. Screens

## 55.1 Command Center
Portfolio view:
- Total models.
- Models by tier.
- Models by lifecycle.
- Models requiring revalidation.
- Open findings.
- Monitoring breaches.
- Monitoring completion.
- DQ health.
- Portfolio governance score.
- Aggregate model risk (§12A REQ-REG-09).

## 55.2 Operations Board
Filters:
- Model type.
- Tier.
- Phase.
- Business line.
- Monitoring status.
- Revalidation status.
- Findings.
- Search.

## 55.3 Model 360
Sections:
- Profile.
- Lifecycle.
- Risk tier.
- Owners.
- Validation.
- Findings.
- Approvals.
- Documents.
- Monitoring.
- CDE/DQ.
- Governance score.
- Audit history.
- Classification, exposure and vendor details (§12A).
- Limitations, overlays and use exceptions.
- Effective challenges.
- Dependencies: upstream and downstream models, "Upstream issue", "Used by AI system".

## 55.4 Monitoring Dashboard
Dedicated monitoring portfolio view.

## 55.5 Data Audit
- CDE registry.
- DQ rules.
- DQ results.
- DQ issues.

## 55.6 Document Centre
Features:
- Folder tree.
- Document list.
- Upload.
- Batch upload.
- Folder upload.
- ZIP upload.
- Search.
- Filter.
- Preview.
- Download.
- Version history.
- Extraction queue.
- Review queue.

## 55.7 Import Centre
Features:
- Template list.
- Blank template download.
- Upload.
- Batch upload.
- Preview.
- Validation.
- Load.
- Error report.
- Import history.

## 55.8 Admin
- Policy settings.
- Required documents.
- Monitoring thresholds.
- Monitoring frequencies.
- Severity rules.
- Roles.
- Users.
- Document types.
- System configuration.

## 55.9 Audit Trail
Filter by:
- User.
- Model.
- Entity.
- Action.
- Date.
- Batch.
- Document.

## 55.10 Model Risk Report
Generate, preview and download the §12A REQ-REG-10 report for a business date; list earlier reports.

---

# 56. Command Center Insights

Insights shall be generated from rules and current data.

Examples:
- High-tier model overdue for revalidation.
- Critical finding overdue.
- Validator independence breach.
- Missing required documentation.
- KPI failure.
- Repeated KPI failure.
- Critical DQ issue.
- Monitoring run overdue.
- Critical monitoring breach.
- Monitoring evidence missing.
- Repeated monitoring breach.
- Significant performance deterioration.
- Model in use with a Rejected outcome or overdue revalidation and no use exception (§12A).
- Overlay or use exception expired.
- Effective challenge overdue.
- Upstream model issue affecting dependent models.
- Vendor model without recent outcomes analysis.
- Revalidation frequency longer than the tier default.

Insights shall contain:
- Severity.
- Message.
- Model ID.
- Source record.
- Date.
- Link to relevant screen.

---

# 57. Governance Score

The existing score shall be retained as the initial baseline.

Components:
- Documentation.
- Validation currency.
- Issue remediation.
- MRC compliance.
- Monitoring.

Initial weights:
- Documentation 25%.
- Validation currency 25%.
- Issue remediation 20%.
- MRC compliance 15%.
- Monitoring 15%.

Weights shall be configurable.

The score must be explainable.

For every score the system shall display:
- Overall score.
- Component score.
- Weight.
- Calculation inputs.
- Missing information.
- Last recalculation time.

---

# 58. Audit Trail

Every material write shall create an audit event.

Events include:
- Create.
- Update.
- Delete/retire.
- Import.
- Upload.
- Extraction.
- Confirmation.
- Rejection.
- Approval.
- Tier override.
- Threshold change.
- Monitoring result confirmation.
- Breach creation.
- Breach closure.
- Document version creation.

Audit records must be immutable to normal application users.

---

# 59. Security and Access Control

The production version shall support authentication.

Recommended:
- OAuth2/OIDC.
- Enterprise identity provider.
- JWT/session-based authorization.

Authorization must be enforced server-side.

UI hiding alone is insufficient.

Examples:
- Auditor cannot modify.
- Executive cannot upload.
- Model Owner can modify assigned models.
- Validator can update assigned validation records.
- Admin can configure policies.
- Monitoring Analyst can manage monitoring records.

---

# 60. AI Governance

AI functionality shall be treated as an assistive service.

AI shall:
- Extract.
- Classify.
- Summarize.
- Search.
- Answer questions from governed data.

AI shall not:
- Approve models.
- Close findings.
- Change risk tier.
- Change monitoring thresholds.
- Change lifecycle phase.
- Delete evidence.
- Make governance decisions.

All AI-generated content that becomes governance data requires human confirmation unless explicitly configured otherwise.

The system shall record:
- AI provider.
- Model.
- Prompt/version identifier.
- Timestamp.
- Input document.
- Output.
- Reviewer.
- Confirmation status.

---

# 61. Audit Copilot

The Copilot shall remain read-only.

Suggested questions:

- Which high-risk models are overdue for revalidation?
- Which models have critical findings?
- Which monitoring KPIs failed this quarter?
- Which models have repeated monitoring breaches?
- Which CDEs are failing?
- Which models are missing required documentation?
- Why did model M-0012's governance score change?
- Show the monitoring history for M-0012.
- What evidence supports the latest monitoring result?

Every answer shall identify the relevant model IDs and underlying records.

---

# 62. Search

The application shall provide global search across:

- Model ID.
- Model name.
- Document name.
- Finding.
- Validation.
- Approval.
- Monitoring run.
- KPI.
- CDE.
- DQ issue.

Optional phase:
- Full-text document search.
- Semantic document search using pgvector.

---

# 63. Notifications

Recommended later capability:

- Monitoring breach.
- Monitoring due.
- Revalidation due.
- Finding overdue.
- Document review pending.
- Approval condition due.

Notification channels can later include:
- In-app.
- Email.
- Teams/Slack.

The notification engine should be decoupled from the rules engine.

---

# 64. Non-Functional Requirements

## Performance
- Dashboard load target: <2 seconds for normal portfolio queries.
- Model 360: <2 seconds excluding document/AI processing.
- Large upload processing shall be asynchronous.
- UI must remain responsive during background ingestion.

## Scalability
Initial target:
- 5,000 models.
- 100,000 documents.
- 1 million monitoring results.
- 10 million audit events.

The architecture should allow horizontal scaling of workers.

## Availability
Production deployment should support:
- Application health checks.
- Database health checks.
- Worker health checks.
- Object storage health checks.

## Reliability
- Failed background jobs shall be retryable.
- Processing shall be idempotent.
- Partial batch failures shall not corrupt successful records.
- Database writes shall be transactional.

## Security
- Encryption in transit.
- Encryption at rest where supported.
- Role-based access.
- Server-side authorization.
- No secrets in frontend.
- File malware scanning recommended before production.
- ZIP path traversal protection.

---

# 65. File Validation and Security

Every uploaded file shall be checked for:

- Extension.
- MIME type.
- File size.
- File signature.
- Malware status where scanner is available.
- ZIP archive safety.
- Maximum file count.
- Maximum decompressed size.
- Path traversal.
- Duplicate checksum.

Default maximum:
- Individual document: 10 MB.
- Configurable at system level.
- ZIP maximum configurable separately.

---

# 66. Error Handling

Errors shall be human-readable.

Examples:

**Invalid model ID**
> Model M-9999 does not exist.

**Duplicate**
> Document already exists with SHA-256 checksum XXXXX.

**SoD**
> Validator U-014 cannot validate model M-0012 because U-014 is also the model owner.

**Monitoring**
> KPI K-0012-01 failed: actual value 0.58 is below breach threshold 0.6175.

**Document**
> Extraction failed validation. No governance record was created.

---

# 67. Auditability and Lineage Requirements

The system shall answer:

- Who uploaded this?
- Where did it come from?
- Which batch contained it?
- Which folder was it uploaded from?
- Which model is it linked to?
- Which version is it?
- Was AI used?
- Who confirmed the AI extraction?
- Which monitoring run produced this breach?
- Which policy threshold was used?
- What was the previous value?
- What changed?

---

# 68. Data Retention

Retention policies shall be configurable.

Documents and audit records shall support:
- Retention start date.
- Retention end date.
- Legal hold flag.
- Archived flag.

Deletion shall be controlled and audited.

---

# 69. Configuration

The following shall be configuration-driven:

- Risk tier thresholds.
- Governance score weights.
- Revalidation lead time.
- Revalidation frequencies.
- Required documents.
- Monitoring frequencies.
- KPI thresholds.
- DQ thresholds.
- Breach severity rules.
- Repeated-breach rules.
- File-size limits.
- Allowed document types.
- Roles.
- Lifecycle phases.

Business rules must not be duplicated throughout frontend components.

---

# 70. Seed and Demo Data

The existing design contains 256 synthetic models and defined seed targets.

The seed generator shall remain deterministic.

Seed data shall be created through the same ingestion/business-service path used by the application where practical.

The reset function shall:
1. Clear/reset application data.
2. Recreate configuration.
3. Load users.
4. Load models.
5. Load governance history.
6. Load CDE/DQ.
7. Load monitoring definitions/results.
8. Load documents/evidence metadata.
9. Recalculate derived fields.

---

# 71. Initial Template Framework

Existing templates shall remain supported:

- T01 Users.
- T02 Model Inventory.
- T03 Validation History.
- T04 Findings.
- T05 Approvals.
- T06 CDE/DQ Rules.
- T07 KPI Definitions.
- T08 KPI Results.
- T09 Performance Curves.
- T10 DQ Results.
- T11 Documents.
- T12 Policy Settings.

New recommended templates:

### T13 Monitoring Plan
### T14 Monitoring Metrics
### T15 Monitoring Results
### T16 Monitoring Breaches
### T17 Document Manifest
### T18 Folder/Package Manifest

Templates added by §12A (column lists in §12A.3):

### T19 Effective Challenge
### T20 Limitations, Overlays and Exceptions
### T21 Model Dependencies

The template registry shall remain the single source of truth for validation and blank template generation.

---

# 72. New Monitoring Templates

## T13 Monitoring Plan

Columns:
- monitoring_plan_id
- model_id
- model_version
- effective_from
- frequency
- owner_id
- reviewer_id
- methodology
- status

## T14 Monitoring Metrics

Columns:
- metric_id
- monitoring_plan_id
- metric_name
- metric_category
- direction
- threshold
- warning_threshold
- breach_threshold
- unit
- frequency
- active
- effective_from

## T15 Monitoring Results

Columns:
- monitoring_run_id
- model_id
- model_version
- metric_id
- period
- run_date
- actual_value
- expected_value
- status
- commentary

`status` is optional and accepts only `Not Applicable`. Pass, Warn, Fail and Not Available are always
calculated by the system against the metric threshold in force on `run_date` (MON-01, MON-05); a file that
supplies any other status has that row rejected.

## T16 Monitoring Breaches

Columns:
- breach_id
- monitoring_run_id
- metric_id
- severity
- detected_date
- owner_id
- due_date
- status
- root_cause
- impact
- management_response

## T17 Document Manifest

Columns:
- relative_path
- model_id
- document_type
- version
- effective_date

## T18 Folder Manifest

Columns:
- relative_path
- model_id
- folder_type
- description

---

# 73. User Journey — Individual Upload

```text
User opens Model 360
        |
Documents
        |
Upload Document
        |
Select file
        |
Select document type
        |
Select version
        |
Upload
        |
Validation
        |
AI extraction (if applicable)
        |
Review
        |
Confirm
        |
Database + object storage
        |
Audit event
```

---

# 74. User Journey — Batch Upload

```text
User opens Document Centre
        |
Batch Upload
        |
Select multiple files
        |
System validates files
        |
System calculates checksums
        |
System identifies models/types
        |
User reviews mapping
        |
Confirm Batch
        |
Background processing
        |
Extraction
        |
Review Queue
        |
Confirmation
        |
Database
        |
Audit Trail
```

---

# 75. User Journey — Folder Upload

```text
Select Folder
      |
Scan folder tree
      |
Display file hierarchy
      |
Identify model folders
      |
Identify document types
      |
User confirms mappings
      |
Create Import Batch
      |
Upload files
      |
Process asynchronously
      |
Create folders
      |
Create documents
      |
AI extraction
      |
Review
      |
Confirm
```

---

# 76. User Journey — Monitoring

```text
Monitoring Plan
      |
Monitoring Run
      |
Load Results
      |
Evaluate Thresholds
      |
Pass / Warn / Fail
      |
Create Breach where required
      |
Assess Impact
      |
Create/Link Finding if required
      |
Reviewer Sign-off
      |
Monitoring Dashboard
      |
Governance Score
```

---

# 76A. Acceptance Criteria — Governance Core

Ported from the test conditions in `C_Requirements/_OLD/design.md` §12, which covered the governance
core in detail but was superseded by this BRD before §77–§79 were written. Without these, the BRD's
acceptance criteria covered only Monitoring, Documents and Structured import — that is, three areas of
which only two are built.

This section is numbered **76A** deliberately: code comments throughout `A_Codes/AB_backend` cite
sections by number (`BRD §44`, `§50`, `§57`, `§59`, `§71`), so the existing numbering must not shift.
Later acceptance-criteria sets should follow the same convention (76B, 76C, …) rather than renumber.

Each criterion carries a stable ID. Automated tests name the IDs they verify, so
`grep -r "INV-03" A_Codes/AB_backend/tests` answers "what proves this?".

## 76A.1 Model inventory (INV)

### INV-01
Model registration refuses a missing mandatory field (§6.1) and names the field.

### INV-02
Every model edit writes an audit event carrying user, role, timestamp, entity, entity ID, before value
and after value.

### INV-03
A validator who is also the model owner or the model developer is refused — on manual creation, on
manual editing and on structured import.

### INV-04
An owner, developer or validator reference that does not exist is refused, naming the user ID.

### INV-05
Mandatory data for the target lifecycle phase is enforced on creation and on editing.

### INV-06
A concurrent edit of the same model is refused as a conflict; the later write never silently overwrites.

### INV-07
Model version is tracked independently of model ID.

### INV-08
A successor relationship is visible from both models; a successor on a model not in Retirement is refused.

### INV-09
A legacy segregation-of-duties exception loaded through the import flag remains visible on the model and
as a governance insight.

## 76A.2 Risk tiering (TIR)

### TIR-01
Tier score equals the sum of the four tiering answers, and the High/Medium/Low band comes from policy,
never from code.

### TIR-02
A tiering answer outside 1–3 is refused.

### TIR-03
Changing `tier_high_min` or `tier_medium_min` re-derives every model's calculated tier; a threshold
combination that is not `4 < medium < high ≤ 12` is refused.

### TIR-04
A tier override requires a reason and an authorised role; an override by an unauthorised role is refused.

### TIR-05
Applying an override retains the calculated tier alongside it and never deletes it.

## 76A.3 Lifecycle (LIF)

### LIF-01
A phase transition records previous phase, new phase, transition date, the user and any reason given.

### LIF-02
The displayed pipeline column equals the lifecycle phase, except that a model in Monitoring whose next
due date falls within the configured lead time, or is past, is shown in Revalidation.

## 76A.4 Validation and revalidation (VAL)

### VAL-01
A validation whose completion date precedes its start date is refused.

### VAL-02
Next validation date equals last validation date plus the configured frequency, with month-end dates
clamped to the last day of the target month.

### VAL-03
A model with no last validation date has no due date and does not appear in the revalidation queue.

### VAL-04
Models are classified Scheduled, Due Soon or Overdue using the configured lead time and due-soon window.

### VAL-05
Validator independence is enforced when a validation is recorded, not only when the model is edited.

### VAL-06
Recording a validation updates the model's validation currency and its next due date.

## 76A.5 Findings and remediation (FND)

### FND-01
A finding with status Closed and no closed date is refused.

### FND-02
Days open, days overdue and overdue status are calculated from the raised date, due date and business date.

### FND-03
An invalid severity or status is refused and the message lists the allowed values.

### FND-04
Closing a finding writes an audit event and removes it from the overdue work queue.

## 76A.6 Approvals and MRC decisions (APR)

### APR-01
A Conditional decision with no conditions recorded is refused.

### APR-02
Only a role holding the approval permission may record a decision.

### APR-03
A Conditional decision stays visible as outstanding until every condition is closed.

### APR-04
Decisions for a model are listed newest first.

## 76A.7 Governance score (SCR)

### SCR-01
Every component score and the overall score match an independent hand calculation to one decimal place.

### SCR-02
A component that is not applicable is dropped and the remaining weights are rescaled to 100%.

### SCR-03
The issue-remediation component floors at zero and never goes negative.

### SCR-04
Changing a component weight in policy changes the model and portfolio scores accordingly.

### SCR-05
The score is explainable: each component shows its weight, effective weight, calculation inputs,
explanation and any missing information.

### SCR-06
A model with no applicable component has no score and states the reason instead of showing zero.

## 76A.8 Configuration (CFG)

### CFG-01
Every configurable value is read from `policy_setting`; a value of the wrong type is refused with a
human-readable message.

### CFG-02
A policy change takes effect on the next read without restarting the application.

### CFG-03
A policy edit writes an audit event with before and after values, and a stale edit is refused as a conflict.

### CFG-04
An unknown policy key returns not-found rather than creating a setting.

## 76A.9 Roles and access control (SEC)

### SEC-01
Every role has a defined permission set, and an unknown role has no permissions.

### SEC-02
Auditor and Executive hold no write permission; a direct API write by either is refused and nothing is saved.

### SEC-03
A Model Owner may edit only the models assigned to them; editing another owner's model is refused.

### SEC-04
Signing in with a role the user does not hold is refused.

### SEC-05
Deactivating a user, or removing their role, invalidates an already-issued token on its next use.

### SEC-06
A missing or malformed token is refused as unauthenticated.

## 76A.10 Audit trail (AUD)

### AUD-01
Every material write creates an audit event in the same transaction as the business change, so the two
commit or roll back together.

### AUD-02
No application route updates or deletes an audit event, and the database enforces append-only.

### AUD-03
The audit trail filters by user, model, entity, action, date, import batch and document.

### AUD-04
Audit access is restricted to roles holding the audit-read permission.

## 76A.11 Command Center and insights (CC)

### CC-01
Every tile equals the count returned by its own drill-down list.

### CC-02
Distribution charts sum to the portfolio total and percentages sum to 100 ± 1.

### CC-03
The revalidation timeline contains exactly the models in the Revalidation column.

### CC-04
Insights are generated from current data, and resolving the underlying cause removes the insight.

## 76A.12 Seed and reset (GEN)

### GEN-01
Reset to seed is deterministic: the same business date reproduces the same row counts and the documented
portfolio distribution.

### GEN-02
Reset is refused for a role without the required permission.

### GEN-03
The demo files with deliberate errors produce the documented valid/rejected split.

## 76A.13 Traceability to the superseded conditions

| New ID | Superseded condition (`design.md` §12) |
|---|---|
| INV-01, INV-05 | TC-INV-01-1, TC-INV-02-1 |
| INV-02 | TC-INV-02-2 |
| INV-03 | TC-INV-03-1, TC-INV-03-2 |
| INV-08 | TC-INV-05-1, TC-INV-05-2 |
| TIR-01, TIR-02 | TC-TIR-01-1, TC-TIR-01-2, TC-TIR-01-3 |
| TIR-04, TIR-05 | TC-TIR-02-1, TC-TIR-02-2, TC-TIR-02-3 |
| LIF-02 | TC-OPS-01-1 |
| VAL-01 | TC-HIS-01-1, TC-HIS-01-2 |
| VAL-02, VAL-03 | TC-INV-04-1, TC-INV-04-2 |
| FND-01 | TC-HIS-02-1, TC-HIS-02-2 |
| APR-01 | TC-HIS-03-1, TC-HIS-03-2 |
| SCR-01, SCR-02, SCR-03 | TC-SCR-01-1, TC-SCR-01-2, TC-SCR-01-3 |
| SCR-04 | TC-CFG-02-1 |
| CFG-01 | TC-CFG-01-1, TC-CFG-01-3 |
| CFG-02 | TC-CFG-02-2 |
| SEC-01, SEC-04 | TC-USR-01-1, TC-USR-01-2, TC-USR-02-1 |
| SEC-02, SEC-03 | TC-USR-03-1, TC-USR-03-2, TC-USR-03-3 |
| AUD-01, AUD-02 | TC-AUD-01-1, TC-AUD-01-2 |
| CC-01, CC-02, CC-03 | TC-CC-01-1, TC-CC-02-1, TC-CC-02-2 |
| CC-04 | TC-CC-04-1, TC-CC-04-2 |
| GEN-01, GEN-02 | TC-GEN-01-1, TC-GEN-01-2 |
| GEN-03 | TC-GEN-02-1 |

Conditions in `design.md` §12 for capabilities that are not yet built — `TC-CDE-*`, `TC-KPI-*`,
`TC-DA-*`, `TC-COP-*`, `TC-M360-*` (E2E), `TC-OPS-02/03`, `TC-NFR-*` — are deliberately **not** ported
here. They belong with Phases 6, 7 and 9 and should be written as MON-, DQ- and COP- criteria when those
phases are specified.

## 76A.14 Known coverage gaps

A criterion ID appears in a test file only where a test actually verifies it, so
`grep -rn "<ID>" A_Codes/AB_backend/tests` is a true coverage signal. Gaps are recorded here rather
than in the test files, so that grep is never polluted by a mention of something not covered. The one
current exception is the range `GEN-01..GEN-03` in the `test_imports.py` module docstring, which makes
`grep GEN-03` a false positive — see "Tagging and spec gaps" below.

**Referenced is not proven.** The earlier figure in this section counted criteria *mentioned* by a
test. What matters is whether the test asserts the criterion's expected result, which is a different
and smaller number.

Coverage at 2026-10-02 (`test-outcome-reviewer`): **69 of 112** criteria (§76A, §76D, §77, §78, §79)
are *proven* — 69 of 85 once the 12 unbuilt monitoring criteria (§77), the 14 unbuilt regulatory
criteria (§76D) and DOC-16 (Phase 5) are excluded. A further 13 have a test that passes without
asserting the whole expected result, and 3 have no test at all.

### Not proven — no test

| Criterion | Gap | Reason |
|---|---|---|
| INV-07 | Model version tracked independently of model ID | `model_version` rows are created and asserted incidentally (`versions[0]`), but no test drives two versions of one model ID. |
| AUD-03 | Audit trail filters by user, model, entity, action, date, batch, document | Individual filters are used throughout the suite to *find* events; none asserts the filter contract itself, and the date range is never exercised. |
| DOC-11 | A user can see batch progress | The progress store (`app/workers/runner.ProgressStore`) has no test. |

### Partly proven — a test exists but misses part of the expected result

| Criterion | What is proven | What is missing |
|---|---|---|
| INV-01 | A valid registration succeeds | No refusal of a missing mandatory field, and no assertion that the field is named. |
| INV-02 | A create is audited; an *import* update records before/after | No audit assertion on a manual `PUT /api/models/{id}` — user, role, timestamp, before and after. |
| INV-03 | SoD refused on create and on import | Not exercised on manual edit, which the criterion names. |
| INV-06 | The stale write returns 409 | Not re-read to show the stale write did not take effect. |
| LIF-01 | `to_phase` on the create event | `from_phase`, transition date, acting user and reason are asserted nowhere; the test carrying the ID ends in a 422. |
| VAL-03 | No last validation date gives no due date | The model is not shown to be absent from the revalidation queue. |
| VAL-06 | `last_validation_date` is updated | The recalculated next due date is not re-read. |
| APR-03 | `condition_status` round-trips through a PATCH | The decision is never observed as outstanding while the condition is open, nor leaving that state when it closes. |
| APR-04 | Three approvals are returned and the first is Pre-implementation | No comparison of `decision_date`, so the ordering itself is unasserted. |
| SCR-05 | `score`, `missing` and `explanation` on the API response | `weight`, `effective_weight`, `inputs` and `calculated_at` are never asserted on a response. |
| SEC-05 | Deactivation invalidates an issued token | Role removal — the criterion's other half, and a different check — is untested. |
| AUD-01 | Seven writes are shown to produce the right audit event | The transactional coupling: no test shows a refused write leaves no audit event, or that a failed audit rolls the business change back. |
| GEN-01 | One reset matches the documented portfolio figures; the committed seed's policy covers the baseline and leaves the dashboard working (added 2026-10-03) | Determinism itself: no second reset at the same business date is compared with the first. |
| DOC-09 | A batch ID is issued in the documented format | Uniqueness across two batches. |

### Correctly open — the capability does not exist yet

| Criterion | Reason |
|---|---|
| DOC-16 | AI extraction cannot persist without confirmation — Phase 5; not yet built. |
| MON-01…MON-12 | All monitoring criteria — Phase 6; not yet built. |
| REG-01…REG-14 | All regulatory alignment criteria — Phase 2A; not yet built. |

### Tagging and spec gaps

- **GEN-03** is substantively proven by `test_tc_imp_03_1_preview_then_partial_load` and
  `test_row_level_errors_by_type`, but neither names the ID; the grep hit comes from the module
  docstring range. Tag the two tests. The "documented" valid/rejected split is also not documented
  anywhere — record it.
- **IMP-01** ("multiple CSV/XLSX files") is tagged on a single-file test; the multi-file proof is on
  `test_cross_file_dependencies_in_one_batch`, tagged IMP-06. Move or add the tag.
- **BRD §65** (file validation and security) has no acceptance criteria, yet five tests cover it
  (`test_file_validation`, `test_oversized_document_rejected`, `test_path_traversal_rejected`, and the
  traversal and zip-bomb halves of `test_doc_05_zip_upload_and_safety`). That work is invisible to every
  coverage count. Add a criteria set (76E) and tag them.
- **Migrations and schema drift** (`test_postgres.py`) likewise map to no criterion.

The three untested criteria and the thirteen partly proven ones are real gaps in built functionality
and should be closed before Phase 6 adds more surface area; AUD-01, APR-03, APR-04 and SEC-05 first.

The `test-outcome-reviewer` agent recalculates this table on every run and proposes replacement text in its
report. Update this section from that report rather than by hand.

---

# 76D. Acceptance Criteria — Regulatory Alignment (REG)

Criteria for §12A. Numbered 76D because 76B (Data Audit, D8) and 76C (Copilot, D11) are reserved.

### REG-01
Saving a Tool or AI system record without `classification_reason` is refused with a message naming the
field; nothing is saved and no audit event is written.

### REG-02
Tool and AI system records are excluded from model counts, tiering, revalidation, the governance score
and the Operations Board, and appear when the class filter selects them.

### REG-03
Changing `inventory_class` writes one audit event with before value, after value and reason. A user
without `REG_CLASSIFY` is refused by the API (403) and nothing is saved.

### REG-04
A model linked to an AI system keeps its tier, validation and score; its Model 360 shows "Used by AI
system", and the AI system's record lists the model.

### REG-05
A High tier or a tier override without `tier_rationale` is refused. With an exposure amount, the
suggested Materiality answer follows `materiality_exposure_bands`, and the saved answer is the user's.

### REG-06
A new model's revalidation frequency defaults from `reval_frequency_by_tier`. A longer frequency without
`frequency_deviation_reason` is refused. Changing the policy leaves existing models' frequencies unchanged
and lists the models now longer than the default.

### REG-07
A vendor model without vendor name or product is refused. Documents in `vendor_required_documents` count
towards completeness for vendor models only. A vendor model in Monitoring with no outcomes-analysis or
backtest run within `vendor_outcomes_max_age_days` raises an insight (needs Phase 6).

### REG-08
A challenge resolved as "Finding raised" creates the linked finding in the same transaction; if the
finding fails validation, neither is saved. A challenge raised by the model's owner or developer is
refused. An open challenge past its due date raises an insight.

### REG-09
An overlay or use exception without rationale, approver, approval date or expiry is refused; an approver
who is the model's owner or developer, or lacks `OVERLAY_APPROVE`, is refused. After the expiry date
(by `app.clock.today()`) the record shows as expired and raises an insight.

### REG-10
A model in Implementation or Monitoring whose latest outcome is Rejected, or whose revalidation is
Overdue, raises a Critical insight unless it has an active use exception; adding the exception clears
the insight.

### REG-11
A self-dependency and a dependency that would create a cycle are refused. When an upstream model has an
open Critical finding, a Critical breach, a Rejected latest outcome or an overdue revalidation, each
downstream model shows "Upstream issue" and an insight is raised; resolving the upstream issue clears
both.

### REG-12
Each aggregate figure on the Command Center (REQ-REG-09) drills down to its models, and the count equals
the number of models listed and the matching Operations Board filter.

### REG-13
The model risk report for a business date contains every REQ-REG-10 section, its figures equal the
Command Center for that date, generating it twice from the same data gives the same content, and each
generation writes an audit event.

### REG-14
T19–T21 rows load through the same service path as the UI; an unknown model, validation or finding
reference rejects the row with a message naming the field and the row. T02 files without the §12A columns
load unchanged. The Auditor role can read all §12A records and download the report and evidence package,
and every Auditor write is refused by the API.

---

# 77. Acceptance Criteria — Monitoring

### MON-01
Given a KPI threshold, the system calculates Pass/Warn/Fail correctly.

### MON-02
A failed critical KPI creates a monitoring breach.

### MON-03
A monitoring breach is linked to its monitoring run and model.

### MON-04
A monitoring run cannot be marked complete without required metrics.

### MON-05
Historical monitoring results remain unchanged when thresholds are subsequently changed.

### MON-06
A user can view at least four historical monitoring periods.

### MON-07
A user can drill from a chart point to the monitoring result.

### MON-08
Repeated KPI failures generate a governance insight.

### MON-09
A monitoring breach may be converted into a formal finding only through an authorised user action.

### MON-10
Monitoring evidence can be attached to the run.

### MON-11
The monitoring dashboard correctly aggregates Pass/Warn/Fail.

### MON-12
The governance score changes when the monitoring component changes.

---

# 78. Acceptance Criteria — Document and Folder Upload

### DOC-01
A user can upload a single PDF.

### DOC-02
A user can upload a single DOCX.

### DOC-03
A user can upload multiple files simultaneously.

### DOC-04
A user can upload a folder.

### DOC-05
A user can upload a ZIP package.

### DOC-06
Nested folder structure is preserved.

### DOC-07
Every file receives a checksum.

### DOC-08
Exact duplicate files are detected.

### DOC-09
A batch has a unique batch ID.

### DOC-10
A failed file does not cause valid files in the same batch to be lost.

### DOC-11
A user can see batch progress.

### DOC-12
A user can download a batch error report.

### DOC-13
A document can be mapped to a model.

### DOC-14
The system can suggest document type.

### DOC-15
The user can override document classification.

### DOC-16
AI extraction cannot persist governance changes without confirmation.

### DOC-17
Document versions remain accessible.

### DOC-18
The folder path is retained.

### DOC-19
Document lineage is visible.

### DOC-20
Document completeness is recalculated after confirmation.

---

# 79. Acceptance Criteria — Structured Batch Import

### IMP-01
User can upload multiple CSV/XLSX files.

### IMP-02
Each file is mapped to a template.

### IMP-03
Invalid files are isolated.

### IMP-04
Valid files continue processing.

### IMP-05
Row-level errors are recorded.

### IMP-06
Foreign-key dependencies are checked.

### IMP-07
Duplicate records are handled according to configured upsert rules.

### IMP-08
All changes are audited.

### IMP-09
Batch history remains available.

---

# 80. Test Strategy

Three levels:

## Unit tests
Business rules:
- Tiering.
- Revalidation.
- KPI status.
- DQ status.
- Governance score.
- Monitoring thresholds.
- Breach severity.
- Duplicate detection.
- Document completeness.

## Integration tests
- API.
- Database.
- Object storage.
- Import processing.
- Background jobs.
- AI extraction.

## End-to-end tests
- Model creation.
- Import.
- Document upload.
- Folder upload.
- Monitoring run.
- Breach.
- Finding.
- Dashboard drill-down.

---

# 81. Recommended Development Phases

## Phase 1 — Foundation
- React.
- FastAPI.
- PostgreSQL.
- Authentication framework.
- Base layout.
- Role model.

## Phase 2 — Existing Governance Core
- Model inventory.
- Tiering.
- Validation.
- Findings.
- Approvals.
- Governance score.

## Phase 2A — Regulatory Alignment (SR 26-2)
- Inventory classification (Model / Tool / AI system) and AI-system links.
- Exposure, tier rationale, proportionate revalidation defaults.
- Vendor model fields and required documents.
- Effective challenge log.
- Limitations, overlays and use exceptions.
- Model dependencies and upstream-issue propagation.
- Aggregate model risk view and model risk report.
- Templates T19–T21, T02 columns, seed additions, criteria REG-01 to REG-14.

## Phase 3 — Import Engine
- Excel.
- CSV.
- Validation.
- Preview.
- Batch import.
- Audit.

## Phase 4 — Document Centre
- Individual upload.
- Batch upload.
- Folder upload.
- ZIP.
- Object storage.
- Document metadata.
- Versioning.

## Phase 5 — AI Extraction
- PDF/DOCX extraction.
- Classification.
- Structured extraction.
- Human review.
- Audit.

## Phase 6 — Monitoring
- Monitoring plans.
- Metrics.
- Thresholds.
- Runs.
- Results.
- Breaches.
- Trends.
- Evidence.
- Dashboard.

## Phase 7 — Data Audit
- CDE.
- DQ.
- Issues.

## Phase 8 — Command Center / Model 360
- Dashboards.
- Drill-down.
- Score.

## Phase 9 — Copilot
- Read-only tools.
- RAG/search.
- Model 360 questions.
- Document questions.

## Phase 10 — Hardening
- Security.
- Performance.
- E2E tests.
- Backup/restore.
- Monitoring.
- Deployment.

---

# 81A. Decisions Required Before Phases 5–9

Numbered 81A so no existing section shifts. Claude Code shall not implement an item until its Decision
column is filled in; the proposed default is a starting point for that decision, not an instruction.

| ID | Decision needed | Sections | Proposed default | Needed before | Decision |
|---|---|---|---|---|---|
| D1 | T07/T08 (KPI definitions and results) and T14/T15 (monitoring metrics and results) describe the same data, and §48 keeps both `kpi`/`kpi_result` and `monitoring_metric`/`monitoring_result`. Which is the system of record? | §48, §71, §72 | `monitoring_metric` and `monitoring_result` only. T07 and T08 stay as import aliases that write to them, so older files still load. T09 curves link to `monitoring_run`. `kpi` and `kpi_result` are not created | Phase 6 | — |
| D2 | The "within range" direction (§16) needs a lower and an upper bound, but a metric has one threshold, one warning and one breach value | §16, §48, T14 | Add `range_lower` and `range_upper`, used only when direction is within range | Phase 6 | — |
| D3 | §20 says the system creates a breach when a threshold is violated; T16 also imports breaches. How do the two meet? | §20, T16 | Breaches are created only by the rules. A T16 row must match an existing breach on run and metric and updates its status, root cause and response; an unmatched row is rejected | Phase 6 | — |
| D4 | Backtests (§23) have fields but no table and no template | §23, §48, §71 | A backtest is a `monitoring_run` with `monitoring_type` = Backtest; methodology is recorded on the run; screens filter it separately | Phase 6 | — |
| D5 | Escalation (§21) and repeated-breach (§22) rules must be configurable, but no policy keys are defined, and Part 0 requires a T12 row for every constant | §21, §22, §69 | T12 keys: `breach_severity_rules` (list), `repeat_breach_consecutive` = 2, `repeat_breach_count` = 3, `repeat_breach_window` = 4, `warn_escalation_periods` = 3 | Phase 6 | — |
| D6 | Once monitoring exists, what feeds the Monitoring component of the governance score, and how are Not Available results treated? | §57 | Share of active metrics whose latest result is Pass. Not Applicable is excluded; Not Available is excluded and listed as missing information | Phase 6 | — |
| D7 | §77 has no criteria for escalation rules (§21), repeated breaches (§22), backtest separation (§23), evidence links (§24) or T13–T16 import validation | §21–§24, §77 | Add MON-13 onwards to §77 before coding starts | Phase 6 | — |
| D8 | Data Audit has no acceptance criteria | §55.5, §76A.13 | Write DQ criteria as §76B | Phase 7 | — |
| D9 | The mock-up generates an MRC governance report (download, AI commentary), but no BRD section requires one | §55 | Decide whether it is in scope; if so, add a requirement and criteria | Any | In scope as the model risk report, §12A REQ-REG-10 and REG-13; AI commentary waits for Phase 9 |
| D10 | Finding statuses Accepted Risk, Deferred and Rejected are "additional recommended" in §11 — required or not? | §11, FND-03 | Required, because breaches already use Accepted Risk (§20) and can become findings (MON-09) | Any | — |
| D11 | The Audit Copilot has no acceptance criteria | §61, §76A.13 | Write COP criteria as §76C | Phase 9 | — |

---

# 82. Claude Code Development Instructions

Claude Code shall treat this BRD as the business specification.

Implementation rules:

1. Do not hard-code business numbers in UI components.
2. Store configurable rules in configuration tables.
3. Keep business rules in a dedicated Python service/rules layer.
4. Keep database models separate from API schemas.
5. Every write must pass through a service.
6. Every material write must generate an audit event.
7. All document binary data must use object storage.
8. PostgreSQL remains the source of truth for metadata.
9. Long-running uploads must be asynchronous.
10. All batch operations must be restartable/idempotent.
11. Never trust client-side role checks.
12. Enforce authorization server-side.
13. Never allow AI output to directly mutate governance records without the required human confirmation.
14. Preserve source lineage.
15. Do not silently overwrite document versions.
16. Do not silently delete evidence.
17. Preserve historical monitoring results.
18. Threshold changes must not rewrite historical outcomes.
19. Write tests for every business rule.
20. Build feature-by-feature and keep the application runnable after every phase.

---

# 83. Suggested Repository Structure

*Superseded by the actual layout in Part 0 → Repository layout. Kept for reference only; do not
restructure the repository to match it.*

```text
mrm-mis/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── features/
│   │   │   ├── models/
│   │   │   ├── monitoring/
│   │   │   ├── documents/
│   │   │   ├── imports/
│   │   │   ├── findings/
│   │   │   └── dashboard/
│   │   └── api/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── rules/
│   │   ├── repositories/
│   │   ├── workers/
│   │   ├── ingestion/
│   │   ├── documents/
│   │   ├── monitoring/
│   │   └── audit/
│   ├── migrations/
│   └── tests/
│
├── seed/
├── demo-files/
├── docs/
│   ├── BRD.md
│   ├── design.md
│   └── templates.md
│
├── docker/
├── docker-compose.yml
└── README.md
```

---

# 84. Development Definition of Done

A feature is complete only when:

- Business requirement implemented.
- API implemented.
- Authorization implemented.
- Database migration implemented.
- Audit events implemented.
- Unit tests implemented.
- Integration test implemented where applicable.
- UI implemented.
- Empty/error/loading states implemented.
- Relevant documentation updated.
- No hard-coded business data.
- Existing functionality remains operational.
- `/review-build` run for the feature, with no open Critical or High finding.
- Mock-up parity checks for the feature's screens are Match or recorded as an accepted difference.

---

# 85. Priority Classification

## Must Have — MVP

- Model inventory.
- Tiering.
- Lifecycle.
- Validation.
- Findings.
- Approvals.
- Governance score.
- Structured imports.
- Individual document upload.
- Batch document upload.
- Folder/ZIP upload.
- Document metadata.
- Document versioning.
- Monitoring plan.
- Monitoring metrics.
- Monitoring results.
- Monitoring thresholds.
- Monitoring breaches.
- Monitoring dashboard.
- Model 360 monitoring.
- CDE/DQ.
- Audit trail.
- RBAC.
- Command Center.
- Operations Board.
- Document Centre.
- Import Centre.
- Regulatory alignment (§12A): inventory classification, vendor models, effective challenge,
  limitations/overlays/use exceptions, model dependencies, aggregate model risk view, model risk report.

## Should Have

- AI document classification.
- AI extraction.
- Repeated breach detection.
- Semantic document search.
- Audit Copilot.
- Automated notifications.
- Manifest-driven package ingestion.
- Advanced trend analysis.

## Could Have

- Enterprise GRC integration.
- SSO.
- API ingestion.
- Email/Teams notifications.
- Advanced ML-based anomaly detection.
- Automated regulatory mapping.

---

# 86. Important Design Principles

## Principle 1 — Database is the source of truth

Files are inputs/evidence.

The UI never calculates portfolio figures from raw uploaded files.

## Principle 2 — Evidence first

Every material governance conclusion should be traceable to evidence.

## Principle 3 — Human in the loop

AI assists; humans confirm.

## Principle 4 — Configuration over code

Thresholds, frequencies and policies must be configurable.

## Principle 5 — Historical immutability

Historical monitoring and governance decisions must not change because current configuration changes.

## Principle 6 — Batch-first architecture

The system must support both one-file and enterprise-scale package ingestion.

## Principle 7 — Async processing

Document extraction and large imports must run as background jobs.

## Principle 8 — Full lineage

Every record must be traceable back to its source.

## Principle 9 — Explainability

Governance scores, KPI statuses and breaches must show how they were calculated.

## Principle 10 — No governance decision by AI

AI must not make or silently implement governance decisions.

---

# 87. Final Target State

The completed system should allow a Model Risk function to perform the following end-to-end process:

```text
Model Inventory
      |
      v
Risk Tiering
      |
      v
Model Lifecycle
      |
      +----------------------+
      |                      |
      v                      v
Validation              Documentation
      |                      |
      v                      v
Findings                 Evidence
      |                      |
      +----------+-----------+
                 |
                 v
          Model Approval
                 |
                 v
            Production
                 |
                 v
        Monitoring Plan
                 |
                 v
        Monitoring Runs
                 |
        +--------+---------+
        |        |         |
        v        v         v
      KPI      Drift      DQ
        |        |         |
        +--------+---------+
                 |
                 v
          Breach / Alert
                 |
                 v
        Investigation
                 |
                 v
          Finding / Action
                 |
                 v
          Review / Closure
                 |
                 v
        Governance Score
                 |
                 v
          Command Center
```

At every point, the system should answer:

**What is the current state?  
What changed?  
Why did it change?  
Who changed it?  
What evidence supports it?  
What action is required?  
What is overdue?  
What is the risk implication?**

This is the core business objective of the Model Governance MIS.
