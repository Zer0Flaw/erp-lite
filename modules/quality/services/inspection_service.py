"""
Inspection service for XPanda ERP-Lite.
Provides business logic for inspection management operations.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from database.models.quality import Inspection, InspectionLine, InspectionType, InspectionStatus
from database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class InspectionService:
    """Service class for inspection operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_inspection(self, inspection_data: Dict[str, Any]) -> Optional[Inspection]:
        """
        Create a new inspection.
        
        Args:
            inspection_data: Dictionary containing inspection information
            
        Returns:
            Created Inspection object or None if failed
        """
        try:
            with self.db_manager.get_session() as session:
                # Check if inspection number already exists
                existing = session.query(Inspection).filter(
                    Inspection.inspection_number == inspection_data['inspection_number'].upper()
                ).first()
                
                if existing:
                    logger.warning(f"Inspection with number {inspection_data['inspection_number']} already exists")
                    return None
                
                # Create new inspection
                inspection = Inspection(
                    inspection_number=inspection_data['inspection_number'].upper(),
                    inspection_type=inspection_data['inspection_type'],
                    status=inspection_data.get('status', InspectionStatus.SCHEDULED.value),
                    work_order_id=inspection_data.get('work_order_id'),
                    sales_order_id=inspection_data.get('sales_order_id'),
                    material_sku=inspection_data.get('material_sku', ''),
                    batch_number=inspection_data.get('batch_number', ''),
                    inspection_date=self._parse_date(inspection_data.get('inspection_date', date.today())),
                    inspector=inspection_data['inspector'],
                    quantity_inspected=inspection_data['quantity_inspected'],
                    quantity_passed=inspection_data.get('quantity_passed', 0),
                    quantity_failed=inspection_data.get('quantity_failed', 0),
                    quantity_rework=inspection_data.get('quantity_rework', 0),
                    overall_result=inspection_data.get('overall_result'),
                    acceptance_rate=Decimal(str(inspection_data.get('acceptance_rate', 0))),
                    inspection_procedure=inspection_data.get('inspection_procedure', ''),
                    specifications=inspection_data.get('specifications', ''),
                    notes=inspection_data.get('notes', ''),
                    created_by=inspection_data.get('created_by', 'System')
                )
                
                session.add(inspection)
                session.flush()  # Get the ID without committing
                
                # Create inspection lines
                inspection_lines_data = inspection_data.get('inspection_lines', [])
                for line_data in inspection_lines_data:
                    inspection_line = InspectionLine(
                        inspection_id=inspection.id,
                        line_number=line_data['line_number'],
                        characteristic=line_data['characteristic'],
                        specification=line_data.get('specification', ''),
                        measurement_method=line_data.get('measurement_method', ''),
                        measured_value=Decimal(str(line_data.get('measured_value', 0))),
                        tolerance_min=Decimal(str(line_data.get('tolerance_min', 0))),
                        tolerance_max=Decimal(str(line_data.get('tolerance_max', 0))),
                        result=line_data.get('result', ''),
                        deviation=Decimal(str(line_data.get('deviation', 0))),
                        notes=line_data.get('notes', '')
                    )
                    session.add(inspection_line)
                
                logger.info(f"Created inspection: {inspection.inspection_number}")
                return inspection
                
        except Exception as e:
            logger.error(f"Failed to create inspection: {e}")
            return None
    
    def get_inspection_by_id(self, inspection_id: UUID) -> Optional[Inspection]:
        """
        Get inspection by ID.
        
        Args:
            inspection_id: UUID of the inspection
            
        Returns:
            Inspection object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(Inspection).filter(
                    Inspection.id == inspection_id
                ).first()
        except Exception as e:
            logger.error(f"Failed to get inspection {inspection_id}: {e}")
            return None
    
    def get_inspection_by_number(self, inspection_number: str) -> Optional[Inspection]:
        """
        Get inspection by number.
        
        Args:
            inspection_number: Inspection number
            
        Returns:
            Inspection object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(Inspection).filter(
                    Inspection.inspection_number == inspection_number.upper()
                ).first()
        except Exception as e:
            logger.error(f"Failed to get inspection {inspection_number}: {e}")
            return None
    
    def get_all_inspections(self, status_filter: Optional[str] = None) -> List[Inspection]:
        """
        Get all inspections.
        
        Args:
            status_filter: Optional status filter
            
        Returns:
            List of Inspection objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Inspection)
                
                if status_filter:
                    query = query.filter(Inspection.status == status_filter)
                
                return query.order_by(Inspection.inspection_number).all()
        except Exception as e:
            logger.error(f"Failed to get inspections: {e}")
            return []
    
    def search_inspections(self, search_term: str, status_filter: Optional[str] = None) -> List[Inspection]:
        """
        Search inspections by number, type, or material.
        
        Args:
            search_term: Search term
            status_filter: Optional status filter
            
        Returns:
            List of matching Inspection objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Inspection)
                
                # Add search conditions
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    (Inspection.inspection_number.ilike(search_pattern)) |
                    (Inspection.inspection_type.ilike(search_pattern)) |
                    (Inspection.material_sku.ilike(search_pattern)) |
                    (Inspection.batch_number.ilike(search_pattern)) |
                    (Inspection.inspector.ilike(search_pattern))
                )
                
                # Add status filter if specified
                if status_filter:
                    query = query.filter(Inspection.status == status_filter)
                
                return query.order_by(Inspection.inspection_number).all()
        except Exception as e:
            logger.error(f"Failed to search inspections: {e}")
            return []
    
    def update_inspection(self, inspection_id: UUID, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing inspection.
        
        Args:
            inspection_id: UUID of the inspection to update
            update_data: Dictionary containing updated fields
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                inspection = session.query(Inspection).filter(
                    Inspection.id == inspection_id
                ).first()
                
                if not inspection:
                    logger.warning(f"Inspection {inspection_id} not found")
                    return False
                
                # Update inspection fields
                for field, value in update_data.items():
                    if hasattr(inspection, field) and field not in ['id', 'created_at', 'created_by', 'inspection_lines']:
                        if field == 'inspection_number':
                            inspection.inspection_number = value.upper()
                        elif field in ['acceptance_rate']:
                            setattr(inspection, field, Decimal(str(value)))
                        elif field in ['inspection_date']:
                            setattr(inspection, field, self._parse_date(value))
                        else:
                            setattr(inspection, field, value)
                
                inspection.updated_at = datetime.utcnow()
                
                # Update inspection lines if provided
                if 'inspection_lines' in update_data:
                    # Remove existing lines
                    session.query(InspectionLine).filter(
                        InspectionLine.inspection_id == inspection_id
                    ).delete()
                    
                    # Add new lines
                    for line_data in update_data['inspection_lines']:
                        inspection_line = InspectionLine(
                            inspection_id=inspection.id,
                            line_number=line_data['line_number'],
                            characteristic=line_data['characteristic'],
                            specification=line_data.get('specification', ''),
                            measurement_method=line_data.get('measurement_method', ''),
                            measured_value=Decimal(str(line_data.get('measured_value', 0))),
                            tolerance_min=Decimal(str(line_data.get('tolerance_min', 0))),
                            tolerance_max=Decimal(str(line_data.get('tolerance_max', 0))),
                            result=line_data.get('result', ''),
                            deviation=Decimal(str(line_data.get('deviation', 0))),
                            notes=line_data.get('notes', '')
                        )
                        session.add(inspection_line)
                
                logger.info(f"Updated inspection: {inspection.inspection_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update inspection {inspection_id}: {e}")
            return False
    
    def update_inspection_status(self, inspection_id: UUID, new_status: str, updated_by: str) -> bool:
        """
        Update inspection status with proper validation.
        
        Args:
            inspection_id: UUID of the inspection
            new_status: New status
            updated_by: User making the change
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                inspection = session.query(Inspection).filter(
                    Inspection.id == inspection_id
                ).first()
                
                if not inspection:
                    logger.warning(f"Inspection {inspection_id} not found")
                    return False
                
                # Validate status transition
                if not self._is_valid_status_transition(inspection.status, new_status):
                    logger.warning(f"Invalid status transition from {inspection.status} to {new_status}")
                    return False
                
                # Update status
                old_status = inspection.status
                inspection.status = new_status
                inspection.updated_at = datetime.utcnow()
                
                logger.info(f"Updated inspection {inspection.inspection_number} status from {old_status} to {new_status}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update inspection status {inspection_id}: {e}")
            return False
    
    def delete_inspection(self, inspection_id: UUID, deleted_by: str) -> bool:
        """
        Delete an inspection (only if in scheduled status).
        
        Args:
            inspection_id: UUID of the inspection to delete
            deleted_by: User performing the deletion
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                inspection = session.query(Inspection).filter(
                    Inspection.id == inspection_id
                ).first()
                
                if not inspection:
                    logger.warning(f"Inspection {inspection_id} not found")
                    return False
                
                # Only allow deletion of scheduled inspections
                if inspection.status != InspectionStatus.SCHEDULED.value:
                    logger.warning(f"Cannot delete inspection {inspection.inspection_number} - status is {inspection.status}")
                    return False
                
                # Delete related records
                session.query(InspectionLine).filter(
                    InspectionLine.inspection_id == inspection_id
                ).delete()
                
                # Delete inspection
                session.delete(inspection)
                
                logger.info(f"Deleted inspection: {inspection.inspection_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete inspection {inspection_id}: {e}")
            return False
    
    def get_inspection_statistics(self) -> Dict[str, Any]:
        """
        Get inspection statistics for dashboard.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.db_manager.get_session() as session:
                # Total inspections
                total_inspections = session.query(Inspection).count()
                
                # Inspections by status
                status_counts = {}
                for status in InspectionStatus:
                    count = session.query(Inspection).filter(
                        Inspection.status == status.value
                    ).count()
                    status_counts[status.value] = count
                
                # Inspections by type
                type_counts = {}
                for inspection_type in InspectionType:
                    count = session.query(Inspection).filter(
                        Inspection.inspection_type == inspection_type.value
                    ).count()
                    type_counts[inspection_type.value] = count
                
                # Calculate acceptance rate
                passed_inspections = session.query(Inspection).filter(
                    Inspection.overall_result == 'PASS'
                ).count()
                
                completed_inspections = session.query(Inspection).filter(
                    Inspection.status.in_(['Passed', 'Failed', 'Rework Required'])
                ).count()
                
                acceptance_rate = (passed_inspections / completed_inspections * 100) if completed_inspections > 0 else 0
                
                return {
                    'total_inspections': total_inspections,
                    'status_counts': status_counts,
                    'type_counts': type_counts,
                    'acceptance_rate': acceptance_rate
                }
                
        except Exception as e:
            logger.error(f"Failed to get inspection statistics: {e}")
            return {
                'total_inspections': 0,
                'status_counts': {},
                'type_counts': {},
                'acceptance_rate': 0
            }
    
    def get_pending_inspections(self) -> List[Inspection]:
        """
        Get pending inspections.
        
        Returns:
            List of pending Inspection objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(Inspection).filter(
                    Inspection.status == InspectionStatus.SCHEDULED.value
                ).order_by(Inspection.inspection_date).all()
        except Exception as e:
            logger.error(f"Failed to get pending inspections: {e}")
            return []
    
    def get_recent_inspections(self, limit: int = 10) -> List[Inspection]:
        """
        Get recent inspections.
        
        Args:
            limit: Maximum number of inspections to return
            
        Returns:
            List of recent Inspection objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(Inspection).order_by(
                    Inspection.created_at.desc()
                ).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get recent inspections: {e}")
            return []
    
    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """Validate inspection status transitions."""
        valid_transitions = {
            InspectionStatus.SCHEDULED.value: [InspectionStatus.IN_PROGRESS.value, InspectionStatus.CANCELLED.value],
            InspectionStatus.IN_PROGRESS.value: [InspectionStatus.PASSED.value, InspectionStatus.FAILED.value, InspectionStatus.REWORK_REQUIRED.value, InspectionStatus.CANCELLED.value],
            InspectionStatus.PASSED.value: [],
            InspectionStatus.FAILED.value: [],
            InspectionStatus.REWORK_REQUIRED.value: [],
            InspectionStatus.CANCELLED.value: []
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}")
            return None
