"""Initial schema - inventory tables

Revision ID: 001
Revises: 
Create Date: 2024-04-17 11:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create material_category enum
    op.execute("CREATE TYPE material_category AS ENUM ('Raw Material', 'Finished Good', 'Consumable', 'Packaging')")
    
    # Create transaction_type enum
    op.execute("CREATE TYPE transaction_type AS ENUM ('Receiving', 'Consumption', 'Adjustment', 'Transfer')")
    
    # Create adjustment_reason enum
    op.execute("CREATE TYPE adjustment_reason AS ENUM ('Damage', 'Theft', 'Count Adjustment', 'Expiry', 'Quality Issue', 'Other')")

    # Create materials table
    op.create_table('materials',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sku', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.Enum('Raw Material', 'Finished Good', 'Consumable', 'Packaging', name='material_category'), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=10), nullable=False),
        sa.Column('weight_per_unit', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('dimensions', sa.String(length=100), nullable=True),
        sa.Column('reorder_point', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('max_stock_level', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('preferred_supplier', sa.String(length=200), nullable=True),
        sa.Column('storage_location', sa.String(length=100), nullable=True),
        sa.Column('standard_cost', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('average_cost', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('last_cost', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('expansion_ratio', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('density_target', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('mold_id', sa.String(length=50), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True, default=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sku')
    )
    op.create_index('ix_materials_sku', 'materials', ['sku'])
    op.create_index('ix_materials_category', 'materials', ['category'])
    op.create_index('ix_materials_active', 'materials', ['active'])

    # Create inventory_transactions table
    op.create_table('inventory_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_type', sa.Enum('Receiving', 'Consumption', 'Adjustment', 'Transfer', name='transaction_type'), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('total_cost', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('reference_type', sa.String(length=20), nullable=True),
        sa.Column('reference_number', sa.String(length=50), nullable=True),
        sa.Column('lot_number', sa.String(length=50), nullable=True),
        sa.Column('batch_number', sa.String(length=50), nullable=True),
        sa.Column('reason_code', sa.Enum('Damage', 'Theft', 'Count Adjustment', 'Expiry', 'Quality Issue', 'Other', name='adjustment_reason'), nullable=True),
        sa.Column('transaction_date', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('posted', sa.Boolean(), nullable=False, default=False),
        sa.Column('posted_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_inventory_transactions_material_id', 'inventory_transactions', ['material_id'])
    op.create_index('ix_inventory_transactions_type', 'inventory_transactions', ['transaction_type'])
    op.create_index('ix_inventory_transactions_date', 'inventory_transactions', ['transaction_date'])

    # Create material_suppliers table
    op.create_table('material_suppliers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('supplier_name', sa.String(length=200), nullable=False),
        sa.Column('supplier_code', sa.String(length=50), nullable=True),
        sa.Column('supplier_sku', sa.String(length=100), nullable=True),
        sa.Column('lead_time_days', sa.Integer(), nullable=True),
        sa.Column('minimum_order_quantity', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('unit_cost', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('preferred', sa.Boolean(), nullable=False, default=False),
        sa.Column('active', sa.Boolean(), nullable=False, default=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_material_suppliers_material_id', 'material_suppliers', ['material_id'])
    op.create_index('ix_material_suppliers_preferred', 'material_suppliers', ['preferred'])

    # Create inventory_summary table
    op.create_table('inventory_summary',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('on_hand', sa.Numeric(precision=10, scale=4), nullable=False, default=0),
        sa.Column('committed', sa.Numeric(precision=10, scale=4), nullable=False, default=0),
        sa.Column('available', sa.Numeric(precision=10, scale=4), nullable=False, default=0),
        sa.Column('on_order', sa.Numeric(precision=10, scale=4), nullable=False, default=0),
        sa.Column('total_value', sa.Numeric(precision=12, scale=4), nullable=False, default=0),
        sa.Column('average_unit_cost', sa.Numeric(precision=10, scale=4), nullable=False, default=0),
        sa.Column('last_transaction_date', sa.DateTime(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('material_id')
    )
    op.create_index('ix_inventory_summary_on_hand', 'inventory_summary', ['on_hand'])

    # Create stock_adjustments table
    op.create_table('stock_adjustments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('adjustment_type', sa.Enum('Damage', 'Theft', 'Count Adjustment', 'Expiry', 'Quality Issue', 'Other', name='adjustment_reason'), nullable=False),
        sa.Column('quantity_before', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('quantity_after', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('adjustment_quantity', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('approved_by', sa.String(length=100), nullable=True),
        sa.Column('adjustment_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_stock_adjustments_material_id', 'stock_adjustments', ['material_id'])
    op.create_index('ix_stock_adjustments_date', 'stock_adjustments', ['adjustment_date'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('stock_adjustments')
    op.drop_table('inventory_summary')
    op.drop_table('material_suppliers')
    op.drop_table('inventory_transactions')
    op.drop_table('materials')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS adjustment_reason")
    op.execute("DROP TYPE IF EXISTS transaction_type")
    op.execute("DROP TYPE IF EXISTS material_category")
