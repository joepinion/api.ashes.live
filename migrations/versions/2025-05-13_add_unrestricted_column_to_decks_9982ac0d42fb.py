"""add unrestricted column to decks

Revision ID: 9982ac0d42fb
Revises: c1d8d8b6925f
Create Date: 2025-05-13 14:42:06.834727+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9982ac0d42fb"
down_revision = "c1d8d8b6925f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("deck", sa.Column("is_unrestricted", sa.Boolean(), nullable=False, server_default='0'))
    op.create_index(
        op.f("ix_deck_is_unrestricted"), "deck", ["is_unrestricted"], unique=False
    )


def downgrade():
    op.drop_column("deck", "is_unrestricted")
