"""Core Model Risk Report (BRD Â§12A REQ-REG-10A; criteria REG-15, REG-16). Plan row G1.16.

The report is built only from data that already exists without the rest of Â§12A, and its whole claim is
that it agrees with the Command Center on the same business date. These tests hold it to that: every
figure is compared with `/api/dashboard/summary` or the list it drills to, rather than with a number
written here, so a change to either side shows up as a disagreement instead of two independently wrong
answers.

The report is always for `app.clock.today()` (D12 amendment, 2026-10-06). There is no past-date
parameter, so there is nothing here that asks for one.
"""
from decimal import Decimal

from tests.conftest import ADMIN, AUDITOR, EXECUTIVE, MRC, VALIDATOR, audit_count, login

SECTIONS = ("inventory", "validation", "findings", "approvals", "score", "documentation", "changes_since")


def _get(client, h, path, **params):
    resp = client.get(path, headers=h, params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _generate(client, h, expect=201):
    resp = client.post("/api/reports/model-risk", headers=h)
    assert resp.status_code == expect, resp.text
    return resp.json()


def _counts(rows: list[dict]) -> dict[str, int]:
    """A distribution as {key: count}, so report and dashboard can be compared directly."""
    return {r["key"]: r["count"] for r in rows}


def test_reg_15_report_has_every_section(loaded_client):
    """REG-15: every REQ-REG-10A section is present, and so is the header."""
    h = login(loaded_client, *VALIDATOR)
    report = _generate(loaded_client, h)

    assert set(SECTIONS) <= set(report["sections"]), "a REQ-REG-10A section is missing"
    for field in ("report_id", "business_date", "generated_by", "generated_at", "framework_label",
                  "content_hash", "previous_report_id"):
        assert field in report, f"header field {field} missing"
    assert report["generated_by"] == VALIDATOR[0]
    assert report["previous_report_id"] is None, "the first report has no predecessor"


def test_reg_15_the_framework_label_comes_from_policy(loaded_client):
    """REG-15: the header label is the policy key `regulatory_framework`, not a string in code."""
    h = login(loaded_client, *ADMIN)
    settings = {s["setting_key"]: s for s in _get(loaded_client, h, "/api/admin/policy")}
    assert "regulatory_framework" in settings, "T12 must define the label (Part 0: no business text in code)"

    before = _generate(loaded_client, h)["framework_label"]
    assert before == settings["regulatory_framework"]["value"]

    resp = loaded_client.put("/api/admin/policy/regulatory_framework", headers=h, json={
        "value": "Local MRM Standard 2026", "row_version": settings["regulatory_framework"]["row_version"],
        "reason": "REG-15 test"})
    assert resp.status_code == 200, resp.text
    assert _generate(loaded_client, h)["framework_label"] == "Local MRM Standard 2026"


def test_reg_15_figures_equal_the_command_center(loaded_client):
    """REG-15: each figure equals the Command Center for the same business date, and the list it drills to."""
    h = login(loaded_client, *VALIDATOR)
    dash = _get(loaded_client, h, "/api/dashboard/summary")
    tiles, dist = dash["tiles"], dash["distributions"]
    s = _generate(loaded_client, h)["sections"]

    # Inventory
    assert s["inventory"]["total"] == tiles["total_models"]
    assert _counts(s["inventory"]["by_tier"]) == _counts(dist["tier"])
    assert _counts(s["inventory"]["by_stage"]) == _counts(dist["stage"])

    # Validation: the status split, and the overdue models themselves
    assert _counts(s["validation"]["by_status"]) == _counts(dist["revalidation_status"])
    overdue_models = _get(loaded_client, h, "/api/models", revalidation_status="Overdue")
    assert {m["model_id"] for m in s["validation"]["overdue"]} == {m["model_id"] for m in overdue_models}
    assert len(s["validation"]["overdue"]) == tiles["revalidation_overdue"]
    # REQ-REG-10A: "with the overdue models listed and ordered by tier".
    rank = {"High": 0, "Medium": 1, "Low": 2}
    tiers = [rank[m["tier"]] for m in s["validation"]["overdue"]]
    assert tiers == sorted(tiers), "overdue models are ordered by tier, highest risk first"

    # Findings
    assert _counts(s["findings"]["open_by_severity"]) == _counts(dist["open_findings_by_severity"])
    assert sum(r["count"] for r in s["findings"]["overdue_by_severity"]) == tiles["overdue_findings"]
    assert len(s["findings"]["critical_overdue"]) == tiles["critical_overdue_findings"]

    # Approvals
    assert {m["model_id"] for m in s["approvals"]["conditional_open"]} == \
        {m["model_id"] for m in _get(loaded_client, h, "/api/models", flag="open_conditions")}

    # Score
    assert _counts(s["score"]["by_band"]) == _counts(dist["score_band"])
    assert s["score"]["portfolio_score"] == tiles["portfolio_score"]

    # Documentation
    assert {m["model_id"] for m in s["documentation"]["models_missing_documents"]} == \
        {m["model_id"] for m in _get(loaded_client, h, "/api/models", flag="doc_gaps")}
    assert s["documentation"]["completeness_pct"] == tiles["document_completeness_pct"]


def test_reg_15_inventory_is_by_displayed_stage_not_raw_lifecycle_phase(loaded_client):
    """REG-15: the inventory summary uses the displayed column (LIF-02), not `lifecycle_phase`.

    This is the half of the criterion that the D12 amendment settled. A model in Monitoring whose next
    due date falls inside the lead time is shown in Revalidation, and the report has to agree with the
    screen. `Revalidation` is not a lifecycle phase at all, so a report built from the raw phase could
    not produce the column â€” which is what makes this assertion able to fail.
    """
    h = login(loaded_client, *VALIDATOR)
    models = _get(loaded_client, h, "/api/models")
    by_stage = _counts(_generate(loaded_client, h)["sections"]["inventory"]["by_stage"])

    assert by_stage.get("Revalidation", 0) > 0, "the sample portfolio should have a revalidation queue"
    assert not any(m["lifecycle_phase"] == "Revalidation" for m in models), \
        "Revalidation is a displayed column, never a stored phase"
    for column, count in by_stage.items():
        assert count == len(_get(loaded_client, h, "/api/models", column=column)), \
            f"stage {column} must equal its own drill-down"


def test_reg_15_changes_since_lists_exactly_the_differences(loaded_client):
    """REG-15/REQ-REG-10A: "changes since the previous report" is the difference from the stored one."""
    h = login(loaded_client, *ADMIN)
    first = _generate(loaded_client, h)
    assert first["sections"]["changes_since"]["previous_report_id"] is None

    # One new model, one phase change, one finding closed.
    new_model = {"model_id": "M-9001", "model_name": "REG-15 probe", "model_type": "Credit Risk",
                 "model_subtype": "PD", "purpose": "Changes-since probe.", "business_line": "Business Banking",
                 "owner_id": "U-003", "developer_id": "U-021", "validator_id": "U-014",
                 "lifecycle_phase": "Development", "version": "v1.0",
                 "q_materiality": 2, "q_complexity": 2, "q_reliance": 2, "q_regulatory_use": 2}
    assert loaded_client.post("/api/models", headers=h, json=new_model).status_code == 201

    second = _generate(loaded_client, h)
    changes = second["sections"]["changes_since"]
    assert changes["previous_report_id"] == first["report_id"]
    assert "M-9001" in [m["model_id"] for m in changes["models_added"]]
    assert changes["models_added"] and not changes["models_retired"]

    # A third report with nothing in between reports no changes at all.
    third = _generate(loaded_client, h)
    changes = third["sections"]["changes_since"]
    assert changes["previous_report_id"] == second["report_id"]
    assert changes["models_added"] == [] and changes["models_retired"] == []
    assert changes["phase_changes"] == []
    assert changes["findings_opened"] == [] and changes["findings_closed"] == []
    assert third["sections"]["approvals"]["decisions_since_previous"] == []

    # A phase change and a new decision both show up in the next report.
    model = _get(loaded_client, h, "/api/models/M-9001")
    assert loaded_client.post("/api/models/M-9001/transition", headers=h, json={
        "to_phase": "Validation", "reason": "REG-15 probe",
        "row_version": model["model"]["row_version"]}).status_code == 200
    assert loaded_client.post("/api/approvals", headers=h, json={
        "approval_id": "A-9001", "model_id": "M-9001", "decision_date": "2026-09-30",
        "forum": "MRC", "decision_type": "Initial approval", "decision": "Approved"}).status_code == 201

    fourth = _generate(loaded_client, h)["sections"]
    assert [c["model_id"] for c in fourth["changes_since"]["phase_changes"]] == ["M-9001"]
    assert fourth["changes_since"]["phase_changes"][0]["to_phase"] == "Validation"
    assert [a["approval_id"] for a in fourth["approvals"]["decisions_since_previous"]] == ["A-9001"]


def test_reg_16_the_same_data_gives_the_same_content_hash(loaded_client):
    """REG-16: generating twice from the same data on the same business date gives the same content."""
    h = login(loaded_client, *MRC)
    first, second = _generate(loaded_client, h), _generate(loaded_client, h)

    assert first["content_hash"] == second["content_hash"], "the hash must not depend on when it ran"
    assert first["report_id"] != second["report_id"], "each generation is still its own stored report"

    # And it must be a hash of the content, not a constant: change the portfolio, change the hash.
    assert loaded_client.post("/api/models", headers=login(loaded_client, *ADMIN), json={
        "model_id": "M-9002", "model_name": "REG-16 probe", "model_type": "Credit Risk",
        "model_subtype": "PD", "purpose": "Hash probe.", "business_line": "Business Banking",
        "owner_id": "U-003", "developer_id": "U-021", "validator_id": "U-014",
        "lifecycle_phase": "Development", "version": "v1.0",
        "q_materiality": 3, "q_complexity": 3, "q_reliance": 3, "q_regulatory_use": 3}).status_code == 201
    assert _generate(loaded_client, h)["content_hash"] != first["content_hash"]


def test_reg_16_each_generation_writes_exactly_one_audit_event(loaded_client):
    """REG-16: one audit event per generation, carrying the report id."""
    h = login(loaded_client, *MRC)
    before = audit_count(loaded_client, h, entity="model_risk_report")
    report = _generate(loaded_client, h)
    after = audit_count(loaded_client, h, entity="model_risk_report")

    assert after == before + 1, "exactly one event per generation"
    events = _get(loaded_client, h, "/api/audit", entity="model_risk_report")
    latest = next(e for e in events if e["entity_id"] == report["report_id"])
    assert latest["action"] == "generate"
    assert latest["user_id"] == MRC[0] and latest["role"] == MRC[1]


def test_reg_16_a_role_without_report_generate_is_refused_and_nothing_is_stored(loaded_client):
    """REG-16: 403 from the API, and neither a stored report nor an audit event."""
    admin = login(loaded_client, *ADMIN)
    before_reports = len(_get(loaded_client, admin, "/api/reports/model-risk"))
    before_audit = audit_count(loaded_client, admin, entity="model_risk_report")

    for who in (EXECUTIVE, AUDITOR):
        h = login(loaded_client, *who)
        assert loaded_client.post("/api/reports/model-risk", headers=h).status_code == 403, who

    assert len(_get(loaded_client, admin, "/api/reports/model-risk")) == before_reports, "nothing stored"
    assert audit_count(loaded_client, admin, entity="model_risk_report") == before_audit, "nothing audited"


def test_reg_16_read_roles_can_list_and_reopen_a_stored_report(loaded_client):
    """REG-16/REG-17 (the read half): generating needs the permission; reading does not."""
    report = _generate(loaded_client, login(loaded_client, *VALIDATOR))

    for who in (EXECUTIVE, AUDITOR):
        h = login(loaded_client, *who)
        listed = _get(loaded_client, h, "/api/reports/model-risk")
        assert report["report_id"] in [r["report_id"] for r in listed]
        reopened = _get(loaded_client, h, f"/api/reports/model-risk/{report['report_id']}")
        assert reopened["content_hash"] == report["content_hash"]
        assert set(SECTIONS) <= set(reopened["sections"]), "a reopened report is the whole report"


def test_reg_16_a_stored_report_renders_as_a_pdf(loaded_client):
    """REQ-REG-10A: the stored report downloads as a PDF. The screen itself is G1.17."""
    h = login(loaded_client, *VALIDATOR)
    report = _generate(loaded_client, h)
    resp = loaded_client.get(f"/api/reports/model-risk/{report['report_id']}/pdf",
                             headers=login(loaded_client, *EXECUTIVE))
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("application/pdf")
    assert resp.content.startswith(b"%PDF-"), "a real PDF, not an error page"
    assert len(resp.content) > 1000, "a report with content, not an empty page"


def test_reg_15_the_score_section_names_the_weakest_component(loaded_client):
    """REQ-REG-10A: the lowest-scoring models are listed with their weakest component."""
    h = login(loaded_client, *VALIDATOR)
    lowest = _generate(loaded_client, h)["sections"]["score"]["lowest"]
    assert lowest, "the sample portfolio has scored models"

    scores = [Decimal(str(m["score"])) for m in lowest]
    assert scores == sorted(scores), "lowest first"
    for entry in lowest:
        assert entry["weakest_component"], f"{entry['model_id']} has no weakest component named"
        detail = _get(loaded_client, h, f"/api/models/{entry['model_id']}")
        components = {c["key"]: c for c in detail["score"]["components"] if c.get("score") is not None}
        assert entry["weakest_component"] in components
        assert components[entry["weakest_component"]]["score"] == min(
            c["score"] for c in components.values()), "it must really be the weakest"


def test_reg_16_the_service_refuses_an_unpermitted_principal_too(db_session):
    """REG-16, at the service rather than the route.

    `require(Permission.REPORT_GENERATE)` on the route rejects an Executive before `generate` is
    reached, so the API test above cannot exercise the service's own check â€” the same blind spot that
    made an earlier permission test in `test_imports.py` prove nothing. The service re-checks because
    the CLI and the seed loader call it directly, and this is the only test that reaches it.
    """
    import pytest

    from app.auth.security import Principal
    from app.models import ModelRiskReport
    from app.services import report_service
    from app.services.errors import ForbiddenError

    with db_session() as db:
        executive = Principal(user_id="U-042", role="Executive", full_name="James Whitfield")
        with pytest.raises(ForbiddenError):
            report_service.generate(db, executive)
        assert db.query(ModelRiskReport).count() == 0, "a refused generation stores nothing"

        # The same call with a permitted role goes through, so the refusal is the permission and not
        # some other failure on the way.
        validator = Principal(user_id="U-014", role="Validator", full_name="Sarah Patel")
        report, _ = report_service.generate(db, validator)
        assert report.generated_by == "U-014"
        assert db.query(ModelRiskReport).count() == 1
