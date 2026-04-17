"""Production schema - BOMs, work orders, production schedules

Revision ID: 002
Revises: 001
Create Date: 2024-04-17 11:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create production enums
    op.execute("CREATE TYPE bom_status AS ENUM ('Draft', 'Active', 'Inactive', 'Archived')")
    op.execute("CREATE TYPE work_order_status AS ENUM ('Planned', 'Released', 'In Progress', 'Completed', 'Cancelled', 'On Hold')")
    op.execute("CREATE TYPE work_order_priority AS ENUM ('Low', 'Normal', 'High', 'Urgent')")
    op.execute("CREATE TYPE production_step_status AS ENUM ('Pending', 'In Progress', 'Completed', 'Skipped', 'Failed')")

    # Create bill_of_materials table
    op.create_table('bill_of_materials',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bom_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('finished_good_sku', sa.String(length=50), nullable=False),
        sa.Column('finished_good_name', sa.String(length=200), nullable=False),
        sa.Column('standard_quantity', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=10), nullable=False),
        sa.Column('status', sa.Enum('Draft', 'Active', 'Inactive', 'Archived', name='bom_status'), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('standard_cycle_time', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('setup_time', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('yield_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bom_code')
    )
    op.create_index('ix_bill_of_materials_bom_code', 'bill_of_materials', ['bom_code'])
    op.create_index('ix_bill_of_materials_finished_good_sku', 'bill_of_materials', ['finished_good_sku'])

    # Create bom_lines table
    op.create_table('bom_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bom_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_sku', sa.String(length=50), nullable=False),
        sa.Column('material_name', sa.String(length=200), nullable=False),
        sa.Column('material_category', sa.String(length=50), nullable=True),
        sa.Column('quantity_required', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=10), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('waste_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('is_optional', sa.Boolean(), nullable=False),
        sa.Column('substitution_sku', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['bom_id'], ['bill_of_materials.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bom_lines_material_sku', 'bom_lines', ['material_sku'])

    # Create work_orders table
    op.create_table('work_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('work_order_number', sa.String(length=50), nullable=False),
        sa.Column('bom_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('finished_good_sku', sa.String(length=50), nullable=False),
        sa.Column('finished_good_name', sa.String(length=200), nullable=False),
        sa.Column('quantity_ordered', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('quantity_produced', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=10), nullable=False),
        sa.Column('order_date', sa.Date(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('completion_date', sa.Date(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('status', sa.Enum('Planned', 'Released', 'In Progress', 'Completed', 'Cancelled', 'On Hold', name='work_order_status'), nullable=False),
        sa.Column('priority', sa.Enum('Low', 'Normal', 'High', 'Urgent', name='work_order_priority'), nullable=False),
        sa.Column('estimated_hours', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('actual_hours', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('yield_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('quality_status', sa.String(length=20), nullable=True),
        sa.Column('inspector', sa.String(length=100), nullable=True),
        sa.Column('inspection_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('completed_by', sa.String(length=100), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['bom_id'], ['bill_of_materials.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('work_order_number')
    )
    op.create_index('ix_work_orders_work_order_number', 'work_orders', ['work_order_number'])
    op.create_index('ix_work_orders_finished_good_sku', 'work_orders', ['finished_good_sku'])
    op.create_index('ix_work_orders_status', 'work_orders', ['status'])

    # Create production_steps table
    op.create_table('production_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('work_order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('step_name', sa.String(length=200), nullable=False),
        sa.Column('step_description', sa.Text(), nullable=True),
        sa.Column('estimated_minutes', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('actual_minutes', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('status', sa.Enum('Pending', 'In Progress', 'Completed', 'Skipped', 'Failed', name='production_step_status'), nullable=False),
        sa.Column('machine_id', sa.String(length=50), nullable=True),
        sa.Column('operator', sa.String(length=100), nullable=True),
        sa.Column('quality_notes', sa.Text(), nullable=True),
        sa.Column('passed_inspection', sa.Boolean(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_production_steps_work_order_id', 'production_steps', ['work_order_id'])

    # Create material_consumptions table
    op.create_table('material_consumptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('work_order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_sku', sa.String(length=50), nullable=False),
        sa.Column('material_name', sa.String(length=200), nullable=False),
        sa.Column('quantity_planned', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('quantity_actual', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('unit_of_measure', sa.String(length=10), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('total_cost', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('consumption_date', sa.DateTime(), nullable=True),
        sa.Column('consumed_by', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_material_consumptions_work_order_id', 'material_consumptions', ['work_order_id'])
    op.create_index('ix_material_consumptions_material_sku', 'material_consumptions', ['material_sku'])

    # Create production_schedules table
    op.create_table('production_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('schedule_date', sa.Date(), nullable=False),
        sa.Column('machine_id', sa.String(length=50), nullable=False),
        sa.Column('machine_name', sa.String(length=200), nullable=True),
        sa.Column('work_order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('work_order_number', sa.String(length=50), nullable=True),
        sa.Column('scheduled_start_time', sa.DateTime(), nullable=True),
        sa.Column('scheduled_end_time', sa.DateTime(), nullable=True),
        sa.Column('actual_start_time', sa.DateTime(), nullable=True),
        sa.Column('actual_end_time', sa.DateTime(), nullable=True),
        sa.Column('scheduled_hours', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('setup_hours', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('run_hours', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_production_schedules_schedule_date', 'production_schedules', ['schedule_date'])
    op.create_index('ix_production_schedules_machine_id', 'production_schedules', ['machine_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('production_schedules')
    op.drop_table('material_consumptions')
    op.drop_table('production_steps')
    op.drop_table('work_orders')
    op.drop_table('bom_lines')
    op.drop_table('bill_of_materials')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS production_step_status")
    op.execute("DROP TYPE IF EXISTS work_order_priority")
    op.execute("DROP TYPE IF EXISTS work_order_status")
    op.execute("DROP TYPE IF EXISTS bom_status")
