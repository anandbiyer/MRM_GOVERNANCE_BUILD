"""G1.32 checkpoint probes (not product tests): can any path leave the reset lock held in-process?
Run: cd A_Codes/AB_backend && .venv/Scripts/python -m pytest -p tests.conftest <this file> -s -q"""
import pytest
from sqlalchemy.exc import OperationalError

from app.auth.security import Principal
from app.models import ImportBatch
from app.services import report_service, reset_service
from app.workers import runner

ADMIN = Principal(user_id="U-001", role="Admin", full_name="Admin")


def _state(db_session, label):
    with db_session() as db:
        lock = reset_service.lock_state(db)
        b = db.get(ImportBatch, lock.batch_id) if lock and lock.batch_id else None
        print(f"\n{label}: held={lock.holder is not None if lock else None} stage={lock.stage if lock else None} "
              f"outcome={lock.last_outcome if lock else None} batch={b.status if b else None}")
        return lock


def test_p1_submit_raises_in_start_reset(db_session, test_settings, monkeypatch):
    def boom(fn, *a):
        raise RuntimeError("cannot schedule new futures after interpreter shutdown")
    monkeypatch.setattr(runner, "submit", boom)
    with db_session() as db:
        with pytest.raises(RuntimeError):
            reset_service.start_reset(db, db_session, ADMIN)
    _state(db_session, "P1 submit raises in start_reset")


def test_p2_submit_raises_at_the_handover(db_session, test_settings, monkeypatch):
    real = runner.submit
    def submit(fn, *a):
        if fn is reset_service._store_evidence_then_seed_report:
            raise RuntimeError("cannot schedule new futures after interpreter shutdown")
        return real(fn, *a)
    monkeypatch.setattr(runner, "submit", submit)
    with db_session() as db:
        with pytest.raises(RuntimeError):
            reset_service.start_reset(db, db_session, ADMIN)
    _state(db_session, "P2 submit raises at the handover")


def test_p3_release_commit_fails(db_session, test_settings, monkeypatch):
    real_release = reset_service.release_reset_lock
    def factory_failing_commit():
        s = db_session()
        def bad():
            raise OperationalError("COMMIT", {}, Exception("database is locked"))
        s.commit = bad
        return s
    monkeypatch.setattr(reset_service, "release_reset_lock",
                        lambda sf, holder, outcome, reason=None: real_release(factory_failing_commit, holder, outcome, reason))
    with db_session() as db:
        reset_service.start_reset(db, db_session, ADMIN)
    _state(db_session, "P3 release commit fails")


def test_p4_stage_write_before_report_fails(db_session, test_settings, monkeypatch):
    real = reset_service.set_reset_stage
    def stage(sf, holder, st, batch_id=None):
        if st == "Seeded example report":
            raise OperationalError("UPDATE", {}, Exception("database is locked"))
        return real(sf, holder, st, batch_id)
    monkeypatch.setattr(reset_service, "set_reset_stage", stage)
    with db_session() as db:
        with pytest.raises(OperationalError):
            reset_service.start_reset(db, db_session, ADMIN)
    _state(db_session, "P4 stage write before report fails")
