"""fixed the fault in the database schema

Revision ID: caff9653c9ca
Revises: 37301fafb676
Create Date: 2026-03-07 12:33:43.457627

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'caff9653c9ca'
down_revision: Union[str, Sequence[str], None] = '37301fafb676'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Columns already exist, just backfill existing rows with defaults
    op.execute("UPDATE users SET role = 'CUSTOMER' WHERE role IS NULL")
    op.execute("UPDATE users SET hashed_password = '' WHERE hashed_password IS NULL")

    # Now safely enforce NOT NULL
    op.alter_column('users', 'role',
        existing_type=postgresql.ENUM('CUSTOMER', 'AGENT', name='userrole'),
        nullable=False
    )
    op.alter_column('users', 'hashed_password',
        existing_type=sa.VARCHAR(),
        nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('users', 'role',
        existing_type=postgresql.ENUM('CUSTOMER', 'AGENT', name='userrole'),
        nullable=True
    )
    op.alter_column('users', 'hashed_password',
        existing_type=sa.VARCHAR(),
        nullable=True
    )