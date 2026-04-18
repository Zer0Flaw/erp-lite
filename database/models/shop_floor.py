"""
Shop Floor database models for XPanda ERP-Lite.
Handles time tracking, production recording, batch traceability, and station management.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from database.connection import Base


class TimeEntryStatus(Enum):
    """Time entry status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


class OperationType(Enum):
    """Production operation types."""
    EXPANSION = "expansion"
    MOLDING = "molding"
    AGING = "aging"
    CUTTING = "cutting"
    FABRICATION = "fabrication"
    PACKAGING = "packaging"
    INSPECTION = "inspection"
    MAINTENANCE = "maintenance"


class ProductionOutputType(Enum):
    """Production output types."""
    FOAM_BLOCK = "foam_block"
    FABRICATED_PART = "fabricated_part"
    SCRAP = "scrap"
    REWORK = "rework"


class BatchType(Enum):
    """Production batch types."""
    EXPANSION = "expansion"
    MOLDING = "molding"
    FABRICATION = "fabrication"
    AGING = "aging"


class StationStatus(Enum):
    """Production station status."""
    AVAILABLE = "available"
    RUNNING = "running"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    CLEANUP = "cleanup"


class StationType(Enum):
    """Production station types."""
    PRE_EXPANDER = "pre_expander"
    BLOCK_MOLD = "block_mold"
    AGING_SILO = "aging_silo"
    HOT_WIRE_CUTTER = "hot_wire_cutter"
    CNC_ROUTER = "cnc_router"
    BAND_SAW = "band_saw"
    PACKAGING = "packaging"
    INSPECTION = "inspection"
    GENERAL = "general"


class TimeEntry(Base):
    """Time entry model for tracking operator work hours."""
    __tablename__ = "time_entries"
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(String(50), nullable=False, index=True)
    employee_name = Column(String(100), nullable=False)
    work_order_id = Column(Integer, nullable=True, index=True)
    operation = Column(String(50), nullable=False)  # OperationType enum value
    station_id = Column(String(50), nullable=True, index=True)
    start_time = Column(DateTime, nullable=False, default=func.now())
    end_time = Column(DateTime, nullable=True)
    total_hours = Column(Numeric(8, 2), nullable=True)
    status = Column(String(20), nullable=False, default=TimeEntryStatus.ACTIVE.value)
    notes = Column(Text, nullable=True)
    badge_scan = Column(String(100), nullable=True)  # Badge scan data
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_time_entry_employee_date', 'employee_id', 'start_time'),
        Index('idx_time_entry_work_order', 'work_order_id'),
        Index('idx_time_entry_station', 'station_id'),
        Index('idx_time_entry_status', 'status'),
    )
    
    @validates('total_hours')
    def validate_total_hours(self, key, value):
        if value is not None and value < 0:
            raise ValueError("Total hours cannot be negative")
        return value
    
    def calculate_total_hours(self):
        """Calculate total hours based on start and end times."""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.total_hours = Decimal(delta.total_seconds() / 3600).quantize(Decimal('0.01'))
        return self.total_hours


class ProductionOutput(Base):
    """Production output model for tracking production quantities and yields."""
    __tablename__ = "production_outputs"
    
    id = Column(Integer, primary_key=True)
    work_order_id = Column(Integer, nullable=False, index=True, default=0)
    work_order_number = Column(String(50), nullable=True, index=True)
    batch_id = Column(Integer, ForeignKey("production_batches.id"), nullable=True, index=True)
    output_type = Column(String(20), nullable=False)  # ProductionOutputType enum value
    quantity_produced = Column(Numeric(12, 2), nullable=False)
    quantity_scrapped = Column(Numeric(12, 2), nullable=False, default=0)
    theoretical_yield = Column(Numeric(12, 2), nullable=True)
    actual_yield = Column(Numeric(12, 2), nullable=True)
    yield_percentage = Column(Numeric(5, 2), nullable=True)
    
    # Foam block specific fields
    length = Column(Numeric(8, 2), nullable=True)  # inches
    width = Column(Numeric(8, 2), nullable=True)   # inches
    height = Column(Numeric(8, 2), nullable=True)  # inches
    density = Column(Numeric(6, 2), nullable=True)  # lb/ft³
    
    # Traceability fields
    lot_number = Column(String(50), nullable=True, index=True)
    bead_batch = Column(String(50), nullable=True, index=True)
    bead_lot_number = Column(String(50), nullable=True, index=True)
    expansion_batch = Column(String(50), nullable=True, index=True)
    mold_id = Column(String(50), nullable=True, index=True)
    
    # Operator and timing
    operator_id = Column(String(50), nullable=False, index=True)
    operator_name = Column(String(100), nullable=False)
    station_id = Column(String(50), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=func.now())
    
    # Additional data
    notes = Column(Text, nullable=True)
    quality_status = Column(String(20), nullable=True)  # pass/fail/pending
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    batch = relationship("ProductionBatch", back_populates="production_outputs")
    
    # Indexes
    __table_args__ = (
        Index('idx_output_work_order', 'work_order_id'),
        Index('idx_output_batch', 'batch_id'),
        Index('idx_output_lot', 'lot_number'),
        Index('idx_output_bead_batch', 'bead_batch'),
        Index('idx_output_operator', 'operator_id'),
        Index('idx_output_timestamp', 'timestamp'),
    )
    
    def calculate_yield(self):
        """Calculate yield percentage."""
        if self.theoretical_yield and self.theoretical_yield > 0:
            self.actual_yield = self.quantity_produced - self.quantity_scrapped
            self.yield_percentage = (self.actual_yield / self.theoretical_yield * 100).quantize(Decimal('0.01'))
        return self.yield_percentage
    
    def calculate_volume(self):
        """Calculate volume for foam blocks."""
        if self.length and self.width and self.height:
            # Convert to cubic feet (inches^3 to ft^3)
            volume_cubic_inches = self.length * self.width * self.height
            volume_cubic_feet = volume_cubic_inches / 1728
            return volume_cubic_feet.quantize(Decimal('0.001'))
        return None


class ProductionBatch(Base):
    """Production batch model for lot traceability."""
    __tablename__ = "production_batches"
    
    id = Column(Integer, primary_key=True)
    batch_number = Column(String(50), nullable=False, unique=True, index=True)
    batch_type = Column(String(20), nullable=False)  # BatchType enum value
    raw_material_lot = Column(String(50), nullable=True, index=True)
    input_batch_id = Column(Integer, ForeignKey("production_batches.id"), nullable=True, index=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=True, index=True)
    
    # Timing
    start_time = Column(DateTime, nullable=False, default=func.now())
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Operator
    operator_id = Column(String(50), nullable=False, index=True)
    operator_name = Column(String(100), nullable=False)
    
    # Station
    station_id = Column(String(50), nullable=True, index=True)
    
    # Process parameters (JSON field for flexible storage)
    parameters = Column(Text, nullable=True)  # JSON string for process parameters
    
    # Quantities
    input_quantity = Column(Numeric(12, 2), nullable=True)
    output_quantity = Column(Numeric(12, 2), nullable=True)
    scrap_quantity = Column(Numeric(12, 2), nullable=True)
    
    # Status and notes
    status = Column(String(20), nullable=False, default="active")
    notes = Column(Text, nullable=True)
    quality_notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    input_batch = relationship("ProductionBatch", remote_side=[id], back_populates="output_batches")
    output_batches = relationship("ProductionBatch", back_populates="input_batch")
    work_order = relationship("WorkOrder", back_populates="production_batches")
    production_outputs = relationship("ProductionOutput", back_populates="batch")
    
    # Indexes
    __table_args__ = (
        Index('idx_batch_number', 'batch_number'),
        Index('idx_batch_type', 'batch_type'),
        Index('idx_batch_raw_material', 'raw_material_lot'),
        Index('idx_batch_work_order', 'work_order_id'),
        Index('idx_batch_operator', 'operator_id'),
        Index('idx_batch_station', 'station_id'),
    )
    
    def generate_batch_number(self, batch_type: str, date: date = None):
        """Generate auto batch number: TYPE-YYYYMMDD-NNN."""
        if date is None:
            date = datetime.now().date()
        
        date_str = date.strftime("%Y%m%d")
        prefix = batch_type.upper()
        
        # This would need to query for existing batches to get sequence
        # For now, using a simple format
        self.batch_number = f"{prefix}-{date_str}-001"
        return self.batch_number
    
    def calculate_duration(self):
        """Calculate batch duration in minutes."""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        return self.duration_minutes


class ProductionStation(Base):
    """Production station model for managing production equipment and work cells."""
    __tablename__ = "production_stations"
    
    id = Column(Integer, primary_key=True)
    station_id = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    station_type = Column(String(30), nullable=False)  # StationType enum value
    status = Column(String(20), nullable=False, default=StationStatus.AVAILABLE.value)
    
    # Current work assignment
    current_work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=True, index=True)
    current_operator_id = Column(String(50), nullable=True, index=True)
    current_operator_name = Column(String(100), nullable=True)
    current_batch_id = Column(Integer, ForeignKey("production_batches.id"), nullable=True, index=True)
    
    # Capacity and specifications
    capacity_per_hour = Column(Numeric(12, 2), nullable=True)
    max_block_size = Column(String(50), nullable=True)  # For molding stations
    temperature_range = Column(String(50), nullable=True)
    
    # Maintenance tracking
    last_maintenance_date = Column(Date, nullable=True)
    next_maintenance_date = Column(Date, nullable=True)
    maintenance_hours = Column(Integer, nullable=False, default=0)
    total_runtime_hours = Column(Numeric(12, 2), nullable=False, default=0)
    
    # Location
    location = Column(String(100), nullable=True)
    department = Column(String(50), nullable=True)
    
    # Status details
    status_reason = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    current_work_order = relationship("WorkOrder")
    current_batch = relationship("ProductionBatch")
    
    # Indexes
    __table_args__ = (
        Index('idx_station_id', 'station_id'),
        Index('idx_station_type', 'station_type'),
        Index('idx_station_status', 'status'),
        Index('idx_station_location', 'location'),
        Index('idx_station_current_work', 'current_work_order_id'),
    )
    
    def is_available(self):
        """Check if station is available for work."""
        return self.status == StationStatus.AVAILABLE.value
    
    def set_status(self, status: str, reason: str = None):
        """Update station status with optional reason."""
        self.status = status
        if reason:
            self.status_reason = reason
        self.updated_at = func.now()
    
    def assign_work(self, work_order_id: int, operator_id: str, operator_name: str):
        """Assign work to station."""
        self.current_work_order_id = work_order_id
        self.current_operator_id = operator_id
        self.current_operator_name = operator_name
        self.status = StationStatus.RUNNING.value
        self.updated_at = func.now()
    
    def release_work(self):
        """Release current work assignment."""
        self.current_work_order_id = None
        self.current_operator_id = None
        self.current_operator_name = None
        self.current_batch_id = None
        self.status = StationStatus.AVAILABLE.value
        self.status_reason = None
        self.updated_at = func.now()


# Add back-references to existing models
from database.models.production import WorkOrder

# Add back-references to WorkOrder
WorkOrder.production_batches = relationship("ProductionBatch", back_populates="work_order")
