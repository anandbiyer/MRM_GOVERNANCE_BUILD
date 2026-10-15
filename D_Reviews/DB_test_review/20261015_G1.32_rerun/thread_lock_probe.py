"""G1.32 thread-mode probe: a real reset on a file-backed SQLite database with background threads.

1. Samples the lock every 2 ms and flags any sample where the reset reads finished before the example
   report exists (the CR-53/TR-65 window class).
2. A second thread attempts a second reset every ~100 ms the way POST /api/admin/reset does: one
   request session that first reads the user (the auth dependency) and then calls start_reset.
   Each attempt is classified: Conflict (409, correct), OperationalError (would be a 500), other
   exception, or ACCEPTED (a second reset started -- a violation).
Run from A_Codes/AB_backend with PYTHONPATH=. ; argument: an existing scratch directory.
"""
import collections, os, sys, threading, time
from pathlib import Path

scratch = Path(sys.argv[1])
db_file = scratch / "probe32.db"
for p in (db_file, Path(str(db_file) + "-wal"), Path(str(db_file) + "-shm")):
    p.unlink(missing_ok=True)
os.environ.update({
    "MRM_DATABASE_URL": f"sqlite:///{db_file.as_posix()}",
    "MRM_JOB_MODE": "thread",
    "MRM_STORAGE_BACKEND": "local",
    "MRM_LOCAL_STORAGE_DIR": str(scratch / "store32"),
    "MRM_TODAY_OVERRIDE": "2026-09-30",
    "MRM_REGENERATE_SEED_ON_RESET": "false",
})
from sqlalchemy import func, select  # noqa: E402
from app.auth.security import Principal  # noqa: E402
from app.db import SessionLocal, engine  # noqa: E402
from app.models import AppUser, Base, Document, ImportBatch, ModelRiskReport  # noqa: E402
from app.services import reset_service  # noqa: E402
from app.services.errors import ConflictError  # noqa: E402
from app.services.bootstrap_service import load_bootstrap  # noqa: E402
from app.config import get_settings  # noqa: E402

ADMIN = Principal(user_id="U-001", role="Admin", full_name="Admin")
Base.metadata.create_all(engine)
with SessionLocal() as db:
    load_bootstrap(db, get_settings().bootstrap_dir)
    batch = reset_service.start_reset(db, lambda: SessionLocal(), ADMIN, get_settings().seed_dir)
    batch_id = batch.batch_id
print("reset started", batch_id, flush=True)

done = threading.Event()
attempts = collections.Counter()
examples = {}

def second_resets():
    while not done.is_set():
        t = time.time()
        try:
            with SessionLocal() as db:
                user = db.get(AppUser, "U-001")  # what the auth dependency does in the same session
                if user is None:
                    kind = "NoUser(401)"
                else:
                    try:
                        reset_service.start_reset(db, lambda: SessionLocal(), ADMIN, get_settings().seed_dir)
                        kind = "ACCEPTED"
                    except ConflictError as e:
                        kind = "Conflict(409)"
                        examples.setdefault(kind, e.message)
        except Exception as e:  # noqa: BLE001
            kind = f"{type(e).__name__}"
            examples.setdefault(kind, str(e).splitlines()[0][:200])
        attempts[kind] += 1
        if kind == "ACCEPTED":
            examples.setdefault("ACCEPTED", f"at t={time.time():.2f}")
        time.sleep(max(0.0, 0.1 - (time.time() - t)))

th = threading.Thread(target=second_resets, daemon=True)
th.start()
violations, samples, t0 = [], 0, time.time()
while time.time() - t0 < 900:
    with SessionLocal() as db:
        running = reset_service.reset_in_progress(db)
        reports = db.scalar(select(func.count()).select_from(ModelRiskReport))
    samples += 1
    if running is None:
        if reports == 0:
            violations.append(f"t={time.time()-t0:.2f}s reset reads finished but no example report yet")
        break
    time.sleep(0.002)
done.set(); th.join(5)
time.sleep(1)
with SessionLocal() as db:
    seed = db.get(ImportBatch, batch_id)
    docs = db.scalar(select(func.count()).select_from(Document))
    reports = db.scalar(select(func.count()).select_from(ModelRiskReport))
    lock = reset_service.lock_state(db)
    print(f"samples={samples} elapsed={time.time()-t0:.1f}s")
    print(f"seed batch {seed.status} ({seed.error_message}); documents={docs}; reports={reports}; "
          f"lock outcome={lock.last_outcome} stage={lock.stage} reason={lock.last_reason}")
    ok = (not violations and seed.status in ("Completed", "Partially Completed")
          and docs > 1000 and reports == 1 and reset_service.reset_in_progress(db) is None)
print("second-reset attempts:", dict(attempts))
for k, v in examples.items():
    print("  example", k, ":", v)
for v in violations:
    print("VIOLATION", v)
print("RESULT", "PASS" if ok and attempts["ACCEPTED"] == 0 else "FAIL")
