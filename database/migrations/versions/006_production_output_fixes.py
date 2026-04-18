"""Add work_order_number to production_outputs

Revision ID: 006_production_output_fixes
Revises: 005_shop_floor_schema
Create Date: 2026-04-17 18:00:00.000000

The production_outputs table stores work_order_id as Integer while work_orders.id
is UUID — a type mismatch from initial scaffolding. The FK constraint was never
successfully created by PostgreSQL. This migration adds a work_order_number text
column so we can store a meaningful reference without relying on the broken FK.
"""
from alembic import op
import sqlalchemy as sa

revision = '006_production_output_fixes'
down_revision = '005_shop_floor_schema'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'production_outputs',
        sa.Column('work_order_number', sa.String(50), nullable=True)
    )
    op.create_index(
        'idx_output_work_order_number',
        'production_outputs',
        ['work_order_number'],
        unique=False
    )


def downgrade():
    op.drop_index('idx_output_work_order_number', table_name='production_outputs')
    op.drop_column('production_outputs', 'work_order_number')
