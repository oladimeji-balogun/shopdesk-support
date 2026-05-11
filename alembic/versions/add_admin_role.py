"""add admin role to userrole enum

Revision ID: add_admin_role
Revises: 06d1449b2894
Create Date: 2026-05-11

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'add_admin_role'
down_revision: Union[str, Sequence[str], None] = '06d1449b2894'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'admin'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values — no-op
    pass
