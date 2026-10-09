"""Core Model Risk Report (BRD §12A REQ-REG-10A; criteria REG-15, REG-16). Plan row G1.16.

The report is built only from data that already exists without the rest of §12A, and its whole claim is
that it agrees with the Command Center on the same business date. These tests hold it to that: every
figure is compared with `/api/dashboard/summary` or the list it drills to, rather than with a number
written here, so a change to either side shows up as a disagreement instead of two independently wrong
answers.

The report is always for `app.clock.today()` (D12 amendment, 2026-10-06). There is no past-date
parameter, so there is nothing here that asks for one.
"""
from decimal import Decimal

from app.services import report_service
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
    not produce the column — which is what makes this assertion able to fail.
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
    reached, so the API test above cannot exercise the service's own check — the same blind spot that
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


def test_reg_17_earlier_reports_are_listed_newest_first(loaded_client):
    """REG-17: the screen's "earlier reports" list, which only means anything in a defined order.

    Ordering was unasserted after G1.16 — the same gap §76A.14 records for APR-04, where a list test
    checked the contents and not the order, and the order then turned out to be right only by
    coincidence of insertion. Asserted here against `generated_at`, not against insertion.
    """
    h = login(loaded_client, *VALIDATOR)
    made = [_generate(loaded_client, h)["report_id"] for _ in range(3)]

    listed = _get(loaded_client, h, "/api/reports/model-risk")
    assert [r["report_id"] for r in listed] == list(reversed(made)), "newest first"
    stamps = [r["generated_at"] for r in listed]
    assert stamps == sorted(stamps, reverse=True), "ordered by when they were generated"


def test_reg_17_an_auditor_can_download_the_pdf(loaded_client):
    """REG-17 names the Auditor explicitly; G1.16 only exercised the Executive.

    SEC-02 gives the Auditor no write permission, so this is also the check that reading a report is
    a read and not an incidental write.
    """
    report = _generate(loaded_client, login(loaded_client, *VALIDATOR))
    h = login(loaded_client, *AUDITOR)

    resp = loaded_client.get(f"/api/reports/model-risk/{report['report_id']}/pdf", headers=h)
    assert resp.status_code == 200, resp.text
    assert resp.content.startswith(b"%PDF-")
    assert report["report_id"] in resp.headers.get("content-disposition", ""), \
        "the download is named after the report, so a user can tell two apart on disk"
    assert audit_count(loaded_client, login(loaded_client, *ADMIN),
                       entity="model_risk_report", action="download") == 0, \
        "downloading is a read: it writes nothing"


def test_reg_15_score_bands_are_labelled_for_a_reader(loaded_client):
    """REG-15: the report reads like the Command Center, which labels bands from the boundaries.

    The label is *stored* with the count rather than resolved on read, so a report reopened after a
    policy change still shows the boundaries that applied when it was generated (§86 Principle 5).
    Without this the board report said "below_warn".
    """
    h = login(loaded_client, *ADMIN)
    meta = _get(loaded_client, h, "/api/models/meta")
    bands = _generate(loaded_client, h)["sections"]["score"]["by_band"]

    assert bands, "the sample portfolio has scored models"
    for row in bands:
        assert row["label"] == meta["score_band_labels"][row["key"]]
        assert not row["label"].startswith(row["key"]), "a label, not the key"

    # Move the boundary: a report generated now carries the new label, the stored one keeps the old.
    before = _generate(loaded_client, h)
    setting = next(s for s in _get(loaded_client, h, "/api/admin/policy")
                   if s["setting_key"] == "score_band_warn_min")
    assert loaded_client.put("/api/admin/policy/score_band_warn_min", headers=h, json={
        "value": "55", "row_version": setting["row_version"], "reason": "REG-15 label test"}).status_code == 200

    after = _generate(loaded_client, h)["sections"]["score"]["by_band"]
    assert any("55" in r["label"] for r in after), "a new report uses the new boundary"
    reopened = _get(loaded_client, h, f"/api/reports/model-risk/{before['report_id']}")
    assert reopened["sections"]["score"]["by_band"] == before["sections"]["score"]["by_band"], \
        "the stored report keeps the labels it was generated with"


def test_reg_15_the_lowest_scoring_count_comes_from_policy(loaded_client):
    """REG-15 / Part 0 "no business number in code" (plan BL.6, taken into G1.18).

    How many models the score section lists was a constant in the service. `dashboard_service` reads
    exactly this kind of limit from policy (`insights_display_limit`), so the precedent in this
    repository is that it belongs in T12 — and a reviewer would rightly flag the constant.
    """
    h = login(loaded_client, *ADMIN)
    settings = {s["setting_key"]: s for s in _get(loaded_client, h, "/api/admin/policy")}
    assert "report_lowest_scoring_limit" in settings, "T12 must define the limit"

    default = int(settings["report_lowest_scoring_limit"]["value"])
    assert len(_generate(loaded_client, h)["sections"]["score"]["lowest"]) == default

    resp = loaded_client.put("/api/admin/policy/report_lowest_scoring_limit", headers=h, json={
        "value": "3", "row_version": settings["report_lowest_scoring_limit"]["row_version"],
        "reason": "BL.6 test"})
    assert resp.status_code == 200, resp.text
    assert len(_generate(loaded_client, h)["sections"]["score"]["lowest"]) == 3, \
        "the limit is read from policy on each generation, not baked in"


def test_reg_17_a_reset_seeds_one_earlier_report_so_changes_since_has_content(client, test_settings):
    """REG-17: "changes since" lists exactly the differences from the previous *stored* report.

    G1.16 could only ever compare two reports generated seconds apart, so the section was always
    empty in a demo. The reset now seeds one earlier report, dated a month back, whose baseline
    differs from the loaded portfolio — so the first report a user generates actually shows changes.
    """
    from datetime import date

    from app.clock import today

    h = login(client, *ADMIN)
    assert client.post("/api/admin/reset", headers=h).status_code == 202

    seeded = _get(client, h, "/api/reports/model-risk")
    assert len(seeded) == 1, "a reset leaves exactly one earlier report to compare against"
    business = date.fromisoformat(seeded[0]["business_date"])
    gap = (today() - business).days
    assert 27 <= gap <= 32, f"dated about a month before the business date, not {gap} days"

    changes = _generate(client, h)["sections"]["changes_since"]
    assert changes["previous_report_id"] == seeded[0]["report_id"]

    # Exact counts, not truthiness: REG-17 says the section lists *exactly* the differences, and
    # truthiness passed even when the seed shaped 120 models instead of 4 (TR-05). The numbers are
    # written out rather than imported from the service, so changing the service cannot quietly
    # change what this test demands.
    assert len(changes["models_added"]) == 4
    assert len(changes["phase_changes"]) == 3
    assert len(changes["findings_closed"]) == 5
    assert changes["models_retired"] == [], "the seed shapes no retirements"
    assert all(c["to_phase"] != "Development" for c in changes["phase_changes"]),         "each listed change moved a model *out* of the phase the baseline showed"


# --- Gaps the R2 checkpoint found by mutating the code (D_Reviews/DB_test_review/20261007_G1.18_risk.md)
#
# Each of these passed against a deliberately broken implementation until now. They are written as the
# checkpoint described the mutation, so each one fails against that exact defect.


def test_reg_16_a_refused_generation_writes_no_audit_event(db_session):
    """REG-16: "nothing is stored and no audit event is written" — the audit half, at the service.

    TR-01. The route's `require()` refuses an Executive before the service runs, so an API test
    proves nothing about the service, which is the path the CLI and the seed loader take. The earlier
    service test checked only that no *report* was stored; a service that audited the refusal and
    committed it passed every test.

    The count is over one entity and is taken from the database, so neither a page cap nor a wider
    filter can make "unchanged" true by accident (the trap recorded for G0.7).
    """
    import pytest
    from sqlalchemy import func, select

    from app.auth.security import Principal
    from app.models import AuditEvent, ModelRiskReport
    from app.services import report_service
    from app.services.errors import ForbiddenError

    def report_events(db) -> int:
        return db.scalar(select(func.count()).select_from(AuditEvent)
                         .where(AuditEvent.entity == "model_risk_report"))

    with db_session() as db:
        before = report_events(db)
        with pytest.raises(ForbiddenError):
            report_service.generate(db, Principal(user_id="U-042", role="Executive",
                                                  full_name="James Whitfield"))
        db.rollback()
        assert report_events(db) == before, "a refused generation writes no audit event"
        assert db.scalar(select(func.count()).select_from(ModelRiskReport)) == 0, "and stores nothing"

        # The control: a permitted generation writes exactly one, so the negative means something.
        report_service.generate(db, Principal(user_id="U-014", role="Validator",
                                              full_name="Sarah Patel"))
        assert report_events(db) == before + 1


def test_reg_16_report_generate_is_held_by_exactly_the_specified_roles():
    """REG-16 / REQ-REG-10A: "`REPORT_GENERATE` (Admin, MRC Member and Validator by default)".

    TR-02. Nothing asserted *who* holds the permission, so granting it to Model Owner and Monitoring
    Analyst passed all 195 tests. The roles are written out rather than derived from the matrix: a
    test that reads the thing it checks cannot fail when that thing is wrong.
    """
    from app.auth.roles import Permission, ROLE_PERMISSIONS

    holders = {role.value for role, perms in ROLE_PERMISSIONS.items()
               if Permission.REPORT_GENERATE in perms}
    assert holders == {"Admin", "MRC Member", "Validator"}


def test_reg_15_the_business_date_is_the_business_date_not_the_calendar_date(loaded_client, test_settings):
    """REG-15: the report is for `app.clock.today()`, which `MRM_TODAY_OVERRIDE` fixes.

    TR-03. Nothing asserted this, so a service reading `date.today()` passed all 195 tests even
    though the suite's business date is years from the real one. Part 0 makes `app.clock.today()` an
    invariant precisely so seeded overdue and revalidation states are reproducible.
    """
    from datetime import date

    from app.clock import today

    assert today() != date.today(), "the fixture must fix a business date that is not today"
    report = _generate(loaded_client, login(loaded_client, *ADMIN))
    assert report["business_date"] == today().isoformat()
    assert report["business_date"] != date.today().isoformat()


def test_gen_01_a_reset_clears_the_report_history_and_reseeds_it(client, test_settings):
    """GEN-01: two resets at the same business date give the same report history.

    The seeded predecessor only ever appeared on a database that had never held a report, so a demo
    that generated a few reports and then reset was left with the old ones and no fresh comparison —
    and the second reset's history depended on what had happened in between, which is exactly what
    determinism forbids.
    """
    h = login(client, *ADMIN)
    assert client.post("/api/admin/reset", headers=h).status_code == 202
    seeded = _get(client, h, "/api/reports/model-risk")
    assert len(seeded) == 1

    _generate(client, h)
    _generate(client, h)
    assert len(_get(client, h, "/api/reports/model-risk")) == 3, "the demo generated two of its own"

    assert client.post("/api/admin/reset", headers=h).status_code == 202
    after = _get(client, h, "/api/reports/model-risk")
    assert len(after) == 1, "a reset clears the report history and leaves one seeded predecessor"
    assert after[0]["report_id"] == seeded[0]["report_id"]
    assert after[0]["content_hash"] == seeded[0]["content_hash"], \
        "GEN-01: the same business date reproduces the same report"


def test_reg_17_the_pdf_is_this_report_and_carries_its_content(loaded_client):
    """REG-17: "downloaded as a PDF" — of *this* report, with its figures in it.

    TR-06. The earlier assertions were `%PDF-` and a size floor, which a renderer returning magic
    bytes plus two thousand junk bytes satisfied. Three things a stub cannot fake: the document
    metadata names this report's business date and framework, the file is structurally complete, and
    the rendered size tracks the content — a report with sixty overdue models is materially longer
    than one with none. The page text itself is inside encoded content streams, so grepping for a
    figure is not available without a PDF parser.
    """
    from app.reports import pdf

    h = login(loaded_client, *VALIDATOR)
    report = _generate(loaded_client, h)
    resp = loaded_client.get(f"/api/reports/model-risk/{report['report_id']}/pdf", headers=h)
    assert resp.status_code == 200
    data = resp.content

    assert data.startswith(b"%PDF-") and data.rstrip().endswith(b"%%EOF"), "a complete document"
    assert f"Model Risk Report {report['business_date']}".encode() in data, \
        "the title names this report's business date, so it is not a generic or stale file"
    assert report["framework_label"].encode() in data, "and the framework it was generated under"

    # The size tracks the content: the same renderer over a report with sixty overdue models must
    # produce a materially longer document than one with none.
    stored = report["sections"]
    sparse = {**stored, "validation": {**stored["validation"], "overdue": []}}
    dense = {**stored, "validation": {**stored["validation"], "overdue": [
        {"model_id": f"M-{i:04d}", "model_name": f"Probe {i}", "tier": "High", "owner_id": "U-003",
         "days_overdue": i} for i in range(60)]}}
    header = {k: v for k, v in report.items() if k != "sections"}
    grew = len(pdf.render(header, dense)) - len(pdf.render(header, sparse))
    assert grew > 2000, (
        f"sixty extra table rows added only {grew} bytes, so the renderer is not putting the sections "
        f"on the page. A ratio was the wrong measure: a real report already carries content, so it is "
        f"the difference that shows whether the rows were rendered")


def test_reg_16_the_hash_ignores_which_report_came_before(loaded_client, loaded_session):
    """REG-16, FT-09: two generations from the same data agree even once a predecessor exists.

    This is the case the test above cannot reach. `loaded_client` starts with no stored report, so
    both of its generations diff *nothing* and hash an identical empty change section — the fixture
    is what makes it pass, not the code. A reset seeds a previous report, and then the first
    generation of a day diffs that while the second diffs the first, so the change lists differ by
    construction. With `changes_since` inside the digest the hashes could never agree, which is how
    REG-16 came to fail in production terms while CI stayed green (FT-09).

    Decided by **S10** (the D12 addendum): the predecessor is provenance, so everything derived
    solely from it is too. The hash covers the report's figures.
    """
    h = login(loaded_client, *MRC)

    # A predecessor with content differences, built the way a reset builds one.
    seeded = report_service.seed_previous_report(loaded_session)
    assert seeded, "the fixture must be able to seed a predecessor"

    first, second, third = (_generate(loaded_client, h) for _ in range(3))
    assert first["content_hash"] == second["content_hash"], (
        "generation 1 diffs the seeded report and generation 2 diffs generation 1; the hash must not "
        "see that difference (FT-09)")
    assert second["content_hash"] == third["content_hash"], "and it must stay stable after that"

    # The change lists really do differ — otherwise this proves nothing about the exclusion.
    assert first["sections"]["changes_since"] != second["sections"]["changes_since"], (
        "the change sections must differ, or the hashes would agree for the wrong reason")

    # The exclusion is narrow: a figure still moves the hash.
    assert loaded_client.post("/api/models", headers=login(loaded_client, *ADMIN), json={
        "model_id": "M-9003", "model_name": "FT-09 probe", "model_type": "Credit Risk",
        "model_subtype": "PD", "purpose": "Hash probe after a predecessor exists.",
        "business_line": "Business Banking", "owner_id": "U-003", "developer_id": "U-021",
        "validator_id": "U-014", "lifecycle_phase": "Development", "version": "v1.0",
        "q_materiality": 3, "q_complexity": 3, "q_reliance": 3, "q_regulatory_use": 3}).status_code == 201
    assert _generate(loaded_client, h)["content_hash"] != first["content_hash"], (
        "a change to the portfolio must still change the hash")


# --- the seeded example: real figures, labelled as an example (S11, S12 / D12 addendum) ------------

def test_s11_the_seeded_report_holds_real_figures(client, test_settings):
    """REG-15, S11 (CR-41, MP-18): a stored report never holds a figure that was not real.

    The seeded example was generated before the reset's evidence loaded, so `completeness` returned
    `score=0` rather than `None` and the 25%-weight documentation component scored zero for every
    model. On screen that read as 0% documentation, 250 of 256 models missing everything and a
    portfolio score of 64.5 against today's 92.9 — a credible-looking governance collapse that
    "recovered" with nothing in the section whose job is to explain it. Every other section showed
    today's numbers, so it was not a snapshot of anything.

    Decided by **S11**: the seeded example is generated by the real service *after* the evidence
    loads. Only its baseline stays shaped, which is diff input rather than a reported figure.
    """
    h = login(client, *ADMIN)
    assert client.post("/api/admin/reset", headers=h).status_code == 202
    h = login(client, *ADMIN)

    reports = _get(client, h, "/api/reports/model-risk")
    assert len(reports) == 1, f"a reset seeds exactly one example report, got {len(reports)}"
    seeded = reports[0]
    detail = _get(client, h, f"/api/reports/model-risk/{seeded['report_id']}")
    doc = detail["sections"]["documentation"]

    assert doc["completeness_pct"] > 0, (
        "the seeded example must be generated after the evidence loads; 0% means it was not")
    models = len(_get(client, h, "/api/models"))
    assert len(doc["models_missing_documents"]) < models, (
        f"all {models} models missing documents means the report saw an empty Document Centre")

    # And its figures are the service's, not shaped: they equal a freshly generated report's.
    fresh = _generate(client, login(client, *ADMIN))
    assert fresh["sections"]["documentation"] == doc, (
        "the seeded example's figures must be what the service computes from the same portfolio")


def test_s12_the_seeded_report_is_labelled_and_a_generated_one_is_not(client, test_settings):
    """S12: the seeded example is disclosed as an example wherever reports are listed or reopened."""
    h = login(client, *ADMIN)
    assert client.post("/api/admin/reset", headers=h).status_code == 202
    h = login(client, *ADMIN)

    seeded = _get(client, h, "/api/reports/model-risk")[0]
    assert seeded["is_seeded"] is True, "the reset's example must say so in the list"
    assert _get(client, h, f"/api/reports/model-risk/{seeded['report_id']}")["is_seeded"] is True, (
        "and when it is reopened")

    generated = _generate(client, login(client, *ADMIN))
    assert generated["is_seeded"] is False, "a report a user generated is not an example"


def test_reg_17_lists_a_retired_model_and_a_newly_opened_finding(loaded_client):
    """REG-17, TR-37: the two change lists that had only negative assertions.

    `models_retired` and `findings_opened` were asserted exclusively as empty — `not
    changes["models_retired"]`, `== []`, `findings_opened == []` — and the seed shapes no
    retirements, so mutations that made the service always return either list empty passed all 22
    report tests. REG-17 says the section "lists exactly the differences", and three of the five
    lists were pinned to exact counts while these two were pinned to nothing.

    So: generate, then retire a model and raise a finding, then generate again and require both to
    appear, exactly once, with the right model and finding. Deliberately also checks what must *not*
    move, because a list that reported everything would satisfy a bare "is it non-empty".
    """
    h = login(loaded_client, *MRC)
    admin = login(loaded_client, *ADMIN)
    first = _generate(loaded_client, h)

    models = _get(loaded_client, admin, "/api/models")
    retirement = _get(loaded_client, admin, "/api/models/meta")["lifecycle_phases"][-1]
    victim = next(m for m in models if m["state"]["displayed_column"] != retirement)
    detail = _get(loaded_client, admin, f"/api/models/{victim['model_id']}")

    moved = loaded_client.post(f"/api/models/{victim['model_id']}/transition", headers=admin, json={
        "to_phase": retirement, "reason": "TR-37: exercise models_retired with content",
        "row_version": detail["model"]["row_version"]})
    assert moved.status_code == 200, moved.text

    raised = loaded_client.post("/api/findings", headers=admin, json={
        "finding_id": "F-9101", "model_id": "M-0012", "title": "TR-37 probe",
        "description": "Exercises findings_opened with content.", "severity": "Medium",
        "category": "Documentation", "status": "Open", "owner_id": "U-003",
        "raised_date": "2026-09-01", "due_date": "2026-12-31"})
    assert raised.status_code == 201, raised.text

    second = _generate(loaded_client, login(loaded_client, *MRC))
    changes = second["sections"]["changes_since"]
    assert changes["previous_report_id"] == first["report_id"]

    assert [r["model_id"] for r in changes["models_retired"]] == [victim["model_id"]], (
        f"the retired model must be listed exactly once: {changes['models_retired']}")
    assert [f["finding_id"] for f in changes["findings_opened"]] == ["F-9101"], (
        f"the newly opened finding must be listed exactly once: {changes['findings_opened']}")

    # And nothing else moved: no model was added or closed, so those lists stay empty. A list that
    # reported every model would pass a non-emptiness check and fail this one.
    assert changes["models_added"] == [], changes["models_added"]
    assert changes["findings_closed"] == [], changes["findings_closed"]


def test_reg_17_a_retirement_is_reported_once_not_twice(loaded_client):
    """REG-17: a retirement is a phase change *and* a retirement, which is one event.

    Found while closing TR-37 and raised by the test reviewer as an aside nothing recorded: a model
    moved into the retirement phase appears in `models_retired` and in `phase_changes`, so a reader
    counting "what changed" counts it twice. Asserted here as the behaviour that was chosen, so a
    future change to it is deliberate rather than silent.
    """
    h = login(loaded_client, *MRC)
    admin = login(loaded_client, *ADMIN)
    _generate(loaded_client, h)

    retirement = _get(loaded_client, admin, "/api/models/meta")["lifecycle_phases"][-1]
    models = _get(loaded_client, admin, "/api/models")
    victim = next(m for m in models if m["state"]["displayed_column"] != retirement)
    detail = _get(loaded_client, admin, f"/api/models/{victim['model_id']}")
    assert loaded_client.post(f"/api/models/{victim['model_id']}/transition", headers=admin, json={
        "to_phase": retirement, "reason": "REG-17: retirement counted once",
        "row_version": detail["model"]["row_version"]}).status_code == 200

    changes = _generate(loaded_client, login(loaded_client, *MRC))["sections"]["changes_since"]
    retired = [r["model_id"] for r in changes["models_retired"]]
    phase_changed = [r["model_id"] for r in changes["phase_changes"]]
    assert retired == [victim["model_id"]]
    assert phase_changed == [victim["model_id"]], (
        "a retirement is currently reported in both lists; if that changes, change this assertion "
        "deliberately rather than deleting it")
