"""add persistent media metadata

Revision ID: 0003_media
Revises: 0002_pet_species_analyses
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_media"
down_revision = "0002_pet_species_analyses"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "media",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pet_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("animal_type", sa.String(length=10), nullable=False),
        sa.Column("media_type", sa.String(length=20), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False, unique=True),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_media_user_id", "media", ["user_id"])
    op.create_index("ix_media_pet_id", "media", ["pet_id"])


def downgrade():
    op.drop_index("ix_media_pet_id", table_name="media")
    op.drop_index("ix_media_user_id", table_name="media")
    op.drop_table("media")
