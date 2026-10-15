import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (admin, audit, auth, dashboard, documents, health, imports, models, records,
                     reports, users)
from app.config import get_settings
from app.services.errors import ServiceError


log = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """At startup, release a reset lock left held by a run this application did not live to finish.

    A reset releases its lock in a `finally`, which cannot run if the process dies mid-reset; jobs run
    in this process, so on a fresh start no reset of its own can be running (G1.32, GEN-05). Without
    this, one killed server would leave the product unable to reset at all. A failure here is logged
    and does not stop the application starting.
    """
    from app.db import SessionLocal
    from app.services import reset_service

    try:
        with SessionLocal() as db:
            reset_service.recover_interrupted_reset(db)
    except Exception:  # noqa: BLE001 — e.g. a database created before migration 0008; never block startup
        log.exception("Could not check the reset lock at startup")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=_lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ServiceError)
    async def service_error_handler(_: Request, exc: ServiceError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, "errors": exc.details})

    for module in (health, auth, users, admin, audit, models, imports, documents, dashboard,
                   reports):
        app.include_router(module.router)
    for router in (records.validations, records.findings, records.approvals):
        app.include_router(router)
    return app


app = create_app()
