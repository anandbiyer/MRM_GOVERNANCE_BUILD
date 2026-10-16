from collections.abc import Callable, Iterator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def configure_sqlite(engine: Engine) -> None:
    """SQLite (dev/tests only): let SQLAlchemy control transactions so SAVEPOINTs work, and enforce FKs.

    This is the workaround documented by SQLAlchemy for the pysqlite driver's transaction handling.

    WAL and a busy timeout are what make concurrent requests survive on one database file. One page
    load of the UI issues several API calls at once, each on its own connection; with the default
    rollback journal, a connection that has read and then needs to write must promote its lock, and
    SQLite refuses a promotion that would roll back another reader by returning SQLITE_BUSY
    *immediately* — without consulting the busy handler, so a timeout alone does not help. Uploading
    a document therefore returned HTTP 500 under ordinary use (FT-01). In WAL mode readers do not
    block the writer and the promotion does not arise. The timeout covers plain write-write waits,
    which the busy handler does serve. On an in-memory database (the test engine) WAL is not
    available and the pragma is a documented no-op returning "memory"; the timeout still applies.
    """
    busy_timeout_ms = get_settings().sqlite_busy_timeout_ms

    @event.listens_for(engine, "connect")
    def _connect(dbapi_conn, _):
        dbapi_conn.isolation_level = None
        dbapi_conn.execute("PRAGMA foreign_keys=ON")
        dbapi_conn.execute("PRAGMA journal_mode=WAL")
        dbapi_conn.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")

    @event.listens_for(engine, "begin")
    def _begin(conn):
        conn.exec_driver_sql("BEGIN")


engine = create_engine(get_settings().database_url, pool_pre_ping=True)
if engine.dialect.name == "sqlite":
    configure_sqlite(engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session_factory() -> Callable[[], Session]:
    """Background jobs open their own sessions from this factory (overridden in tests)."""
    return SessionLocal
