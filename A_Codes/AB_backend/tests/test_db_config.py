"""Database engine configuration (app/db.configure_sqlite).

SQLite is the dev and test engine (Part 0), and the settings applied here are what let concurrent
requests share one database file. The UI issues several API calls per page load, so this is ordinary
use, not a stress case: with the default rollback journal, a connection that had read and then
needed to write could not promote its lock and SQLite returned SQLITE_BUSY immediately, without
consulting the busy handler. Uploading a document returned HTTP 500 (FT-01, plan G0.17).

BRD §64 (Reliability: "Database writes shall be transactional") is the requirement these serve.
§64 has no acceptance criteria, the same gap §76A.14 records for §65, so these tests cite the
section and the issue rather than a criterion ID.
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.db import configure_sqlite


def _pragma(engine, name: str):
    with engine.connect() as conn:
        return conn.execute(text(f"PRAGMA {name}")).scalar()


@pytest.fixture
def file_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'probe.db'}")
    configure_sqlite(engine)
    yield engine
    engine.dispose()


def test_a_file_database_uses_wal(file_engine):
    """WAL is the load-bearing half: in WAL mode readers do not block the writer at all.

    Without it, an upload while the dashboard's queries are open fails outright rather than waiting,
    so no timeout value can rescue it.
    """
    assert _pragma(file_engine, "journal_mode") == "wal"


def test_foreign_keys_stay_enforced(file_engine):
    """Guards the pre-existing behaviour the new pragmas sit next to."""
    assert _pragma(file_engine, "foreign_keys") == 1


def test_an_in_memory_database_still_works(tmp_path):
    """The test suite's own engine is in-memory, where WAL does not exist.

    SQLite answers "memory" and does not raise, so the WAL pragma must not be made conditional on
    something that would break this engine. The timeout still applies.
    """
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    configure_sqlite(engine)
    try:
        assert _pragma(engine, "journal_mode") == "memory"
        assert _pragma(engine, "busy_timeout") > 0, "a timeout is set; its value is proved below"
        assert _pragma(engine, "foreign_keys") == 1
    finally:
        engine.dispose()


def test_the_busy_timeout_is_applied_and_configurable(tmp_path, monkeypatch):
    """Proves both that the pragma is set and that the value is not hard-coded.

    It has to override the setting to prove anything. Asserting the default would be a test that
    cannot fail: pysqlite already applies a 5000 ms busy timeout of its own, which is exactly our
    default, so such a test passes identically whether or not `configure_sqlite` sets the pragma.
    An earlier version of this file made that mistake and only the defect simulation caught it.
    """
    monkeypatch.setenv("MRM_SQLITE_BUSY_TIMEOUT_MS", "12345")
    get_settings.cache_clear()
    try:
        engine = create_engine(f"sqlite:///{tmp_path / 'configured.db'}")
        configure_sqlite(engine)
        try:
            assert _pragma(engine, "busy_timeout") == 12345
        finally:
            engine.dispose()
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()  # the cache would otherwise hand the override to later tests


def test_settings_are_cached_once_per_process():
    """Why the test above must clear the cache in teardown, not just undo the environment variable:
    settings are read once and reused, so a leaked override would apply to every later test."""
    assert get_settings() is get_settings()
    assert hasattr(get_settings, "cache_clear"), "the teardown above depends on this"


def test_a_dev_database_gains_a_nullable_column_a_newer_build_added(tmp_path):
    """§64, G1.31: the launcher keeps a `create_all` dev database usable across a column addition.

    `create_all` adds missing tables but never missing columns, so after G1.31 added
    `model_risk_report.figures_as_of`, an existing `dev.db` would fail on its first report read
    (CR-62's class). `add_missing_columns` adds nullable columns the ORM has and SQLite lacks, and
    nothing else: it never alters, drops, or adds a NOT NULL column it could not fill.
    """
    from app.db import add_missing_columns
    from app.models import Base

    engine = create_engine(f"sqlite:///{(tmp_path / 'old.db').as_posix()}")
    configure_sqlite(engine)
    Base.metadata.create_all(engine)
    with engine.begin() as conn:  # make the table look like it did before G1.31
        conn.execute(text("ALTER TABLE model_risk_report DROP COLUMN figures_as_of"))

    added = add_missing_columns(engine)
    assert added == ["model_risk_report.figures_as_of"]
    with engine.connect() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(model_risk_report)"))}
    assert "figures_as_of" in cols
    assert add_missing_columns(engine) == [], "and a second run finds nothing to add"
