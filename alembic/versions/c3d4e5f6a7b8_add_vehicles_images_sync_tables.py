"""add vehicles, vehicle_images, and vehicle_syncs tables

Revision ID: c3d4e5f6a7b8
Revises: b1a2c3d4e5f6
Create Date: 2026-09-25 17:21:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b1a2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create vehicles table
    op.create_table(
        'vehicles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('erp_id', sa.String(length=100), nullable=False),
        sa.Column('vin', sa.String(length=50), nullable=True),
        sa.Column('stock_number', sa.String(length=100), nullable=True),
        sa.Column('make', sa.String(length=100), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('trim', sa.String(length=150), nullable=True),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('mileage', sa.Integer(), nullable=True),
        sa.Column('fuel_type', sa.String(length=50), nullable=True),
        sa.Column('transmission', sa.String(length=50), nullable=True),
        sa.Column('color', sa.String(length=100), nullable=True),
        sa.Column('body_type', sa.String(length=100), nullable=True),
        sa.Column('features', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='available', nullable=False),
        sa.Column('erp_status_raw', sa.String(length=255), nullable=True),
        sa.Column('is_new_to_us', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('isonline', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('issold', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('isnewinstock', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('first_seen_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_seen_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('sold_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('raw_payload', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicles_id'), 'vehicles', ['id'], unique=False)
    op.create_index(op.f('ix_vehicles_erp_id'), 'vehicles', ['erp_id'], unique=True)
    op.create_index(op.f('ix_vehicles_vin'), 'vehicles', ['vin'], unique=False)
    op.create_index(op.f('ix_vehicles_status'), 'vehicles', ['status'], unique=False)

    # 2. Create vehicle_images table
    op.create_table(
        'vehicle_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('vehicle_id', 'url', name='uq_vehicle_images_vehicle_id_url')
    )
    op.create_index(op.f('ix_vehicle_images_id'), 'vehicle_images', ['id'], unique=False)
    op.create_index(op.f('ix_vehicle_images_vehicle_id'), 'vehicle_images', ['vehicle_id'], unique=False)

    # 3. Create vehicle_syncs table
    op.create_table(
        'vehicle_syncs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=50), server_default='n8n', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='running', nullable=False),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('finished_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('fetched_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('updated_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('sold_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('skipped_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('meta', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_syncs_id'), 'vehicle_syncs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_vehicle_syncs_id'), table_name='vehicle_syncs')
    op.drop_table('vehicle_syncs')

    op.drop_index(op.f('ix_vehicle_images_vehicle_id'), table_name='vehicle_images')
    op.drop_index(op.f('ix_vehicle_images_id'), table_name='vehicle_images')
    op.drop_table('vehicle_images')

    op.drop_index(op.f('ix_vehicles_status'), table_name='vehicles')
    op.drop_index(op.f('ix_vehicles_vin'), table_name='vehicles')
    op.drop_index(op.f('ix_vehicles_erp_id'), table_name='vehicles')
    op.drop_index(op.f('ix_vehicles_id'), table_name='vehicles')
    op.drop_table('vehicles')
