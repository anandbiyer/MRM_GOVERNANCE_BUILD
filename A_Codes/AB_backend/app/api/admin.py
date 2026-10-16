from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentPrincipal, DbSession, require
from app.db import get_session_factory
from app.auth.roles import Permission
from app.auth.security import Principal
from app.schemas.core import PolicySettingOut, PolicySettingUpdate
from app.schemas.ingestion import ImportBatchOut, ResetStatusOut
from app.services import policy_service, reset_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/policy", response_model=list[PolicySettingOut])
def list_policy(db: DbSession, _: CurrentPrincipal):
    return policy_service.list_settings(db)


@router.put("/policy/{key}", response_model=PolicySettingOut)
def update_policy(
    key: str, body: PolicySettingUpdate, db: DbSession,
    principal: Annotated[Principal, Depends(require(Permission.POLICY_EDIT))],
):
    return policy_service.update_setting(db, principal, key, body.value, body.row_version, body.reason)


@router.post("/reset", response_model=ImportBatchOut, status_code=202)
def reset_to_seed(
    db: DbSession, principal: Annotated[Principal, Depends(require(Permission.POLICY_EDIT))],
    session_factory: Annotated[object, Depends(get_session_factory)],
):
    """Clear governance data and reload the seed through the import engine (demo/dev only)."""
    return reset_service.start_reset(db, session_factory, principal)


@router.get("/reset/status", response_model=ResetStatusOut)
def reset_status(db: DbSession, _: CurrentPrincipal):
    """Whether a reset is still running, which batch it is, and how the last one ended.

    Read from the reset lock alone (G1.32), which a reset holds from its first step to its last. The
    batch id returned by POST /reset is not the signal: its status reads Completed once the seed is
    loaded, while the reset is still writing (FT-02, CR-53, TR-65).
    """
    lock = reset_service.lock_state(db)
    if lock is None:
        return ResetStatusOut(in_progress=False, batch=None)
    running = lock.holder is not None
    batch = reset_service.running_batch(db, lock)
    return ResetStatusOut(in_progress=running, batch=batch, stage=lock.stage, acquired_at=lock.acquired_at,
                          released_at=lock.released_at, last_outcome=lock.last_outcome,
                          last_reason=lock.last_reason)
