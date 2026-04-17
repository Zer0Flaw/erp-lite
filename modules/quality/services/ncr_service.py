"""
NCR service for XPanda ERP-Lite.
Provides business logic for Non-Conformance Report operations.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date

from database.models.quality import NonConformanceReport, NCRStatus, NCRSeverity, NCRDisposition
from database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class NCRService:
    """Service class for NCR operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_ncr(self, ncr_data: Dict[str, Any]) -> Optional[NonConformanceReport]:
        """
        Create a new NCR.
        
        Args:
            ncr_data: Dictionary containing NCR information
            
        Returns:
            Created NonConformanceReport object or None if failed
        """
        try:
            with self.db_manager.get_session() as session:
                # Check if NCR number already exists
                existing = session.query(NonConformanceReport).filter(
                    NonConformanceReport.ncr_number == ncr_data['ncr_number'].upper()
                ).first()
                
                if existing:
                    logger.warning(f"NCR with number {ncr_data['ncr_number']} already exists")
                    return None
                
                # Create new NCR
                ncr = NonConformanceReport(
                    ncr_number=ncr_data['ncr_number'].upper(),
                    status=ncr_data.get('status', NCRStatus.OPEN.value),
                    severity=ncr_data['severity'],
                    disposition=ncr_data.get('disposition'),
                    inspection_id=ncr_data.get('inspection_id'),
                    work_order_id=ncr_data.get('work_order_id'),
                    sales_order_id=ncr_data.get('sales_order_id'),
                    material_sku=ncr_data.get('material_sku', ''),
                    batch_number=ncr_data.get('batch_number', ''),
                    discovery_date=self._parse_date(ncr_data.get('discovery_date', date.today())),
                    reported_by=ncr_data['reported_by'],
                    description=ncr_data['description'],
                    location=ncr_data.get('location', ''),
                    investigation_summary=ncr_data.get('investigation_summary', ''),
                    root_cause=ncr_data.get('root_cause', ''),
                    investigation_date=self._parse_date(ncr_data.get('investigation_date')),
                    investigator=ncr_data.get('investigator', ''),
                    disposition_date=self._parse_date(ncr_data.get('disposition_date')),
                    disposition_by=ncr_data.get('disposition_by', ''),
                    disposition_notes=ncr_data.get('disposition_notes', ''),
                    closure_date=self._parse_date(ncr_data.get('closure_date')),
                    closed_by=ncr_data.get('closed_by', ''),
                    closure_notes=ncr_data.get('closure_notes', ''),
                    created_by=ncr_data.get('created_by', 'System')
                )
                
                session.add(ncr)
                logger.info(f"Created NCR: {ncr.ncr_number}")
                return ncr
                
        except Exception as e:
            logger.error(f"Failed to create NCR: {e}")
            return None
    
    def get_ncr_by_id(self, ncr_id: UUID) -> Optional[NonConformanceReport]:
        """
        Get NCR by ID.
        
        Args:
            ncr_id: UUID of the NCR
            
        Returns:
            NonConformanceReport object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(NonConformanceReport).filter(
                    NonConformanceReport.id == ncr_id
                ).first()
        except Exception as e:
            logger.error(f"Failed to get NCR {ncr_id}: {e}")
            return None
    
    def get_ncr_by_number(self, ncr_number: str) -> Optional[NonConformanceReport]:
        """
        Get NCR by number.
        
        Args:
            ncr_number: NCR number
            
        Returns:
            NonConformanceReport object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(NonConformanceReport).filter(
                    NonConformanceReport.ncr_number == ncr_number.upper()
                ).first()
        except Exception as e:
            logger.error(f"Failed to get NCR {ncr_number}: {e}")
            return None
    
    def get_all_ncrs(self, status_filter: Optional[str] = None) -> List[NonConformanceReport]:
        """
        Get all NCRs.
        
        Args:
            status_filter: Optional status filter
            
        Returns:
            List of NonConformanceReport objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(NonConformanceReport)
                
                if status_filter:
                    query = query.filter(NonConformanceReport.status == status_filter)
                
                return query.order_by(NonConformanceReport.ncr_number).all()
        except Exception as e:
            logger.error(f"Failed to get NCRs: {e}")
            return []
    
    def search_ncrs(self, search_term: str, status_filter: Optional[str] = None) -> List[NonConformanceReport]:
        """
        Search NCRs by number, material, or description.
        
        Args:
            search_term: Search term
            status_filter: Optional status filter
            
        Returns:
            List of matching NonConformanceReport objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(NonConformanceReport)
                
                # Add search conditions
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    (NonConformanceReport.ncr_number.ilike(search_pattern)) |
                    (NonConformanceReport.material_sku.ilike(search_pattern)) |
                    (NonConformanceReport.batch_number.ilike(search_pattern)) |
                    (NonConformanceReport.description.ilike(search_pattern)) |
                    (NonConformanceReport.reported_by.ilike(search_pattern))
                )
                
                # Add status filter if specified
                if status_filter:
                    query = query.filter(NonConformanceReport.status == status_filter)
                
                return query.order_by(NonConformanceReport.ncr_number).all()
        except Exception as e:
            logger.error(f"Failed to search NCRs: {e}")
            return []
    
    def update_ncr(self, ncr_id: UUID, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing NCR.
        
        Args:
            ncr_id: UUID of the NCR to update
            update_data: Dictionary containing updated fields
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                ncr = session.query(NonConformanceReport).filter(
                    NonConformanceReport.id == ncr_id
                ).first()
                
                if not ncr:
                    logger.warning(f"NCR {ncr_id} not found")
                    return False
                
                # Update NCR fields
                for field, value in update_data.items():
                    if hasattr(ncr, field) and field not in ['id', 'created_at', 'created_by', 'capa_actions']:
                        if field == 'ncr_number':
                            ncr.ncr_number = value.upper()
                        elif field in ['discovery_date', 'investigation_date', 'disposition_date', 'closure_date']:
                            setattr(ncr, field, self._parse_date(value))
                        else:
                            setattr(ncr, field, value)
                
                ncr.updated_at = datetime.utcnow()
                
                logger.info(f"Updated NCR: {ncr.ncr_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update NCR {ncr_id}: {e}")
            return False
    
    def update_ncr_status(self, ncr_id: UUID, new_status: str, updated_by: str) -> bool:
        """
        Update NCR status with proper validation.
        
        Args:
            ncr_id: UUID of the NCR
            new_status: New status
            updated_by: User making the change
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                ncr = session.query(NonConformanceReport).filter(
                    NonConformanceReport.id == ncr_id
                ).first()
                
                if not ncr:
                    logger.warning(f"NCR {ncr_id} not found")
                    return False
                
                # Validate status transition
                if not self._is_valid_status_transition(ncr.status, new_status):
                    logger.warning(f"Invalid status transition from {ncr.status} to {new_status}")
                    return False
                
                # Update status and related fields
                old_status = ncr.status
                ncr.status = new_status
                ncr.updated_at = datetime.utcnow()
                
                # Handle status-specific updates
                if new_status == NCRStatus.INVESTIGATION.value:
                    ncr.investigation_date = date.today()
                elif new_status == NCRStatus.DISPOSITION.value:
                    ncr.disposition_date = date.today()
                elif new_status == NCRStatus.CLOSED.value:
                    ncr.closure_date = date.today()
                
                logger.info(f"Updated NCR {ncr.ncr_number} status from {old_status} to {new_status}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update NCR status {ncr_id}: {e}")
            return False
    
    def close_ncr(self, ncr_id: UUID, closed_by: str, closure_notes: str = '') -> bool:
        """
        Close an NCR.
        
        Args:
            ncr_id: UUID of the NCR to close
            closed_by: User closing the NCR
            closure_notes: Optional closure notes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                ncr = session.query(NonConformanceReport).filter(
                    NonConformanceReport.id == ncr_id
                ).first()
                
                if not ncr:
                    logger.warning(f"NCR {ncr_id} not found")
                    return False
                
                # Only allow closing if disposition is set
                if not ncr.disposition:
                    logger.warning(f"Cannot close NCR {ncr.ncr_number} - no disposition set")
                    return False
                
                ncr.status = NCRStatus.CLOSED.value
                ncr.closure_date = date.today()
                ncr.closed_by = closed_by
                ncr.closure_notes = closure_notes
                ncr.updated_at = datetime.utcnow()
                
                logger.info(f"Closed NCR: {ncr.ncr_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to close NCR {ncr_id}: {e}")
            return False
    
    def cancel_ncr(self, ncr_id: UUID, cancelled_by: str) -> bool:
        """
        Cancel an NCR.
        
        Args:
            ncr_id: UUID of the NCR to cancel
            cancelled_by: User cancelling the NCR
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                ncr = session.query(NonConformanceReport).filter(
                    NonConformanceReport.id == ncr_id
                ).first()
                
                if not ncr:
                    logger.warning(f"NCR {ncr_id} not found")
                    return False
                
                ncr.status = NCRStatus.CANCELLED.value
                ncr.updated_at = datetime.utcnow()
                
                logger.info(f"Cancelled NCR: {ncr.ncr_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to cancel NCR {ncr_id}: {e}")
            return False
    
    def get_ncr_statistics(self) -> Dict[str, Any]:
        """
        Get NCR statistics for dashboard.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.db_manager.get_session() as session:
                # Total NCRs
                total_ncrs = session.query(NonConformanceReport).count()
                
                # NCRs by status
                status_counts = {}
                for status in NCRStatus:
                    count = session.query(NonConformanceReport).filter(
                        NonConformanceReport.status == status.value
                    ).count()
                    status_counts[status.value] = count
                
                # NCRs by severity
                severity_counts = {}
                for severity in NCRSeverity:
                    count = session.query(NonConformanceReport).filter(
                        NonConformanceReport.severity == severity.value
                    ).count()
                    severity_counts[severity.value] = count
                
                # Open NCRs
                open_ncrs = session.query(NonConformanceReport).filter(
                    NonConformanceReport.status == NCRStatus.OPEN.value
                ).count()
                
                # Overdue NCRs (open for more than 30 days)
                from datetime import timedelta
                thirty_days_ago = date.today() - timedelta(days=30)
                overdue_ncrs = session.query(NonConformanceReport).filter(
                    NonConformanceReport.status == NCRStatus.OPEN.value,
                    NonConformanceReport.discovery_date < thirty_days_ago
                ).count()
                
                return {
                    'total_ncrs': total_ncrs,
                    'status_counts': status_counts,
                    'severity_counts': severity_counts,
                    'open_ncrs': open_ncrs,
                    'overdue_ncrs': overdue_ncrs
                }
                
        except Exception as e:
            logger.error(f"Failed to get NCR statistics: {e}")
            return {
                'total_ncrs': 0,
                'status_counts': {},
                'severity_counts': {},
                'open_ncrs': 0,
                'overdue_ncrs': 0
            }
    
    def get_open_ncrs(self) -> List[NonConformanceReport]:
        """
        Get open NCRs.
        
        Returns:
            List of open NonConformanceReport objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(NonConformanceReport).filter(
                    NonConformanceReport.status == NCRStatus.OPEN.value
                ).order_by(NonConformanceReport.discovery_date).all()
        except Exception as e:
            logger.error(f"Failed to get open NCRs: {e}")
            return []
    
    def get_overdue_ncrs(self) -> List[NonConformanceReport]:
        """
        Get overdue NCRs.
        
        Returns:
            List of overdue NonConformanceReport objects
        """
        try:
            with self.db_manager.get_session() as session:
                from datetime import timedelta
                thirty_days_ago = date.today() - timedelta(days=30)
                
                return session.query(NonConformanceReport).filter(
                    NonConformanceReport.status == NCRStatus.OPEN.value,
                    NonConformanceReport.discovery_date < thirty_days_ago
                ).order_by(NonConformanceReport.discovery_date).all()
        except Exception as e:
            logger.error(f"Failed to get overdue NCRs: {e}")
            return []
    
    def get_recent_ncrs(self, limit: int = 10) -> List[NonConformanceReport]:
        """
        Get recent NCRs.
        
        Args:
            limit: Maximum number of NCRs to return
            
        Returns:
            List of recent NonConformanceReport objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(NonConformanceReport).order_by(
                    NonConformanceReport.created_at.desc()
                ).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get recent NCRs: {e}")
            return []
    
    def get_ncrs_by_severity(self, severity: str) -> List[NonConformanceReport]:
        """
        Get NCRs by severity level.
        
        Args:
            severity: Severity level
            
        Returns:
            List of NonConformanceReport objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(NonConformanceReport).filter(
                    NonConformanceReport.severity == severity
                ).order_by(NonConformanceReport.discovery_date.desc()).all()
        except Exception as e:
            logger.error(f"Failed to get NCRs by severity {severity}: {e}")
            return []
    
    def get_ncrs_by_material(self, material_sku: str) -> List[NonConformanceReport]:
        """
        Get NCRs by material SKU.
        
        Args:
            material_sku: Material SKU
            
        Returns:
            List of NonConformanceReport objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(NonConformanceReport).filter(
                    NonConformanceReport.material_sku == material_sku
                ).order_by(NonConformanceReport.discovery_date.desc()).all()
        except Exception as e:
            logger.error(f"Failed to get NCRs by material {material_sku}: {e}")
            return []
    
    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """Validate NCR status transitions."""
        valid_transitions = {
            NCRStatus.OPEN.value: [NCRStatus.INVESTIGATION.value, NCRStatus.CANCELLED.value],
            NCRStatus.INVESTIGATION.value: [NCRStatus.DISPOSITION.value, NCRStatus.OPEN.value, NCRStatus.CANCELLED.value],
            NCRStatus.DISPOSITION.value: [NCRStatus.CLOSED.value, NCRStatus.INVESTIGATION.value, NCRStatus.CANCELLED.value],
            NCRStatus.CLOSED.value: [],  # No transitions from closed
            NCRStatus.CANCELLED.value: []  # No transitions from cancelled
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
