"""Core Model Risk Report (BRD Â§12A REQ-REG-10A, criteria REG-15 and REG-16).

The report's whole claim is that it agrees with the Command Center, so it is built from the same two
sources the Command Center is built from â€” `dashboard_service.summary` for the distributions and
`governance_view.portfolio` for the models behind them â€” and never from its own queries over the
governance tables. Anything else would be a second implementation of the same figures, free to drift.

A report is always generated for the current business date (`app.clock.today()`, D12 amendment). There
is deliberately no date parameter: derived state is recomputed on read, so an earlier date would mean
threading a date through those two modules and would still not reconstruct the portfolio as it stood.
The stored reports are the history.
"""
import hashlib
import json
from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import service as audit
from app.auth.roles import Permission, has_permission
from app.auth.security import Principal
from app.clock import today
from app.models import Approval, Finding, Model, ModelRiskReport
from app.rules import revalidation
from app.services import dashboard_service, governance_view
from app.services.errors import ForbiddenError, NotFoundError
from app.services.policy_access import Policy
from app.storage import get_store

#: How many of the weakest-scoring models the score section lists. Presentation, not a business rule:
#: it changes what a page shows, never what a figure means, so it is not a policy setting.
LOWEST_SCORING_LISTED = 10

TIER_ORDER = ("High", "Medium", "Low")


def _dist(rows: Sequence[dict]) -> list[dict]:
    """A dashboard distribution reduced to what the report states: the key and its count."""
    return [{"key": r["key"], "count": r["count"]} for r in rows]


def _plain(value: Any) -> Any:
    """JSON-safe, and stable: Decimal and date must not depend on repr for the content hash."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


#: Provenance, not content: which report came before does not change what this one says about the
#: portfolio. They are excluded from the hash so that two generations from the same data on the same
#: business date match (REG-16) â€” the second one necessarily has a predecessor and the first does not.
#: The change *lists* stay in: those are findings about the portfolio, and they do differ.
_NOT_CONTENT = ("previous_report_id", "previous_generated_at")


def content_hash(sections: dict) -> str:
    """SHA-256 of the canonical content.

    `generated_at`, `generated_by` and `report_id` are not part of it, nor is the predecessor's
    identity, so two generations from the same data on the same business date hash the same (REG-16)
    while a change to any figure does not.
    """
    content = {k: v for k, v in sections.items() if k != "changes_since"}
    content["changes_since"] = {k: v for k, v in sections["changes_since"].items()
                               if k not in _NOT_CONTENT}
    canonical = json.dumps(_plain(content), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _inventory(summary: dict) -> dict:
    """Models by tier and by *displayed stage* (LIF-02), which is what the Command Center shows.

    Not the raw `lifecycle_phase`: a model in Monitoring whose next due date falls inside the lead
    time is displayed in Revalidation, and REQ-REG-10A requires the report to equal the screen. The
    D12 amendment settled this; "Revalidation" is not a stored phase at all.
    """
    return {
        "total": summary["tiles"]["total_models"],
        "by_tier": _dist(summary["distributions"]["tier"]),
        "by_stage": _dist(summary["distributions"]["stage"]),
    }


def _validation(summary: dict, rows: list[tuple[Model, Any]]) -> dict:
    overdue = [
        {"model_id": m.model_id, "model_name": m.model_name, "tier": m.effective_tier,
         "owner_id": m.owner_id, "next_due": s.next_due, "days_overdue": -s.days_to_due
         if s.days_to_due is not None else None, "latest_decision": s.latest_decision}
        for m, s in rows if s.revalidation_status == revalidation.OVERDUE
    ]
    # REQ-REG-10A: "with the overdue models listed and ordered by tier".
    overdue.sort(key=lambda r: (TIER_ORDER.index(r["tier"]) if r["tier"] in TIER_ORDER else len(TIER_ORDER),
                                r["model_id"]))
    return {"by_status": _dist(summary["distributions"]["revalidation_status"]), "overdue": overdue}


def _findings(db: Session, summary: dict, policy: Policy) -> dict:
    """Open and overdue findings by severity, with the critical overdue ones listed.

    The dashboard supplies open-by-severity; overdue-by-severity is not one of its distributions, so
    it is counted here from the same `finding` rows and the same open-status list, and the totals are
    reconciled against the dashboard's own tiles by the tests.
    """
    on = today()
    open_statuses = set(policy.list("finding_open_statuses"))
    severities = policy.list("finding_severities")

    overdue_rows = [
        f for f in db.scalars(select(Finding))
        if f.status in open_statuses and f.due_date is not None and f.due_date < on
    ]
    by_sev = {sev: 0 for sev in severities}
    for f in overdue_rows:
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1

    critical = sorted(
        ({"finding_id": f.finding_id, "model_id": f.model_id, "title": f.title,
          "severity": f.severity, "status": f.status, "due_date": f.due_date,
          "days_overdue": (on - f.due_date).days}
         for f in overdue_rows if f.severity == severities[0]),
        key=lambda r: (-r["days_overdue"], r["finding_id"]),
    )
    return {
        "open_by_severity": _dist(summary["distributions"]["open_findings_by_severity"]),
        "overdue_by_severity": [{"key": k, "count": v} for k, v in by_sev.items()],
        "critical_overdue": critical,
    }


def _approvals(db: Session, rows: list[tuple[Model, Any]], seen_before: set[str] | None) -> dict:
    """Conditional approvals with open conditions, and decisions since the previous report.

    "Since" is which approvals the previous stored report had already seen, not a timestamp window â€”
    the same reason as `_baseline`: one-second timestamps lose anything recorded in the same second
    as the report.
    """
    conditional = sorted(
        ({"model_id": m.model_id, "model_name": m.model_name, "tier": m.effective_tier,
          "open_conditions": s.open_conditions, "latest_decision": s.latest_decision}
         for m, s in rows if s.open_conditions),
        key=lambda r: r["model_id"],
    )
    decisions: list[dict] = []
    if seen_before is not None:
        decisions = sorted(
            ({"approval_id": a.approval_id, "model_id": a.model_id, "decision": a.decision,
              "decision_type": a.decision_type, "forum": a.forum, "decision_date": a.decision_date}
             for a in db.scalars(select(Approval)) if a.approval_id not in seen_before),
            key=lambda r: (str(r["decision_date"]), r["approval_id"]),
        )
    return {"conditional_open": conditional, "decisions_since_previous": decisions}


def _score(summary: dict, rows: list[tuple[Model, Any]], policy: Policy) -> dict:
    """Band distribution, and the weakest models with the component dragging each one down.

    The band *label* is stored alongside the key, not resolved when the report is read. A board
    report cannot say "below_warn", and the boundaries come from policy â€” so a report reopened after
    a policy change must still show the label that applied when it was generated (Principle 5).
    """
    labels = policy.score_bands.labels()
    scored = []
    for m, s in rows:
        if s.score is None or s.score.overall is None:
            continue
        applicable = [c for c in s.score.components if c.score is not None]
        weakest = min(applicable, key=lambda c: (c.score, c.key)) if applicable else None
        scored.append({"model_id": m.model_id, "model_name": m.model_name, "tier": m.effective_tier,
                       "score": s.score.overall,
                       "weakest_component": weakest.key if weakest else None,
                       "weakest_component_score": weakest.score if weakest else None})
    scored.sort(key=lambda r: (r["score"], r["model_id"]))
    return {
        "by_band": [{**r, "label": labels.get(r["key"], r["key"])}
                    for r in _dist(summary["distributions"]["score_band"])],
        "portfolio_score": summary["tiles"]["portfolio_score"],
        "scored_models": summary["tiles"]["scored_models"],
        "lowest": scored[:LOWEST_SCORING_LISTED],
    }


def _documentation(summary: dict, rows: list[tuple[Model, Any]]) -> dict:
    missing = sorted(
        ({"model_id": m.model_id, "model_name": m.model_name, "lifecycle_phase": m.lifecycle_phase,
          "missing": list(s.missing_documents)}
         for m, s in rows if s.missing_documents),
        key=lambda r: r["model_id"],
    )
    return {
        "completeness_pct": summary["tiles"]["document_completeness_pct"],
        "models_missing_documents": missing,
    }


def _baseline(rows: list[tuple[Model, Any]], findings: dict[str, str],
              approvals: list[str]) -> dict:
    """The identities a later report diffs against: which models existed, in which phase, and the
    status of every finding.

    This is what makes "changes since the previous report" a comparison of two stored reports rather
    than a time-window query. Timestamps looked like the obvious way, but `created_at` and
    `generated_at` have one-second granularity, so anything that happened in the same second as the
    previous report was invisible â€” and that is exactly what a user clicking twice would do.
    """
    return {
        "models": {m.model_id: {"phase": m.lifecycle_phase, "tier": m.effective_tier,
                                "name": m.model_name} for m, _ in rows},
        "findings": findings,
        "approvals": approvals,
    }


def _changes_since(previous_content: dict | None, previous: ModelRiskReport | None,
                   baseline: dict, policy: Policy) -> dict:
    """The difference between this report's baseline and the previous stored report's.

    With no predecessor the section is present and empty: the first report has nothing to compare
    against, which is not the same as having nothing to report.
    """
    empty = {"previous_report_id": None, "previous_generated_at": None, "models_added": [],
             "models_retired": [], "phase_changes": [], "findings_opened": [], "findings_closed": []}
    if previous is None or not previous_content:
        return empty

    was = previous_content.get("baseline") or {"models": {}, "findings": {}}
    before_models, now_models = was.get("models", {}), baseline["models"]
    before_findings, now_findings = was.get("findings", {}), baseline["findings"]
    retired = policy.retirement_phase
    open_statuses = set(policy.list("finding_open_statuses"))

    added = sorted(({"model_id": mid, "model_name": m["name"], "tier": m["tier"]}
                    for mid, m in now_models.items() if mid not in before_models),
                   key=lambda r: r["model_id"])
    newly_retired = sorted(({"model_id": mid, "model_name": m["name"]}
                            for mid, m in now_models.items()
                            if m["phase"] == retired and before_models.get(mid, {}).get("phase")
                            not in (None, retired)),
                           key=lambda r: r["model_id"])
    phase_changes = sorted(
        ({"model_id": mid, "from_phase": before_models[mid]["phase"], "to_phase": m["phase"]}
         for mid, m in now_models.items()
         if mid in before_models and before_models[mid]["phase"] != m["phase"]),
        key=lambda r: r["model_id"],
    )
    opened = sorted(fid for fid, status in now_findings.items()
                    if status in open_statuses and fid not in before_findings)
    closed = sorted(fid for fid, status in now_findings.items()
                    if status not in open_statuses
                    and before_findings.get(fid) in open_statuses)
    return {
        "previous_report_id": previous.report_id,
        "previous_generated_at": previous.generated_at,
        "models_added": added,
        "models_retired": newly_retired,
        "phase_changes": phase_changes,
        "findings_opened": [{"finding_id": f} for f in opened],
        "findings_closed": [{"finding_id": f} for f in closed],
    }


def latest(db: Session) -> ModelRiskReport | None:
    return db.scalars(
        select(ModelRiskReport).order_by(ModelRiskReport.generated_at.desc(),
                                         ModelRiskReport.report_id.desc()).limit(1)
    ).first()


def list_reports(db: Session) -> list[ModelRiskReport]:
    return list(db.scalars(select(ModelRiskReport).order_by(ModelRiskReport.generated_at.desc(),
                                                            ModelRiskReport.report_id.desc())))


def get_report(db: Session, report_id: str) -> ModelRiskReport:
    report = db.get(ModelRiskReport, report_id)
    if report is None:
        raise NotFoundError(f"Report {report_id} does not exist.")
    return report


def sections(db: Session, previous: ModelRiskReport | None) -> dict:
    """Every REQ-REG-10A section, from the Command Center's own aggregates.

    `baseline` is not one of the seven sections: it is the identity snapshot the *next* report diffs
    against, carried in the stored copy so "changes since" needs no clock.
    """
    policy = Policy.load(db)
    summary = dashboard_service.summary(db)
    rows = governance_view.portfolio(db)
    previous_content = read_sections(previous) if previous is not None else None
    statuses = {f.finding_id: f.status for f in db.scalars(select(Finding))}
    approval_ids = sorted(a.approval_id for a in db.scalars(select(Approval)))
    baseline = _baseline(rows, statuses, approval_ids)
    seen_before = (set((previous_content.get("baseline") or {}).get("approvals") or [])
                   if previous_content else None)
    return {
        "inventory": _inventory(summary),
        "validation": _validation(summary, rows),
        "findings": _findings(db, summary, policy),
        "approvals": _approvals(db, rows, seen_before),
        "score": _score(summary, rows, policy),
        "documentation": _documentation(summary, rows),
        "changes_since": _changes_since(previous_content, previous, baseline, policy),
        "baseline": baseline,
    }


def read_sections(report: ModelRiskReport) -> dict:
    """The stored copy, so a report reopens as what it said at the time (REQ-REG-10A)."""
    return json.loads(get_store().get(report.storage_path).decode("utf-8"))


def _next_report_id(db: Session, on) -> str:
    prefix = f"MRR-{on:%Y%m%d}"
    used = db.scalars(select(ModelRiskReport.report_id)
                      .where(ModelRiskReport.report_id.like(f"{prefix}-%"))).all()
    return f"{prefix}-{len(used) + 1:03d}"


def generate(db: Session, principal: Principal | None) -> tuple[ModelRiskReport, dict]:
    """Generate, store and audit one report for the current business date.

    The stored copy is written before the row is committed, so a committed report always has its
    content; a failed store leaves neither. The audit event is recorded in the same transaction as
    the row (Part 0), so there is no committed report without its event.
    """
    if principal and not has_permission(principal.role, Permission.REPORT_GENERATE):
        raise ForbiddenError("Generating the model risk report requires the report:generate permission.")

    on = today()
    previous = latest(db)
    content = sections(db, previous)
    digest = content_hash(content)
    report_id = _next_report_id(db, on)
    path = f"reports/model-risk/{on:%Y}/{report_id}.json"

    get_store().put(path, json.dumps(_plain(content), sort_keys=True, ensure_ascii=False).encode("utf-8"),
                    content_type="application/json")

    report = ModelRiskReport(
        report_id=report_id,
        business_date=on,
        generated_by=principal.user_id if principal else None,
        # No explicit value: `generated_at` takes the same `func.now()` the `created_at` and
        # `updated_at` columns use, so "changed since the previous report" compares one clock.
        # Setting it from `datetime.now()` here made every comparison wrong by the UTC offset.
        framework_label=Policy.load(db).text("regulatory_framework"),
        content_hash=digest,
        storage_path=path,
        previous_report_id=previous.report_id if previous else None,
    )
    db.add(report)
    audit.record(db, principal, action="generate", entity="model_risk_report", entity_id=report_id,
                 after={"business_date": on.isoformat(), "content_hash": digest,
                        "previous_report_id": report.previous_report_id},
                 reason="Model risk report generated")
    db.commit()
    db.refresh(report)
    return report, content
