"""Command Center tie-out tests: every tile and chart must equal what its drill-down list shows.

Criteria: BRD §76A CC-01..CC-04 (superseding design.md REQ-CC-01..04).
"""
from decimal import Decimal

from tests.conftest import ADMIN, EXECUTIVE, login


def _get(client, h, path, **params):
    resp = client.get(path, headers=h, params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_tiles_tie_out_to_lists(loaded_client):
    """CC-01: every tile equals the count returned by its own drill-down list."""
    h = login(loaded_client, *EXECUTIVE)
    d = _get(loaded_client, h, "/api/dashboard/summary")
    t = d["tiles"]
    models = _get(loaded_client, h, "/api/models")
    assert t["total_models"] == len(models) == 79
    assert t["high_tier"] == len(_get(loaded_client, h, "/api/models", tier="High"))
    assert t["revalidation_queue"] == len(_get(loaded_client, h, "/api/models", column="Revalidation"))
    assert t["revalidation_overdue"] == len(_get(loaded_client, h, "/api/models", revalidation_status="Overdue"))
    assert t["in_production"] == len(_get(loaded_client, h, "/api/models", flag="in_production"))
    assert t["sod_breaches"] == len(_get(loaded_client, h, "/api/models", flag="sod_breach")) == 1  # M-0078
    assert t["models_with_document_gaps"] == len(_get(loaded_client, h, "/api/models", flag="doc_gaps")) == \
        len(_get(loaded_client, h, "/api/documents/completeness", missing_only=True))
    assert t["models_with_open_conditions"] == len(_get(loaded_client, h, "/api/models", flag="open_conditions"))

    findings = _get(loaded_client, h, "/api/findings")
    open_statuses = {"Open", "In Progress", "Deferred"}
    assert t["open_findings"] == sum(1 for f in findings if f["status"] in open_statuses)
    # CR-05: the tiles that open a model list must be counted in models, not findings.
    assert t["models_with_open_findings"] == len(_get(loaded_client, h, "/api/models", flag="open_findings"))
    assert t["models_with_overdue_findings"] == len(_get(loaded_client, h, "/api/models", flag="overdue_findings"))
    assert t["models_with_critical_overdue"] == len(_get(loaded_client, h, "/api/models", flag="critical_overdue"))
    overdue = _get(loaded_client, h, "/api/findings", overdue_only=True)
    assert t["overdue_findings"] == len(overdue)
    assert t["critical_overdue_findings"] == sum(1 for f in overdue if f["severity"] == "Critical")

    scores = [Decimal(m["state"]["score"]) for m in models if m["state"]["score"] is not None]
    assert t["scored_models"] == len(scores)
    assert t["portfolio_score"] == float(round(sum(scores) / len(scores), 1))


def test_distributions_sum_and_match_filters(loaded_client):
    """CC-02: distributions sum to the portfolio total, percentages to 100 ± 1, and match their filters."""
    h = login(loaded_client, *EXECUTIVE)
    d = _get(loaded_client, h, "/api/dashboard/summary")
    total = d["tiles"]["total_models"]
    for key in ("tier", "model_type", "stage", "business_line"):
        assert sum(x["count"] for x in d["distributions"][key]) == total, key
        assert abs(sum(x["pct"] for x in d["distributions"][key]) - 100) <= 1, key
    for x in d["distributions"]["stage"]:
        assert x["count"] == len(_get(loaded_client, h, "/api/models", column=x["key"])), x
    for x in d["distributions"]["model_type"]:
        assert x["count"] == len(_get(loaded_client, h, "/api/models", model_type=x["key"])), x
    sev = {x["key"]: x["count"] for x in d["distributions"]["open_findings_by_severity"]}
    assert sum(sev.values()) == d["tiles"]["open_findings"]
    bands = {x["key"]: x["count"] for x in d["distributions"]["score_band"]}
    # Band keys carry no numbers — the boundaries are policy (CR-01).
    assert bands["below_warn"] == len(_get(loaded_client, h, "/api/models", flag="scored_below_warn"))
    assert sum(bands.values()) == d["tiles"]["scored_models"]


def test_revalidation_timeline_is_the_revalidation_column(loaded_client):
    """CC-03: the timeline contains exactly the Revalidation column, most urgent first."""
    h = login(loaded_client, *EXECUTIVE)
    d = _get(loaded_client, h, "/api/dashboard/summary")
    column = {m["model_id"] for m in _get(loaded_client, h, "/api/models", column="Revalidation")}
    timeline = d["revalidation_timeline"]
    assert {x["model_id"] for x in timeline} == column
    days = [x["days_to_due"] for x in timeline]
    assert days == sorted(days)  # most urgent first
    assert timeline[0]["model_id"] == "M-0042" and timeline[0]["status"] == "Overdue"


def test_insights_are_generated_from_data(loaded_client):
    """CC-04: insight counts equal the underlying data and every insight links to a real model."""
    h = login(loaded_client, *EXECUTIVE)
    d = _get(loaded_client, h, "/api/dashboard/summary")
    rules = d["insight_counts_by_rule"]
    assert rules["sod_breach"] == 1 and rules["revalidation_overdue"] == d["tiles"]["revalidation_overdue"]
    assert rules["critical_finding_overdue"] == d["tiles"]["critical_overdue_findings"]
    shown = d["insights"]
    assert shown[0]["rule"] == "sod_breach" and shown[0]["model_id"] == "M-0078"
    assert [i["severity"] for i in shown] == sorted((i["severity"] for i in shown),
                                                    key=["Critical", "High", "Medium", "Low"].index)
    models = {m["model_id"] for m in _get(loaded_client, h, "/api/models")}
    assert all(i["model_id"] in models and i["link"] == f"/models/{i['model_id']}" for i in shown)
    assert len(shown) <= 10 and d["insight_count"] >= len(shown)


def test_insight_disappears_when_resolved(loaded_client):
    """CC-04 (TC-CC-04-2): close the overdue Critical finding and its insight goes away."""
    admin = login(loaded_client, *ADMIN)
    before = _get(loaded_client, admin, "/api/dashboard/summary")["insight_counts_by_rule"]["critical_finding_overdue"]
    f = next(x for x in _get(loaded_client, admin, "/api/findings", model_id="M-0012", overdue_only=True)
             if x["severity"] == "Critical")
    loaded_client.patch(f"/api/findings/{f['finding_id']}", headers=admin,
                        json={"status": "Closed", "row_version": f["row_version"], "reason": "Remediated"})
    after = _get(loaded_client, admin, "/api/dashboard/summary")["insight_counts_by_rule"]["critical_finding_overdue"]
    assert after == before - 1


def test_cr_05_each_severity_bar_drills_to_its_own_models(loaded_client):
    """CC-01, CC-02: every severity bar opens the models holding findings of that severity.

    Regression for CR-05: `linkFor` discarded the bar key, so clicking "Critical" listed every model
    with any open finding, and `/api/models` had no severity filter at all.
    """
    h = login(loaded_client, *EXECUTIVE)
    d = _get(loaded_client, h, "/api/dashboard/summary")
    sev = {x["key"]: x["count"] for x in d["distributions"]["open_findings_by_severity"]}
    assert sum(sev.values()) == d["tiles"]["open_findings"]

    open_statuses = set(_get(loaded_client, h, "/api/models/meta")["finding_open_statuses"])
    seen_models: list[set[str]] = []
    for severity, finding_count in sev.items():
        models = _get(loaded_client, h, "/api/models", finding_severity=severity)
        ids = {m["model_id"] for m in models}
        seen_models.append(ids)
        # Every model returned really holds an open finding of that severity...
        for model_id in ids:
            found = _get(loaded_client, h, "/api/findings", model_id=model_id)
            assert any(f["severity"] == severity and f["status"] in open_statuses for f in found), (severity, model_id)
        # ...and the list is never larger than the number of findings behind the bar.
        assert len(ids) <= finding_count, (severity, len(ids), finding_count)

    # The bars no longer all open the same list.
    assert len({frozenset(s) for s in seen_models}) > 1, "each severity must drill to a different set"

    bad = loaded_client.get("/api/models", headers=h, params={"finding_severity": "Severe"})
    assert bad.status_code == 422 and "Allowed:" in bad.json()["detail"]


def test_cr_01_score_bands_come_from_policy(loaded_client):
    """SCR-04, CFG-02, CC-02: the R8 band boundaries are policy, not literals.

    Regression for CR-01: 60 and 80 were hard-coded in governance_view, dashboard_service and three
    frontend files, so the bands, their drill-downs and the score pill colours could not be changed.
    """
    admin = login(loaded_client, *ADMIN)

    def put(key, value):
        s = next(x for x in _get(loaded_client, admin, "/api/admin/policy") if x["setting_key"] == key)
        return loaded_client.put(f"/api/admin/policy/{key}", headers=admin,
                                 json={"value": value, "row_version": s["row_version"]})

    meta = _get(loaded_client, admin, "/api/models/meta")
    assert (meta["score_band_warn_min"], meta["score_band_good_min"]) == (60, 80)
    assert meta["score_band_labels"] == {
        "below_warn": "Below 60", "warn_to_good": "60 – 80", "good_plus": "80 and above"}

    before = {x["key"]: x["count"] for x in
              _get(loaded_client, admin, "/api/dashboard/summary")["distributions"]["score_band"]}

    # Raise the amber floor: models between the old and new floor move down a band.
    assert put("score_band_warn_min", "75").status_code == 200
    after = {x["key"]: x["count"] for x in
             _get(loaded_client, admin, "/api/dashboard/summary")["distributions"]["score_band"]}
    assert after["below_warn"] > before["below_warn"], (before, after)
    assert sum(after.values()) == sum(before.values())

    # The drill-down follows the same boundary, and the labels restate it.
    assert after["below_warn"] == len(_get(loaded_client, admin, "/api/models", flag="scored_below_warn"))
    assert _get(loaded_client, admin, "/api/models/meta")["score_band_labels"]["below_warn"] == "Below 75"

    # The boundaries must stay ordered and inside 0-100.
    assert put("score_band_warn_min", "90").status_code == 422
    assert put("score_band_good_min", "70").status_code == 422
    assert put("score_band_good_min", "140").status_code == 422


def test_cr_02_renaming_the_monitoring_phase_does_not_break_the_dashboard(loaded_client):
    """CC-01, CFG-02: the Command Center survives a renamed lifecycle phase.

    Regression for CR-02: `policy.phases.index("Monitoring")` was unguarded, so renaming the phase
    made GET /api/dashboard/summary raise ValueError and the Command Center stopped loading.
    """
    admin = login(loaded_client, *ADMIN)

    def put(key, value):
        s = next(x for x in _get(loaded_client, admin, "/api/admin/policy") if x["setting_key"] == key)
        return loaded_client.put(f"/api/admin/policy/{key}", headers=admin,
                                 json={"value": value, "row_version": s["row_version"]})

    phases = _get(loaded_client, admin, "/api/models/meta")["lifecycle_phases"]
    renamed = "; ".join("In Use" if p == "Monitoring" else p for p in phases)
    # Before: models sit in Monitoring, so R3 displaces some of them into the derived column.
    before = _get(loaded_client, admin, "/api/dashboard/summary")
    assert "Revalidation" in [x["key"] for x in before["distributions"]["stage"]]

    # Both settings must move together, and the order is enforced (see the paired policy rule).
    assert put("lifecycle_phases", renamed).status_code == 422
    assert put("monitoring_phase", "In Use").status_code == 422, "the phase does not exist yet"

    assert put("monitoring_phase", "Nonexistent Phase").status_code == 422
    assert put("lifecycle_phases", renamed).status_code == 422
    # Rename in a consistent order: add the new phase, point at it, then drop the old one. The end
    # state has no "Monitoring" phase at all, which is what made the old unguarded .index() raise.
    assert put("lifecycle_phases", "; ".join([*phases, "In Use"])).status_code == 200
    assert put("monitoring_phase", "In Use").status_code == 200
    assert put("lifecycle_phases", renamed).status_code == 200
    assert "Monitoring" not in _get(loaded_client, admin, "/api/models/meta")["lifecycle_phases"]

    # The dashboard still renders — this is the regression. It previously raised ValueError -> 500.
    summary = loaded_client.get("/api/dashboard/summary", headers=admin)
    assert summary.status_code == 200, summary.text
    d = summary.json()
    # No model occupies "In Use", so nothing is displaced and the derived column drops out of the
    # distribution. The figures must still be coherent.
    stage = d["distributions"]["stage"]
    assert "Revalidation" not in [x["key"] for x in stage]
    assert sum(x["count"] for x in stage) == d["tiles"]["total_models"]

    # The derived column is still ordered against the configured phase, wherever it sits.
    meta = _get(loaded_client, admin, "/api/models/meta")["displayed_columns"]
    assert meta.index("Revalidation") == meta.index("In Use") + 1


def test_unknown_flag_rejected(loaded_client):
    resp = loaded_client.get("/api/models", headers=login(loaded_client, *EXECUTIVE), params={"flag": "everything"})
    assert resp.status_code == 422 and "Allowed:" in resp.json()["detail"]
