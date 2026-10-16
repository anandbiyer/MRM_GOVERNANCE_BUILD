"""Model risk report endpoints (BRD §54 `/api/reports`, §12A REQ-REG-10A)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import CurrentPrincipal, DbSession, require
from app.auth.roles import Permission
from app.auth.security import Principal
from app.reports import pdf
from app.schemas.governance import ModelRiskReportDetail, ModelRiskReportOut
from app.services import report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/model-risk", response_model=ModelRiskReportDetail, status_code=201)
def generate_model_risk_report(
    db: DbSession,
    principal: Annotated[Principal, Depends(require(Permission.REPORT_GENERATE))],
):
    """Generate a report for the current business date (REQ-REG-10A).

    There is no date parameter by design: a report is always for `app.clock.today()`, and history is
    the stored reports below.
    """
    report, content = report_service.generate(db, principal)
    return ModelRiskReportDetail(**ModelRiskReportOut.model_validate(report).model_dump(),
                                 sections=content)


@router.get("/model-risk", response_model=list[ModelRiskReportOut])
def list_model_risk_reports(db: DbSession, _: CurrentPrincipal):
    """Earlier reports, newest first. Any read role may list them (REQ-REG-10A)."""
    return report_service.list_reports(db)


@router.get("/model-risk/{report_id}", response_model=ModelRiskReportDetail)
def read_model_risk_report(report_id: str, db: DbSession, _: CurrentPrincipal):
    report = report_service.get_report(db, report_id)
    return ModelRiskReportDetail(**ModelRiskReportOut.model_validate(report).model_dump(),
                                 sections=report_service.read_sections(report))


@router.get("/model-risk/{report_id}/pdf")
def download_model_risk_report(report_id: str, db: DbSession, _: CurrentPrincipal):
    """The stored report as a PDF. Rendered from the stored copy, never recomputed."""
    report = report_service.get_report(db, report_id)
    header = ModelRiskReportOut.model_validate(report).model_dump()
    data = pdf.render(header, report_service.read_sections(report))
    return Response(content=data, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="{report_id}.pdf"'})
