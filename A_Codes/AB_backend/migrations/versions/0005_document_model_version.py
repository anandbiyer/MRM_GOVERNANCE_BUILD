"""Evidence is about one version of a model (BRD §24, §27): document.model_version and the staging
column behind it, document_upload_item.model_version.

Nullable, and the foreign key is composite over (model_id, model_version) — a NULL in any column of a
composite foreign key skips the check, so existing documents stay valid without a backfill.

Landed before Phase 6 on purpose: once monitoring runs attach evidence, adding the column would mean
migrating live associations rather than adding an empty one (review finding CR-07).

Revision ID: 0005_document_model_version
Revises: 0004_documents
Create Date: 2026-10-04
"""
import sqlalchemy as sa
from alembic import op

revision = "0005_document_model_version"
down_revision = "0004_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("document", sa.Column("model_version", sa.String(length=40), nullable=True))
    op.add_column("document_upload_item", sa.Column("model_version", sa.String(length=40), nullable=True))
    op.create_foreign_key(
        "fk_document_model_version", "document", "model_version",
        ["model_id", "model_version"], ["model_id", "version"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_document_model_version", "document", type_="foreignkey")
    op.drop_column("document_upload_item", "model_version")
    op.drop_column("document", "model_version")
