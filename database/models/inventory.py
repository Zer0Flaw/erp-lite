"""
Inventory database models for XPanda ERP-Lite.
Defines the data structure for materials, inventory transactions, and related entities.
"""

import uuid
from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import (
    Column, String, Text, Numeric, Integer, DateTime, 
    ForeignKey, CheckConstraint, Index, Boolean
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property

from database.connection import Base


class MaterialCategory(str, Enum):
    """Material category enumeration."""
    RAW_MATERIAL = "Raw Material"
    FINISHED_GOOD = "Finished Good"
    CONSUMABLE = "Consumable"
    PACKAGING = "Packaging"


class TransactionType(str, Enum):
    """Inventory transaction type enumeration."""
    RECEIVING = "Receiving"
    ADJUSTMENT = "Adjustment"
    CONSUMPTION = "Consumption"
    TRANSFER = "Transfer"
    RETURN = "Return"


class AdjustmentReason(str, Enum):
    """Stock adjustment reason enumeration."""
    DAMAGE = "Damage"
    CYCLE_COUNT = "Cycle Count"
    SCRAP = "Scrap"
    RETURN = "Return"
    OTHER = "Other"


class Material(Base):
    """
    Material master record.
    Defines the basic properties of all inventory items.
    """
    __tablename__ = 'materials'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False, default=MaterialCategory.RAW_MATERIAL.value)
    
    # Unit of measure and dimensions
    unit_of_measure = Column(String(10), nullable=False, default='EA')
    weight_per_unit = Column(Numeric(10, 4))  # Weight per unit in pounds
    dimensions = Column(String(100))  # L x W x H format
    
    # Inventory management
    reorder_point = Column(Numeric(12, 4), default=0)
    max_stock_level = Column(Numeric(12, 4))
    preferred_supplier = Column(String(200))
    storage_location = Column(String(50))
    
    # Cost information
    standard_cost = Column(Numeric(12, 4))
    average_cost = Column(Numeric(12, 4))
    last_cost = Column(Numeric(12, 4))
    
    # EPS-specific fields (for foam manufacturing)
    expansion_ratio = Column(Numeric(8, 4))  # EPS expansion ratio
    density_target = Column(Numeric(8, 4))   # Target density (lb/ft³)
    mold_id = Column(String(50))             # Associated mold ID
    
    # Status and flags
    active = Column(Boolean, default=True, nullable=False)
    is_kit = Column(Boolean, default=False)  # For BOM kits
    notes = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=False)
    deleted_at = Column(DateTime)  # Soft delete
    
    # Relationships
    inventory_transactions = relationship("InventoryTransaction", back_populates="material")
    material_suppliers = relationship("MaterialSupplier", back_populates="material")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('reorder_point >= 0', name='check_reorder_point_positive'),
        CheckConstraint('standard_cost >= 0', name='check_standard_cost_positive'),
        CheckConstraint('average_cost >= 0', name='check_average_cost_positive'),
        CheckConstraint('last_cost >= 0', name='check_last_cost_positive'),
        Index('idx_material_category', 'category'),
        Index('idx_material_active', 'active'),
        Index('idx_material_deleted_at', 'deleted_at'),
    )
    
    @validates('sku')
    def validate_sku(self, key, sku):
        """Validate SKU format."""
        if not sku or len(sku.strip()) == 0:
            raise ValueError('SKU cannot be empty')
        return sku.strip().upper()
    
    @validates('category')
    def validate_category(self, key, category):
        """Validate category is a valid enum value."""
        valid_categories = [cat.value for cat in MaterialCategory]
        if category not in valid_categories:
            raise ValueError(f'Invalid category: {category}')
        return category
    
    @hybrid_property
    def is_low_stock(self) -> bool:
        """Check if material is below reorder point."""
        # This will be calculated based on current stock levels
        # Implementation will use current_on_hand from inventory aggregation
        return False  # Placeholder - will be implemented with proper stock calculation
    
    def __repr__(self):
        return f"<Material(sku='{self.sku}', name='{self.name}', category='{self.category}')>"


class InventoryTransaction(Base):
    """
    Inventory transaction record.
    Tracks all stock movements for materials.
    """
    __tablename__ = 'inventory_transactions'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Transaction details
    material_id = Column(UUID(as_uuid=True), ForeignKey('materials.id'), nullable=False)
    transaction_type = Column(String(20), nullable=False)
    quantity = Column(Numeric(12, 4), nullable=False)
    unit_cost = Column(Numeric(12, 4))
    total_cost = Column(Numeric(12, 4))
    
    # Reference information
    reference_type = Column(String(20))  # PO, WO, ADJ, etc.
    reference_number = Column(String(50))
    lot_number = Column(String(50))
    batch_number = Column(String(50))
    
    # Transaction metadata
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    reason_code = Column(String(50))  # For adjustments
    notes = Column(Text)
    
    # Status
    posted = Column(Boolean, default=False, nullable=False)
    posted_date = Column(DateTime)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=False)
    
    # Relationships
    material = relationship("Material", back_populates="inventory_transactions")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('quantity <> 0', name='check_quantity_nonzero'),
        CheckConstraint('unit_cost >= 0', name='check_unit_cost_positive'),
        CheckConstraint('total_cost >= 0', name='check_total_cost_positive'),
        Index('idx_transaction_material', 'material_id'),
        Index('idx_transaction_date', 'transaction_date'),
        Index('idx_transaction_type', 'transaction_type'),
        Index('idx_transaction_reference', 'reference_type', 'reference_number'),
        Index('idx_transaction_posted', 'posted'),
    )
    
    @validates('transaction_type')
    def validate_transaction_type(self, key, transaction_type):
        """Validate transaction type."""
        valid_types = [t.value for t in TransactionType]
        if transaction_type not in valid_types:
            raise ValueError(f'Invalid transaction type: {transaction_type}')
        return transaction_type
    
    @validates('reason_code')
    def validate_reason_code(self, key, reason_code):
        """Validate reason code for adjustments."""
        if self.transaction_type == TransactionType.ADJUSTMENT.value and reason_code:
            valid_reasons = [r.value for r in AdjustmentReason]
            if reason_code not in valid_reasons:
                raise ValueError(f'Invalid adjustment reason: {reason_code}')
        return reason_code
    
    def __repr__(self):
        return f"<InventoryTransaction(material_id='{self.material_id}', type='{self.transaction_type}', quantity={self.quantity})>"


class MaterialSupplier(Base):
    """
    Material to supplier relationship.
    Tracks which suppliers can provide which materials.
    """
    __tablename__ = 'material_suppliers'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    material_id = Column(UUID(as_uuid=True), ForeignKey('materials.id'), nullable=False)
    supplier_name = Column(String(200), nullable=False)
    supplier_part_number = Column(String(100))
    
    # Supplier information
    lead_time_days = Column(Integer)
    minimum_order_quantity = Column(Numeric(12, 4))
    order_multiple = Column(Numeric(12, 4))
    
    # Pricing
    unit_price = Column(Numeric(12, 4))
    price_effective_date = Column(DateTime)
    
    # Status
    preferred = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=False)
    
    # Relationships
    material = relationship("Material", back_populates="material_suppliers")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('lead_time_days >= 0', name='check_lead_time_positive'),
        CheckConstraint('minimum_order_quantity >= 0', name='check_moq_positive'),
        CheckConstraint('order_multiple >= 0', name='check_order_multiple_positive'),
        CheckConstraint('unit_price >= 0', name='check_unit_price_positive'),
        Index('idx_material_supplier_material', 'material_id'),
        Index('idx_material_supplier_name', 'supplier_name'),
        Index('idx_material_supplier_preferred', 'preferred'),
    )
    
    def __repr__(self):
        return f"<MaterialSupplier(material_id='{self.material_id}', supplier='{self.supplier_name}')>"


class InventorySummary(Base):
    """
    Materialized view for current inventory levels.
    Provides fast access to current stock quantities.
    """
    __tablename__ = 'inventory_summary'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Material reference
    material_id = Column(UUID(as_uuid=True), ForeignKey('materials.id'), nullable=False, unique=True)
    
    # Current quantities
    on_hand = Column(Numeric(12, 4), default=0, nullable=False)
    committed = Column(Numeric(12, 4), default=0, nullable=False)
    available = Column(Numeric(12, 4), default=0, nullable=False)
    on_order = Column(Numeric(12, 4), default=0, nullable=False)
    
    # Value calculations
    total_value = Column(Numeric(14, 4), default=0, nullable=False)
    average_unit_cost = Column(Numeric(12, 4), default=0, nullable=False)
    
    # Last updated
    last_transaction_date = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    material = relationship("Material")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('on_hand >= 0', name='check_on_hand_positive'),
        CheckConstraint('committed >= 0', name='check_committed_positive'),
        CheckConstraint('available >= 0', name='check_available_positive'),
        CheckConstraint('on_order >= 0', name='check_on_order_positive'),
        CheckConstraint('total_value >= 0', name='check_total_value_positive'),
        Index('idx_summary_material', 'material_id'),
        Index('idx_summary_available', 'available'),
        Index('idx_summary_last_updated', 'last_updated'),
    )
    
    @hybrid_property
    def is_low_stock(self) -> bool:
        """Check if material is below reorder point."""
        if self.material and self.material.reorder_point:
            return self.available <= self.material.reorder_point
        return False
    
    def __repr__(self):
        return f"<InventorySummary(material_id='{self.material_id}', on_hand={self.on_hand}, available={self.available})>"


class StockAdjustment(Base):
    """
    Stock adjustment records.
    Detailed tracking of manual inventory adjustments.
    """
    __tablename__ = 'stock_adjustments'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Adjustment details
    material_id = Column(UUID(as_uuid=True), ForeignKey('materials.id'), nullable=False)
    adjustment_type = Column(String(50), nullable=False)
    quantity_before = Column(Numeric(12, 4), nullable=False)
    quantity_after = Column(Numeric(12, 4), nullable=False)
    adjustment_quantity = Column(Numeric(12, 4), nullable=False)
    
    # Reason and approval
    reason = Column(String(100), nullable=False)
    detailed_reason = Column(Text)
    approved_by = Column(String(100))
    approved_date = Column(DateTime)
    
    # Status
    status = Column(String(20), default='Pending')  # Pending, Approved, Rejected
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=False)
    
    # Relationships
    material = relationship("Material")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('quantity_before >= 0', name='check_quantity_before_positive'),
        CheckConstraint('quantity_after >= 0', name='check_quantity_after_positive'),
        CheckConstraint('adjustment_quantity <> 0', name='check_adjustment_nonzero'),
        Index('idx_adjustment_material', 'material_id'),
        Index('idx_adjustment_date', 'created_at'),
        Index('idx_adjustment_status', 'status'),
    )
    
    @validates('adjustment_type')
    def validate_adjustment_type(self, key, adjustment_type):
        """Validate adjustment type."""
        valid_types = [r.value for r in AdjustmentReason]
        if adjustment_type not in valid_types:
            raise ValueError(f'Invalid adjustment type: {adjustment_type}')
        return adjustment_type
    
    def __repr__(self):
        return f"<StockAdjustment(material_id='{self.material_id}', type='{self.adjustment_type}', qty={self.adjustment_quantity})>"
