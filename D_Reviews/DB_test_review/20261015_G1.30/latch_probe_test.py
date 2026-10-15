import pytest
from sqlalchemy.exc import OperationalError
from app.models import ImportBatch
from app.services import reset_service, report_service


def test_final_restore_failure_latches(db_session, test_settings, monkeypatch):
    with db_session() as db:
        db.add(ImportBatch(batch_id="B-PROBE", batch_type="seed", source="reset", status="Processing", options={}))
        db.commit()
    state = {"armed": False}

    def fake_report(_sf):
        state["armed"] = True

    def factory():
        s = db_session()
        if state["armed"]:
            def bad_commit():
                raise OperationalError("COMMIT", {}, Exception("database is locked"))
            s.commit = bad_commit
        return s

    monkeypatch.setattr(report_service, "seed_previous_report", fake_report)
    with pytest.raises(OperationalError):
        reset_service._store_evidence_then_seed_report(factory, None, "B-PROBE", "Completed")
    with db_session() as db:
        b = db.get(ImportBatch, "B-PROBE")
        running = reset_service.reset_in_progress(db)
        print("STATUS", b.status, "ERR", b.error_message, "IN_PROGRESS", running.batch_id if running else None)
        assert b.status == "Processing"  # latched: the restore failure is outside the try
        assert running is not None
