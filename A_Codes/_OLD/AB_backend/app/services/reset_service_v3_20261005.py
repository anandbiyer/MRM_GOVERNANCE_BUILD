"""Demo/dev "reset to seed" (BRD §70, REQ-GEN-01).

Clears governance data and rebuilds it through the import engine from the seed files in
B_Inputs/AC_seed — the same path a user import takes — then loads the seed evidence documents
through the Document Centre batch path. Stored objects of cleared documents remain in object storage. The audit trail and import history are
kept: audit records are immutable, and the reset itself is recorded as an audit event.
"""
import csv
import importlib.util
from collections.abc import Callable
from pathlib import Path

from sqlalchemy import delete, func, select
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
    ModelVersion,
    PolicySetting,
    TieringAnswer,
    TierOverride,
    UserRole,
    Validation,
)
from app.services import bootstrap_service
from app.services.errors import ForbiddenError, ValidationFailedError
from app.services.policy_access import Policy
from app.workers import runner

# Children before parents.
DELETE_ORDER = (Finding, Approval, Validation, DocumentLink, DocumentVersion, Document, DocumentFolder, ModelRelationship,
                ModelVersion, ModelPhaseHistory, TierOverride, TieringAnswer, Model, UserRole, AppUser, PolicySetting)


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


def start_reset(db: Session, session_factory: Callable[[], Session], principal: Principal | None,
                directory: Path | None = None) -> ImportBatch:
    if not get_settings().allow_reset:
        raise ForbiddenError("Reset is disabled in this environment (MRM_ALLOW_RESET=false).")
    if principal and not has_permission(principal.role, Permission.POLICY_EDIT):
        raise ForbiddenError("Only an Admin can reset the application data.")
    directory = directory or get_settings().seed_dir
    if get_settings().regenerate_seed_on_reset:
        regenerate_seed(directory)
    uploads = seed_files(directory)
    batch = import_service.create_batch(db, None, uploads, source="reset", batch_type="seed")
    batch.uploaded_by = principal.user_id if principal else None
    db.commit()
    runner.submit(_reset_job, session_factory, batch.batch_id, principal)
    return batch


def _reset_job(session_factory: Callable[[], Session], batch_id: str, principal: Principal | None) -> None:
    with session_factory() as db:
        counts = {m.__tablename__: db.scalar(select(func.count()).select_from(m)) for m in DELETE_ORDER}
        for m in DELETE_ORDER:
            db.execute(delete(m))
        Policy.invalidate(db)
        audit.record(db, principal, action="reset", entity="application", entity_id="all", import_batch_id=batch_id,
                     before=counts, reason="Reset to seed")
        batch = db.get(ImportBatch, batch_id)
        batch.status = "Processing"
        db.commit()
    engine.run(session_factory, batch_id, "load", None)

    # Fail loudly on an incomplete configuration rather than leaving a 500 for the first user.
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
            return

    load_seed_documents(session_factory, get_settings().seed_dir / "documents")


def load_seed_documents(session_factory: Callable[[], Session], directory: Path) -> str | None:
    """Seed evidence goes through the Document Centre batch path: folder/file classification, then
    automatic confirmation of confidently classified files (system seed only)."""
    if not directory.is_dir():
        return None
    uploads = [(p.relative_to(directory).as_posix(), p.read_bytes()) for p in sorted(directory.rglob("*")) if p.is_file()]
    if not uploads:
        return None
    from app.documents import batch as doc_batch

    with session_factory() as db:
        return doc_batch.create_batch(db, session_factory, None, uploads, source="seed", auto_confirm=True).batch_id
