"""drop validation_reports table

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-04-26 00:00:00.000000

The validation_reports table backed an unused REST surface. The frontend
stopped calling those endpoints (commits 0f79481, 8e286f6, e0c1dc6 on main),
the backend endpoints/model/Celery task were removed, and no consumer
remains. Drop the table.

Idempotent on upgrade (`IF EXISTS`) — works whether the SDE chain or the
ai-interviewer chain created the table first. Downgrade recreates the
original column shape so a future revival has a working schema.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS validation_reports CASCADE")


def downgrade() -> None:
    op.create_table(
        'validation_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('pipeline_jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('mode', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('twin_count', sa.Integer(), nullable=True),
        sa.Column('real_count', sa.Integer(), nullable=True),
        sa.Column('report_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
