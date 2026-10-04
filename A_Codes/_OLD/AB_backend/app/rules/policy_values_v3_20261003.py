"""Parsing and validation of policy_setting values by value_type. Pure functions."""
from decimal import Decimal, InvalidOperation

VALUE_TYPES = ("integer", "decimal", "percent", "text", "list", "boolean")


class PolicyValueError(ValueError):
    pass


def parse_policy_value(value: str, value_type: str):
    """Return the typed value, or raise PolicyValueError with a human-readable message."""
    if value_type not in VALUE_TYPES:
        raise PolicyValueError(f"Unknown value type '{value_type}'. Allowed: {', '.join(VALUE_TYPES)}.")
    raw = (value or "").strip()
    if value_type == "text":
        if not raw:
            raise PolicyValueError("A text setting cannot be blank.")
        return raw
    if value_type == "list":
        items = [item.strip() for item in raw.split(";") if item.strip()]
        if not items:
            raise PolicyValueError("A list setting needs at least one item, separated by ';'.")
        return items
    if value_type == "boolean":
        if raw.upper() in ("Y", "TRUE", "YES"):
            return True
        if raw.upper() in ("N", "FALSE", "NO"):
            return False
        raise PolicyValueError(f"'{raw}' is not a yes/no value. Use Y or N.")
    if value_type == "integer":
        try:
            return int(raw)
        except ValueError:
            raise PolicyValueError(f"'{raw}' is not a whole number.") from None
    try:
        number = Decimal(raw)
    except InvalidOperation:
        raise PolicyValueError(f"'{raw}' is not a number.") from None
    if value_type == "percent" and not (0 <= number <= 100):
        raise PolicyValueError(f"{raw} is outside 0–100. Percentages are whole numbers, e.g. 98 means 98%.")
    return number


def check_key_specific(key: str, parsed, others: dict[str, object]) -> None:
    """Cross-field and format checks for settings whose value has internal structure."""
    if key == "revalidation_frequencies":
        for item in parsed:
            name, sep, months = item.partition("=")
            if not sep or not name.strip() or not months.strip().isdigit() or int(months) <= 0:
                raise PolicyValueError(f"'{item}' must be written as Name=months, e.g. Annual=12.")
    if key in ("tier_high_min", "tier_medium_min"):
        high = parsed if key == "tier_high_min" else others.get("tier_high_min")
        medium = parsed if key == "tier_medium_min" else others.get("tier_medium_min")
        if high is not None and medium is not None and not (4 < int(medium) < int(high) <= 12):
            raise PolicyValueError("Tier thresholds must satisfy 4 < medium minimum < high minimum ≤ 12.")
    if key.startswith("weight_") and parsed < 0:
        raise PolicyValueError("Score weights cannot be negative.")
    # R3 needs the monitoring phase to be a real lifecycle phase; checked from either side, because
    # renaming the phase list is how the two drifted apart before (review finding CR-02). `others` is
    # empty on the bootstrap/import path, so this only guards interactive edits — see CR-03.
    if key == "monitoring_phase":
        phases = others.get("lifecycle_phases")
        if phases and parsed not in phases:
            raise PolicyValueError(
                f"'{parsed}' is not one of the configured lifecycle phases ({'; '.join(phases)}). "
                f"The Revalidation column is derived from it.")
    if key == "lifecycle_phases":
        monitoring = others.get("monitoring_phase")
        if monitoring and monitoring not in parsed:
            raise PolicyValueError(
                f"the list must still contain the configured monitoring phase '{monitoring}', which the "
                f"Revalidation column is derived from. Change 'monitoring_phase' first.")


def normalise_policy_value(value: str, value_type: str) -> str:
    """Canonical text form that is stored in the database."""
    parsed = parse_policy_value(value, value_type)
    if value_type == "list":
        return "; ".join(parsed)
    if value_type == "boolean":
        return "Y" if parsed else "N"
    return str(parsed)
