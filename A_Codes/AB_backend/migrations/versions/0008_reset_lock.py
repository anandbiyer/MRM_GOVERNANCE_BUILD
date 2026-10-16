"""Add reset_lock, the explicit lock a reset holds from start to end (plan G1.32, BRD §48).

Replaces inferring "a reset is running" from import batch statuses, which failed twice in the same
way (review findings CR-53 and TR-65): each time one commit left every reset batch terminal while the
reset still had writing to do, and a second reset would have been accepted with its deletes racing
the first. A reset now claims the single row with one conditional UPDATE, holds it, and releases it
in a `finally` that records the outcome and, on failure, the stage.

One row, inserted here, so the claim is always an UPDATE of an existing row — an atomic compare-and-
set on both SQLite and PostgreSQL, which also closes BL.12 (the old read-then-proceed guard could
interleave two resets on PostgreSQL). No foreign keys, for two reasons (corrected by CR-59):
`acquired_by` points at an `app_user` row the reset deletes and reloads, the reasoning of
`import_batch.uploaded_by`; `batch_id` points at an `import_batch` row the reset keeps, and has no
foreign key so that releasing the lock, which happens in a `finally`, can never fail a referential check.

Revision ID: 0008_reset_lock
Revises: 0007_model_risk_report
Create Date: 2026-10-15
"""
import sqlalchemy as sa
from alembic import op

revision = "0008_reset_lock"
down_revision = "0007_model_risk_report"
branch_labels = None
depends_on = None


def upgrade() -> None:
    table = op.create_table(
        "reset_lock",
        sa.Column("lock_id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("holder", sa.String(40), nullable=True),
        sa.Column("batch_id", sa.String(40), nullable=True),
        sa.Column("acquired_by", sa.String(20), nullable=True),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stage", sa.String(80), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_outcome", sa.String(20), nullable=True),
        sa.Column("last_reason", sa.Text(), nullable=True),
    )
    op.bulk_insert(table, [{"lock_id": 1}])


def downgrade() -> None:
    op.drop_table("reset_lock")
