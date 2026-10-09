"""Stored model risk reports (BRD §48 `model_risk_report`, §12A REQ-REG-10A)."""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy import false as sa_false
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ModelRiskReport(Base):
    """One generated report. The figures live in the stored copy at `storage_path`, not here.

    A report is always generated for the current business date (REQ-REG-10A, D12 amendment): there is
    no past-date parameter, because derived governance state is recomputed on read. These rows *are*
    the history, which is why nothing about them is recalculated later.
    """

    __tablename__ = "model_risk_report"

    report_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    business_date: Mapped[date] = mapped_column(Date, index=True)
    # Plain user id, no FK: report history must survive a demo reset that reloads users, the same
    # reasoning as `import_batch.uploaded_by`.
    generated_by: Mapped[str | None] = mapped_column(String(20), index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    framework_label: Mapped[str] = mapped_column(String(200))
    # SHA-256 of the canonical content, so REG-16 can compare two generations without diffing text.
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    storage_path: Mapped[str] = mapped_column(String(400))
    previous_report_id: Mapped[str | None] = mapped_column(
        String(40), ForeignKey("model_risk_report.report_id"))
    # The example a reset seeds, so the screens can say so (S11, S12 / the D12 addendum). Its
    # *figures* are the service's, like any other report; what is shaped is its baseline, which
    # exists to be diffed and is not a reported figure. The flag is what discloses that.
    is_seeded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False,
                                            server_default=sa_false())
