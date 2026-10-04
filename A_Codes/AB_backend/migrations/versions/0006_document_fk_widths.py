"""Narrow validation.report_document_id and approval.supporting_document_id to VARCHAR(20) so the
migrated schema matches the ORM.

Migration 0002 created both as String(40), before the `document` table existed to be referenced. The
ORM declares them as `ForeignKey("document.document_id")` with no explicit length, so SQLAlchemy takes
the referenced column's type — String(20). The two have disagreed ever since, and nothing noticed
because the drift guard (tests/test_postgres.py::test_migrations_match_orm_models) only runs when
MRM_TEST_POSTGRES_URL is set, which had never happened locally or in CI.

Narrowing is safe: document ids are of the form "D-000001" (8 characters) and the column is only ever
written with one.

Found while verifying 0005 against a real PostgreSQL, not by the change itself.

Revision ID: 0006_document_fk_widths
Revises: 0005_document_model_version
Create Date: 2026-10-04
"""
import sqlalchemy as sa
from alembic import op

revision = "0006_document_fk_widths"
down_revision = "0005_document_model_version"
branch_labels = None
depends_on = None

_COLUMNS = (("validation", "report_document_id"), ("approval", "supporting_document_id"))


def upgrade() -> None:
    for table, column in _COLUMNS:
        op.alter_column(table, column, existing_type=sa.String(40), type_=sa.String(20),
                        existing_nullable=True)


def downgrade() -> None:
    for table, column in _COLUMNS:
        op.alter_column(table, column, existing_type=sa.String(20), type_=sa.String(40),
                        existing_nullable=True)
