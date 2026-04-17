"""Quality schema - inspections, NCRs, CAPAs

Revision ID: 004
Revises: 003
Create Date: 2024-04-17 11:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create quality enums
    op.execute("CREATE TYPE inspection_type AS ENUM ('Incoming', 'In Process', 'Final', 'Customer Return')")
    op.execute("CREATE TYPE inspection_status AS ENUM ('Scheduled', 'In Progress', 'Passed', 'Failed', 'Rework Required', 'Cancelled')")
    op.execute("CREATE TYPE ncr_status AS ENUM ('Open', 'Under Investigation', 'Disposition Required', 'Closed', 'Cancelled')")
    op.execute("CREATE TYPE ncr_severity AS ENUM ('Minor', 'Major', 'Critical')")
    op.execute("CREATE TYPE ncr_disposition AS ENUM ('Use As Is', 'Rework', 'Repair', 'Scrap', 'Return to Vendor')")
    op.execute("CREATE TYPE capa_status AS ENUM ('Open', 'In Progress', 'Completed', 'Verified', 'Closed', 'Cancelled')")
    op.execute("CREATE TYPE capa_priority AS ENUM ('Low', 'Medium', 'High', 'Urgent')")

    # Create inspections table
    op.create_table('inspections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inspection_number', sa.String(length=50), nullable=False),
        sa.Column('inspection_type', sa.Enum('Incoming', 'In Process', 'Final', 'Customer Return', name='inspection_type'), nullable=False),
        sa.Column('status', sa.Enum('Scheduled', 'In Progress', 'Passed', 'Failed', 'Rework Required', 'Cancelled', name='inspection_status'), nullable=False),
        sa.Column('work_order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sales_order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('material_sku', sa.String(length=50), nullable=True),
        sa.Column('batch_number', sa.String(length=50), nullable=True),
        sa.Column('inspection_date', sa.Date(), nullable=False, server_default=sa.text('current_date')),
        sa.Column('inspector', sa.String(length=100), nullable=False),
        sa.Column('quantity_inspected', sa.Integer(), nullable=False),
        sa.Column('quantity_passed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quantity_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quantity_rework', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('overall_result', sa.String(length=10), nullable=True),
        sa.Column('acceptance_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('inspection_procedure', sa.String(length=100), nullable=True),
        sa.Column('specifications', sa.String(length=200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('inspection_number')
    )
    op.create_index('ix_inspections_inspection_number', 'inspections', ['inspection_number'])
    op.create_index('ix_inspections_status', 'inspections', ['status'])
    op.create_index('ix_inspections_material_sku', 'inspections', ['material_sku'])
    op.create_index('ix_inspections_batch_number', 'inspections', ['batch_number'])

    # Create inspection_lines table
    op.create_table('inspection_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('characteristic', sa.String(length=200), nullable=False),
        sa.Column('specification', sa.String(length=200), nullable=True),
        sa.Column('measurement_method', sa.String(length=100), nullable=True),
        sa.Column('measured_value', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('tolerance_min', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('tolerance_max', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('result', sa.String(length=10), nullable=True),
        sa.Column('deviation', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_inspection_lines_inspection_id', 'inspection_lines', ['inspection_id'])

    # Create non_conformance_reports table
    op.create_table('non_conformance_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ncr_number', sa.String(length=50), nullable=False),
        sa.Column('status', sa.Enum('Open', 'Under Investigation', 'Disposition Required', 'Closed', 'Cancelled', name='ncr_status'), nullable=False),
        sa.Column('severity', sa.String(length=10), nullable=False),
        sa.Column('disposition', sa.String(length=20), nullable=True),
        sa.Column('inspection_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('work_order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sales_order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('material_sku', sa.String(length=50), nullable=True),
        sa.Column('batch_number', sa.String(length=50), nullable=True),
        sa.Column('discovery_date', sa.Date(), nullable=False, server_default=sa.text('current_date')),
        sa.Column('reported_by', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('investigation_summary', sa.Text(), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('investigation_date', sa.Date(), nullable=True),
        sa.Column('investigator', sa.String(length=100), nullable=True),
        sa.Column('disposition_date', sa.Date(), nullable=True),
        sa.Column('disposition_by', sa.String(length=100), nullable=True),
        sa.Column('disposition_notes', sa.Text(), nullable=True),
        sa.Column('closure_date', sa.Date(), nullable=True),
        sa.Column('closed_by', sa.String(length=100), nullable=True),
        sa.Column('closure_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], ),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ncr_number')
    )
    op.create_index('ix_non_conformance_reports_ncr_number', 'non_conformance_reports', ['ncr_number'])
    op.create_index('ix_non_conformance_reports_status', 'non_conformance_reports', ['status'])
    op.create_index('ix_non_conformance_reports_severity', 'non_conformance_reports', ['severity'])
    op.create_index('ix_non_conformance_reports_material_sku', 'non_conformance_reports', ['material_sku'])

    # Create capa_actions table
    op.create_table('capa_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('capa_number', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('status', sa.Enum('Open', 'In Progress', 'Completed', 'Verified', 'Closed', 'Cancelled', name='capa_status'), nullable=False),
        sa.Column('priority', sa.Enum('Low', 'Medium', 'High', 'Urgent', name='capa_priority'), nullable=False),
        sa.Column('ncr_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('corrective_action', sa.Text(), nullable=True),
        sa.Column('preventive_action', sa.Text(), nullable=True),
        sa.Column('assigned_to', sa.String(length=100), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('created_date', sa.Date(), nullable=False, server_default=sa.text('current_date')),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('completion_date', sa.Date(), nullable=True),
        sa.Column('verification_date', sa.Date(), nullable=True),
        sa.Column('effectiveness_rating', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('effectiveness_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('completed_by', sa.String(length=100), nullable=True),
        sa.Column('verified_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['ncr_id'], ['non_conformance_reports.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('capa_number')
    )
    op.create_index('ix_capa_actions_capa_number', 'capa_actions', ['capa_number'])
    op.create_index('ix_capa_actions_status', 'capa_actions', ['status'])
    op.create_index('ix_capa_actions_priority', 'capa_actions', ['priority'])
    op.create_index('ix_capa_actions_assigned_to', 'capa_actions', ['assigned_to'])

    # Create quality_metrics table
    op.create_table('quality_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('target_value', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('actual_value', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('variance', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('denominator', sa.Integer(), nullable=True),
        sa.Column('numerator', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_quality_metrics_metric_name', 'quality_metrics', ['metric_name'])
    op.create_index('ix_quality_metrics_period_start', 'quality_metrics', ['period_start'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('quality_metrics')
    op.drop_table('capa_actions')
    op.drop_table('non_conformance_reports')
    op.drop_table('inspection_lines')
    op.drop_table('inspections')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS capa_priority")
    op.execute("DROP TYPE IF EXISTS capa_status")
    op.execute("DROP TYPE IF EXISTS ncr_disposition")
    op.execute("DROP TYPE IF EXISTS ncr_severity")
    op.execute("DROP TYPE IF EXISTS ncr_status")
    op.execute("DROP TYPE IF EXISTS inspection_status")
    op.execute("DROP TYPE IF EXISTS inspection_type")
