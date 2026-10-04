"""Typed, read-only view of policy_setting for services and rules. Loaded once per request/operation."""
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import event, select
from sqlalchemy.orm import Session

from app.models import PolicySetting
from app.rules import score as score_rules
from app.rules.model_rules import PhaseRequirements
from app.rules.policy_values import parse_policy_value
from app.services.errors import ServiceError


_CACHE_KEY = "mrm_policy"


@event.listens_for(Session, "after_soft_rollback")
def _drop_cache_on_rollback(session: Session, _previous_transaction) -> None:
    """Any rollback (including a savepoint) may undo policy changes the cache has seen."""
    session.info.pop(_CACHE_KEY, None)


class PolicyMissingError(ServiceError):
    status_code = 500


@dataclass(frozen=True)
class ScoreBands:
    """The two R8 band boundaries, read from policy. Classification lives in `rules.score`."""
    warn_min: int
    good_min: int

    def of(self, value) -> str:
        return score_rules.band_of(value, self.warn_min, self.good_min)

    def labels(self) -> dict[str, str]:
        return score_rules.band_labels(self.warn_min, self.good_min)


@dataclass
class Policy:
    values: dict[str, object]

    @classmethod
    def load(cls, db: Session) -> "Policy":
        """Parsed once per session; any policy write calls invalidate() so later reads see the change."""
        cached = db.info.get(_CACHE_KEY)
        if cached is not None:
            return cached
        rows = db.scalars(select(PolicySetting))
        policy = cls({r.setting_key: parse_policy_value(r.value, r.value_type) for r in rows})
        db.info[_CACHE_KEY] = policy
        return policy

    @staticmethod
    def invalidate(db: Session) -> None:
        db.info.pop(_CACHE_KEY, None)

    def _get(self, key: str):
        if key not in self.values:
            raise PolicyMissingError(f"Policy setting '{key}' is not configured. Load it in Admin or the bootstrap file.")
        return self.values[key]

    def int(self, key: str) -> int:
        return int(self._get(key))

    def decimal(self, key: str) -> Decimal:
        return Decimal(self._get(key))

    def text(self, key: str) -> str:
        return str(self._get(key))

    def list(self, key: str) -> list[str]:
        value = self._get(key)
        return list(value) if isinstance(value, list) else [str(value)]

    # --- derived accessors --------------------------------------------------------------

    @property
    def frequency_months(self) -> dict[str, int]:
        """revalidation_frequencies items are 'Name=months'."""
        result = {}
        for item in self.list("revalidation_frequencies"):
            name, _, months = item.partition("=")
            result[name.strip()] = int(months) if months.strip() else 12
        return result

    @property
    def phases(self) -> list[str]:
        return self.list("lifecycle_phases")

    @property
    def phase_requirements(self) -> PhaseRequirements:
        return PhaseRequirements(
            phases=self.phases,
            validator_from=self.text("validator_required_from_phase"),
            validation_data_from=self.text("validation_data_required_from_phase"),
            retirement_phase=self.phases[-1],
        )

    @property
    def retirement_phase(self) -> str:
        return self.phases[-1]

    @property
    def monitoring_phase(self) -> str:
        """The lifecycle phase R3 can displace into the Revalidation column (BRD §8, §10)."""
        return self.text("monitoring_phase")

    @property
    def score_bands(self) -> "ScoreBands":
        """R8 governance score bands. The only place these two numbers are read (§57, §69)."""
        return ScoreBands(warn_min=self.int("score_band_warn_min"), good_min=self.int("score_band_good_min"))

    def score_weights(self) -> dict[str, Decimal]:
        return {k: self.decimal(f"weight_{k}") for k in
                ("documentation", "validation_currency", "issue_remediation", "mrc_compliance", "monitoring")}
