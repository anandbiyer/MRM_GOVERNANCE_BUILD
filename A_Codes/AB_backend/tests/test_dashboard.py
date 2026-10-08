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

    The first version asserted soundness (every model listed really holds such a finding) and an
    upper bound (no more models than findings), but never **completeness** — so a filter returning
    half its models stayed green, which is the same class of defect CR-05 itself was (TR-26,
    verified by mutation: 178 passed). The set is now compared for equality against the models
    derived independently from `/api/findings?severity=…`, which is a different code path
    (`finding_service.list_findings`) from the one under test (`governance_view`'s model filter).
    """
    h = login(loaded_client, *EXECUTIVE)
    d = _get(loaded_client, h, "/api/dashboard/summary")
    sev = {x["key"]: x["count"] for x in d["distributions"]["open_findings_by_severity"]}
    assert sum(sev.values()) == d["tiles"]["open_findings"]

    open_statuses = set(_get(loaded_client, h, "/api/models/meta")["finding_open_statuses"])
    seen_models: list[set[str]] = []
    for severity, finding_count in sev.items():
        ids = {m["model_id"] for m in _get(loaded_client, h, "/api/models", finding_severity=severity)}
        seen_models.append(ids)

        # The models that *should* be listed, derived from the findings themselves through a
        # different service than the one under test. Set equality, so a filter that drops models is
        # caught as well as one that adds them — the upper bound alone was not enough (TR-26).
        expected = {f["model_id"] for f in _get(loaded_client, h, "/api/findings", severity=severity)
                    if f["status"] in open_statuses}
        assert ids == expected, (
            f"{severity}: missing {sorted(expected - ids)}, unexpected {sorted(ids - expected)}")
        assert expected, f"{severity} has a bar but no open findings behind it"

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
    # Every setting naming the old phase has to move, not just this one: the guard now covers all of
    # them, because CR-21 showed the same rename silently disabling a different rule.
    assert put("lifecycle_phases", renamed).status_code == 422, "validation_data_required_from_phase still names it"
    assert put("validation_data_required_from_phase", "In Use").status_code == 200
    assert put("production_phases", "In Use; Reg/Audit").status_code == 200
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


def test_cr_21_renaming_a_phase_does_not_empty_the_required_document_list(loaded_client):
    """DOC-20, CFG-01, SCR-02: renaming a lifecycle phase must not silently empty the required
    document list — and must not raise every governance score as a side effect.

    Regression for CR-21, which is CR-02's failure mode one file across. `required_types` picked the
    required-document set by comparing against the literal phase names "Implementation",
    "Validation" and "Development", while `lifecycle_phases` is an editable T12 list. Renaming
    Implementation made `"Implementation" in phases` false, so the production band was skipped and
    the dict lookup for "Monitoring" returned `[]`: `missing_documents` emptied, the Documentation
    component became not-applicable, **its 25% was rescaled away and every score rose**, and the
    completeness tile and insight stopped firing. Silently — no exception anywhere.

    The failure direction is what makes this High. A governance system may under-report a score by
    accident; it must not over-report one.
    """
    admin = login(loaded_client, *ADMIN)

    def put(key, value):
        s = next(x for x in _get(loaded_client, admin, "/api/admin/policy") if x["setting_key"] == key)
        return loaded_client.put(f"/api/admin/policy/{key}", headers=admin,
                                 json={"value": value, "row_version": s["row_version"]})

    comp = _get(loaded_client, admin, "/api/documents/completeness")
    target = next(c for c in comp if c["required"] and c["lifecycle_phase"] == "Monitoring")
    required_before, model_id = target["required"], target["model_id"]
    before = _get(loaded_client, admin, f"/api/models/{model_id}")["score"]
    doc_before = next(c for c in before["components"] if c["key"] == "documentation")
    assert doc_before["score"] is not None, "the fixture must have an applicable Documentation component"

    phases = _get(loaded_client, admin, "/api/models/meta")["lifecycle_phases"]
    assert "Implementation" in phases
    renamed = "; ".join("Rollout" if p == "Implementation" else p for p in phases)

    # Dropping a phase another setting names is refused from the list side, as CR-02 established for
    # `monitoring_phase`. Two settings name Implementation, so both have to move first.
    assert put("lifecycle_phases", renamed).status_code == 422
    assert put("lifecycle_phases", "; ".join([*phases, "Rollout"])).status_code == 200
    for key in ("mrc_required_from_phase", "required_docs_production_from_phase"):
        assert put(key, "Rollout").status_code == 200, key
    assert put("lifecycle_phases", renamed).status_code == 200
    assert "Implementation" not in _get(loaded_client, admin, "/api/models/meta")["lifecycle_phases"]

    # The regression: the model is still in Monitoring, so its required set is unchanged.
    after = next(c for c in _get(loaded_client, admin, "/api/documents/completeness")
                 if c["model_id"] == model_id)
    assert after["required"] == required_before, after
    assert after["missing"] == target["missing"], after

    # And the Documentation component is still applicable, so its weight is not rescaled away and
    # the overall score has not drifted upwards.
    doc_after = next(c for c in _get(loaded_client, admin, f"/api/models/{model_id}")["score"]["components"]
                     if c["key"] == "documentation")
    assert doc_after["score"] == doc_before["score"], doc_after
    assert doc_after["effective_weight"] == doc_before["effective_weight"], doc_after

    # The portfolio-level symptom: completeness gaps do not vanish.
    gaps = _get(loaded_client, admin, "/api/documents/completeness?missing_only=true")
    assert gaps, "renaming a phase must not empty every model's required-document list"
