"""Pure business-rule tests.

Each test names the BRD §76A acceptance criteria it verifies, so
`grep -rn "TIR-01" tests/` answers "what proves this criterion?".
Function names additionally keep the superseded design.md §12 condition IDs (TC-*); BRD §76A.13 maps
the two sets.
"""
from datetime import date
from decimal import Decimal

import pytest

from app.rules import governance_rules, model_rules, revalidation, score, tiering

FREQ = {"Monthly": 1, "Quarterly": 3, "Semi-annual": 6, "Annual": 12, "Biennial": 24}
TODAY = date(2026, 9, 30)


# --- R1 tiering ------------------------------------------------------------------------

@pytest.mark.parametrize(("answers", "tier"), [((3, 3, 2, 2), "High"), ((3, 2, 2, 2), "Medium"),
                                               ((2, 2, 2, 1), "Medium"), ((2, 2, 1, 1), "Low")])
def test_tc_tir_01_1_tier_bands(answers, tier):
    """TIR-01: tier score is the sum of the four answers and the band follows the configured minima."""
    result = tiering.calculate_tier(dict(zip(tiering.TIERING_QUESTIONS, answers)), high_min=10, medium_min=7)
    assert result.tier == tier
    assert result.score == sum(answers)


def test_tier_thresholds_come_from_policy():
    """TIR-01, CFG-01: the same answers give a different tier when the policy minimum changes."""
    answers = dict(zip(tiering.TIERING_QUESTIONS, (3, 3, 2, 2)))
    assert tiering.calculate_tier(answers, high_min=11, medium_min=7).tier == "Medium"


@pytest.mark.parametrize("bad", [0, 4, None])
def test_tc_tir_01_2_answers_must_be_1_to_3(bad):
    """TIR-02: a tiering answer outside 1–3 is refused."""
    answers = {"q_materiality": bad, "q_complexity": 2, "q_reliance": 2, "q_regulatory_use": 2}
    assert tiering.validate_answers(answers)


def test_override_replaces_but_keeps_calculated():
    """TIR-05: the override becomes the effective tier; the calculated tier is retained."""
    assert tiering.effective_tier("High", "Medium") == "Medium"
    assert tiering.effective_tier("High", None) == "High"


# --- R2–R4 revalidation ------------------------------------------------------------------

@pytest.mark.parametrize(("freq", "expected"), [("Monthly", date(2025, 9, 30)), ("Quarterly", date(2025, 11, 30)),
                                                ("Semi-annual", date(2026, 2, 28)), ("Annual", date(2026, 8, 31)),
                                                ("Biennial", date(2027, 8, 31))])
def test_tc_inv_04_1_due_dates_clamp_month_end(freq, expected):
    """VAL-02: next due date = last validation + frequency, month-end clamped."""
    assert revalidation.next_due_date(date(2025, 8, 31), freq, FREQ) == expected


def test_add_months_mid_month_and_leap_year():
    """VAL-02: mid-month dates are preserved and leap years clamp correctly."""
    assert revalidation.add_months(date(2025, 1, 15), 1) == date(2025, 2, 15)
    assert revalidation.add_months(date(2024, 2, 29), 12) == date(2025, 2, 28)
    assert revalidation.add_months(date(2025, 1, 30), 1) == date(2025, 2, 28)


def test_tc_inv_04_2_no_last_validation_no_due_date():
    """VAL-03: no last validation date means no due date."""
    assert revalidation.next_due_date(None, "Annual", FREQ) is None


@pytest.mark.parametrize(("days", "status"), [(-1, "Overdue"), (0, "Due Soon"), (30, "Due Soon"), (31, "Scheduled")])
def test_revalidation_status(days, status):
    """VAL-04: Scheduled / Due Soon / Overdue classification from the configured window."""
    from datetime import timedelta
    state = revalidation.revalidation_state(TODAY + timedelta(days=days), TODAY, due_soon_days=30)
    assert state.status == status and state.days_to_due == days


def test_tc_ops_01_1_revalidation_column_uses_lead_time():
    """LIF-02: a Monitoring model inside the lead time shows in Revalidation; other phases never do."""
    from datetime import timedelta
    assert revalidation.displayed_column("Monitoring", TODAY + timedelta(days=60), TODAY, 60, "Monitoring") == "Revalidation"
    assert revalidation.displayed_column("Monitoring", TODAY + timedelta(days=61), TODAY, 60, "Monitoring") == "Monitoring"
    assert revalidation.displayed_column("Monitoring", TODAY - timedelta(days=5), TODAY, 60, "Monitoring") == "Revalidation"
    assert revalidation.displayed_column("Reg/Audit", TODAY - timedelta(days=5), TODAY, 60, "Monitoring") == "Reg/Audit"


def test_lif_02_monitoring_phase_comes_from_policy():
    """LIF-02, CFG-01: R3 follows the configured monitoring phase, not the literal "Monitoring"."""
    from datetime import timedelta
    due = TODAY + timedelta(days=10)
    # Renamed phase: the new name is displaced, the old name is not.
    assert revalidation.displayed_column("In Use", due, TODAY, 60, "In Use") == "Revalidation"
    assert revalidation.displayed_column("Monitoring", due, TODAY, 60, "In Use") == "Monitoring"


def test_displayed_columns_inserts_revalidation_after_the_monitoring_phase():
    """LIF-02: the column order used by the Operations Board and the Command Center."""
    phases = ["Initiation", "Development", "Monitoring", "Retirement"]
    assert revalidation.displayed_columns(phases, "Monitoring") == [
        "Initiation", "Development", "Monitoring", "Revalidation", "Retirement"]
    # A renamed phase keeps the column in the right place.
    renamed = ["Initiation", "In Use", "Retirement"]
    assert revalidation.displayed_columns(renamed, "In Use") == [
        "Initiation", "In Use", "Revalidation", "Retirement"]


def test_displayed_columns_degrades_when_the_monitoring_phase_is_absent():
    """CR-02: an inconsistent policy must not raise — the old code called .index() unguarded, which
    turned a renamed phase into an unhandled 500 on the Command Center."""
    phases = ["Initiation", "Development", "Retirement"]
    assert revalidation.displayed_columns(phases, "Monitoring") == [*phases, "Revalidation"]
    assert revalidation.displayed_columns([], "Monitoring") == ["Revalidation"]


# --- R5 segregation of duties and phase requirements -------------------------------------

def test_tc_inv_03_sod():
    """INV-03: a validator who is also the owner or the developer is refused; a third person is not."""
    assert "also the model owner" in model_rules.sod_violation("M-0012", "U-1", "U-2", "U-1")
    assert "also the model developer" in model_rules.sod_violation("M-0012", "U-1", "U-2", "U-2")
    assert model_rules.sod_violation("M-0012", "U-1", "U-2", "U-3") is None
    assert model_rules.sod_violation("M-0012", "U-1", "U-2", None) is None


REQ = model_rules.PhaseRequirements(
    phases=["Initiation", "Development", "Validation", "Implementation", "Monitoring", "Reg/Audit", "Retirement"],
    validator_from="Validation", validation_data_from="Monitoring")


def test_phase_requirements():
    """INV-05: mandatory data for the target phase is enforced, and only from the phase it applies to."""
    errs = dict(model_rules.field_errors({"lifecycle_phase": "Monitoring"}, REQ, TODAY))
    assert {"validator_id", "go_live_date", "revalidation_frequency", "last_validation_date"} <= errs.keys()
    assert model_rules.field_errors({"lifecycle_phase": "Development"}, REQ, TODAY) == []
    assert model_rules.field_errors({"lifecycle_phase": "Retirement"}, REQ, TODAY) == []


def test_last_validation_date_not_in_future():
    """INV-05: a last validation date after the business date is refused."""
    fields = {"lifecycle_phase": "Development", "last_validation_date": date(2026, 10, 1)}
    assert dict(model_rules.field_errors(fields, REQ, TODAY))["last_validation_date"]


def test_tc_inv_05_2_successor_only_in_retirement():
    """INV-08: a successor is allowed only in Retirement; a model cannot relate to itself."""
    assert model_rules.relationship_error("M-1", "M-2", "successor", "Monitoring")
    assert model_rules.relationship_error("M-1", "M-2", "successor", "Retirement") is None
    assert model_rules.relationship_error("M-1", "M-1", "related", "Monitoring")


# --- record rules ------------------------------------------------------------------------

def test_tc_his_01_1_completion_not_before_start():
    """VAL-01: a completion date before the start date is refused; In Progress needs no completion date."""
    assert governance_rules.validation_errors(date(2026, 5, 1), date(2026, 4, 1), "Approved")
    assert governance_rules.validation_errors(date(2026, 5, 1), None, "Approved")
    assert governance_rules.validation_errors(date(2026, 5, 1), None, "In Progress") == []


OPEN = ["Open", "In Progress", "Deferred"]


def test_tc_his_02_2_closed_needs_closed_date():
    """FND-01: status Closed requires a closed date; a due date before the raised date is refused."""
    assert governance_rules.finding_errors("Closed", date(2026, 1, 1), date(2026, 3, 1), None, OPEN)
    assert governance_rules.finding_errors("Open", date(2026, 1, 1), date(2026, 3, 1), None, OPEN) == []
    assert governance_rules.finding_errors("Open", date(2026, 3, 1), date(2026, 1, 1), None, OPEN)


def test_finding_ageing():
    """FND-02: days open, days overdue and overdue status; a closed finding stops ageing."""
    a = governance_rules.finding_age("Open", date(2026, 7, 1), date(2026, 9, 20), None, TODAY, OPEN)
    assert (a.days_open, a.days_overdue, a.is_overdue) == (91, 10, True)
    closed = governance_rules.finding_age("Closed", date(2026, 7, 1), date(2026, 9, 20), date(2026, 8, 1), TODAY, OPEN)
    assert (closed.days_open, closed.is_overdue) == (31, False)


def test_tc_his_03_1_conditional_needs_conditions():
    """APR-01: a Conditional decision with no conditions is refused; Approved needs none."""
    assert governance_rules.approval_errors("Conditional", "", None, None)
    assert governance_rules.approval_errors("Conditional", "Fix X", date(2026, 12, 1), "Open") == []
    assert governance_rules.approval_errors("Approved", None, None, None) == []


# --- R8 score ----------------------------------------------------------------------------

D = Decimal


def test_tc_scr_01_1_components_and_rescaling():
    """SCR-01, SCR-02: components match the hand calculation and unavailable weights are rescaled to 100%."""
    comps = [
        score.not_available("documentation", "Documentation", D(25), "n/a", []),
        score.validation_currency(True, 10, D(2), D(25)),                      # 80
        score.issue_remediation({"Critical": 1, "Medium": 1, "Low": 0}, 1,
                                {"Critical": D(25), "Medium": D(10), "Low": D(3)}, D(10), D(20)),  # 55
        score.mrc_compliance("Conditional", True, True, D(70), D(15)),         # 70
        score.not_available("monitoring", "Monitoring", D(15), "n/a", []),
    ]
    result = score.combine(comps)
    # (80*25 + 55*20 + 70*15) / 60 = 69.1666…
    assert result.overall == D("69.2")
    assert [c.effective_weight for c in comps if c.score is not None] == [D("41.7"), D("33.3"), D("25.0")]


def test_tc_scr_01_3_remediation_floors_at_zero():
    """SCR-03: issue remediation floors at zero rather than going negative."""
    c = score.issue_remediation({"Critical": 5}, 0, {"Critical": D(25)}, D(10), D(20))
    assert c.score == 0


def test_tc_scr_01_2_not_applicable_before_first_validation():
    """SCR-02: components that do not yet apply return no score, not zero."""
    assert score.validation_currency(False, 0, D(2), D(25)).score is None
    assert score.mrc_compliance(None, False, False, D(70), D(15)).score is None
    assert score.mrc_compliance(None, False, True, D(70), D(15)).score == 0


def test_no_applicable_component_gives_no_score():
    """SCR-06: with no applicable component there is no score and a stated reason."""
    result = score.combine([score.not_available("documentation", "Documentation", D(25), "n/a", [])])
    assert result.overall is None and result.reason
