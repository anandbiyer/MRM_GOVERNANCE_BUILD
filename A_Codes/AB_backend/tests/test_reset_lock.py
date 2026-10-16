"""The explicit reset lock (plan G1.32; GEN-04, GEN-05; review findings TR-65..TR-69, BL.12).

Until G1.32, "is a reset running?" was inferred from batch statuses, and that inference failed twice
in the same way: CR-53 found both reset batches terminal while the example report was written, and
TR-65 found the seed batch committed `Completed` by `engine.run` a moment before the reset re-held it.
Each time a second reset would have been accepted with its deletes racing the first. The owner chose
to stop inferring: a reset claims one lock row at its very start, holds it to its very end, and
releases it in a `finally` that records the outcome and, on failure, the stage. The in-flight check
and `GET /api/admin/reset/status` read only the lock.
"""
import pytest
from sqlalchemy import event as sa_event
from sqlalchemy import func, select
from sqlalchemy.orm import Session as SASession

from app.auth.security import Principal
from app.db import get_session_factory
from app.models import ImportBatch, ModelRiskReport, ResetLock
from app.services import report_service, reset_service
from app.services.errors import ConflictError
from tests.conftest import ADMIN, login

ADMIN_PRINCIPAL = Principal(user_id="U-001", role="Admin", full_name="Admin")


def _factory(client):
    return client.app.dependency_overrides[get_session_factory]()


@pytest.fixture
def file_client(tmp_path, test_settings):
    """A client over a file-backed database, so a second, independent connection can watch it.

    The shared fixtures use one in-memory connection (StaticPool), which a probe cannot open
    alongside a session that is mid-commit. A file with its own pool is also closer to the product.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db import configure_sqlite
    from app.models import Base
    from app.services.bootstrap_service import load_bootstrap
    from tests.conftest import _client_for

    url = f"sqlite:///{(tmp_path / 'lock.db').as_posix()}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    configure_sqlite(engine)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as db:
        load_bootstrap(db, test_settings.bootstrap_dir)
    probe_engine = create_engine(url, connect_args={"check_same_thread": False})
    configure_sqlite(probe_engine)
    yield _client_for(factory), sessionmaker(bind=probe_engine), factory
    probe_engine.dispose()
    engine.dispose()


def test_g1_32_after_every_commit_of_a_reset_the_lock_is_held_until_it_is_released(file_client):
    """GEN-05, GEN-04 (TR-65): no commit inside a reset leaves it looking finished, except the last.

    This is the form that would have caught both CR-53 and TR-65 — each was one commit after which
    the inferred signal read "finished" while the reset still had writing to do. Every commit made
    during an inline reset is observed, and after each one an independent connection asks the same
    question `start_reset` asks. Only the final commit, the release, may answer "not running".
    """
    client, probe, _ = file_client
    seen: list[bool] = []

    def after_commit(_session):
        with probe() as db:
            seen.append(reset_service.reset_in_progress(db) is not None)

    headers = login(client, *ADMIN)  # before listening: signing in is not part of the reset
    sa_event.listen(SASession, "after_commit", after_commit)
    try:
        resp = client.post("/api/admin/reset", headers=headers)
    finally:
        sa_event.remove(SASession, "after_commit", after_commit)

    assert resp.status_code == 202, resp.text
    assert len(seen) > 10, f"a reset makes many commits; only {len(seen)} were observed"
    assert seen[-1] is False, "the last commit is the release, after which the reset is over"
    # The reset begins at the claim. At most one commit may precede it: inserting the lock row on a
    # `create_all` database, which has none until the first reset (migration 0008 inserts it).
    claim = seen.index(True)
    assert claim <= 1, f"{claim} commits happened before the lock was claimed; the claim must come first"
    early = [i for i, held in enumerate(seen[:-1]) if i >= claim and not held]
    assert early == [], (
        f"after commit(s) {early} of {len(seen)} the reset read as finished while it was still "
        f"writing, so a second reset would have been accepted there (TR-65, CR-53)")


def test_g1_32_a_second_reset_during_the_report_write_is_refused_409(client, test_settings, monkeypatch):
    """GEN-04 (TR-69): refused, not merely reported as running — at the last stage, where CR-53 was."""
    factory = _factory(client)
    real = report_service.seed_previous_report
    refusal = {}

    def spy(session_factory):
        with factory() as db:
            # TR-76: if the lock were not held, `start_reset` would begin a nested reset and recurse
            # into this spy without end; record the failure instead, so the test fails and returns.
            if reset_service.reset_in_progress(db) is None:
                refusal["status"], refusal["message"] = None, "the lock was not held during the report write"
                return real(session_factory)
            with pytest.raises(ConflictError) as err:
                reset_service.start_reset(db, factory, ADMIN_PRINCIPAL)
            refusal["status"], refusal["message"] = err.value.status_code, err.value.message
        return real(session_factory)

    monkeypatch.setattr(report_service, "seed_previous_report", spy)
    resp = client.post("/api/admin/reset", headers=login(client, *ADMIN))
    assert resp.status_code == 202, resp.text
    assert refusal["status"] == 409
    assert resp.json()["batch_id"] in refusal["message"], "the refusal names the reset in flight"
    assert "Seeded example report" in refusal["message"], "and the stage it is at"


def _fail(monkeypatch, target, name):
    def boom(*_args, **_kwargs):
        raise RuntimeError(f"{name} exploded")
    monkeypatch.setattr(target, name, boom)


@pytest.mark.parametrize("stage, patch", [
    ("Seed preparation", lambda mp: _fail(mp, reset_service, "seed_files")),
    ("Seed load", lambda mp: _fail(mp, reset_service.engine, "run")),
    ("Seed evidence staging", lambda mp: _fail(mp, reset_service, "stage_seed_documents")),
    ("Seed evidence analysis", lambda mp: _fail(mp, __import__("app.documents.batch", fromlist=["x"]),
                                                "analyse_job")),
    ("Seeded example report", lambda mp: _fail(mp, report_service, "seed_previous_report")),
])
def test_g1_32_a_failure_in_any_stage_releases_the_lock_and_records_the_stage(
        client, test_settings, monkeypatch, stage, patch):
    """GEN-05 (TR-67, TR-68): whatever stage fails, the lock is released and says where and why.

    TR-67 found that a crash in the job's last write latched the seed batch `Processing` for ever.
    With a lock released in a `finally`, no stage can latch it, and the failure is recorded rather
    than only logged. The stage is asserted, not just the status (TR-68).
    """
    factory = _factory(client)
    patch(monkeypatch)
    with factory() as db:
        with pytest.raises(RuntimeError, match="exploded"):
            reset_service.start_reset(db, factory, ADMIN_PRINCIPAL)

    with factory() as db:
        assert reset_service.reset_in_progress(db) is None, f"a failure at {stage!r} must release the lock"
        lock = db.get(ResetLock, reset_service.LOCK_ID)
        assert lock.last_outcome == "Failed"
        assert lock.last_reason.startswith(f"{stage} failed"), lock.last_reason
        assert "exploded" in lock.last_reason


def test_g1_32_an_analysis_failure_writes_no_report_and_fails_the_reset(client, test_settings, monkeypatch):
    """GEN-05, S11 (TR-66): a report over a half-loaded portfolio would be worse than none."""
    from app.documents import batch as doc_batch

    factory = _factory(client)
    _fail(monkeypatch, doc_batch, "analyse_job")
    with factory() as db:
        with pytest.raises(RuntimeError):
            reset_service.start_reset(db, factory, ADMIN_PRINCIPAL)
    with factory() as db:  # a fresh session: the one above holds the batch as it created it
        assert db.scalar(select(func.count()).select_from(ModelRiskReport)) == 0, "no example was written"
        seed = db.scalars(select(ImportBatch).where(ImportBatch.source == "reset")
                          .order_by(ImportBatch.batch_id.desc())).first()
        assert seed.status == "Failed" and "Seed evidence analysis" in (seed.error_message or ""), \
            "the batch the caller was given says the reset failed, and where"


def test_g1_32_the_lock_is_claimed_atomically(db_session):
    """GEN-04, BL.12: two claimants cannot both hold it.

    The old guard read "is anything running?" and then proceeded, so two requests interleaving
    inside that window both saw nothing — on PostgreSQL they would have interleaved two destructive
    resets. The claim is now one conditional UPDATE: whoever's update matched the free row holds it.
    """
    with db_session() as db:
        assert reset_service.acquire_reset_lock(db, "first", "U-001") is True
        assert reset_service.acquire_reset_lock(db, "second", "U-001") is False
        assert reset_service.reset_in_progress(db).holder == "first"


def test_g1_32_only_the_holder_can_release_the_lock(db_session):
    """GEN-04: a late or repeated release by a finished reset cannot free someone else's lock."""
    with db_session() as db:
        assert reset_service.acquire_reset_lock(db, "current", "U-001")
    reset_service.release_reset_lock(db_session, "stale", "Completed")
    with db_session() as db:
        assert reset_service.reset_in_progress(db).holder == "current"
    reset_service.release_reset_lock(db_session, "current", "Completed")
    with db_session() as db:
        assert reset_service.reset_in_progress(db) is None


def test_g1_32_a_lock_left_by_a_stopped_application_is_recovered_with_a_reason(db_session):
    """GEN-05: the `finally` cannot run if the process itself dies mid-reset.

    Jobs run in the application's own process (`app.workers.runner`), so when it starts again no reset
    of its own can be running: a lock still held was left by an interrupted run. Startup releases it
    and records that, rather than leaving the product unresettable — FT-05's failure mode one level
    up.
    """
    with db_session() as db:
        assert reset_service.acquire_reset_lock(db, "dead", "U-001")
        reset_service.set_reset_stage(db_session, "dead", "Seed load")
        assert reset_service.recover_interrupted_reset(db) is True
        assert reset_service.reset_in_progress(db) is None
        lock = db.get(ResetLock, reset_service.LOCK_ID)
        assert lock.last_outcome == "Interrupted" and "Seed load" in lock.last_reason
        assert reset_service.recover_interrupted_reset(db) is False, "and does nothing when nothing is held"


def test_g1_32_starting_the_application_releases_an_interrupted_lock(db_session, monkeypatch):
    """GEN-05: the recovery above is wired to startup, not merely available."""
    from fastapi.testclient import TestClient

    import app.db
    from app.main import create_app

    monkeypatch.setattr(app.db, "SessionLocal", db_session)
    with db_session() as db:
        assert reset_service.acquire_reset_lock(db, "dead", "U-001")
    with TestClient(create_app()):  # entering the client runs the application's startup
        pass
    with db_session() as db:
        assert reset_service.reset_in_progress(db) is None
        assert db.get(ResetLock, reset_service.LOCK_ID).last_outcome == "Interrupted"


def test_g1_32_a_missing_baseline_releases_the_lock_as_failed(client, test_settings, monkeypatch):
    """GEN-05 (TR-72): the one stage that ends the reset without raising still releases the lock."""
    factory = _factory(client)
    monkeypatch.setattr(reset_service, "missing_baseline_settings", lambda _db: ["probe_setting"])
    with factory() as db:
        reset_service.start_reset(db, factory, ADMIN_PRINCIPAL)  # completes: the failure is recorded, not raised
    with factory() as db:
        assert reset_service.reset_in_progress(db) is None, "the baseline path must release the lock"
        lock = db.get(ResetLock, reset_service.LOCK_ID)
        assert lock.last_outcome == "Failed" and lock.last_reason.startswith("Baseline check failed")


def test_g1_32_a_refused_reset_deletes_nothing_regenerates_nothing_and_submits_nothing(
        client, db_session, test_settings, monkeypatch):
    """GEN-04 (TR-74): "nothing is deleted and no second job is submitted" - the clause no test held.

    Moving `regenerate_seed` ahead of the claim used to pass every test, although rewriting the seed
    folder under a running reset is exactly what the in-flight check exists to prevent.
    """
    from app.models import Model
    from app.workers import runner

    h = login(client, *ADMIN)
    with db_session() as db:
        assert reset_service.acquire_reset_lock(db, "running", "U-001")
        before = (db.scalar(select(func.count()).select_from(ImportBatch)),
                  db.scalar(select(func.count()).select_from(Model)))

    calls = []
    monkeypatch.setattr(reset_service, "regenerate_seed", lambda *a: calls.append("regenerate"))
    monkeypatch.setattr(reset_service, "seed_files", lambda *a: calls.append("seed_files") or [])
    monkeypatch.setattr(runner, "submit", lambda fn, *a: calls.append(f"submit:{fn.__name__}"))

    assert client.post("/api/admin/reset", headers=h).status_code == 409
    assert calls == [], f"a refused reset did {calls}; it must do nothing at all"
    with db_session() as db:
        after = (db.scalar(select(func.count()).select_from(ImportBatch)),
                 db.scalar(select(func.count()).select_from(Model)))
        assert after == before, "no batch created and nothing deleted"
        assert reset_service.reset_in_progress(db).holder == "running", \
            "and the running reset still holds the lock"


def test_g1_32_a_database_lock_on_the_claim_is_a_409_not_a_500(client, db_session, test_settings, monkeypatch):
    """GEN-04 (TR-70): a claim that cannot get SQLite's write lock means a reset is running.

    The claim is a write, so while a reset holds the write lock it fails with "database is locked"
    rather than matching zero rows. That reached the client as an HTTP 500 in 65% of second attempts
    in thread mode. It is the same answer as a refused claim, and gets the same 409.
    """
    from sqlalchemy.exc import OperationalError

    def locked(*_a, **_k):
        raise OperationalError("UPDATE reset_lock ...", {}, Exception("database is locked"))

    monkeypatch.setattr(reset_service, "acquire_reset_lock", locked)
    resp = client.post("/api/admin/reset", headers=login(client, *ADMIN))
    assert resp.status_code == 409, resp.text
    assert "already running" in resp.json()["detail"]


def test_g1_32_a_held_lock_is_answered_from_a_read_without_claiming(client, db_session, test_settings,
                                                                    monkeypatch):
    """GEN-04 (TR-70): when the lock is visibly held, the refusal is a plain read - no write is tried."""
    with db_session() as db:
        assert reset_service.acquire_reset_lock(db, "running", "U-001")

    def must_not_claim(*_a, **_k):
        raise AssertionError("a held lock must be answered from a read, before any claim is attempted")

    monkeypatch.setattr(reset_service, "acquire_reset_lock", must_not_claim)
    assert client.post("/api/admin/reset", headers=login(client, *ADMIN)).status_code == 409


def test_g1_32_in_thread_mode_every_second_reset_during_a_running_one_gets_409(file_client, test_settings):
    """GEN-04 (TR-70): the regression in the mode the product runs in, which CI's inline mode hides.

    One reset runs in background threads on a file-backed database while this test keeps trying to
    start another, through the same service call the API makes. Every attempt must be refused with a
    conflict - never accepted, never an unexpected error. Called at the service rather than over HTTP
    because a reset deletes and reloads users, so authenticated requests 401 for a moment (TR-71,
    BL.1) - a separate issue that would mask this one.
    """
    import time

    client, probe, factory = file_client
    test_settings.job_mode = "thread"  # restored by the test_settings fixture
    with factory() as db:
        reset_service.start_reset(db, factory, ADMIN_PRINCIPAL)

    refused, unexpected, accepted = 0, [], 0
    deadline = time.time() + 600
    while time.time() < deadline:
        with probe() as db:
            if reset_service.reset_in_progress(db) is None:
                break
        with factory() as db:
            try:
                reset_service.start_reset(db, factory, ADMIN_PRINCIPAL)
                accepted += 1
            except ConflictError as exc:
                assert exc.status_code == 409
                refused += 1
            except Exception as exc:  # noqa: BLE001 - collected, so the assertion can name them
                unexpected.append(f"{type(exc).__name__}: {exc}"[:200])
        time.sleep(0.01)
    else:
        pytest.fail("the background reset did not finish within 10 minutes")

    assert accepted == 0, f"{accepted} second reset(s) were accepted while one was running"
    assert unexpected == [], f"{len(unexpected)} attempt(s) failed with an error instead of 409: {unexpected[:3]}"
    assert refused > 10, f"only {refused} attempts were made while the reset ran; the test proved little"
    with probe() as db:
        lock = db.get(ResetLock, reset_service.LOCK_ID)
        assert lock.last_outcome == "Completed", lock.last_reason
