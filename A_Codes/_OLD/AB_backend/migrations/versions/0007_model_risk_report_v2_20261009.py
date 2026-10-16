"""Add model_risk_report for the core Model Risk Report (BRD §48, §12A REQ-REG-10A).

The figures are not stored in the row. A report's content lives in the object store at
`storage_path`, and `content_hash` is the SHA-256 of that content, so REG-16 can compare two
generations without reading either. The row is the record that a report was produced, by whom, and
for which business date.

`generated_by` is a plain user id with no foreign key, the same choice as `import_batch.uploaded_by`:
report history has to survive a demo reset, which deletes and reloads `app_user`.

`previous_report_id` is self-referential and nullable — the first report has no predecessor, which is
why "changes since the previous report" is empty rather than absent in that one.

`is_seeded` marks the example a reset creates, so the report list and the reopened report can say so
(spec issues S11 and S12, the D12 addendum). Edited into this migration rather than added by a
follow-up, because 0007 has not reached `main`.

Revision ID: 0007_model_risk_report
Revises: 0006_document_fk_widths
Create Date: 2026-10-07
"""
import sqlalchemy as sa
from alembic import op

revision = "0007_model_risk_report"
down_revision = "0006_document_fk_widths"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_risk_report",
        sa.Column("report_id", sa.String(40), primary_key=True),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.Column("generated_by", sa.String(20), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.Column("framework_label", sa.String(200), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("storage_path", sa.String(400), nullable=False),
        sa.Column("previous_report_id", sa.String(40),
                  sa.ForeignKey("model_risk_report.report_id"), nullable=True),
        # The example a reset seeds. Not derived from `generated_by is None`: "no user generated
        # this" and "this is a shaped example" are different statements, and only the second is
        # safe to put on a screen (S11, S12).
        sa.Column("is_seeded", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_model_risk_report_business_date", "model_risk_report", ["business_date"])
    op.create_index("ix_model_risk_report_generated_by", "model_risk_report", ["generated_by"])
    op.create_index("ix_model_risk_report_content_hash", "model_risk_report", ["content_hash"])


def downgrade() -> None:
    op.drop_index("ix_model_risk_report_content_hash", table_name="model_risk_report")
    op.drop_index("ix_model_risk_report_generated_by", table_name="model_risk_report")
    op.drop_index("ix_model_risk_report_business_date", table_name="model_risk_report")
    op.drop_table("model_risk_report")
