"""Shop Floor schema

Revision ID: 005_shop_floor_schema
Revises: 004_quality_schema
Create Date: 2026-04-17 13:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_shop_floor_schema'
down_revision = '004_quality_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Create time_entries table
    op.create_table('time_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.String(length=50), nullable=False),
        sa.Column('employee_name', sa.String(length=100), nullable=False),
        sa.Column('work_order_id', sa.Integer(), nullable=True),
        sa.Column('operation', sa.String(length=50), nullable=False),
        sa.Column('station_id', sa.String(length=50), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('total_hours', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('badge_scan', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_time_entry_employee_date', 'time_entries', ['employee_id', 'start_time'], unique=False)
    op.create_index('idx_time_entry_work_order', 'time_entries', ['work_order_id'], unique=False)
    op.create_index('idx_time_entry_station', 'time_entries', ['station_id'], unique=False)
    op.create_index('idx_time_entry_status', 'time_entries', ['status'], unique=False)

    # Create production_outputs table
    op.create_table('production_outputs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('work_order_id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=True),
        sa.Column('output_type', sa.String(length=20), nullable=False),
        sa.Column('quantity_produced', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('quantity_scrapped', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('theoretical_yield', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('actual_yield', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('yield_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('length', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('width', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('height', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('density', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('lot_number', sa.String(length=50), nullable=True),
        sa.Column('bead_batch', sa.String(length=50), nullable=True),
        sa.Column('bead_lot_number', sa.String(length=50), nullable=True),
        sa.Column('expansion_batch', sa.String(length=50), nullable=True),
        sa.Column('mold_id', sa.String(length=50), nullable=True),
        sa.Column('operator_id', sa.String(length=50), nullable=False),
        sa.Column('operator_name', sa.String(length=100), nullable=False),
        sa.Column('station_id', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('quality_status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['production_batches.id'], ),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_output_work_order', 'production_outputs', ['work_order_id'], unique=False)
    op.create_index('idx_output_batch', 'production_outputs', ['batch_id'], unique=False)
    op.create_index('idx_output_lot', 'production_outputs', ['lot_number'], unique=False)
    op.create_index('idx_output_bead_batch', 'production_outputs', ['bead_batch'], unique=False)
    op.create_index('idx_output_operator', 'production_outputs', ['operator_id'], unique=False)
    op.create_index('idx_output_timestamp', 'production_outputs', ['timestamp'], unique=False)

    # Create production_batches table
    op.create_table('production_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_number', sa.String(length=50), nullable=False),
        sa.Column('batch_type', sa.String(length=20), nullable=False),
        sa.Column('raw_material_lot', sa.String(length=50), nullable=True),
        sa.Column('input_batch_id', sa.Integer(), nullable=True),
        sa.Column('work_order_id', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('operator_id', sa.String(length=50), nullable=False),
        sa.Column('operator_name', sa.String(length=100), nullable=False),
        sa.Column('station_id', sa.String(length=50), nullable=True),
        sa.Column('parameters', sa.Text(), nullable=True),
        sa.Column('input_quantity', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('output_quantity', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('scrap_quantity', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('quality_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['input_batch_id'], ['production_batches.id'], ),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('batch_number')
    )
    op.create_index('idx_batch_number', 'production_batches', ['batch_number'], unique=False)
    op.create_index('idx_batch_type', 'production_batches', ['batch_type'], unique=False)
    op.create_index('idx_batch_raw_material', 'production_batches', ['raw_material_lot'], unique=False)
    op.create_index('idx_batch_work_order', 'production_batches', ['work_order_id'], unique=False)
    op.create_index('idx_batch_operator', 'production_batches', ['operator_id'], unique=False)
    op.create_index('idx_batch_station', 'production_batches', ['station_id'], unique=False)

    # Create production_stations table
    op.create_table('production_stations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('station_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('station_type', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('current_work_order_id', sa.Integer(), nullable=True),
        sa.Column('current_operator_id', sa.String(length=50), nullable=True),
        sa.Column('current_operator_name', sa.String(length=100), nullable=True),
        sa.Column('current_batch_id', sa.Integer(), nullable=True),
        sa.Column('capacity_per_hour', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('max_block_size', sa.String(length=50), nullable=True),
        sa.Column('temperature_range', sa.String(length=50), nullable=True),
        sa.Column('last_maintenance_date', sa.Date(), nullable=True),
        sa.Column('next_maintenance_date', sa.Date(), nullable=True),
        sa.Column('maintenance_hours', sa.Integer(), nullable=False),
        sa.Column('total_runtime_hours', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('department', sa.String(length=50), nullable=True),
        sa.Column('status_reason', sa.String(length=200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['current_batch_id'], ['production_batches.id'], ),
        sa.ForeignKeyConstraint(['current_work_order_id'], ['work_orders.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('station_id')
    )
    op.create_index('idx_station_id', 'production_stations', ['station_id'], unique=False)
    op.create_index('idx_station_type', 'production_stations', ['station_type'], unique=False)
    op.create_index('idx_station_status', 'production_stations', ['status'], unique=False)
    op.create_index('idx_station_location', 'production_stations', ['location'], unique=False)
    op.create_index('idx_station_current_work', 'production_stations', ['current_work_order_id'], unique=False)


def downgrade():
    # Drop production_stations table
    op.drop_table('production_stations')
    
    # Drop production_batches table
    op.drop_table('production_batches')
    
    # Drop production_outputs table
    op.drop_table('production_outputs')
    
    # Drop time_entries table
    op.drop_table('time_entries')
