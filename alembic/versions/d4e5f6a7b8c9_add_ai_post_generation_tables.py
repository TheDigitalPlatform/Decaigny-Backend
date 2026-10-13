"""add ai post generation tables

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-10-12 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. prompts.prompt_type (existing rows become tones)
    op.add_column('prompts', sa.Column('prompt_type', sa.String(length=50), server_default='tone', nullable=False))
    op.create_index(op.f('ix_prompts_prompt_type'), 'prompts', ['prompt_type'], unique=False)

    # 2. app_settings.value -> Text
    op.alter_column('app_settings', 'value', existing_type=sa.String(length=255), type_=sa.Text(), existing_nullable=True)

    # 3. dealership_profiles
    op.create_table(
        'dealership_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('tagline', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=150), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=150), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('default_language', sa.String(length=5), server_default='nl', nullable=False),
        sa.Column('call_to_action', sa.Text(), nullable=True),
        sa.Column('signature', sa.Text(), nullable=True),
        sa.Column('hashtags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('preferred_phrases', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('banned_phrases', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('use_emojis', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_dealership_profiles_id'), 'dealership_profiles', ['id'], unique=False)

    # 4. generated_posts
    op.create_table(
        'generated_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('post_type', sa.String(length=30), nullable=False),
        sa.Column('tone_prompt_id', sa.Integer(), nullable=True),
        sa.Column('tone_name', sa.String(length=100), nullable=True),
        sa.Column('language', sa.String(length=5), nullable=False),
        sa.Column('headline', sa.String(length=255), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('call_to_action', sa.Text(), nullable=True),
        sa.Column('hashtags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='draft', nullable=False),
        sa.Column('version', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('is_current', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('ai_model', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tone_prompt_id'], ['prompts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_generated_posts_id'), 'generated_posts', ['id'], unique=False)
    op.create_index(op.f('ix_generated_posts_vehicle_id'), 'generated_posts', ['vehicle_id'], unique=False)
    op.create_index(op.f('ix_generated_posts_post_type'), 'generated_posts', ['post_type'], unique=False)
    op.create_index(op.f('ix_generated_posts_status'), 'generated_posts', ['status'], unique=False)
    op.create_index(op.f('ix_generated_posts_is_current'), 'generated_posts', ['is_current'], unique=False)
    op.create_index(
        'uq_generated_posts_current',
        'generated_posts',
        ['vehicle_id', 'post_type'],
        unique=True,
        postgresql_where=sa.text('is_current'),
    )

    # 5. ai_generation_logs
    op.create_table(
        'ai_generation_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=True),
        sa.Column('generated_post_id', sa.Integer(), nullable=True),
        sa.Column('post_type', sa.String(length=30), nullable=True),
        sa.Column('tone_name', sa.String(length=100), nullable=True),
        sa.Column('language', sa.String(length=5), nullable=True),
        sa.Column('source', sa.String(length=30), server_default='manual', nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('attempt', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('ai_model', sa.String(length=100), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('user_prompt', sa.Text(), nullable=True),
        sa.Column('raw_response', sa.Text(), nullable=True),
        sa.Column('validation_errors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['generated_post_id'], ['generated_posts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_generation_logs_id'), 'ai_generation_logs', ['id'], unique=False)
    op.create_index(op.f('ix_ai_generation_logs_vehicle_id'), 'ai_generation_logs', ['vehicle_id'], unique=False)
    op.create_index(op.f('ix_ai_generation_logs_post_type'), 'ai_generation_logs', ['post_type'], unique=False)
    op.create_index(op.f('ix_ai_generation_logs_status'), 'ai_generation_logs', ['status'], unique=False)
    op.create_index(op.f('ix_ai_generation_logs_created_at'), 'ai_generation_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('ai_generation_logs')
    op.drop_index('uq_generated_posts_current', table_name='generated_posts')
    op.drop_table('generated_posts')
    op.drop_table('dealership_profiles')
    op.alter_column('app_settings', 'value', existing_type=sa.Text(), type_=sa.String(length=255), existing_nullable=True)
    op.drop_index(op.f('ix_prompts_prompt_type'), table_name='prompts')
    op.drop_column('prompts', 'prompt_type')
