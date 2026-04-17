"""
Orders database models for XPanda ERP-Lite.
Contains models for customers, sales orders, order lines, and fulfillment.
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from enum import Enum

from sqlalchemy import Column, String, Integer, Numeric, DateTime, Date, Boolean, Text, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from database.connection import Base

logger = logging.getLogger(__name__)


class CustomerStatus(Enum):
    """Customer status enumeration."""
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    SUSPENDED = "Suspended"
    BLACKLISTED = "Blacklisted"


class OrderStatus(Enum):
    """Order status enumeration."""
    DRAFT = "Draft"
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    IN_PRODUCTION = "In Production"
    READY_TO_SHIP = "Ready to Ship"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"
    RETURNED = "Returned"


class OrderPriority(Enum):
    """Order priority enumeration."""
    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"
    URGENT = "Urgent"


class PaymentStatus(Enum):
    """Payment status enumeration."""
    PENDING = "Pending"
    PAID = "Paid"
    PARTIALLY_PAID = "Partially Paid"
    OVERDUE = "Overdue"
    REFUNDED = "Refunded"


class FulfillmentStatus(Enum):
    """Fulfillment status enumeration."""
    PENDING = "Pending"
    PARTIALLY_FULFILLED = "Partially Fulfilled"
    FULFILLED = "Fulfilled"
    BACKORDERED = "Backordered"
    CANCELLED = "Cancelled"


class Customer(Base):
    """Customer model for managing customer information."""
    
    __tablename__ = 'customers'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Basic information
    customer_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    company_name = Column(String(200), nullable=True)
    
    # Contact information
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    website = Column(String(200), nullable=True)
    
    # Address information
    billing_address_line1 = Column(String(200), nullable=False)
    billing_address_line2 = Column(String(200), nullable=True)
    billing_city = Column(String(100), nullable=False)
    billing_state = Column(String(50), nullable=False)
    billing_postal_code = Column(String(20), nullable=False)
    billing_country = Column(String(100), nullable=False, default='USA')
    
    shipping_address_line1 = Column(String(200), nullable=True)
    shipping_address_line2 = Column(String(200), nullable=True)
    shipping_city = Column(String(100), nullable=True)
    shipping_state = Column(String(50), nullable=True)
    shipping_postal_code = Column(String(20), nullable=True)
    shipping_country = Column(String(100), nullable=True)
    
    # Business information
    customer_type = Column(String(50), nullable=True)  # Wholesale, Retail, etc.
    tax_exempt = Column(Boolean, nullable=False, default=False)
    tax_id = Column(String(50), nullable=True)
    credit_limit = Column(Numeric(12, 2), nullable=True)
    payment_terms = Column(String(50), nullable=True)  # NET30, NET15, etc.
    
    # Status and lifecycle
    status = Column(String(20), nullable=False, default=CustomerStatus.ACTIVE.value)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    sales_orders = relationship("SalesOrder", back_populates="customer")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('credit_limit >= 0', name='check_credit_limit_positive'),
    )
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status value."""
        valid_statuses = [s.value for s in CustomerStatus]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        return status
    
    @property
    def is_active(self) -> bool:
        """Check if customer is active."""
        return self.status == CustomerStatus.ACTIVE.value
    
    @property
    def full_billing_address(self) -> str:
        """Get full billing address."""
        address_parts = [
            self.billing_address_line1,
            self.billing_address_line2,
            f"{self.billing_city}, {self.billing_state} {self.billing_postal_code}",
            self.billing_country
        ]
        return ", ".join(filter(None, address_parts))
    
    @property
    def full_shipping_address(self) -> str:
        """Get full shipping address."""
        if self.shipping_address_line1:
            address_parts = [
                self.shipping_address_line1,
                self.shipping_address_line2,
                f"{self.shipping_city}, {self.shipping_state} {self.shipping_postal_code}",
                self.shipping_country or self.billing_country
            ]
            return ", ".join(filter(None, address_parts))
        return self.full_billing_address
    
    def __repr__(self):
        return f"<Customer(customer_code='{self.customer_code}', name='{self.name}', status='{self.status}')>"


class SalesOrder(Base):
    """Sales order model for managing customer orders."""
    
    __tablename__ = 'sales_orders'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Order information
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=False)
    customer_purchase_order = Column(String(100), nullable=True)
    
    # Dates
    order_date = Column(Date, nullable=False, default=func.current_date())
    requested_ship_date = Column(Date, nullable=True)
    promised_ship_date = Column(Date, nullable=True)
    actual_ship_date = Column(Date, nullable=True)
    delivery_date = Column(Date, nullable=True)
    
    # Status and priority
    status = Column(String(20), nullable=False, default=OrderStatus.DRAFT.value)
    priority = Column(String(10), nullable=False, default=OrderPriority.NORMAL.value)
    
    # Financial information
    subtotal = Column(Numeric(12, 2), nullable=False, default=Decimal('0.00'))
    tax_amount = Column(Numeric(12, 2), nullable=False, default=Decimal('0.00'))
    shipping_amount = Column(Numeric(12, 2), nullable=False, default=Decimal('0.00'))
    total_amount = Column(Numeric(12, 2), nullable=False, default=Decimal('0.00'))
    paid_amount = Column(Numeric(12, 2), nullable=False, default=Decimal('0.00'))
    
    # Payment information
    payment_status = Column(String(20), nullable=False, default=PaymentStatus.PENDING.value)
    payment_method = Column(String(50), nullable=True)
    payment_terms = Column(String(50), nullable=True)
    
    # Fulfillment information
    fulfillment_status = Column(String(25), nullable=False, default=FulfillmentStatus.PENDING.value)
    tracking_number = Column(String(100), nullable=True)
    carrier = Column(String(100), nullable=True)
    
    # Internal information
    sales_rep = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="sales_orders")
    order_lines = relationship("OrderLine", back_populates="sales_order", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('subtotal >= 0', name='check_subtotal_positive'),
        CheckConstraint('tax_amount >= 0', name='check_tax_amount_positive'),
        CheckConstraint('shipping_amount >= 0', name='check_shipping_amount_positive'),
        CheckConstraint('total_amount >= 0', name='check_total_amount_positive'),
        CheckConstraint('paid_amount >= 0', name='check_paid_amount_positive'),
    )
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status value."""
        valid_statuses = [s.value for s in OrderStatus]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        return status
    
    @validates('priority')
    def validate_priority(self, key, priority):
        """Validate priority value."""
        valid_priorities = [p.value for p in OrderPriority]
        if priority not in valid_priorities:
            raise ValueError(f"Invalid priority: {priority}. Must be one of {valid_priorities}")
        return priority
    
    @validates('payment_status')
    def validate_payment_status(self, key, payment_status):
        """Validate payment status value."""
        valid_statuses = [s.value for s in PaymentStatus]
        if payment_status not in valid_statuses:
            raise ValueError(f"Invalid payment status: {payment_status}. Must be one of {valid_statuses}")
        return payment_status
    
    @validates('fulfillment_status')
    def validate_fulfillment_status(self, key, fulfillment_status):
        """Validate fulfillment status value."""
        valid_statuses = [s.value for s in FulfillmentStatus]
        if fulfillment_status not in valid_statuses:
            raise ValueError(f"Invalid fulfillment status: {fulfillment_status}. Must be one of {valid_statuses}")
        return fulfillment_status
    
    @property
    def balance_due(self) -> Decimal:
        """Calculate balance due."""
        return self.total_amount - self.paid_amount
    
    @property
    def is_overdue(self) -> bool:
        """Check if payment is overdue."""
        if self.payment_status in [PaymentStatus.PAID.value, PaymentStatus.REFUNDED.value]:
            return False
        
        # Simple check - if order is older than 30 days and not paid
        if self.order_date:
            days_old = (date.today() - self.order_date).days
            return days_old > 30 and self.balance_due > 0
        
        return False
    
    @property
    def total_quantity(self) -> Decimal:
        """Calculate total quantity across all order lines."""
        return sum(line.quantity for line in self.order_lines)
    
    @property
    def fulfillment_percentage(self) -> Decimal:
        """Calculate fulfillment percentage."""
        if self.total_quantity == 0:
            return Decimal('0')
        
        fulfilled_quantity = sum(line.quantity_shipped for line in self.order_lines)
        return (fulfilled_quantity / self.total_quantity) * Decimal('100')
    
    def __repr__(self):
        return f"<SalesOrder(order_number='{self.order_number}', status='{self.status}', total={self.total_amount})>"


class OrderLine(Base):
    """Order line model for individual items in a sales order."""
    
    __tablename__ = 'order_lines'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Foreign key
    sales_order_id = Column(UUID(as_uuid=True), ForeignKey('sales_orders.id'), nullable=False)
    
    # Product information
    product_sku = Column(String(50), nullable=False, index=True)
    product_name = Column(String(200), nullable=False)
    product_description = Column(Text, nullable=True)
    
    # Quantity information
    quantity = Column(Numeric(10, 4), nullable=False)
    quantity_shipped = Column(Numeric(10, 4), nullable=False, default=Decimal('0'))
    quantity_backordered = Column(Numeric(10, 4), nullable=False, default=Decimal('0'))
    unit_of_measure = Column(String(10), nullable=False, default='EA')
    
    # Pricing information
    unit_price = Column(Numeric(12, 4), nullable=False)
    discount_percentage = Column(Numeric(5, 2), nullable=False, default=Decimal('0'))
    line_total = Column(Numeric(12, 2), nullable=False)
    
    # Additional information
    notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # Relationships
    sales_order = relationship("SalesOrder", back_populates="order_lines")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        CheckConstraint('quantity_shipped >= 0', name='check_quantity_shipped_positive'),
        CheckConstraint('quantity_backordered >= 0', name='check_quantity_backordered_positive'),
        CheckConstraint('unit_price >= 0', name='check_unit_price_positive'),
        CheckConstraint('discount_percentage >= 0 AND discount_percentage <= 100', name='check_discount_percentage_range'),
    )
    
    @property
    def effective_price(self) -> Decimal:
        """Calculate effective price after discount."""
        if self.discount_percentage > 0:
            discount_amount = self.unit_price * (self.discount_percentage / Decimal('100'))
            return self.unit_price - discount_amount
        return self.unit_price
    
    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity to ship."""
        return self.quantity - self.quantity_shipped
    
    @property
    def is_fully_shipped(self) -> bool:
        """Check if line is fully shipped."""
        return self.quantity_shipped >= self.quantity
    
    @property
    def is_backordered(self) -> bool:
        """Check if line has backordered quantity."""
        return self.quantity_backordered > 0
    
    def __repr__(self):
        return f"<OrderLine(product_sku='{self.product_sku}', quantity={self.quantity}, unit_price={self.unit_price})>"


class Shipment(Base):
    """Shipment model for tracking order fulfillment."""
    
    __tablename__ = 'shipments'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Shipment information
    shipment_number = Column(String(50), unique=True, nullable=False, index=True)
    sales_order_id = Column(UUID(as_uuid=True), ForeignKey('sales_orders.id'), nullable=True)
    
    # Dates
    ship_date = Column(Date, nullable=False, default=func.current_date())
    expected_delivery_date = Column(Date, nullable=True)
    actual_delivery_date = Column(Date, nullable=True)
    
    # Shipping information
    carrier = Column(String(100), nullable=False)
    tracking_number = Column(String(100), nullable=True)
    shipping_method = Column(String(50), nullable=True)
    freight_cost = Column(Numeric(12, 2), nullable=True)
    
    # Address information
    ship_to_address_line1 = Column(String(200), nullable=False)
    ship_to_address_line2 = Column(String(200), nullable=True)
    ship_to_city = Column(String(100), nullable=False)
    ship_to_state = Column(String(50), nullable=False)
    ship_to_postal_code = Column(String(20), nullable=False)
    ship_to_country = Column(String(100), nullable=False, default='USA')
    
    # Status
    status = Column(String(20), nullable=False, default='Shipped')
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    sales_order = relationship("SalesOrder")
    shipment_lines = relationship("ShipmentLine", back_populates="shipment", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('freight_cost >= 0', name='check_freight_cost_positive'),
    )
    
    @property
    def full_ship_to_address(self) -> str:
        """Get full shipping address."""
        address_parts = [
            self.ship_to_address_line1,
            self.ship_to_address_line2,
            f"{self.ship_to_city}, {self.ship_to_state} {self.ship_to_postal_code}",
            self.ship_to_country
        ]
        return ", ".join(filter(None, address_parts))
    
    def __repr__(self):
        return f"<Shipment(shipment_number='{self.shipment_number}', carrier='{self.carrier}', status='{self.status}')>"


class ShipmentLine(Base):
    """Shipment line model for tracking items in a shipment."""
    
    __tablename__ = 'shipment_lines'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Foreign key
    shipment_id = Column(UUID(as_uuid=True), ForeignKey('shipments.id'), nullable=False)
    order_line_id = Column(UUID(as_uuid=True), ForeignKey('order_lines.id'), nullable=False)
    
    # Product information
    product_sku = Column(String(50), nullable=False)
    product_name = Column(String(200), nullable=False)
    
    # Quantity information
    quantity = Column(Numeric(10, 4), nullable=False)
    unit_of_measure = Column(String(10), nullable=False, default='EA')
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # Relationships
    shipment = relationship("Shipment", back_populates="shipment_lines")
    order_line = relationship("OrderLine")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_shipment_quantity_positive'),
    )
    
    def __repr__(self):
        return f"<ShipmentLine(product_sku='{self.product_sku}', quantity={self.quantity})>"
