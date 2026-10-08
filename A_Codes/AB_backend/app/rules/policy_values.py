"""Parsing and validation of policy_setting values by value_type. Pure functions."""
from decimal import Decimal, InvalidOperation

VALUE_TYPES = ("integer", "decimal", "percent", "text", "list", "boolean")


class PolicyValueError(ValueError):
    pass


# Settings whose value is the *name* of a lifecycle phase, and settings that are a *list* of phase
# names. `lifecycle_phases` is editable, so every one of these is a reference that a rename can
# break — CR-02 was `monitoring_phase`, CR-21 was the required-document bands, and the rest were
# only ever unbroken by luck. Both directions are checked below from one list rather than key by
# key, so a new phase-naming setting is guarded by adding its name here and nowhere else.
PHASE_NAME_KEYS = (
    "monitoring_phase",
    "mrc_required_from_phase",
    "validator_required_from_phase",
    "validation_data_required_from_phase",
    "required_docs_development_from_phase",
    "required_docs_validation_from_phase",
    "required_docs_production_from_phase",
)
PHASE_LIST_KEYS = ("production_phases",)


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
    # §21 breach severity rules, §81A D5: Condition=Severity items, the same shape as
    # revalidation_frequencies. Only the shape is checked here — the condition vocabulary and the
    # breach severity vocabulary are settled in Phase 6 with D3 and D7, and this check should then
    # validate against them rather than accepting any names.
    if key == "breach_severity_rules":
        for item in parsed:
            condition, sep, severity = item.partition("=")
            if not sep or not condition.strip() or not severity.strip():
                raise PolicyValueError(
                    f"'{item}' must be written as Condition=Severity, e.g. repeated_breach=High.")
    if key in ("tier_high_min", "tier_medium_min"):
        high = parsed if key == "tier_high_min" else others.get("tier_high_min")
        medium = parsed if key == "tier_medium_min" else others.get("tier_medium_min")
        if high is not None and medium is not None and not (4 < int(medium) < int(high) <= 12):
            raise PolicyValueError("Tier thresholds must satisfy 4 < medium minimum < high minimum ≤ 12.")
    if key.startswith("weight_") and parsed < 0:
        raise PolicyValueError("Score weights cannot be negative.")
    # A setting that names a lifecycle phase must name a real one; checked from either side, because
    # renaming the phase list is how the two drifted apart before (review findings CR-02, CR-21).
    # `others` is empty on the bootstrap/import path, so this only guards interactive edits — CR-03.
    if key in PHASE_NAME_KEYS or key in PHASE_LIST_KEYS:
        phases = others.get("lifecycle_phases")
        named = parsed if key in PHASE_LIST_KEYS else [parsed]
        unknown = [n for n in named if n not in (phases or named)]
        if phases and unknown:
            raise PolicyValueError(
                f"{', '.join(repr(n) for n in unknown)} is not one of the configured lifecycle phases "
                f"({'; '.join(phases)}). Add the phase first, then point this setting at it.")
    if key in ("score_band_warn_min", "score_band_good_min"):
        warn = parsed if key == "score_band_warn_min" else others.get("score_band_warn_min")
        good = parsed if key == "score_band_good_min" else others.get("score_band_good_min")
        if not 0 <= int(parsed) <= 100:
            raise PolicyValueError(f"{parsed} is outside 0–100; governance scores are percentages.")
        if warn is not None and good is not None and not int(warn) < int(good):
            raise PolicyValueError(
                f"the amber minimum ({warn}) must be below the green minimum ({good}).")
    if key == "lifecycle_phases":
        # Every setting that names a phase must still find it. Dropping a phase another setting
        # names is how a rename silently disabled a rule: the Revalidation column (CR-02) and the
        # required-document bands (CR-21), where the required list fell to [] and *raised* every
        # governance score. Refusing the edit forces the caller to move the setting first.
        for other_key in PHASE_NAME_KEYS:
            named = others.get(other_key)
            if named and named not in parsed:
                raise PolicyValueError(
                    f"the list must still contain '{named}', which '{other_key}' names. "
                    f"Change '{other_key}' first.")
        for other_key in PHASE_LIST_KEYS:
            missing = [n for n in (others.get(other_key) or []) if n not in parsed]
            if missing:
                raise PolicyValueError(
                    f"the list must still contain {', '.join(repr(n) for n in missing)}, which "
                    f"'{other_key}' names. Change '{other_key}' first.")


def normalise_policy_value(value: str, value_type: str) -> str:
    """Canonical text form that is stored in the database."""
    parsed = parse_policy_value(value, value_type)
    if value_type == "list":
        return "; ".join(parsed)
    if value_type == "boolean":
        return "Y" if parsed else "N"
    return str(parsed)
