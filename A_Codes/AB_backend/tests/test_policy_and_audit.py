"""Configuration and audit-trail tests (BRD §58, §69; criteria §76A CFG-01..CFG-04, AUD-01..AUD-04, GEN-01)."""
from decimal import Decimal

import pytest

from app.rules.policy_values import (
    PolicyValueError,
    check_key_specific,
    normalise_policy_value,
    parse_policy_value,
)
from tests.conftest import ADMIN, AUDITOR, EXECUTIVE, audit_count, login


# --- rules --------------------------------------------------------------------------

@pytest.mark.parametrize(("value", "value_type", "expected"), [
    ("60", "integer", 60),
    ("98", "percent", Decimal("98")),
    ("0.65", "decimal", Decimal("0.65")),
    ("ToR; MDD", "list", ["ToR", "MDD"]),
    ("Y", "boolean", True),
])
def test_parse_valid_values(value, value_type, expected):
    """CFG-01: each value type parses to its typed form."""
    assert parse_policy_value(value, value_type) == expected


@pytest.mark.parametrize(("value", "value_type", "message"), [
    ("sixty", "integer", "not a whole number"),
    ("101", "percent", "outside 0–100"),
    ("", "text", "cannot be blank"),
    (" ; ", "list", "at least one item"),
    ("maybe", "boolean", "not a yes/no value"),
])
def test_parse_invalid_values(value, value_type, message):
    """CFG-01: a value of the wrong type is refused with a human-readable message."""
    with pytest.raises(PolicyValueError, match=message):
        parse_policy_value(value, value_type)


def test_d5_breach_severity_rules_use_condition_equals_severity():
    """CFG-01, §81A D5: severity rules follow the `Name=months` shape of revalidation_frequencies.

    Only the shape is enforced today; the condition and severity vocabularies are settled in Phase 6
    with D3 and D7, at which point this check should validate against them.
    """
    good = "metric_fail=Medium; repeated_breach=High; high_tier_critical_metric_fail=Critical"
    assert parse_policy_value(good, "list") == [
        "metric_fail=Medium", "repeated_breach=High", "high_tier_critical_metric_fail=Critical"]
    check_key_specific("breach_severity_rules", parse_policy_value(good, "list"), {})

    for bad in ("repeated_breach", "=High", "repeated_breach=", " = "):
        with pytest.raises(PolicyValueError, match="Condition=Severity"):
            check_key_specific("breach_severity_rules", parse_policy_value(bad, "list"), {})


def test_d5_and_d10_decided_keys_are_configured(client):
    """§81A D5 and D10: the decided configuration ships in T12, not just in the decision log."""
    settings = {s["setting_key"]: s["value"] for s in
                client.get("/api/admin/policy", headers=login(client, *EXECUTIVE)).json()}

    # D5: the three shipped names kept, the two missing ones added, the renames never introduced.
    assert settings["repeated_breach_consecutive_periods"] == "2"
    assert settings["repeated_breach_window_fails"] == "3"
    assert settings["repeated_breach_window_periods"] == "4"
    assert settings["warning_escalation_periods"] == "3"
    assert "repeated_breach=High" in settings["breach_severity_rules"]
    for rejected in ("repeat_breach_consecutive", "repeat_breach_count", "repeat_breach_window",
                     "warn_escalation_periods"):
        assert rejected not in settings, f"{rejected} was the rejected name in §81A's proposal"

    # D10: all six statuses, and the three that count as open.
    assert settings["finding_statuses"].split("; ") == [
        "Open", "In Progress", "Deferred", "Closed", "Accepted Risk", "Rejected"]
    assert settings["finding_open_statuses"].split("; ") == ["Open", "In Progress", "Deferred"]
    assert "Accepted Risk" not in settings["finding_open_statuses"], "D10: an accepted risk is not open"


def test_list_values_are_normalised():
    """CFG-01: list settings are stored in a canonical form."""
    assert normalise_policy_value("ToR;MDD ;  Validation Report", "list") == "ToR; MDD; Validation Report"


# --- API ----------------------------------------------------------------------------

def _setting(client, headers, key):
    return next(s for s in client.get("/api/admin/policy", headers=headers).json() if s["setting_key"] == key)


def test_bootstrap_loaded_policy(client):
    """CFG-01: the configurable values the rules depend on are present after bootstrap."""
    settings = client.get("/api/admin/policy", headers=login(client, *EXECUTIVE)).json()
    keys = {s["setting_key"] for s in settings}
    assert {"tier_high_min", "weight_monitoring", "document_types"} <= keys


def test_admin_updates_policy_with_audit_before_and_after(client):
    """CFG-03, AUD-01: a policy edit is audited with before and after values and the stated reason."""
    admin = login(client, *ADMIN)
    current = _setting(client, admin, "reval_lead_days")
    resp = client.put("/api/admin/policy/reval_lead_days", headers=admin,
                      json={"value": "90", "row_version": current["row_version"], "reason": "Policy review"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["value"] == "90" and body["updated_by"] == "U-001"
    assert body["row_version"] == current["row_version"] + 1

    events = client.get("/api/audit", headers=admin, params={"entity": "policy_setting", "action": "update"}).json()
    event = next(e for e in events if e["entity_id"] == "reval_lead_days")
    assert event["before_json"]["value"] == "60"
    assert event["after_json"]["value"] == "90"
    assert event["reason"] == "Policy review"


def test_invalid_policy_value_is_rejected_with_message(client):
    """CFG-01: the API refuses a wrongly typed value and names the setting."""
    admin = login(client, *ADMIN)
    current = _setting(client, admin, "reval_lead_days")
    resp = client.put("/api/admin/policy/reval_lead_days", headers=admin,
                      json={"value": "sixty", "row_version": current["row_version"]})
    assert resp.status_code == 422
    assert resp.json()["detail"] == "Invalid value for 'reval_lead_days': 'sixty' is not a whole number."


def test_stale_policy_update_is_a_conflict(client):
    """CFG-03: a stale policy edit is refused as a conflict rather than overwriting."""
    admin = login(client, *ADMIN)
    current = _setting(client, admin, "due_soon_days")
    ok = client.put("/api/admin/policy/due_soon_days", headers=admin,
                    json={"value": "45", "row_version": current["row_version"]})
    assert ok.status_code == 200
    stale = client.put("/api/admin/policy/due_soon_days", headers=admin,
                       json={"value": "20", "row_version": current["row_version"]})
    assert stale.status_code == 409


def test_unknown_policy_key_is_404(client):
    """CFG-04: an unknown key returns not-found instead of creating a setting."""
    resp = client.put("/api/admin/policy/no_such_key", headers=login(client, *ADMIN),
                      json={"value": "1", "row_version": 1})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Policy setting 'no_such_key' does not exist."


def test_audit_trail_has_no_write_routes(client):
    """AUD-02: no application route updates or deletes an audit event."""
    admin = login(client, *ADMIN)
    event_id = client.get("/api/audit", headers=admin).json()[0]["event_id"]
    for method in ("post", "put", "patch", "delete"):
        resp = getattr(client, method)(f"/api/audit/{event_id}", headers=admin)
        assert resp.status_code in (404, 405), method


def test_audit_read_is_restricted(client):
    """AUD-04: audit access needs the audit-read permission; Executive is refused."""
    assert client.get("/api/audit", headers=login(client, *AUDITOR)).status_code == 200
    assert client.get("/api/audit", headers=login(client, *EXECUTIVE)).status_code == 403


def test_aud_01_a_refused_write_leaves_no_audit_event(loaded_client):
    """AUD-01: a write that is refused must leave both the record and the audit trail untouched.

    Seven tests prove an event appears after a *successful* write; none proved the other direction
    (review finding TR-01). Three refusal paths are checked, because they fail at different depths:
    a rule inside the service, a permission check, and a value that fails parsing.
    """
    admin = login(loaded_client, *ADMIN)
    # Counted per slice rather than in total: the endpoint caps a page at 1000 events, and a capped
    # page would make "unchanged" true by accident.
    creates = audit_count(loaded_client, admin, entity="model", action="create")
    policy_updates = audit_count(loaded_client, admin, entity="policy_setting", action="update")

    # 1. A business rule inside the service: segregation of duties on model creation.
    sod = loaded_client.post("/api/models", headers=admin, json={
        "model_id": "M-0400", "model_name": "SoD probe", "model_type": "Credit Risk", "model_subtype": "PD",
        "purpose": "Checks that a refused create writes nothing.", "business_line": "Business Banking",
        "owner_id": "U-003", "developer_id": "U-021", "validator_id": "U-003", "lifecycle_phase": "Validation",
        "version": "v1.0", "q_materiality": 2, "q_complexity": 2, "q_reliance": 2, "q_regulatory_use": 2})
    assert sod.status_code == 422
    assert loaded_client.get("/api/models/M-0400", headers=admin).status_code == 404
    assert audit_count(loaded_client, admin, entity="model", action="create") == creates
    assert audit_count(loaded_client, admin, model_id="M-0400") == 0

    # 2. A permission refusal: the Auditor may not edit policy.
    current = _setting(loaded_client, admin, "reval_lead_days")
    refused = loaded_client.put("/api/admin/policy/reval_lead_days", headers=login(loaded_client, *AUDITOR),
                                json={"value": "90", "row_version": current["row_version"]})
    assert refused.status_code == 403
    assert _setting(loaded_client, admin, "reval_lead_days")["value"] == current["value"]
    assert audit_count(loaded_client, admin, entity="policy_setting", action="update") == policy_updates

    # 3. A value that fails parsing.
    bad = loaded_client.put("/api/admin/policy/reval_lead_days", headers=admin,
                            json={"value": "sixty", "row_version": current["row_version"]})
    assert bad.status_code == 422
    assert _setting(loaded_client, admin, "reval_lead_days")["value"] == current["value"]
    assert audit_count(loaded_client, admin, entity="policy_setting", action="update") == policy_updates

    # Control: a permitted, valid write of the same setting *does* add exactly one event, so the
    # three assertions above are not passing because auditing is simply broken.
    ok = loaded_client.put("/api/admin/policy/reval_lead_days", headers=admin,
                           json={"value": "90", "row_version": current["row_version"]})
    assert ok.status_code == 200, ok.text
    assert audit_count(loaded_client, admin, entity="policy_setting", action="update") == policy_updates + 1


def test_aud_01_a_failed_audit_rolls_back_the_business_change(db_session):
    """AUD-01: the audit event and the business change share one transaction.

    Every service calls `audit.record(...)` and only then `db.commit()`, so a failure in the audit
    write must take the business change with it. Forced here by making `record` raise: without the
    shared transaction the policy value would already be committed.
    """
    from sqlalchemy import select

    from app.audit import service as audit
    from app.auth.security import Principal
    from app.models import PolicySetting
    from app.services import policy_service

    principal = Principal(user_id="U-001", role="Admin", full_name="Priya Raman")
    key = "reval_lead_days"

    with db_session() as db:
        setting = db.get(PolicySetting, key)
        original, version = setting.value, setting.row_version
    assert original != "90"

    boom = RuntimeError("audit storage unavailable")
    original_record = audit.record
    audit.record = lambda *a, **k: (_ for _ in ()).throw(boom)
    try:
        with db_session() as db:
            with pytest.raises(RuntimeError, match="audit storage unavailable"):
                policy_service.update_setting(db, principal, key, "90", version)
            db.rollback()
    finally:
        audit.record = original_record

    # A separate session: proves nothing reached the database, not merely that this session forgot.
    with db_session() as db:
        assert db.get(PolicySetting, key).value == original
        assert db.get(PolicySetting, key).row_version == version

    # Control: the same write succeeds once auditing works, so the test is not passing by accident.
    with db_session() as db:
        policy_service.update_setting(db, principal, key, "90", version)
    with db_session() as db:
        assert db.get(PolicySetting, key).value == "90"


def test_bootstrap_is_idempotent(db_session):
    """GEN-01: re-running bootstrap changes nothing and writes no further audit events."""
    from sqlalchemy import func, select

    from app.config import get_settings
    from app.models import AuditEvent
    from app.services.bootstrap_service import load_bootstrap

    with db_session() as s:
        before = s.scalar(select(func.count()).select_from(AuditEvent))
        load_bootstrap(s, get_settings().bootstrap_dir)
        after = s.scalar(select(func.count()).select_from(AuditEvent))
    assert after == before
