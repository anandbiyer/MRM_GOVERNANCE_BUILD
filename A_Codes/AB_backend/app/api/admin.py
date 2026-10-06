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
    """Whether a reset is still running, and which batch to watch.

    A reset creates two batches — the seed import and then one for the evidence files — so the batch
    id returned by POST /reset reports Completed while the reset is still writing. This is the signal
    that covers the whole operation (FT-02).
    """
    running = reset_service.reset_in_progress(db)
    return ResetStatusOut(in_progress=running is not None, batch=running)
