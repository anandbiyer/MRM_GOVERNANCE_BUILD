"""Demo/dev "reset to seed" (BRD §70, REQ-GEN-01).

Clears governance data and rebuilds it through the import engine from the seed files in
B_Inputs/AC_seed — the same path a user import takes — then loads the seed evidence documents
through the Document Centre batch path. Stored objects of cleared documents remain in object storage. The audit trail and import history are
kept: audit records are immutable, and the reset itself is recorded as an audit event.
"""
import csv
import importlib.util
import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit import service as audit
from app.auth.roles import Permission, has_permission
from app.auth.security import Principal
from app.clock import today
from app.config import get_settings
from app.ingestion import engine
from app.ingestion import service as import_service
from app.models import (
    AppUser,
    Approval,
    Document,
    DocumentFolder,
    DocumentLink,
    DocumentVersion,
    Finding,
    ImportBatch,
    Model,
    ModelPhaseHistory,
    ModelRelationship,
    ModelRiskReport,
    ModelVersion,
    PolicySetting,
    ResetLock,
    TieringAnswer,
    TierOverride,
    UserRole,
    Validation,
)
from app.services import bootstrap_service, report_service
from app.services.errors import ConflictError, ForbiddenError, ValidationFailedError
from app.services.policy_access import Policy
from app.workers import runner

log = logging.getLogger(__name__)

# Children before parents. `ModelRiskReport` is first: it references itself through
# `previous_report_id`, and a reset must leave the report history as reproducible as everything else
# (GEN-01) — otherwise the next reset's seeded predecessor depends on what a demo did in between.
DELETE_ORDER = (ModelRiskReport, Finding, Approval, Validation, DocumentLink, DocumentVersion, Document,
                DocumentFolder, ModelRelationship, ModelVersion, ModelPhaseHistory, TierOverride,
                TieringAnswer, Model, UserRole, AppUser, PolicySetting)

# The §42 batch statuses that mean a batch has finished, one way or another. The rest — Uploaded,
# Validating, Ready, Processing — mean work is still expected. No longer what the reset guard reads
# (that is the lock, G1.32); kept as the §42 contract the batch tests check against.
TERMINAL_BATCH_STATUSES = ("Completed", "Partially Completed", "Failed", "Validation Failed", "Cancelled")

# The single row of `reset_lock` (G1.32). "Is a reset running?" is answered by this row alone.
LOCK_ID = 1


def regenerate_seed(directory: Path) -> None:
    """Rewrite the seed templates (and demo files) for today's business date using A_Codes/AD_seed."""
    s = get_settings()
    spec = importlib.util.spec_from_file_location("generate_seed", s.seed_generator)
    if spec is None or not s.seed_generator.exists():
        raise ValidationFailedError(f"Seed generator not found at {s.seed_generator}.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.generate(directory, today(), demo_dir=s.demo_files_dir)


def missing_baseline_settings(db: Session) -> list[str]:
    """Policy keys the bootstrap baseline defines that the loaded seed did not supply.

    A reset deletes `policy_setting` and reloads it from the seed's T12 alone, so a seed generated
    before a new setting was introduced silently removes it. Every rule reads its thresholds from
    this table, so the first screen to need the missing key fails with a 500 — the application looks
    broken rather than misconfigured. B_Inputs/AA_bootstrap is the canonical baseline configuration
    (`app.cli bootstrap` loads exactly it), so the seed must never be a subset of it.

    Returns [] when the baseline file is absent: not every deployment ships one, and a missing
    baseline is not evidence of an incomplete seed.
    """
    baseline = get_settings().bootstrap_dir / bootstrap_service.POLICY_FILE
    if not baseline.exists():
        return []
    with baseline.open(newline="", encoding="utf-8-sig") as fh:
        expected = {(row.get("setting_key") or "").strip() for row in csv.DictReader(fh)}
    expected.discard("")
    loaded = set(db.scalars(select(PolicySetting.setting_key)))
    return sorted(expected - loaded)


def seed_files(directory: Path) -> list[tuple[str, bytes]]:
    files = sorted(p for p in directory.glob("*") if p.suffix.lower() in (".xlsx", ".csv"))
    if not files:
        raise ValidationFailedError(f"No seed files found in {directory}. Run A_Codes/AD_seed/generate_seed.py.")
    return [(p.name, p.read_bytes()) for p in files]


# --- the reset lock (G1.32) -------------------------------------------------------------------------
#
# Until G1.32 "is a reset running?" was inferred from import batch statuses, and that inference failed
# twice in the same way. CR-53: both reset batches were terminal while the example report was still
# being written. TR-65: `engine.run` commits the seed batch `Completed` a moment before the reset
# re-holds it. Each time, for that window, a second reset would have been accepted with its deletes
# racing the first. Rather than patch each window as it is found, a reset now claims an explicit lock
# at its very start, holds it to its very end, and releases it in a `finally` that records how it
# ended. The in-flight check and `GET /api/admin/reset/status` read the lock and nothing else.
#
# Writes to the lock are processing state, like a batch status, so they are not audited; the reset
# itself is (`_reset_job`). Each helper uses its own short transaction so the lock is visible to other
# sessions the moment it changes.


def _now() -> datetime:
    return datetime.now(UTC)


def _lock_row(db: Session) -> ResetLock | None:
    """The lock row, re-read from the database rather than from this session's identity map."""
    return db.execute(select(ResetLock).where(ResetLock.lock_id == LOCK_ID)
                      .execution_options(populate_existing=True)).scalar_one_or_none()


def _ensure_lock_row(db: Session) -> None:
    """Migration 0008 inserts the row; a `create_all` database (the dev launcher, tests) does not."""
    if _lock_row(db) is not None:
        return
    db.add(ResetLock(lock_id=LOCK_ID))
    try:
        db.commit()
    except IntegrityError:  # another session inserted it first, which is just as good
        db.rollback()


def acquire_reset_lock(db: Session, holder: str, acquired_by: str | None) -> bool:
    """Claim the lock for `holder`. True if this call now holds it, False if a reset already does.

    One conditional UPDATE — "set the holder where there is none" — so of two claimants exactly one
    matches the free row. That is atomic on SQLite and PostgreSQL alike, which is what BL.12 found the
    old read-then-proceed guard was not: on PostgreSQL two requests could both read "nothing running"
    and both reach the delete loop.
    """
    _ensure_lock_row(db)
    claimed = db.execute(
        update(ResetLock)
        .where(ResetLock.lock_id == LOCK_ID, ResetLock.holder.is_(None))
        .values(holder=holder, acquired_by=acquired_by, acquired_at=_now(), stage="Starting",
                batch_id=None, released_at=None, last_outcome=None, last_reason=None)
        .execution_options(synchronize_session=False)
    ).rowcount
    db.commit()
    return claimed == 1


def set_reset_stage(session_factory: Callable[[], Session], holder: str, stage: str,
                    batch_id: str | None = None) -> None:
    """Record the stage the running reset has reached (and its batch, once that exists)."""
    values = {"stage": stage} | ({"batch_id": batch_id} if batch_id else {})
    with session_factory() as db:
        db.execute(update(ResetLock)
                   .where(ResetLock.lock_id == LOCK_ID, ResetLock.holder == holder)
                   .values(**values).execution_options(synchronize_session=False))
        db.commit()


def release_reset_lock(session_factory: Callable[[], Session], holder: str, outcome: str,
                       reason: str | None = None) -> None:
    """Release the lock if `holder` holds it, recording how the reset ended. Never raises.

    Only the holder can release, so a late or repeated release — an inline-mode job that already
    released, a test re-running a stage — cannot free someone else's reset. It never raises because it
    runs in `finally` blocks while an exception may already be in flight. If the release itself cannot
    be written (the database is gone, say), the lock stays held and `recover_interrupted_reset` frees
    it when the application next starts.
    """
    try:
        with session_factory() as db:
            db.execute(update(ResetLock)
                       .where(ResetLock.lock_id == LOCK_ID, ResetLock.holder == holder)
                       .values(holder=None, released_at=_now(), last_outcome=outcome, last_reason=reason)
                       .execution_options(synchronize_session=False))
            db.commit()
    except Exception:  # noqa: BLE001 — see the docstring: never mask the original failure
        log.exception("Could not release the reset lock held by %s", holder)


def reset_in_progress(db: Session) -> ResetLock | None:
    """The lock of the reset that is running, or None. The only answer to "is a reset running?"."""
    lock = _lock_row(db)
    return lock if lock is not None and lock.holder is not None else None


def lock_state(db: Session) -> ResetLock | None:
    """The lock row whether held or not, for the status endpoint's "how did the last one end"."""
    return _lock_row(db)


def running_batch(db: Session, lock: ResetLock) -> ImportBatch | None:
    """The seed batch of the reset holding `lock`, or None when the lock is free or not yet bound."""
    return db.get(ImportBatch, lock.batch_id) if lock.holder is not None and lock.batch_id else None


def recover_interrupted_reset(db: Session) -> bool:
    """Release a lock left held by an application that stopped mid-reset. True if one was released.

    The `finally` that releases the lock cannot run if the process itself dies. Jobs run inside the
    application's own process (`app.workers.runner`), so when it starts again no reset of its own can
    be running: a lock still held was left by an interrupted run. Called once at startup. Known limit,
    recorded with G1.32: a CLI reset (`python -m app.cli reset`) runs in its own process, so starting the
    API server while one is running would release that run's lock. When jobs move to separate workers
    (G7.3) this needs a holder heartbeat instead.
    """
    lock = reset_in_progress(db)
    if lock is None:
        return False
    reason = (f"Interrupted: the application stopped during the reset, at stage "
              f"{lock.stage or 'unknown'}; the lock was released when it started again.")
    db.execute(update(ResetLock)
               .where(ResetLock.lock_id == LOCK_ID, ResetLock.holder == lock.holder)
               .values(holder=None, released_at=_now(), last_outcome="Interrupted", last_reason=reason)
               .execution_options(synchronize_session=False))
    db.commit()
    log.warning("Released a reset lock left by an interrupted run (batch %s, stage %s)",
                lock.batch_id, lock.stage)
    return True


def _failure(stage: str, exc: BaseException) -> str:
    """The reason recorded on the lock, worded like `record_job_failure`'s on the batch."""
    return f"{stage} failed: {type(exc).__name__}: {exc}"


# --- the reset -------------------------------------------------------------------------------------


def start_reset(db: Session, session_factory: Callable[[], Session], principal: Principal | None,
                directory: Path | None = None) -> ImportBatch:
    if not get_settings().allow_reset:
        raise ForbiddenError("Reset is disabled in this environment (MRM_ALLOW_RESET=false).")
    if principal and not has_permission(principal.role, Permission.POLICY_EDIT):
        raise ForbiddenError("Only an Admin can reset the application data.")
    # Claim the lock before regenerating the seed or deleting anything: a reset clears every
    # governance table and reloads it, so two overlapping runs would interleave one's deletes with
    # the other's inserts. After the permission checks, so an unauthorised caller still gets 403 and
    # learns nothing about whether a reset is running (GEN-04).
    holder = uuid.uuid4().hex
    if not acquire_reset_lock(db, holder, principal.user_id if principal else None):
        running = reset_in_progress(db)
        started = running.acquired_at.strftime("%Y-%m-%d %H:%M:%S UTC") if running and running.acquired_at else "earlier"
        raise ConflictError(
            f"A reset is already running: batch {(running.batch_id if running else None) or '(being created)'}, "
            f"stage {(running.stage if running else None) or 'unknown'}, started {started}. "
            f"Wait for it to finish and try again (GET /api/admin/reset/status)."
        )
    stage = "Seed preparation"
    try:
        set_reset_stage(session_factory, holder, stage)
        directory = directory or get_settings().seed_dir
        if get_settings().regenerate_seed_on_reset:
            regenerate_seed(directory)
        uploads = seed_files(directory)
        batch = import_service.create_batch(db, None, uploads, source="reset", batch_type="seed")
        batch.uploaded_by = principal.user_id if principal else None
        db.commit()
        set_reset_stage(session_factory, holder, "Clearing data", batch_id=batch.batch_id)
    except BaseException as exc:
        db.rollback()
        release_reset_lock(session_factory, holder, "Failed", _failure(stage, exc))
        raise
    # From here the lock belongs to the job: it is released by whichever stage ends the reset. In
    # inline mode the job runs inside this call and has released the lock by the time it returns.
    runner.submit(_reset_job, session_factory, batch.batch_id, principal, holder)
    return batch


def _reset_job(session_factory: Callable[[], Session], batch_id: str, principal: Principal | None,
               holder: str) -> None:
    """Clear, load the seed, check the baseline, stage the evidence, then hand over (see below).

    Runs under the lock `holder` claimed in `start_reset`. Any failure records the stage on the seed
    batch (FT-05) and on the lock, and releases it, so no stage can leave a reset latched (TR-67).
    """
    stage = "Clearing data"
    try:
        with session_factory() as db:
            counts = {m.__tablename__: db.scalar(select(func.count()).select_from(m)) for m in DELETE_ORDER}
            for m in DELETE_ORDER:
                db.execute(delete(m))
            Policy.invalidate(db)
            audit.record(db, principal, action="reset", entity="application", entity_id="all",
                         import_batch_id=batch_id, before=counts, reason="Reset to seed")
            batch = db.get(ImportBatch, batch_id)
            batch.status = "Processing"
            db.commit()
        stage = "Seed load"
        set_reset_stage(session_factory, holder, stage)
        engine.run(session_factory, batch_id, "load", None)

        # Fail loudly on an incomplete configuration rather than leaving a 500 for the first user.
        stage = "Baseline check"
        set_reset_stage(session_factory, holder, stage)
        with session_factory() as db:
            missing = missing_baseline_settings(db)
            if missing:
                batch = db.get(ImportBatch, batch_id)
                batch.status = "Failed"
                batch.error_message = (
                    f"Reset loaded the seed but {len(missing)} policy setting(s) required by the baseline "
                    f"are missing: {', '.join(missing)}. The seed's T12 is older than the configuration "
                    f"the rules need. Regenerate it (A_Codes/AD_seed/generate_seed.py) or run "
                    f"`python -m app.cli bootstrap` to restore the baseline."
                )
                audit.record(db, principal, action="reset_incomplete", entity="application", entity_id="all",
                             import_batch_id=batch_id, after={"missing_policy_settings": missing},
                             reason="Seed policy settings do not cover the baseline")
                db.commit()
                release_reset_lock(session_factory, holder, "Failed",
                                   f"{stage} failed: {len(missing)} required policy setting(s) missing")
                return

        stage = "Seed evidence staging"
        set_reset_stage(session_factory, holder, stage)
        staged = stage_seed_documents(session_factory, get_settings().seed_dir / "documents")
        # The last write before the handover (FT-04): the job continues from here.
        set_reset_stage(session_factory, holder, "Seed evidence analysis")
    except BaseException as exc:
        import_service.record_job_failure(session_factory, batch_id, stage, exc)
        release_reset_lock(session_factory, holder, "Failed", _failure(stage, exc))
        raise
    # **FT-04**: the reset makes no database write after submitting a job. In thread mode such a
    # write races the job for SQLite's write lock and the job loses — once, that cost all 1,116
    # evidence documents behind an HTTP 202. So the handover is the last thing this function does, and
    # the lock passes to the job with it. **S11**: the example report's figures must be a real
    # portfolio state, so the report is written after the evidence loads, inside the same job.
    #
    # Neither batch's status is a signal for "the reset has finished" any more (CR-53, TR-65); the
    # lock is. The seed batch keeps the status the seed load concluded with, unless a later stage
    # fails, in which case it is marked Failed with that stage, so the Import Centre shows why.
    runner.submit(_store_evidence_then_seed_report, session_factory, staged, batch_id, holder)


def _store_evidence_then_seed_report(session_factory: Callable[[], Session], documents_batch_id: str | None,
                                     seed_batch_id: str, holder: str) -> None:
    """Analyse and store the seed evidence, write the example report, then release the lock.

    The release is in a `finally`, so whatever happens here the reset ends and says how (GEN-05,
    TR-67). On a failure the seed batch is also marked `Failed` with the stage (CR-57, FT-05's class)
    and the exception is re-raised so the runner still logs it. If the *analysis* fails, `analyse_job`
    has already marked the documents batch `Failed`, and no example is written: a report over a
    half-loaded portfolio would be worse than none (TR-66).
    """
    from app.documents import batch as doc_batch

    stage, outcome, reason = "Seed evidence analysis", "Completed", None
    try:
        if documents_batch_id:
            doc_batch.analyse_job(session_factory, documents_batch_id, None)
        stage = "Seeded example report"
        set_reset_stage(session_factory, holder, stage)
        report_service.seed_previous_report(session_factory)
    except BaseException as exc:
        outcome, reason = "Failed", _failure(stage, exc)
        import_service.record_job_failure(session_factory, seed_batch_id, stage, exc)
        raise
    finally:
        release_reset_lock(session_factory, holder, outcome, reason)


def stage_seed_documents(session_factory: Callable[[], Session], directory: Path) -> str | None:
    """Stage the seed evidence as a Document Centre batch and return its id, without analysing it.

    Seed evidence goes through the Document Centre batch path: folder/file classification, then
    automatic confirmation of confidently classified files (system seed only). Analysis is started by
    the caller once it has no writes left of its own — see `_reset_job` and FT-04.
    """
    if not directory.is_dir():
        return None
    uploads = [(p.relative_to(directory).as_posix(), p.read_bytes()) for p in sorted(directory.rglob("*")) if p.is_file()]
    if not uploads:
        return None
    from app.documents import batch as doc_batch

    with session_factory() as db:
        return doc_batch.create_batch(db, session_factory, None, uploads, source="seed", auto_confirm=True,
                                      start_analysis=False).batch_id
