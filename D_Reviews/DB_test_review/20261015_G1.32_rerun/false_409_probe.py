"""G1.32 re-run probe: can start_reset answer "A reset is already running" (409) when none is?

Mirrors one POST /api/admin/reset request on a file-backed SQLite database in WAL mode, as configured
by app.db.configure_sqlite: the auth dependency reads app_user in the request session (configure_sqlite
emits BEGIN on the first statement, so that read opens a deferred transaction and pins a WAL snapshot),
and then start_reset runs in the same session. Between the two, an unrelated write commits on another
connection - an ordinary write, not a reset. No reset lock is held at any time.
Case W: unrelated commit between the auth read and start_reset (stale snapshot -> SQLITE_BUSY_SNAPSHOT).
Case H: unrelated writer holding the write lock longer than busy_timeout during start_reset.
Run from A_Codes/AB_backend with PYTHONPATH=. ; argument: an existing scratch directory.
"""
import os, sys, threading, time
from pathlib import Path

scratch = Path(sys.argv[1])
db_file = scratch / "false409.db"
for p in (db_file, Path(str(db_file) + "-wal"), Path(str(db_file) + "-shm")):
    p.unlink(missing_ok=True)
os.environ.update({"MRM_DATABASE_URL": f"sqlite:///{db_file.as_posix()}", "MRM_JOB_MODE": "inline",
                   "MRM_STORAGE_BACKEND": "local", "MRM_LOCAL_STORAGE_DIR": str(scratch / "storef"),
                   "MRM_TODAY_OVERRIDE": "2026-09-30", "MRM_REGENERATE_SEED_ON_RESET": "false",
                   "MRM_SQLITE_BUSY_TIMEOUT_MS": "300"})
from sqlalchemy import text  # noqa: E402
from app.auth.security import Principal  # noqa: E402
from app.db import SessionLocal, engine  # noqa: E402
from app.models import AppUser, Base  # noqa: E402
from app.services import reset_service  # noqa: E402
from app.services.errors import ConflictError  # noqa: E402
from app.services.bootstrap_service import load_bootstrap  # noqa: E402
from app.config import get_settings  # noqa: E402

ADMIN = Principal(user_id="U-001", role="Admin", full_name="Admin")
Base.metadata.create_all(engine)
with SessionLocal() as db:
    load_bootstrap(db, get_settings().bootstrap_dir)
    reset_service._ensure_lock_row(db)
print("busy_timeout_ms =", get_settings().sqlite_busy_timeout_ms)

def unrelated_write():
    with SessionLocal() as other:
        other.execute(text("UPDATE app_user SET full_name = full_name WHERE user_id = 'U-001'"))
        other.commit()

def attempt(label, between=None, during=None):
    # Never actually run a reset: stop at the first step after a successful claim.
    orig = reset_service.set_reset_stage
    class Claimed(Exception): pass
    def stop(*a, **k): raise Claimed()
    reset_service.set_reset_stage = stop
    try:
        with SessionLocal() as db:
            assert db.get(AppUser, "U-001") is not None      # what the auth dependency does
            if between: between()
            if during: during()
            try:
                reset_service.start_reset(db, lambda: SessionLocal(), ADMIN)
                out = "ACCEPTED (returned)"
            except Claimed:
                out = "ACCEPTED (claimed the lock; stopped before any delete)"
            except ConflictError as e:
                out = f"409 {e.message}"
            except Exception as e:  # noqa: BLE001
                out = f"500 {type(e).__name__}: {str(e).splitlines()[0][:160]}"
    finally:
        reset_service.set_reset_stage = orig
    with SessionLocal() as db:
        lock = reset_service.lock_state(db)
        if lock.holder:  # release our own probe claim
            reset_service.release_reset_lock(lambda: SessionLocal(), lock.holder, "Probe")
        held = reset_service.reset_in_progress(db)
    print(f"[{label}] {out}\n      lock held by another reset at any time: no; lock now: {held}")
    return out

attempt("control: nothing else happening")
attempt("W: unrelated commit between auth read and start_reset", between=unrelated_write)

hold_started, release = threading.Event(), threading.Event()
def holder():
    with engine.connect() as c:
        c.exec_driver_sql("UPDATE app_user SET full_name = full_name WHERE user_id = 'U-002'")  # BEGIN emitted
        hold_started.set(); release.wait(5); c.rollback()
t = threading.Thread(target=holder); t.start(); hold_started.wait(5)
try:
    attempt("H: unrelated writer holds the write lock > busy_timeout")
finally:
    release.set(); t.join()
attempt("control again")
