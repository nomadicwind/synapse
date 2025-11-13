"""add last_error column to knowledge_items

Revision ID: 002_add_last_error_column
Revises: 001
Create Date: 2024-02-20 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002_add_last_error_column"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("knowledge_items", sa.Column("last_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("knowledge_items", "last_error")
