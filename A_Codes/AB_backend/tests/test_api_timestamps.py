"""Every timestamp the API emits carries a UTC offset (plan BL.28, review findings MP-15/MP-16).

No acceptance criterion covers this, which is part of the problem and is recorded with the other
untraced coverage in §76A.14. The defect it guards against is user-visible: the Model 360 Score tab
showed `10/7/2026` while the History tab showed `10/8/2026` for events minutes apart, because
`score.calculated_at` is built in Python as `datetime.now(UTC)` and so serialised with a `Z`, while
`occurred_at`, `changed_at`, `recorded_at` and `uploaded_at` come from the database default and were
serialised **naive** — which JavaScript parses as *local*, rendering a UTC wall-clock time as though
it were local and landing on the previous or next day.

The columns are already `DateTime(timezone=True)`. The naiveness is a SQLite artefact: SQLite has no
timezone type, so `func.now()` returns a string that SQLAlchemy parses without a zone. PostgreSQL —
the system of record (§49) — returns these aware. So the fix belongs at the serialisation boundary,
where it makes dev behave like production and is a no-op on PostgreSQL.

A date-only field must NOT acquire a time: `effective_date`, `due_date` and the rest are calendar
days, and labelling them with a zone would reintroduce the one-day shift from the other direction.
"""
import re
from datetime import UTC, datetime

from tests.conftest import ADMIN, AUDITOR, login

# An ISO timestamp with an explicit offset: "...T12:00:00Z" or "...T12:00:00+00:00".
AWARE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
NAIVE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$")
DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _timestamps(node, path="") -> list[tuple[str, str]]:
    """Every (json path, value) in the response that looks like a datetime, aware or not."""
    found = []
    if isinstance(node, dict):
        for k, v in node.items():
            found += _timestamps(v, f"{path}.{k}")
    elif isinstance(node, list):
        for n, v in enumerate(node[:5]):  # five of each collection is plenty and keeps it quick
            found += _timestamps(v, f"{path}[{n}]")
    elif isinstance(node, str) and (AWARE.match(node) or NAIVE.match(node)):
        found.append((path, node))
    return found


def test_bl_28_every_api_timestamp_is_timezone_aware(loaded_client):
    """A naive timestamp is the bug: the browser reads it as local time and shifts the day."""
    h = login(loaded_client, *ADMIN)
    model_id = loaded_client.get("/api/models", headers=h).json()[0]["model_id"]
    endpoints = [
        "/api/models", f"/api/models/{model_id}", "/api/dashboard/summary", "/api/findings",
        "/api/validations", "/api/approvals", "/api/documents", "/api/documents/batches",
        "/api/imports/batches", "/api/admin/policy", "/api/users",
    ]
    checked, naive = 0, []
    for ep in endpoints:
        resp = loaded_client.get(ep, headers=login(loaded_client, *ADMIN))
        assert resp.status_code == 200, f"{ep}: {resp.text}"
        for path, value in _timestamps(resp.json(), ep):
            checked += 1
            if not AWARE.match(value):
                naive.append(f"{path} = {value}")
    audit = loaded_client.get("/api/audit", headers=login(loaded_client, *AUDITOR)).json()
    for path, value in _timestamps(audit, "/api/audit"):
        checked += 1
        if not AWARE.match(value):
            naive.append(f"{path} = {value}")

    assert checked > 10, f"only {checked} timestamps seen — the sweep is not reaching the data"
    assert not naive, (
        f"{len(naive)} of {checked} API timestamps have no timezone, so a browser will read them as "
        f"local and can show the wrong calendar day (MP-15):\n  " + "\n  ".join(sorted(naive)[:12])
    )


def test_bl_28_a_date_only_field_does_not_acquire_a_time(loaded_client):
    """The other direction of the same defect: a calendar day must stay a calendar day."""
    h = login(loaded_client, *ADMIN)
    model_id = loaded_client.get("/api/models", headers=h).json()[0]["model_id"]
    detail = loaded_client.get(f"/api/models/{model_id}", headers=h).json()
    for field in ("go_live_date", "last_validation_date"):
        value = detail["model"].get(field)
        if value is not None:
            assert DATE_ONLY.match(value), f"{field} must stay a calendar day, got {value!r}"

    findings = loaded_client.get("/api/findings", headers=h).json()
    assert findings, "the fixture must have findings"
    for f in findings[:5]:
        for field in ("raised_date", "due_date", "closed_date"):
            if f.get(field) is not None:
                assert DATE_ONLY.match(f[field]), f"finding {field} must stay a calendar day, got {f[field]!r}"


def test_bl_28_an_aware_value_is_left_alone(loaded_client):
    """`calculated_at` was already aware; normalising must not shift it."""
    h = login(loaded_client, *ADMIN)
    model_id = loaded_client.get("/api/models", headers=h).json()[0]["model_id"]
    calculated = loaded_client.get(f"/api/models/{model_id}", headers=h).json()["score"]["calculated_at"]
    assert AWARE.match(calculated), calculated
    parsed = datetime.fromisoformat(calculated)
    assert parsed.utcoffset() == UTC.utcoffset(None), f"{calculated} is not UTC"
