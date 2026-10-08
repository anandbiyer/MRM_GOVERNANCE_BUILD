"""API schemas for Phase 1 (kept separate from ORM models, BRD §82 rule 4)."""
from datetime import UTC, datetime
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field


def _as_utc(value: datetime | None) -> datetime | None:
    """Label a naive timestamp as UTC, and leave an aware one alone.

    Every timestamp column is `DateTime(timezone=True)` and every value is written either by
    `datetime.now(UTC)` or by the database's `now()`, so a naive value read back is always UTC
    wall-clock. SQLite has no timezone type, so it returns these without a zone, and PostgreSQL —
    the system of record (§49) — returns them with one. Serialising the naive form sent the browser
    a time it read as *local*, which rendered a UTC wall-clock as local and landed on the adjacent
    calendar day: the Model 360 Score tab said 10/7 while its History tab said 10/8 for events
    minutes apart (review finding MP-15, plan BL.28).

    Applied through the `Utc` annotation below rather than per field, so a new timestamp field is
    covered by declaring its type. Deliberately **not** applied to `date` fields: a calendar day
    carries no zone, and giving it one would reintroduce the same shift from the other direction.
    """
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


#: A timestamp as the API emits it: always with an offset. Use for anything that is an instant.
Utc = Annotated[datetime, AfterValidator(_as_utc)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- auth ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    user_id: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    user_id: str
    full_name: str
    role: str
    roles: list[str]
    permissions: list[str]


class DevUser(BaseModel):
    user_id: str
    full_name: str
    roles: list[str]


# --- users --------------------------------------------------------------------------

class UserOut(ORMModel):
    user_id: str
    full_name: str
    email: str
    business_line: str | None
    active: bool
    roles: list[str] = Field(validation_alias="role_names")
    row_version: int


class UserCreate(BaseModel):
    user_id: str = Field(pattern=r"^U-\d{3,}$")
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    business_line: str | None = None
    roles: list[str] = Field(min_length=1)
    active: bool = True


# --- policy -------------------------------------------------------------------------

class PolicySettingOut(ORMModel):
    setting_key: str
    value: str
    value_type: str
    category: str | None
    description: str | None
    updated_by: str | None
    updated_at: Utc | None
    row_version: int


class PolicySettingUpdate(BaseModel):
    value: str
    row_version: int
    reason: str | None = None


# --- audit --------------------------------------------------------------------------

class AuditEventOut(ORMModel):
    event_id: int
    occurred_at: Utc
    user_id: str | None
    role: str | None
    action: str
    entity: str
    entity_id: str
    model_id: str | None
    import_batch_id: str | None
    document_id: str | None
    reason: str | None
    before_json: dict[str, Any] | None
    after_json: dict[str, Any] | None


# --- health -------------------------------------------------------------------------

class ComponentHealth(BaseModel):
    status: str  # ok | down
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str  # ok | degraded | down
    components: dict[str, ComponentHealth]
