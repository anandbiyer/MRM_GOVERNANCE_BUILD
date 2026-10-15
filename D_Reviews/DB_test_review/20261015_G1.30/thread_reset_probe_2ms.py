"""Thread-mode probe for G1.30 (CR-53): run a real reset on a file-backed SQLite database with
background threads, sample the reset status throughout, and check the end state.

Fails if, at any sample, the reset reads finished while the example report has not been written,
or if the reset ends without the evidence, the report, or a terminal seed batch.
Run from A_Codes/AB_backend with PYTHONPATH=. ; all output stays in the scratchpad.
"""
import os
import sys
import time
from pathlib import Path

scratch = Path(sys.argv[1])
db_file = scratch / "probe.db"
for p in (db_file, Path(str(db_file) + "-wal"), Path(str(db_file) + "-shm")):
    p.unlink(missing_ok=True)
os.environ.update({
    "MRM_DATABASE_URL": f"sqlite:///{db_file.as_posix()}",
    "MRM_JOB_MODE": "thread",
    "MRM_STORAGE_BACKEND": "local",
    "MRM_LOCAL_STORAGE_DIR": str(scratch / "store"),
    "MRM_TODAY_OVERRIDE": "2026-09-30",
    "MRM_REGENERATE_SEED_ON_RESET": "false",
})

from sqlalchemy import func, select  # noqa: E402

from app.db import SessionLocal, engine  # noqa: E402
from app.models import Base, Document, ImportBatch, ModelRiskReport  # noqa: E402
from app.services import reset_service  # noqa: E402
from app.services.bootstrap_service import load_bootstrap  # noqa: E402
from app.config import get_settings  # noqa: E402

Base.metadata.create_all(engine)
with SessionLocal() as db:
    load_bootstrap(db, get_settings().bootstrap_dir)
    batch = reset_service.start_reset(db, lambda: SessionLocal(), None, get_settings().seed_dir)
    batch_id = batch.batch_id
print("reset started", batch_id, flush=True)

violations, samples, t0 = [], 0, time.time()
while time.time() - t0 < 900:
    with SessionLocal() as db:
        running = reset_service.reset_in_progress(db)
        reports = db.scalar(select(func.count()).select_from(ModelRiskReport))
        seedb = db.get(ImportBatch, batch_id)
        docb = db.scalars(select(ImportBatch).where(ImportBatch.source == "seed")).first()
        st = (seedb.status if seedb else None, docb.status if docb else None)
    samples += 1
    if running is None:
        if reports == 0:
            violations.append(f"t={time.time()-t0:.2f}s finished-with-no-report seed/docs={st}")
        else:
            break
    time.sleep(0.002)

time.sleep(1)  # let any trailing thread work settle before reading the end state
with SessionLocal() as db:
    seed = db.get(ImportBatch, batch_id)
    docs = db.scalar(select(func.count()).select_from(Document))
    reports = db.scalar(select(func.count()).select_from(ModelRiskReport))
    docs_batch = db.scalars(select(ImportBatch).where(ImportBatch.source == "seed")).first()
    print(f"samples={samples} elapsed={time.time()-t0:.1f}s")
    print(f"seed batch {seed.status} ({seed.error_message}); documents batch "
          f"{docs_batch.status if docs_batch else None}; documents={docs}; reports={reports}")
    ok = (not violations and seed.status in ("Completed", "Partially Completed")
          and docs > 1000 and reports == 1 and reset_service.reset_in_progress(db) is None)
for v in violations:
    print("VIOLATION", v)
print("RESULT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
