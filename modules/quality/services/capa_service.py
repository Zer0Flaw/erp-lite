"""
CAPA service for XPanda ERP-Lite.
Provides business logic for Corrective Action Plan operations.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from database.models.quality import CAPAAction, CAPAStatus, CAPAPriority
from database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class CAPAService:
    """Service class for CAPA operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_capa(self, capa_data: Dict[str, Any]) -> Optional[CAPAAction]:
        """
        Create a new CAPA.
        
        Args:
            capa_data: Dictionary containing CAPA information
            
        Returns:
            Created CAPAAction object or None if failed
        """
        try:
            with self.db_manager.get_session() as session:
                # Check if CAPA number already exists
                existing = session.query(CAPAAction).filter(
                    CAPAAction.capa_number == capa_data['capa_number'].upper()
                ).first()
                
                if existing:
                    logger.warning(f"CAPA with number {capa_data['capa_number']} already exists")
                    return None
                
                # Create new CAPA
                capa = CAPAAction(
                    capa_number=capa_data['capa_number'].upper(),
                    title=capa_data['title'],
                    status=capa_data.get('status', CAPAStatus.OPEN.value),
                    priority=capa_data.get('priority', CAPAPriority.MEDIUM.value),
                    ncr_id=capa_data.get('ncr_id'),
                    source_type=capa_data.get('source_type', ''),
                    source_id=capa_data.get('source_id'),
                    description=capa_data['description'],
                    root_cause=capa_data.get('root_cause', ''),
                    corrective_action=capa_data.get('corrective_action', ''),
                    preventive_action=capa_data.get('preventive_action', ''),
                    assigned_to=capa_data['assigned_to'],
                    department=capa_data.get('department', ''),
                    created_date=self._parse_date(capa_data.get('created_date', date.today())),
                    due_date=self._parse_date(capa_data.get('due_date')),
                    completion_date=self._parse_date(capa_data.get('completion_date')),
                    verification_date=self._parse_date(capa_data.get('verification_date')),
                    effectiveness_rating=Decimal(str(capa_data.get('effectiveness_rating', 0))),
                    effectiveness_notes=capa_data.get('effectiveness_notes', ''),
                    created_by=capa_data.get('created_by', 'System'),
                    completed_by=capa_data.get('completed_by', ''),
                    verified_by=capa_data.get('verified_by', '')
                )
                
                session.add(capa)
                logger.info(f"Created CAPA: {capa.capa_number}")
                return capa
                
        except Exception as e:
            logger.error(f"Failed to create CAPA: {e}")
            return None
    
    def get_capa_by_id(self, capa_id: UUID) -> Optional[CAPAAction]:
        """
        Get CAPA by ID.
        
        Args:
            capa_id: UUID of the CAPA
            
        Returns:
            CAPAAction object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(CAPAAction).filter(
                    CAPAAction.id == capa_id
                ).first()
        except Exception as e:
            logger.error(f"Failed to get CAPA {capa_id}: {e}")
            return None
    
    def get_capa_by_number(self, capa_number: str) -> Optional[CAPAAction]:
        """
        Get CAPA by number.
        
        Args:
            capa_number: CAPA number
            
        Returns:
            CAPAAction object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(CAPAAction).filter(
                    CAPAAction.capa_number == capa_number.upper()
                ).first()
        except Exception as e:
            logger.error(f"Failed to get CAPA {capa_number}: {e}")
            return None
    
    def get_all_capas(self, status_filter: Optional[str] = None) -> List[CAPAAction]:
        """
        Get all CAPAs.
        
        Args:
            status_filter: Optional status filter
            
        Returns:
            List of CAPAAction objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(CAPAAction)
                
                if status_filter:
                    query = query.filter(CAPAAction.status == status_filter)
                
                return query.order_by(CAPAAction.capa_number).all()
        except Exception as e:
            logger.error(f"Failed to get CAPAs: {e}")
            return []
    
    def search_capas(self, search_term: str, status_filter: Optional[str] = None) -> List[CAPAAction]:
        """
        Search CAPAs by number, title, or assignee.
        
        Args:
            search_term: Search term
            status_filter: Optional status filter
            
        Returns:
            List of matching CAPAAction objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(CAPAAction)
                
                # Add search conditions
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    (CAPAAction.capa_number.ilike(search_pattern)) |
                    (CAPAAction.title.ilike(search_pattern)) |
                    (CAPAAction.assigned_to.ilike(search_pattern)) |
                    (CAPAAction.description.ilike(search_pattern)) |
                    (CAPAAction.department.ilike(search_pattern))
                )
                
                # Add status filter if specified
                if status_filter:
                    query = query.filter(CAPAAction.status == status_filter)
                
                return query.order_by(CAPAAction.capa_number).all()
        except Exception as e:
            logger.error(f"Failed to search CAPAs: {e}")
            return []
    
    def update_capa(self, capa_id: UUID, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing CAPA.
        
        Args:
            capa_id: UUID of the CAPA to update
            update_data: Dictionary containing updated fields
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                capa = session.query(CAPAAction).filter(
                    CAPAAction.id == capa_id
                ).first()
                
                if not capa:
                    logger.warning(f"CAPA {capa_id} not found")
                    return False
                
                # Update CAPA fields
                for field, value in update_data.items():
                    if hasattr(capa, field) and field not in ['id', 'created_at', 'created_by', 'ncr']:
                        if field == 'capa_number':
                            capa.capa_number = value.upper()
                        elif field in ['effectiveness_rating']:
                            setattr(capa, field, Decimal(str(value)))
                        elif field in ['created_date', 'due_date', 'completion_date', 'verification_date']:
                            setattr(capa, field, self._parse_date(value))
                        else:
                            setattr(capa, field, value)
                
                capa.updated_at = datetime.utcnow()
                
                logger.info(f"Updated CAPA: {capa.capa_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update CAPA {capa_id}: {e}")
            return False
    
    def update_capa_status(self, capa_id: UUID, new_status: str, updated_by: str) -> bool:
        """
        Update CAPA status with proper validation.
        
        Args:
            capa_id: UUID of the CAPA
            new_status: New status
            updated_by: User making the change
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                capa = session.query(CAPAAction).filter(
                    CAPAAction.id == capa_id
                ).first()
                
                if not capa:
                    logger.warning(f"CAPA {capa_id} not found")
                    return False
                
                # Validate status transition
                if not self._is_valid_status_transition(capa.status, new_status):
                    logger.warning(f"Invalid status transition from {capa.status} to {new_status}")
                    return False
                
                # Update status and related fields
                old_status = capa.status
                capa.status = new_status
                capa.updated_at = datetime.utcnow()
                
                # Handle status-specific updates
                if new_status == CAPAStatus.IN_PROGRESS.value:
                    # No specific field updates for in progress
                    pass
                elif new_status == CAPAStatus.COMPLETED.value:
                    capa.completion_date = date.today()
                    capa.completed_by = updated_by
                elif new_status == CAPAStatus.VERIFIED.value:
                    capa.verification_date = date.today()
                    capa.verified_by = updated_by
                elif new_status == CAPAStatus.CLOSED.value:
                    # CAPA should be verified before closing
                    if capa.status != CAPAStatus.VERIFIED.value:
                        logger.warning(f"Cannot close CAPA {capa.capa_number} - not verified")
                        return False
                
                logger.info(f"Updated CAPA {capa.capa_number} status from {old_status} to {new_status}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update CAPA status {capa_id}: {e}")
            return False
    
    def complete_capa(self, capa_id: UUID, completed_by: str) -> bool:
        """
        Complete a CAPA.
        
        Args:
            capa_id: UUID of the CAPA to complete
            completed_by: User completing the CAPA
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                capa = session.query(CAPAAction).filter(
                    CAPAAction.id == capa_id
                ).first()
                
                if not capa:
                    logger.warning(f"CAPA {capa_id} not found")
                    return False
                
                # Only allow completion if in progress
                if capa.status != CAPAStatus.IN_PROGRESS.value:
                    logger.warning(f"Cannot complete CAPA {capa.capa_number} - status is {capa.status}")
                    return False
                
                capa.status = CAPAStatus.COMPLETED.value
                capa.completion_date = date.today()
                capa.completed_by = completed_by
                capa.updated_at = datetime.utcnow()
                
                logger.info(f"Completed CAPA: {capa.capa_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to complete CAPA {capa_id}: {e}")
            return False
    
    def verify_capa(self, capa_id: UUID, verified_by: str, effectiveness_rating: float, effectiveness_notes: str = '') -> bool:
        """
        Verify a CAPA.
        
        Args:
            capa_id: UUID of the CAPA to verify
            verified_by: User verifying the CAPA
            effectiveness_rating: Effectiveness rating (1-5)
            effectiveness_notes: Optional effectiveness notes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                capa = session.query(CAPAAction).filter(
                    CAPAAction.id == capa_id
                ).first()
                
                if not capa:
                    logger.warning(f"CAPA {capa_id} not found")
                    return False
                
                # Only allow verification if completed
                if capa.status != CAPAStatus.COMPLETED.value:
                    logger.warning(f"Cannot verify CAPA {capa.capa_number} - not completed")
                    return False
                
                # Validate effectiveness rating
                if not (1 <= effectiveness_rating <= 5):
                    logger.warning(f"Invalid effectiveness rating: {effectiveness_rating}")
                    return False
                
                capa.status = CAPAStatus.VERIFIED.value
                capa.verification_date = date.today()
                capa.verified_by = verified_by
                capa.effectiveness_rating = Decimal(str(effectiveness_rating))
                capa.effectiveness_notes = effectiveness_notes
                capa.updated_at = datetime.utcnow()
                
                logger.info(f"Verified CAPA: {capa.capa_number} with rating {effectiveness_rating}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to verify CAPA {capa_id}: {e}")
            return False
    
    def close_capa(self, capa_id: UUID, closed_by: str) -> bool:
        """
        Close a CAPA.
        
        Args:
            capa_id: UUID of the CAPA to close
            closed_by: User closing the CAPA
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                capa = session.query(CAPAAction).filter(
                    CAPAAction.id == capa_id
                ).first()
                
                if not capa:
                    logger.warning(f"CAPA {capa_id} not found")
                    return False
                
                # Only allow closing if verified
                if capa.status != CAPAStatus.VERIFIED.value:
                    logger.warning(f"Cannot close CAPA {capa.capa_number} - not verified")
                    return False
                
                capa.status = CAPAStatus.CLOSED.value
                capa.updated_at = datetime.utcnow()
                
                logger.info(f"Closed CAPA: {capa.capa_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to close CAPA {capa_id}: {e}")
            return False
    
    def cancel_capa(self, capa_id: UUID, cancelled_by: str) -> bool:
        """
        Cancel a CAPA.
        
        Args:
            capa_id: UUID of the CAPA to cancel
            cancelled_by: User cancelling the CAPA
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                capa = session.query(CAPAAction).filter(
                    CAPAAction.id == capa_id
                ).first()
                
                if not capa:
                    logger.warning(f"CAPA {capa_id} not found")
                    return False
                
                capa.status = CAPAStatus.CANCELLED.value
                capa.updated_at = datetime.utcnow()
                
                logger.info(f"Cancelled CAPA: {capa.capa_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to cancel CAPA {capa_id}: {e}")
            return False
    
    def get_capa_statistics(self) -> Dict[str, Any]:
        """
        Get CAPA statistics for dashboard.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.db_manager.get_session() as session:
                # Total CAPAs
                total_capas = session.query(CAPAAction).count()
                
                # CAPAs by status
                status_counts = {}
                for status in CAPAStatus:
                    count = session.query(CAPAAction).filter(
                        CAPAAction.status == status.value
                    ).count()
                    status_counts[status.value] = count
                
                # CAPAs by priority
                priority_counts = {}
                for priority in CAPAPriority:
                    count = session.query(CAPAAction).filter(
                        CAPAAction.priority == priority.value
                    ).count()
                    priority_counts[priority.value] = count
                
                # Active CAPAs
                active_capas = session.query(CAPAAction).filter(
                    CAPAAction.status.in_([CAPAStatus.OPEN.value, CAPAStatus.IN_PROGRESS.value])
                ).count()
                
                # Overdue CAPAs
                today = date.today()
                overdue_capas = session.query(CAPAAction).filter(
                    CAPAAction.due_date < today,
                    CAPAAction.status.in_([CAPAStatus.OPEN.value, CAPAStatus.IN_PROGRESS.value])
                ).count()
                
                # Average effectiveness rating
                verified_capas = session.query(CAPAAction).filter(
                    CAPAAction.effectiveness_rating.isnot(None)
                ).all()
                
                avg_effectiveness = 0
                if verified_capas:
                    total_rating = sum(float(capa.effectiveness_rating) for capa in verified_capas)
                    avg_effectiveness = total_rating / len(verified_capas)
                
                return {
                    'total_capas': total_capas,
                    'status_counts': status_counts,
                    'priority_counts': priority_counts,
                    'active_capas': active_capas,
                    'overdue_capas': overdue_capas,
                    'avg_effectiveness': avg_effectiveness
                }
                
        except Exception as e:
            logger.error(f"Failed to get CAPA statistics: {e}")
            return {
                'total_capas': 0,
                'status_counts': {},
                'priority_counts': {},
                'active_capas': 0,
                'overdue_capas': 0,
                'avg_effectiveness': 0
            }
    
    def get_active_capas(self) -> List[CAPAAction]:
        """
        Get active CAPAs.
        
        Returns:
            List of active CAPAAction objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(CAPAAction).filter(
                    CAPAAction.status.in_([CAPAStatus.OPEN.value, CAPAStatus.IN_PROGRESS.value])
                ).order_by(CAPAAction.due_date).all()
        except Exception as e:
            logger.error(f"Failed to get active CAPAs: {e}")
            return []
    
    def get_overdue_capas(self) -> List[CAPAAction]:
        """
        Get overdue CAPAs.
        
        Returns:
            List of overdue CAPAAction objects
        """
        try:
            with self.db_manager.get_session() as session:
                today = date.today()
                
                return session.query(CAPAAction).filter(
                    CAPAAction.due_date < today,
                    CAPAAction.status.in_([CAPAStatus.OPEN.value, CAPAStatus.IN_PROGRESS.value])
                ).order_by(CAPAAction.due_date).all()
        except Exception as e:
            logger.error(f"Failed to get overdue CAPAs: {e}")
            return []
    
    def get_recent_capas(self, limit: int = 10) -> List[CAPAAction]:
        """
        Get recent CAPAs.
        
        Args:
            limit: Maximum number of CAPAs to return
            
        Returns:
            List of recent CAPAAction objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(CAPAAction).order_by(
                    CAPAAction.created_at.desc()
                ).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get recent CAPAs: {e}")
            return []
    
    def get_capas_by_assignee(self, assigned_to: str) -> List[CAPAAction]:
        """
        Get CAPAs assigned to a specific person.
        
        Args:
            assigned_to: Assignee name
            
        Returns:
            List of CAPAAction objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(CAPAAction).filter(
                    CAPAAction.assigned_to == assigned_to
                ).order_by(CAPAAction.due_date).all()
        except Exception as e:
            logger.error(f"Failed to get CAPAs by assignee {assigned_to}: {e}")
            return []
    
    def get_capas_by_priority(self, priority: str) -> List[CAPAAction]:
        """
        Get CAPAs by priority level.
        
        Args:
            priority: Priority level
            
        Returns:
            List of CAPAAction objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(CAPAAction).filter(
                    CAPAAction.priority == priority
                ).order_by(CAPAAction.due_date).all()
        except Exception as e:
            logger.error(f"Failed to get CAPAs by priority {priority}: {e}")
            return []
    
    def get_capas_by_department(self, department: str) -> List[CAPAAction]:
        """
        Get CAPAs by department.
        
        Args:
            department: Department name
            
        Returns:
            List of CAPAAction objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(CAPAAction).filter(
                    CAPAAction.department == department
                ).order_by(CAPAAction.due_date).all()
        except Exception as e:
            logger.error(f"Failed to get CAPAs by department {department}: {e}")
            return []
    
    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """Validate CAPA status transitions."""
        valid_transitions = {
            CAPAStatus.OPEN.value: [CAPAStatus.IN_PROGRESS.value, CAPAStatus.CANCELLED.value],
            CAPAStatus.IN_PROGRESS.value: [CAPAStatus.COMPLETED.value, CAPAStatus.OPEN.value, CAPAStatus.CANCELLED.value],
            CAPAStatus.COMPLETED.value: [CAPAStatus.VERIFIED.value, CAPAStatus.IN_PROGRESS.value, CAPAStatus.CANCELLED.value],
            CAPAStatus.VERIFIED.value: [CAPAStatus.CLOSED.value, CAPAStatus.COMPLETED.value, CAPAStatus.CANCELLED.value],
            CAPAStatus.CLOSED.value: [],  # No transitions from closed
            CAPAStatus.CANCELLED.value: []  # No transitions from cancelled
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
