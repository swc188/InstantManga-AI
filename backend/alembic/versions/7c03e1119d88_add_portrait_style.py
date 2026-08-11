"""add portrait_style to characters

Revision ID: 7c03e1119d88
Revises: 6b02d0009cd7
Create Date: 2026-08-11
"""
from alembic import op
import sqlalchemy as sa

revision = '7c03e1119d88'
down_revision = '6b02d0009cd7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('characters', sa.Column('portrait_style', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('characters', 'portrait_style')
