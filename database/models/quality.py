"""
Quality database models for XPanda ERP-Lite.
Contains models for inspections, non-conformance reports, and corrective actions.
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


class InspectionType(Enum):
    """Inspection type enumeration."""
    INCOMING = "Incoming"
    IN_PROCESS = "In Process"
    FINAL = "Final"
    CUSTOMER_RETURN = "Customer Return"


class InspectionStatus(Enum):
    """Inspection status enumeration."""
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    PASSED = "Passed"
    FAILED = "Failed"
    REWORK_REQUIRED = "Rework Required"
    CANCELLED = "Cancelled"


class NCRStatus(Enum):
    """Non-Conformance Report status enumeration."""
    OPEN = "Open"
    INVESTIGATION = "Under Investigation"
    DISPOSITION = "Disposition Required"
    CLOSED = "Closed"
    CANCELLED = "Cancelled"


class NCRSeverity(Enum):
    """Non-Conformance Report severity enumeration."""
    MINOR = "Minor"
    MAJOR = "Major"
    CRITICAL = "Critical"


class NCRDisposition(Enum):
    """Non-Conformance Report disposition enumeration."""
    USE_AS_IS = "Use As Is"
    REWORK = "Rework"
    REPAIR = "Repair"
    SCRAP = "Scrap"
    RETURN_TO_VENDOR = "Return to Vendor"


class CAPAStatus(Enum):
    """Corrective Action Plan status enumeration."""
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    VERIFIED = "Verified"
    CLOSED = "Closed"
    CANCELLED = "Cancelled"


class CAPAPriority(Enum):
    """Corrective Action Plan priority enumeration."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class Inspection(Base):
    """Inspection model for quality control activities."""
    
    __tablename__ = 'inspections'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Inspection information
    inspection_number = Column(String(50), unique=True, nullable=False, index=True)
    inspection_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default=InspectionStatus.SCHEDULED.value)
    
    # Related entities
    work_order_id = Column(UUID(as_uuid=True), ForeignKey('work_orders.id'), nullable=True)
    sales_order_id = Column(UUID(as_uuid=True), ForeignKey('sales_orders.id'), nullable=True)
    material_sku = Column(String(50), nullable=True, index=True)
    batch_number = Column(String(50), nullable=True, index=True)
    
    # Inspection details
    inspection_date = Column(Date, nullable=False, default=func.current_date())
    inspector = Column(String(100), nullable=False)
    quantity_inspected = Column(Integer, nullable=False)
    quantity_passed = Column(Integer, nullable=False, default=0)
    quantity_failed = Column(Integer, nullable=False, default=0)
    quantity_rework = Column(Integer, nullable=False, default=0)
    
    # Results
    overall_result = Column(String(10), nullable=True)  # PASS, FAIL, REWORK
    acceptance_rate = Column(Numeric(5, 2), nullable=True)
    
    # Documentation
    inspection_procedure = Column(String(100), nullable=True)
    specifications = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    work_order = relationship("WorkOrder")
    sales_order = relationship("SalesOrder")
    inspection_lines = relationship("InspectionLine", back_populates="inspection", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity_inspected > 0', name='check_quantity_inspected_positive'),
        CheckConstraint('quantity_passed >= 0', name='check_quantity_passed_positive'),
        CheckConstraint('quantity_failed >= 0', name='check_quantity_failed_positive'),
        CheckConstraint('quantity_rework >= 0', name='check_quantity_rework_positive'),
        CheckConstraint('acceptance_rate >= 0 AND acceptance_rate <= 100', name='check_acceptance_rate_range'),
    )
    
    @validates('inspection_type')
    def validate_inspection_type(self, key, inspection_type):
        """Validate inspection type value."""
        valid_types = [t.value for t in InspectionType]
        if inspection_type not in valid_types:
            raise ValueError(f"Invalid inspection type: {inspection_type}. Must be one of {valid_types}")
        return inspection_type
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status value."""
        valid_statuses = [s.value for s in InspectionStatus]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        return status
    
    @validates('overall_result')
    def validate_overall_result(self, key, overall_result):
        """Validate overall result value."""
        valid_results = ['PASS', 'FAIL', 'REWORK']
        if overall_result and overall_result not in valid_results:
            raise ValueError(f"Invalid overall result: {overall_result}. Must be one of {valid_results}")
        return overall_result
    
    @property
    def total_quantity(self) -> int:
        """Calculate total quantity from all results."""
        return self.quantity_passed + self.quantity_failed + self.quantity_rework
    
    @property
    def is_passed(self) -> bool:
        """Check if inspection passed."""
        return self.overall_result == 'PASS'
    
    @property
    def is_failed(self) -> bool:
        """Check if inspection failed."""
        return self.overall_result == 'FAIL'
    
    @property
    def requires_rework(self) -> bool:
        """Check if inspection requires rework."""
        return self.overall_result == 'REWORK' or self.quantity_rework > 0
    
    def __repr__(self):
        return f"<Inspection(inspection_number='{self.inspection_number}', type='{self.inspection_type}', status='{self.status}')>"


class InspectionLine(Base):
    """Inspection line model for individual inspection criteria."""
    
    __tablename__ = 'inspection_lines'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Foreign key
    inspection_id = Column(UUID(as_uuid=True), ForeignKey('inspections.id'), nullable=False)
    
    # Line information
    line_number = Column(Integer, nullable=False)
    characteristic = Column(String(200), nullable=False)
    specification = Column(String(200), nullable=True)
    measurement_method = Column(String(100), nullable=True)
    
    # Results
    measured_value = Column(Numeric(10, 4), nullable=True)
    tolerance_min = Column(Numeric(10, 4), nullable=True)
    tolerance_max = Column(Numeric(10, 4), nullable=True)
    result = Column(String(10), nullable=True)  # PASS, FAIL, REWORK
    deviation = Column(Numeric(10, 4), nullable=True)
    
    # Additional information
    notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # Relationships
    inspection = relationship("Inspection", back_populates="inspection_lines")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('line_number > 0', name='check_line_number_positive'),
        CheckConstraint('result IN (\'PASS\', \'FAIL\', \'REWORK\')', name='check_inspection_line_result'),
    )
    
    @property
    def is_within_tolerance(self) -> bool:
        """Check if measurement is within tolerance."""
        if self.measured_value is None:
            return False
        
        if self.tolerance_min is not None and self.measured_value < self.tolerance_min:
            return False
        
        if self.tolerance_max is not None and self.measured_value > self.tolerance_max:
            return False
        
        return True
    
    def __repr__(self):
        return f"<InspectionLine(characteristic='{self.characteristic}', result='{self.result}')>"


class NonConformanceReport(Base):
    """Non-Conformance Report model for quality issues."""
    
    __tablename__ = 'non_conformance_reports'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # NCR information
    ncr_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), nullable=False, default=NCRStatus.OPEN.value)
    severity = Column(String(10), nullable=False)
    disposition = Column(String(20), nullable=True)
    
    # Related entities
    inspection_id = Column(UUID(as_uuid=True), ForeignKey('inspections.id'), nullable=True)
    work_order_id = Column(UUID(as_uuid=True), ForeignKey('work_orders.id'), nullable=True)
    sales_order_id = Column(UUID(as_uuid=True), ForeignKey('sales_orders.id'), nullable=True)
    material_sku = Column(String(50), nullable=True, index=True)
    batch_number = Column(String(50), nullable=True, index=True)
    
    # Issue details
    discovery_date = Column(Date, nullable=False, default=func.current_date())
    reported_by = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(200), nullable=True)
    
    # Investigation
    investigation_summary = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    investigation_date = Column(Date, nullable=True)
    investigator = Column(String(100), nullable=True)
    
    # Disposition
    disposition_date = Column(Date, nullable=True)
    disposition_by = Column(String(100), nullable=True)
    disposition_notes = Column(Text, nullable=True)
    
    # Closure
    closure_date = Column(Date, nullable=True)
    closed_by = Column(String(100), nullable=True)
    closure_notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    inspection = relationship("Inspection")
    work_order = relationship("WorkOrder")
    sales_order = relationship("SalesOrder")
    capa_actions = relationship("CAPAAction", back_populates="ncr", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('severity IN (\'Minor\', \'Major\', \'Critical\')', name='check_ncr_severity'),
        CheckConstraint('disposition IN (\'Use As Is\', \'Rework\', \'Repair\', \'Scrap\', \'Return to Vendor\')', name='check_ncr_disposition'),
    )
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status value."""
        valid_statuses = [s.value for s in NCRStatus]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        return status
    
    @validates('severity')
    def validate_severity(self, key, severity):
        """Validate severity value."""
        valid_severities = [s.value for s in NCRSeverity]
        if severity not in valid_severities:
            raise ValueError(f"Invalid severity: {severity}. Must be one of {valid_severities}")
        return severity
    
    @validates('disposition')
    def validate_disposition(self, key, disposition):
        """Validate disposition value."""
        if disposition:
            valid_dispositions = [d.value for d in NCRDisposition]
            if disposition not in valid_dispositions:
                raise ValueError(f"Invalid disposition: {disposition}. Must be one of {valid_dispositions}")
        return disposition
    
    @property
    def is_open(self) -> bool:
        """Check if NCR is open."""
        return self.status == NCRStatus.OPEN.value
    
    @property
    def is_closed(self) -> bool:
        """Check if NCR is closed."""
        return self.status == NCRStatus.CLOSED.value
    
    @property
    def days_open(self) -> int:
        """Calculate days NCR has been open."""
        if self.discovery_date:
            end_date = self.closure_date or date.today()
            return (end_date - self.discovery_date).days
        return 0
    
    def __repr__(self):
        return f"<NCR(ncr_number='{self.ncr_number}', status='{self.status}', severity='{self.severity}')>"


class CAPAAction(Base):
    """Corrective Action Plan model for quality improvements."""
    
    __tablename__ = 'capa_actions'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # CAPA information
    capa_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default=CAPAStatus.OPEN.value)
    priority = Column(String(10), nullable=False, default=CAPAPriority.MEDIUM.value)
    
    # Related entities
    ncr_id = Column(UUID(as_uuid=True), ForeignKey('non_conformance_reports.id'), nullable=True)
    source_type = Column(String(50), nullable=True)  # NCR, Audit, Customer Complaint, etc.
    source_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to source entity
    
    # Action details
    description = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=True)
    corrective_action = Column(Text, nullable=True)
    preventive_action = Column(Text, nullable=True)
    
    # Responsibility
    assigned_to = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    
    # Dates
    created_date = Column(Date, nullable=False, default=func.current_date())
    due_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    verification_date = Column(Date, nullable=True)
    
    # Effectiveness
    effectiveness_rating = Column(Numeric(3, 2), nullable=True)
    effectiveness_notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    completed_by = Column(String(100), nullable=True)
    verified_by = Column(String(100), nullable=True)
    
    # Relationships
    ncr = relationship("NonConformanceReport", back_populates="capa_actions")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('status IN (\'Open\', \'In Progress\', \'Completed\', \'Verified\', \'Closed\', \'Cancelled\')', name='check_capa_status'),
        CheckConstraint('priority IN (\'Low\', \'Medium\', \'High\', \'Urgent\')', name='check_capa_priority'),
        CheckConstraint('effectiveness_rating >= 0 AND effectiveness_rating <= 5', name='check_effectiveness_rating_range'),
    )
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status value."""
        valid_statuses = [s.value for s in CAPAStatus]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        return status
    
    @validates('priority')
    def validate_priority(self, key, priority):
        """Validate priority value."""
        valid_priorities = [p.value for p in CAPAPriority]
        if priority not in valid_priorities:
            raise ValueError(f"Invalid priority: {priority}. Must be one of {valid_priorities}")
        return priority
    
    @property
    def is_overdue(self) -> bool:
        """Check if CAPA is overdue."""
        if self.due_date and self.status not in [CAPAStatus.COMPLETED.value, CAPAStatus.VERIFIED.value, CAPAStatus.CLOSED.value]:
            return date.today() > self.due_date
        return False
    
    @property
    def days_overdue(self) -> int:
        """Calculate days CAPA is overdue."""
        if self.is_overdue and self.due_date:
            return (date.today() - self.due_date).days
        return 0
    
    @property
    def completion_days(self) -> int:
        """Calculate days to complete CAPA."""
        if self.completion_date and self.created_date:
            return (self.completion_date - self.created_date).days
        return 0
    
    def __repr__(self):
        return f"<CAPA(capa_number='{self.capa_number}', status='{self.status}', priority='{self.priority}')>"


class QualityMetric(Base):
    """Quality metrics model for tracking quality performance."""
    
    __tablename__ = 'quality_metrics'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Metric information
    metric_name = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)  # Defect Rate, Rework Rate, etc.
    
    # Period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Values
    target_value = Column(Numeric(10, 4), nullable=True)
    actual_value = Column(Numeric(10, 4), nullable=False)
    variance = Column(Numeric(10, 4), nullable=True)
    
    # Additional data
    denominator = Column(Integer, nullable=True)  # Total items inspected
    numerator = Column(Integer, nullable=True)  # Defect items, rework items, etc.
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint('denominator > 0', name='check_denominator_positive'),
        CheckConstraint('numerator >= 0', name='check_numerator_positive'),
        CheckConstraint('actual_value >= 0', name='check_actual_value_positive'),
    )
    
    @property
    def meets_target(self) -> bool:
        """Check if metric meets target."""
        if self.target_value is None:
            return True  # No target to compare against
        
        # For quality metrics, lower is better (defect rate, rework rate, etc.)
        return self.actual_value <= self.target_value
    
    def __repr__(self):
        return f"<QualityMetric(metric_name='{self.metric_name}', actual_value={self.actual_value}, target_value={self.target_value})>"
