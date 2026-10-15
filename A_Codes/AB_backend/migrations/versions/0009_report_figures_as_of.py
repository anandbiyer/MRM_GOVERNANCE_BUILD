"""Add model_risk_report.figures_as_of — the business date a report's figures were computed for.

Decided by **D14** (2026-10-15, review findings TR-48 and CR-55). The seeded example a reset creates is
dated a month before the seed's business date, so the first real report has a month of changes to
show, while its figures are computed from the seed as it stands. TR-48 found the two dates silently
disagreeing. D14 keeps the earlier date and discloses both, which needs the figures' date stored:
`generated_at` is itself shaped on the seeded example, and deriving the date from the seeding offset
would misdate already-stored reports if that offset ever changed.

For every report a user generates `figures_as_of` equals `business_date`; only the seeded example
differs. Nullable, because reports stored before this migration have no value. No index: it is
displayed, never filtered on.

Revision ID: 0009_report_figures_as_of
Revises: 0008_reset_lock
Create Date: 2026-10-15
"""
import sqlalchemy as sa
from alembic import op

revision = "0009_report_figures_as_of"
down_revision = "0008_reset_lock"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("model_risk_report", sa.Column("figures_as_of", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("model_risk_report", "figures_as_of")
