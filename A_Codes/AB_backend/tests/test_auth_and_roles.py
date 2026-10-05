"""Role model and access-control tests (BRD §5, §59; criteria §76A SEC-01..SEC-06, AUD-01)."""
from app.auth.roles import ROLE_PERMISSIONS, Permission, Role, has_permission
from tests.conftest import ADMIN, AUDITOR, EXECUTIVE, VALIDATOR, login

READ_ONLY_ROLES = (Role.AUDITOR, Role.EXECUTIVE)
WRITE_PERMISSIONS = set(Permission) - {Permission.READ, Permission.AUDIT_READ}


def test_every_role_has_a_permission_set():
    """SEC-01: every declared role has a permission set."""
    assert set(ROLE_PERMISSIONS) == set(Role)


def test_auditor_and_executive_are_read_only():
    """SEC-02: Auditor and Executive hold no write permission at all."""
    for role in READ_ONLY_ROLES:
        assert not (ROLE_PERMISSIONS[role] & WRITE_PERMISSIONS), role


def test_unknown_role_has_no_permissions():
    """SEC-01: an unrecognised role name grants nothing, not even read."""
    assert not has_permission("Superuser", Permission.READ)


def test_login_and_me(client):
    """SEC-01: the session reports exactly the permissions of the signed-in role."""
    headers = login(client, *VALIDATOR)
    me = client.get("/api/auth/me", headers=headers).json()
    assert me["user_id"] == "U-014"
    assert me["role"] == "Validator"
    assert "document:upload" in me["permissions"]
    assert "policy:edit" not in me["permissions"]


def test_login_with_role_user_does_not_hold_is_refused(client):
    """SEC-04: signing in with a role the user does not hold is refused."""
    resp = client.post("/api/auth/login", json={"user_id": "U-041", "role": "Admin"})
    assert resp.status_code == 403
    assert "does not hold the role 'Admin'" in resp.json()["detail"]


def test_multi_role_user_can_log_in_as_either_role(client):
    """SEC-04: a user holding two roles may sign in as either, one at a time."""
    for role in ("MRC Member", "Executive"):
        assert client.get("/api/auth/me", headers=login(client, "U-040", role)).json()["role"] == role


def test_missing_or_bad_token_is_401(client):
    """SEC-06: a missing or malformed token is refused as unauthenticated."""
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer nonsense"}).status_code == 401


def test_dev_users_lists_active_users(client):
    """SEC-04: the development sign-in list offers only active users."""
    users = client.get("/api/auth/dev-users").json()
    assert {"U-001", "U-041"} <= {u["user_id"] for u in users}


def test_auditor_cannot_edit_policy_and_nothing_changes(client):
    """SEC-02, CFG-03: a refused policy write leaves the stored value untouched."""
    before = {s["setting_key"]: s for s in client.get("/api/admin/policy", headers=login(client, *ADMIN)).json()}
    resp = client.put("/api/admin/policy/reval_lead_days", headers=login(client, *AUDITOR),
                      json={"value": "90", "row_version": before["reval_lead_days"]["row_version"]})
    assert resp.status_code == 403
    after = {s["setting_key"]: s for s in client.get("/api/admin/policy", headers=login(client, *ADMIN)).json()}
    assert after["reval_lead_days"]["value"] == "60"


def test_executive_cannot_create_users(client):
    """SEC-02: a read-only role cannot create users."""
    resp = client.post("/api/users", headers=login(client, *EXECUTIVE), json={
        "user_id": "U-900", "full_name": "Test Person", "email": "t.person@demo-bank.example", "roles": ["Validator"],
    })
    assert resp.status_code == 403


def test_admin_creates_user_with_audit_event(client):
    """AUD-01: creating a user writes exactly one audit event carrying the acting user and role."""
    admin = login(client, *ADMIN)
    resp = client.post("/api/users", headers=admin, json={
        "user_id": "U-900", "full_name": "Test Person", "email": "t.person@demo-bank.example",
        "roles": ["Validator", "Model Developer"],
    })
    assert resp.status_code == 201, resp.text
    assert resp.json()["roles"] == ["Model Developer", "Validator"]
    events = client.get("/api/audit", headers=admin, params={"entity": "app_user", "action": "create"}).json()
    created = [e for e in events if e["entity_id"] == "U-900"]
    assert len(created) == 1
    assert created[0]["user_id"] == "U-001" and created[0]["role"] == "Admin"


def test_create_user_with_unknown_role_is_rejected(client):
    """SEC-01: a user cannot be created with a role outside the role model."""
    resp = client.post("/api/users", headers=login(client, *ADMIN), json={
        "user_id": "U-901", "full_name": "Test Person", "email": "t2@demo-bank.example", "roles": ["Superuser"],
    })
    assert resp.status_code == 422
    assert "Unknown role(s): Superuser" in resp.json()["detail"]


def test_deactivated_user_token_stops_working(client, db_session):
    """SEC-05: deactivating a user invalidates an already-issued token on its next use."""
    headers = login(client, *VALIDATOR)
    from app.models import AppUser
    with db_session() as s:
        s.get(AppUser, "U-014").active = False
        s.commit()
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def _set_roles(db_session, user_id: str, roles: list[str]) -> None:
    """Change a user's roles the way a T01 re-import does, rather than editing rows by hand."""
    from app.models import AppUser
    from app.services import user_service

    with db_session() as s:
        u = s.get(AppUser, user_id)
        user_service.upsert_user(s, None, user_id=u.user_id, full_name=u.full_name, email=u.email,
                                 business_line=u.business_line, roles=roles, active=u.active)
        s.commit()


def test_sec_05_removing_a_role_invalidates_a_token_for_that_role(client, db_session):
    """SEC-05: *removing a role* invalidates an issued token — a different check from deactivation.

    The token carries a role, which must be re-validated against the user's current roles on every
    request. Only the deactivation half was tested (review finding TR-04). The user stays active
    here, so an `active` check alone would let the old token through.
    """
    headers = login(client, *VALIDATOR)  # U-014, whose only role is Validator
    assert client.get("/api/auth/me", headers=headers).status_code == 200

    _set_roles(db_session, "U-014", ["Model Developer"])

    refused = client.get("/api/auth/me", headers=headers)
    assert refused.status_code == 403, refused.text
    assert "no longer holds the role 'Validator'" in refused.json()["detail"]

    # Still active — so this was the role check, not the active check.
    assert client.get("/api/users/U-014", headers=login(client, *ADMIN)).json()["active"] is True
    # And the user can sign in again under the role they now hold.
    assert client.get("/api/auth/me", headers=login(client, "U-014", "Model Developer")).status_code == 200


def test_sec_05_removing_one_role_leaves_tokens_for_the_others(client, db_session):
    """SEC-05: the check is per role, not per user — U-040 holds MRC Member and Executive."""
    mrc_token = login(client, "U-040", "MRC Member")
    exec_token = login(client, "U-040", "Executive")
    assert client.get("/api/auth/me", headers=mrc_token).status_code == 200
    assert client.get("/api/auth/me", headers=exec_token).status_code == 200

    _set_roles(db_session, "U-040", ["Executive"])

    assert client.get("/api/auth/me", headers=mrc_token).status_code == 403
    assert client.get("/api/auth/me", headers=exec_token).status_code == 200, "the retained role still works"
    assert client.get("/api/auth/me", headers=exec_token).json()["role"] == "Executive"
