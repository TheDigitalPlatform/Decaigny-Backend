"""add prompts and app_settings tables

Revision ID: b1a2c3d4e5f6
Revises: 00a5eaeae2eb
Create Date: 2026-08-24 15:59:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1a2c3d4e5f6'
down_revision: Union[str, None] = '00a5eaeae2eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create app_settings table
    op.create_table(
        'app_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_app_settings_id'), 'app_settings', ['id'], unique=False)
    op.create_index(op.f('ix_app_settings_key'), 'app_settings', ['key'], unique=True)

    # Create prompts table
    op.create_table(
        'prompts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prompts_id'), 'prompts', ['id'], unique=False)
    op.create_index(op.f('ix_prompts_name'), 'prompts', ['name'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_prompts_name'), table_name='prompts')
    op.drop_index(op.f('ix_prompts_id'), table_name='prompts')
    op.drop_table('prompts')

    op.drop_index(op.f('ix_app_settings_key'), table_name='app_settings')
    op.drop_index(op.f('ix_app_settings_id'), table_name='app_settings')
    op.drop_table('app_settings')
