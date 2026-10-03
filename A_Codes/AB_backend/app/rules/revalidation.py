"""R2–R4 Revalidation (BRD §10). Pure date arithmetic; policy values are parameters."""
import calendar
from dataclasses import dataclass
from datetime import date

SCHEDULED, DUE_SOON, OVERDUE = "Scheduled", "Due Soon", "Overdue"
REVALIDATION_COLUMN = "Revalidation"


def add_months(d: date, months: int) -> date:
    """Calendar month addition; month-end dates clamp to the last day of the target month."""
    month_index = d.month - 1 + months
    year, month = d.year + month_index // 12, month_index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    # A date on the last day of its month stays on the last day (2025-08-31 + 6 → 2026-02-28).
    day = last_day if d.day == calendar.monthrange(d.year, d.month)[1] else min(d.day, last_day)
    return date(year, month, day)


def next_due_date(last_validation: date | None, frequency: str | None, frequency_months: dict[str, int]) -> date | None:
    """R2: last validation date + frequency. No last validation (or no frequency) means no due date."""
    if last_validation is None or not frequency or frequency not in frequency_months:
        return None
    return add_months(last_validation, frequency_months[frequency])


@dataclass(frozen=True)
class RevalidationState:
    due_date: date | None
    days_to_due: int | None
    status: str | None  # Scheduled | Due Soon | Overdue | None when no due date


def revalidation_state(due: date | None, today: date, due_soon_days: int) -> RevalidationState:
    """R4: Overdue if days to due < 0; Due Soon if 0..due_soon_days; else Scheduled."""
    if due is None:
        return RevalidationState(None, None, None)
    days = (due - today).days
    if days < 0:
        status = OVERDUE
    elif days <= due_soon_days:
        status = DUE_SOON
    else:
        status = SCHEDULED
    return RevalidationState(due, days, status)


def displayed_column(phase: str, due: date | None, today: date, lead_days: int, monitoring_phase: str) -> str:
    """R3: a model in the monitoring phase, within the lead time of (or past) its due date, shows in
    Revalidation.

    Revalidation is a governance work state, not a stored lifecycle phase (BRD §8). `monitoring_phase`
    has no default on purpose: it is the configurable `monitoring_phase` setting, and a default here
    would let a caller silently fall back to a phase name the policy no longer uses, which is how R3
    quietly stopped applying before (review finding CR-02).
    """
    if phase == monitoring_phase and due is not None and (due - today).days <= lead_days:
        return REVALIDATION_COLUMN
    return phase


def displayed_columns(phases: list[str], monitoring_phase: str) -> list[str]:
    """The lifecycle phases in order with the derived Revalidation column inserted after the
    monitoring phase — the column set the Operations Board and the Command Center both work in.

    Degrades rather than raising when `monitoring_phase` is not one of `phases`: the configuration is
    then inconsistent, but a dashboard that renders without the derived column is far better than one
    that returns a 500. Validation of the setting belongs to the write path, not here.
    """
    if monitoring_phase not in phases:
        return [*phases, REVALIDATION_COLUMN]
    cut = phases.index(monitoring_phase) + 1
    return [*phases[:cut], REVALIDATION_COLUMN, *phases[cut:]]
