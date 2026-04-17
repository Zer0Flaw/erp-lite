"""
Production database models for XPanda ERP-Lite.
Contains models for BOMs, work orders, production schedules, and related entities.
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


class BillOfMaterialStatus(Enum):
    """BOM status enumeration."""
    DRAFT = "Draft"
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    ARCHIVED = "Archived"


class WorkOrderStatus(Enum):
    """Work order status enumeration."""
    PLANNED = "Planned"
    RELEASED = "Released"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    ON_HOLD = "On Hold"


class WorkOrderPriority(Enum):
    """Work order priority enumeration."""
    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"
    URGENT = "Urgent"


class ProductionStepStatus(Enum):
    """Production step status enumeration."""
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    SKIPPED = "Skipped"
    FAILED = "Failed"


class BillOfMaterial(Base):
    """Bill of Materials (BOM) model."""
    
    __tablename__ = 'bill_of_materials'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Basic information
    bom_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), nullable=False, default="1.0")
    
    # Product information
    finished_good_sku = Column(String(50), nullable=False, index=True)
    finished_good_name = Column(String(200), nullable=False)
    standard_quantity = Column(Numeric(10, 4), nullable=False, default=Decimal('1.0'))
    unit_of_measure = Column(String(10), nullable=False, default='EA')
    
    # Status and lifecycle
    status = Column(String(20), nullable=False, default=BillOfMaterialStatus.DRAFT.value)
    effective_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    
    # Production information
    standard_cycle_time = Column(Numeric(8, 2), nullable=True)  # minutes
    setup_time = Column(Numeric(8, 2), nullable=True)  # minutes
    yield_percentage = Column(Numeric(5, 2), nullable=True, default=Decimal('100.0'))
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    bom_lines = relationship("BillOfMaterialLine", back_populates="bom", cascade="all, delete-orphan")
    work_orders = relationship("WorkOrder", back_populates="bom")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('standard_quantity > 0', name='check_standard_quantity_positive'),
        CheckConstraint('yield_percentage >= 0 AND yield_percentage <= 100', name='check_yield_percentage_range'),
        CheckConstraint('standard_cycle_time >= 0', name='check_standard_cycle_time_positive'),
        CheckConstraint('setup_time >= 0', name='check_setup_time_positive'),
    )
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status value."""
        valid_statuses = [s.value for s in BillOfMaterialStatus]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        return status
    
    @property
    def is_active(self) -> bool:
        """Check if BOM is active."""
        today = date.today()
        return (self.status == BillOfMaterialStatus.ACTIVE.value and 
                (self.effective_date is None or self.effective_date <= today) and
                (self.expiry_date is None or self.expiry_date >= today))
    
    def __repr__(self):
        return f"<BillOfMaterial(bom_code='{self.bom_code}', name='{self.name}', version='{self.version}')>"


class BillOfMaterialLine(Base):
    """Bill of Materials line item model."""
    
    __tablename__ = 'bom_lines'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Foreign key
    bom_id = Column(UUID(as_uuid=True), ForeignKey('bill_of_materials.id'), nullable=False)
    
    # Material information
    material_sku = Column(String(50), nullable=False, index=True)
    material_name = Column(String(200), nullable=False)
    material_category = Column(String(50), nullable=True)
    
    # Quantity information
    quantity_required = Column(Numeric(10, 4), nullable=False)
    unit_of_measure = Column(String(10), nullable=False, default='EA')
    
    # Cost and waste
    unit_cost = Column(Numeric(10, 4), nullable=True)
    waste_percentage = Column(Numeric(5, 2), nullable=True, default=Decimal('0.0'))
    
    # Substitutions
    is_optional = Column(Boolean, nullable=False, default=False)
    substitution_sku = Column(String(50), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # Relationships
    bom = relationship("BillOfMaterial", back_populates="bom_lines")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity_required > 0', name='check_quantity_required_positive'),
        CheckConstraint('waste_percentage >= 0 AND waste_percentage <= 100', name='check_waste_percentage_range'),
    )
    
    @property
    def effective_quantity(self) -> Decimal:
        """Calculate effective quantity including waste."""
        if self.waste_percentage:
            return self.quantity_required * (Decimal('1.0') + (self.waste_percentage / Decimal('100.0')))
        return self.quantity_required
    
    @property
    def line_cost(self) -> Optional[Decimal]:
        """Calculate line total cost."""
        if self.unit_cost:
            return self.effective_quantity * self.unit_cost
        return None
    
    def __repr__(self):
        return f"<BOMLine(material_sku='{self.material_sku}', quantity={self.quantity_required})>"


class WorkOrder(Base):
    """Work order model for production planning."""
    
    __tablename__ = 'work_orders'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Work order information
    work_order_number = Column(String(50), unique=True, nullable=False, index=True)
    bom_id = Column(UUID(as_uuid=True), ForeignKey('bill_of_materials.id'), nullable=True)
    
    # Product information
    finished_good_sku = Column(String(50), nullable=False, index=True)
    finished_good_name = Column(String(200), nullable=False)
    
    # Quantity and scheduling
    quantity_ordered = Column(Numeric(10, 4), nullable=False)
    quantity_produced = Column(Numeric(10, 4), nullable=False, default=Decimal('0.0'))
    unit_of_measure = Column(String(10), nullable=False, default='EA')
    
    # Dates
    order_date = Column(Date, nullable=False, default=func.current_date())
    start_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    
    # Status and priority
    status = Column(String(20), nullable=False, default=WorkOrderStatus.PLANNED.value)
    priority = Column(String(10), nullable=False, default=WorkOrderPriority.NORMAL.value)
    
    # Production information
    estimated_hours = Column(Numeric(8, 2), nullable=True)
    actual_hours = Column(Numeric(8, 2), nullable=True)
    yield_percentage = Column(Numeric(5, 2), nullable=True)
    
    # Quality information
    quality_status = Column(String(20), nullable=True)
    inspector = Column(String(100), nullable=True)
    inspection_date = Column(DateTime, nullable=True)
    
    # Notes and attachments
    notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    completed_by = Column(String(100), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    bom = relationship("BillOfMaterial", back_populates="work_orders")
    production_steps = relationship("ProductionStep", back_populates="work_order", cascade="all, delete-orphan")
    material_consumptions = relationship("MaterialConsumption", back_populates="work_order", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity_ordered > 0', name='check_quantity_ordered_positive'),
        CheckConstraint('quantity_produced >= 0', name='check_quantity_produced_positive'),
        CheckConstraint('estimated_hours >= 0', name='check_estimated_hours_positive'),
        CheckConstraint('actual_hours >= 0', name='check_actual_hours_positive'),
        CheckConstraint('yield_percentage >= 0 AND yield_percentage <= 100', name='check_yield_percentage_range'),
    )
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status value."""
        valid_statuses = [s.value for s in WorkOrderStatus]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        return status
    
    @validates('priority')
    def validate_priority(self, key, priority):
        """Validate priority value."""
        valid_priorities = [p.value for p in WorkOrderPriority]
        if priority not in valid_priorities:
            raise ValueError(f"Invalid priority: {priority}. Must be one of {valid_priorities}")
        return priority
    
    @property
    def completion_percentage(self) -> Decimal:
        """Calculate completion percentage."""
        if self.quantity_ordered > 0:
            return (self.quantity_produced / self.quantity_ordered) * Decimal('100.0')
        return Decimal('0.0')
    
    @property
    def is_overdue(self) -> bool:
        """Check if work order is overdue."""
        if self.due_date and self.status not in [WorkOrderStatus.COMPLETED.value, WorkOrderStatus.CANCELLED.value]:
            return date.today() > self.due_date
        return False
    
    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity to produce."""
        return self.quantity_ordered - self.quantity_produced
    
    def __repr__(self):
        return f"<WorkOrder(number='{self.work_order_number}', status='{self.status}', quantity={self.quantity_ordered})>"


class ProductionStep(Base):
    """Production step model for work order operations."""
    
    __tablename__ = 'production_steps'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Foreign key
    work_order_id = Column(UUID(as_uuid=True), ForeignKey('work_orders.id'), nullable=False)
    
    # Step information
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(200), nullable=False)
    step_description = Column(Text, nullable=True)
    
    # Timing
    estimated_minutes = Column(Numeric(8, 2), nullable=True)
    actual_minutes = Column(Numeric(8, 2), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default=ProductionStepStatus.PENDING.value)
    
    # Resources
    machine_id = Column(String(50), nullable=True)
    operator = Column(String(100), nullable=True)
    
    # Quality
    quality_notes = Column(Text, nullable=True)
    passed_inspection = Column(Boolean, nullable=True)
    
    # Audit fields
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # Relationships
    work_order = relationship("WorkOrder", back_populates="production_steps")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('step_number > 0', name='check_step_number_positive'),
        CheckConstraint('estimated_minutes >= 0', name='check_estimated_minutes_positive'),
        CheckConstraint('actual_minutes >= 0', name='check_actual_minutes_positive'),
    )
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status value."""
        valid_statuses = [s.value for s in ProductionStepStatus]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        return status
    
    @property
    def is_completed(self) -> bool:
        """Check if step is completed."""
        return self.status == ProductionStepStatus.COMPLETED.value
    
    def __repr__(self):
        return f"<ProductionStep(step_number={self.step_number}, name='{self.step_name}', status='{self.status}')>"


class MaterialConsumption(Base):
    """Material consumption model for work orders."""
    
    __tablename__ = 'material_consumptions'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Foreign key
    work_order_id = Column(UUID(as_uuid=True), ForeignKey('work_orders.id'), nullable=False)
    
    # Material information
    material_sku = Column(String(50), nullable=False, index=True)
    material_name = Column(String(200), nullable=False)
    
    # Quantity information
    quantity_planned = Column(Numeric(10, 4), nullable=False)
    quantity_actual = Column(Numeric(10, 4), nullable=True)
    unit_of_measure = Column(String(10), nullable=False, default='EA')
    
    # Cost information
    unit_cost = Column(Numeric(10, 4), nullable=True)
    total_cost = Column(Numeric(12, 4), nullable=True)
    
    # Consumption details
    consumption_date = Column(DateTime, nullable=True)
    consumed_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # Relationships
    work_order = relationship("WorkOrder", back_populates="material_consumptions")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity_planned > 0', name='check_quantity_planned_positive'),
        CheckConstraint('quantity_actual >= 0', name='check_quantity_actual_positive'),
    )
    
    @property
    def variance_quantity(self) -> Optional[Decimal]:
        """Calculate variance between planned and actual consumption."""
        if self.quantity_actual is not None:
            return self.quantity_actual - self.quantity_planned
        return None
    
    @property
    def variance_percentage(self) -> Optional[Decimal]:
        """Calculate variance percentage."""
        if self.quantity_actual is not None and self.quantity_planned > 0:
            return (self.variance_quantity / self.quantity_planned) * Decimal('100.0')
        return None
    
    def __repr__(self):
        return f"<MaterialConsumption(material_sku='{self.material_sku}', planned={self.quantity_planned}, actual={self.quantity_actual})>"


class ProductionSchedule(Base):
    """Production schedule model for planning production capacity."""
    
    __tablename__ = 'production_schedules'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Schedule information
    schedule_date = Column(Date, nullable=False, index=True)
    machine_id = Column(String(50), nullable=False, index=True)
    machine_name = Column(String(200), nullable=True)
    
    # Work order assignment
    work_order_id = Column(UUID(as_uuid=True), ForeignKey('work_orders.id'), nullable=True)
    work_order_number = Column(String(50), nullable=True)
    
    # Timing
    scheduled_start_time = Column(DateTime, nullable=True)
    scheduled_end_time = Column(DateTime, nullable=True)
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    
    # Capacity
    scheduled_hours = Column(Numeric(8, 2), nullable=True)
    setup_hours = Column(Numeric(8, 2), nullable=True)
    run_hours = Column(Numeric(8, 2), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default='Scheduled')
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('scheduled_hours >= 0', name='check_scheduled_hours_positive'),
        CheckConstraint('setup_hours >= 0', name='check_setup_hours_positive'),
        CheckConstraint('run_hours >= 0', name='check_run_hours_positive'),
    )
    
    def __repr__(self):
        return f"<ProductionSchedule(date='{self.schedule_date}', machine='{self.machine_id}', status='{self.status}')>"
