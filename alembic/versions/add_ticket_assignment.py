"""add assigned_to column to escalation_tickets

Revision ID: add_ticket_assignment
Revises: add_session_rating
Create Date: 2026-05-11

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = 'add_ticket_assignment'
down_revision: Union[str, Sequence[str], None] = 'add_session_rating'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'escalation_tickets',
        sa.Column('assigned_to', UUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('escalation_tickets', 'assigned_to')
