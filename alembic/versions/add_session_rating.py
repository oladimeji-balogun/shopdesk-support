"""add rating column to sessions

Revision ID: add_session_rating
Revises: add_admin_role
Create Date: 2026-05-11

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'add_session_rating'
down_revision: Union[str, Sequence[str], None] = 'add_admin_role'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sessions', sa.Column('rating', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('sessions', 'rating')
