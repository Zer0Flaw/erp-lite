"""Orders schema - customers, sales orders, shipments

Revision ID: 003
Revises: 002
Create Date: 2024-04-17 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create orders enums
    op.execute("CREATE TYPE customer_status AS ENUM ('Active', 'Inactive', 'Suspended', 'Blacklisted')")
    op.execute("CREATE TYPE order_status AS ENUM ('Draft', 'Pending', 'Confirmed', 'In Production', 'Ready to Ship', 'Shipped', 'Delivered', 'Cancelled', 'Returned')")
    op.execute("CREATE TYPE order_priority AS ENUM ('Low', 'Normal', 'High', 'Urgent')")
    op.execute("CREATE TYPE payment_status AS ENUM ('Pending', 'Paid', 'Partially Paid', 'Overdue', 'Refunded')")
    op.execute("CREATE TYPE fulfillment_status AS ENUM ('Pending', 'Partially Fulfilled', 'Fulfilled', 'Backordered', 'Cancelled')")

    # Create customers table
    op.create_table('customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('company_name', sa.String(length=200), nullable=True),
        sa.Column('contact_person', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('website', sa.String(length=200), nullable=True),
        sa.Column('billing_address_line1', sa.String(length=200), nullable=False),
        sa.Column('billing_address_line2', sa.String(length=200), nullable=True),
        sa.Column('billing_city', sa.String(length=100), nullable=False),
        sa.Column('billing_state', sa.String(length=50), nullable=False),
        sa.Column('billing_postal_code', sa.String(length=20), nullable=False),
        sa.Column('billing_country', sa.String(length=100), nullable=False, server_default='USA'),
        sa.Column('shipping_address_line1', sa.String(length=200), nullable=True),
        sa.Column('shipping_address_line2', sa.String(length=200), nullable=True),
        sa.Column('shipping_city', sa.String(length=100), nullable=True),
        sa.Column('shipping_state', sa.String(length=50), nullable=True),
        sa.Column('shipping_postal_code', sa.String(length=20), nullable=True),
        sa.Column('shipping_country', sa.String(length=100), nullable=True),
        sa.Column('customer_type', sa.String(length=50), nullable=True),
        sa.Column('tax_exempt', sa.Boolean(), nullable=False),
        sa.Column('tax_id', sa.String(length=50), nullable=True),
        sa.Column('credit_limit', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('payment_terms', sa.String(length=50), nullable=True),
        sa.Column('status', sa.Enum('Active', 'Inactive', 'Suspended', 'Blacklisted', name='customer_status'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_code')
    )
    op.create_index('ix_customers_customer_code', 'customers', ['customer_code'])
    op.create_index('ix_customers_status', 'customers', ['status'])

    # Create sales_orders table
    op.create_table('sales_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_number', sa.String(length=50), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_purchase_order', sa.String(length=100), nullable=True),
        sa.Column('order_date', sa.Date(), nullable=False, server_default=sa.text('current_date')),
        sa.Column('requested_ship_date', sa.Date(), nullable=True),
        sa.Column('promised_ship_date', sa.Date(), nullable=True),
        sa.Column('actual_ship_date', sa.Date(), nullable=True),
        sa.Column('delivery_date', sa.Date(), nullable=True),
        sa.Column('status', sa.Enum('Draft', 'Pending', 'Confirmed', 'In Production', 'Ready to Ship', 'Shipped', 'Delivered', 'Cancelled', 'Returned', name='order_status'), nullable=False),
        sa.Column('priority', sa.Enum('Low', 'Normal', 'High', 'Urgent', name='order_priority'), nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('shipping_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('paid_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('payment_status', sa.Enum('Pending', 'Paid', 'Partially Paid', 'Overdue', 'Refunded', name='payment_status'), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('payment_terms', sa.String(length=50), nullable=True),
        sa.Column('fulfillment_status', sa.Enum('Pending', 'Partially Fulfilled', 'Fulfilled', 'Backordered', 'Cancelled', name='fulfillment_status'), nullable=False),
        sa.Column('tracking_number', sa.String(length=100), nullable=True),
        sa.Column('carrier', sa.String(length=100), nullable=True),
        sa.Column('sales_rep', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number')
    )
    op.create_index('ix_sales_orders_order_number', 'sales_orders', ['order_number'])
    op.create_index('ix_sales_orders_customer_id', 'sales_orders', ['customer_id'])
    op.create_index('ix_sales_orders_status', 'sales_orders', ['status'])

    # Create order_lines table
    op.create_table('order_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sales_order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_sku', sa.String(length=50), nullable=False),
        sa.Column('product_name', sa.String(length=200), nullable=False),
        sa.Column('product_description', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('quantity_shipped', sa.Numeric(precision=10, scale=4), nullable=False, server_default='0.00'),
        sa.Column('quantity_backordered', sa.Numeric(precision=10, scale=4), nullable=False, server_default='0.00'),
        sa.Column('unit_of_measure', sa.String(length=10), nullable=False, server_default='EA'),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('discount_percentage', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('line_total', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_order_lines_sales_order_id', 'order_lines', ['sales_order_id'])
    op.create_index('ix_order_lines_product_sku', 'order_lines', ['product_sku'])

    # Create shipments table
    op.create_table('shipments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shipment_number', sa.String(length=50), nullable=False),
        sa.Column('sales_order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ship_date', sa.Date(), nullable=False, server_default=sa.text('current_date')),
        sa.Column('expected_delivery_date', sa.Date(), nullable=True),
        sa.Column('actual_delivery_date', sa.Date(), nullable=True),
        sa.Column('carrier', sa.String(length=100), nullable=False),
        sa.Column('tracking_number', sa.String(length=100), nullable=True),
        sa.Column('shipping_method', sa.String(length=50), nullable=True),
        sa.Column('freight_cost', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('ship_to_address_line1', sa.String(length=200), nullable=False),
        sa.Column('ship_to_address_line2', sa.String(length=200), nullable=True),
        sa.Column('ship_to_city', sa.String(length=100), nullable=False),
        sa.Column('ship_to_state', sa.String(length=50), nullable=False),
        sa.Column('ship_to_postal_code', sa.String(length=20), nullable=False),
        sa.Column('ship_to_country', sa.String(length=100), nullable=False, server_default='USA'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='Shipped'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('shipment_number')
    )
    op.create_index('ix_shipments_shipment_number', 'shipments', ['shipment_number'])
    op.create_index('ix_shipments_sales_order_id', 'shipments', ['sales_order_id'])

    # Create shipment_lines table
    op.create_table('shipment_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shipment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_line_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_sku', sa.String(length=50), nullable=False),
        sa.Column('product_name', sa.String(length=200), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=10), nullable=False, server_default='EA'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ),
        sa.ForeignKeyConstraint(['order_line_id'], ['order_lines.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_shipment_lines_shipment_id', 'shipment_lines', ['shipment_id'])
    op.create_index('ix_shipment_lines_order_line_id', 'shipment_lines', ['order_line_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('shipment_lines')
    op.drop_table('shipments')
    op.drop_table('order_lines')
    op.drop_table('sales_orders')
    op.drop_table('customers')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS fulfillment_status")
    op.execute("DROP TYPE IF EXISTS payment_status")
    op.execute("DROP TYPE IF EXISTS order_priority")
    op.execute("DROP TYPE IF EXISTS order_status")
    op.execute("DROP TYPE IF EXISTS customer_status")
