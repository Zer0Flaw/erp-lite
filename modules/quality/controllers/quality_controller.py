"""
Quality controller for XPanda ERP-Lite.
Bridges UI components with quality services and handles business logic coordination.
"""

import logging
from typing import List, Optional, Dict, Any, Callable
from uuid import UUID
from datetime import date

from database.connection import DatabaseManager
from ..services.quality_service import QualityService
from ..services.inspection_service import InspectionService
from ..services.ncr_service import NCRService
from ..services.capa_service import CAPAService

logger = logging.getLogger(__name__)


class QualityController:
    """Controller class for quality operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.quality_service = QualityService(db_manager)
        self.inspection_service = InspectionService(db_manager)
        self.ncr_service = NCRService(db_manager)
        self.capa_service = CAPAService(db_manager)
        
        # Callbacks for UI updates
        self._data_changed_callbacks: List[Callable] = []
        self._status_message_callbacks: List[Callable[[str, int], None]] = []
    
    def register_data_changed_callback(self, callback: Callable) -> None:
        """Register a callback for data change notifications."""
        self._data_changed_callbacks.append(callback)
    
    def register_status_message_callback(self, callback: Callable[[str, int], None]) -> None:
        """Register a callback for status message notifications."""
        self._status_message_callbacks.append(callback)
    
    def _notify_data_changed(self) -> None:
        """Notify all registered callbacks that data has changed."""
        for callback in self._data_changed_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in data changed callback: {e}")
    
    def _show_status_message(self, message: str, timeout: int = 3000) -> None:
        """Show status message through registered callbacks."""
        for callback in self._status_message_callbacks:
            try:
                callback(message, timeout)
            except Exception as e:
                logger.error(f"Error in status message callback: {e}")
    
    # Inspection Management Methods
    
    def create_inspection(self, inspection_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a new inspection.
        
        Args:
            inspection_data: Dictionary containing inspection information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate required fields
            required_fields = ['inspection_number', 'inspection_type', 'inspector', 'quantity_inspected', 'created_by']
            missing_fields = [field for field in required_fields if field not in inspection_data]
            
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
            
            # Create inspection
            inspection = self.inspection_service.create_inspection(inspection_data)
            
            if inspection:
                self._notify_data_changed()
                self._show_status_message(f"Inspection '{inspection.inspection_number}' created successfully")
                return True, f"Inspection '{inspection.inspection_number}' created successfully"
            else:
                return False, "Failed to create inspection"
                
        except Exception as e:
            logger.error(f"Error creating inspection: {e}")
            return False, f"Error creating inspection: {e}"
    
    def update_inspection(self, inspection_id: UUID, update_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update an existing inspection.
        
        Args:
            inspection_id: UUID of the inspection to update
            update_data: Dictionary containing updated fields
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.inspection_service.update_inspection(inspection_id, update_data)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("Inspection updated successfully")
                return True, "Inspection updated successfully"
            else:
                return False, "Failed to update inspection"
                
        except Exception as e:
            logger.error(f"Error updating inspection: {e}")
            return False, f"Error updating inspection: {e}"
    
    def update_inspection_status(self, inspection_id: UUID, new_status: str, updated_by: str) -> Tuple[bool, str]:
        """
        Update inspection status.
        
        Args:
            inspection_id: UUID of the inspection
            new_status: New status
            updated_by: User making the change
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.inspection_service.update_inspection_status(inspection_id, new_status, updated_by)
            
            if success:
                self._notify_data_changed()
                self._show_status_message(f"Inspection status updated to {new_status}")
                return True, f"Inspection status updated to {new_status}"
            else:
                return False, "Failed to update inspection status"
                
        except Exception as e:
            logger.error(f"Error updating inspection status: {e}")
            return False, f"Error updating inspection status: {e}"
    
    def delete_inspection(self, inspection_id: UUID, deleted_by: str) -> Tuple[bool, str]:
        """
        Delete an inspection.
        
        Args:
            inspection_id: UUID of the inspection to delete
            deleted_by: User performing the deletion
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.inspection_service.delete_inspection(inspection_id, deleted_by)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("Inspection deleted successfully")
                return True, "Inspection deleted successfully"
            else:
                return False, "Failed to delete inspection - may not be in scheduled status"
                
        except Exception as e:
            logger.error(f"Error deleting inspection: {e}")
            return False, f"Error deleting inspection: {e}"
    
    def get_inspection_by_id(self, inspection_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get inspection details by ID.
        
        Args:
            inspection_id: UUID of the inspection
            
        Returns:
            Inspection dictionary or None if not found
        """
        try:
            inspection = self.inspection_service.get_inspection_by_id(inspection_id)
            if inspection:
                return {
                    'id': str(inspection.id),
                    'inspection_number': inspection.inspection_number,
                    'inspection_type': inspection.inspection_type,
                    'status': inspection.status,
                    'work_order_id': str(inspection.work_order_id) if inspection.work_order_id else None,
                    'sales_order_id': str(inspection.sales_order_id) if inspection.sales_order_id else None,
                    'material_sku': inspection.material_sku,
                    'batch_number': inspection.batch_number,
                    'inspection_date': inspection.inspection_date.strftime('%Y-%m-%d') if inspection.inspection_date else None,
                    'inspector': inspection.inspector,
                    'quantity_inspected': inspection.quantity_inspected,
                    'quantity_passed': inspection.quantity_passed,
                    'quantity_failed': inspection.quantity_failed,
                    'quantity_rework': inspection.quantity_rework,
                    'overall_result': inspection.overall_result,
                    'acceptance_rate': float(inspection.acceptance_rate) if inspection.acceptance_rate else 0,
                    'inspection_procedure': inspection.inspection_procedure,
                    'specifications': inspection.specifications,
                    'notes': inspection.notes,
                    'inspection_lines': [
                        {
                            'id': str(line.id),
                            'line_number': line.line_number,
                            'characteristic': line.characteristic,
                            'specification': line.specification,
                            'measurement_method': line.measurement_method,
                            'measured_value': float(line.measured_value) if line.measured_value else 0,
                            'tolerance_min': float(line.tolerance_min) if line.tolerance_min else 0,
                            'tolerance_max': float(line.tolerance_max) if line.tolerance_max else 0,
                            'result': line.result,
                            'deviation': float(line.deviation) if line.deviation else 0,
                            'notes': line.notes
                        }
                        for line in inspection.inspection_lines
                    ]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting inspection {inspection_id}: {e}")
            return None
    
    def search_inspections(self, search_term: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search inspections.
        
        Args:
            search_term: Search term
            status_filter: Optional status filter
            
        Returns:
            List of inspection dictionaries
        """
        try:
            inspections = self.inspection_service.search_inspections(search_term, status_filter)
            
            return [
                {
                    'id': str(inspection.id),
                    'inspection_number': inspection.inspection_number,
                    'inspection_type': inspection.inspection_type,
                    'status': inspection.status,
                    'material_sku': inspection.material_sku,
                    'batch_number': inspection.batch_number,
                    'inspector': inspection.inspector,
                    'overall_result': inspection.overall_result,
                    'acceptance_rate': float(inspection.acceptance_rate) if inspection.acceptance_rate else 0,
                    'inspection_date': inspection.inspection_date.strftime('%Y-%m-%d') if inspection.inspection_date else None
                }
                for inspection in inspections
            ]
        except Exception as e:
            logger.error(f"Error searching inspections: {e}")
            return []
    
    # NCR Management Methods
    
    def create_ncr(self, ncr_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a new NCR.
        
        Args:
            ncr_data: Dictionary containing NCR information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate required fields
            required_fields = ['ncr_number', 'severity', 'reported_by', 'description', 'created_by']
            missing_fields = [field for field in required_fields if field not in ncr_data]
            
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
            
            # Create NCR
            ncr = self.ncr_service.create_ncr(ncr_data)
            
            if ncr:
                self._notify_data_changed()
                self._show_status_message(f"NCR '{ncr.ncr_number}' created successfully")
                return True, f"NCR '{ncr.ncr_number}' created successfully"
            else:
                return False, "Failed to create NCR"
                
        except Exception as e:
            logger.error(f"Error creating NCR: {e}")
            return False, f"Error creating NCR: {e}"
    
    def update_ncr(self, ncr_id: UUID, update_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update an existing NCR.
        
        Args:
            ncr_id: UUID of the NCR to update
            update_data: Dictionary containing updated fields
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.ncr_service.update_ncr(ncr_id, update_data)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("NCR updated successfully")
                return True, "NCR updated successfully"
            else:
                return False, "Failed to update NCR"
                
        except Exception as e:
            logger.error(f"Error updating NCR: {e}")
            return False, f"Error updating NCR: {e}"
    
    def update_ncr_status(self, ncr_id: UUID, new_status: str, updated_by: str) -> Tuple[bool, str]:
        """
        Update NCR status.
        
        Args:
            ncr_id: UUID of the NCR
            new_status: New status
            updated_by: User making the change
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.ncr_service.update_ncr_status(ncr_id, new_status, updated_by)
            
            if success:
                self._notify_data_changed()
                self._show_status_message(f"NCR status updated to {new_status}")
                return True, f"NCR status updated to {new_status}"
            else:
                return False, "Failed to update NCR status"
                
        except Exception as e:
            logger.error(f"Error updating NCR status: {e}")
            return False, f"Error updating NCR status: {e}"
    
    def close_ncr(self, ncr_id: UUID, closed_by: str, closure_notes: str = '') -> Tuple[bool, str]:
        """
        Close an NCR.
        
        Args:
            ncr_id: UUID of the NCR to close
            closed_by: User closing the NCR
            closure_notes: Optional closure notes
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.ncr_service.close_ncr(ncr_id, closed_by, closure_notes)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("NCR closed successfully")
                return True, "NCR closed successfully"
            else:
                return False, "Failed to close NCR - may not have disposition set"
                
        except Exception as e:
            logger.error(f"Error closing NCR: {e}")
            return False, f"Error closing NCR: {e}"
    
    def get_ncr_by_id(self, ncr_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get NCR details by ID.
        
        Args:
            ncr_id: UUID of the NCR
            
        Returns:
            NCR dictionary or None if not found
        """
        try:
            ncr = self.ncr_service.get_ncr_by_id(ncr_id)
            if ncr:
                return {
                    'id': str(ncr.id),
                    'ncr_number': ncr.ncr_number,
                    'severity': ncr.severity,
                    'status': ncr.status,
                    'disposition': ncr.disposition,
                    'inspection_id': str(ncr.inspection_id) if ncr.inspection_id else None,
                    'work_order_id': str(ncr.work_order_id) if ncr.work_order_id else None,
                    'sales_order_id': str(ncr.sales_order_id) if ncr.sales_order_id else None,
                    'material_sku': ncr.material_sku,
                    'batch_number': ncr.batch_number,
                    'discovery_date': ncr.discovery_date.strftime('%Y-%m-%d') if ncr.discovery_date else None,
                    'reported_by': ncr.reported_by,
                    'location': ncr.location,
                    'description': ncr.description,
                    'investigation_summary': ncr.investigation_summary,
                    'root_cause': ncr.root_cause,
                    'investigation_date': ncr.investigation_date.strftime('%Y-%m-%d') if ncr.investigation_date else None,
                    'investigator': ncr.investigator,
                    'disposition_date': ncr.disposition_date.strftime('%Y-%m-%d') if ncr.disposition_date else None,
                    'disposition_by': ncr.disposition_by,
                    'disposition_notes': ncr.disposition_notes,
                    'closure_date': ncr.closure_date.strftime('%Y-%m-%d') if ncr.closure_date else None,
                    'closed_by': ncr.closed_by,
                    'closure_notes': ncr.closure_notes
                }
            return None
        except Exception as e:
            logger.error(f"Error getting NCR {ncr_id}: {e}")
            return None
    
    def search_ncrs(self, search_term: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search NCRs.
        
        Args:
            search_term: Search term
            status_filter: Optional status filter
            
        Returns:
            List of NCR dictionaries
        """
        try:
            ncrs = self.ncr_service.search_ncrs(search_term, status_filter)
            
            return [
                {
                    'id': str(ncr.id),
                    'ncr_number': ncr.ncr_number,
                    'severity': ncr.severity,
                    'status': ncr.status,
                    'material_sku': ncr.material_sku,
                    'batch_number': ncr.batch_number,
                    'discovery_date': ncr.discovery_date.strftime('%Y-%m-%d') if ncr.discovery_date else None,
                    'reported_by': ncr.reported_by,
                    'days_open': ncr.days_open
                }
                for ncr in ncrs
            ]
        except Exception as e:
            logger.error(f"Error searching NCRs: {e}")
            return []
    
    # CAPA Management Methods
    
    def create_capa(self, capa_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a new CAPA.
        
        Args:
            capa_data: Dictionary containing CAPA information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate required fields
            required_fields = ['capa_number', 'title', 'assigned_to', 'description', 'created_by']
            missing_fields = [field for field in required_fields if field not in capa_data]
            
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
            
            # Create CAPA
            capa = self.capa_service.create_capa(capa_data)
            
            if capa:
                self._notify_data_changed()
                self._show_status_message(f"CAPA '{capa.capa_number}' created successfully")
                return True, f"CAPA '{capa.capa_number}' created successfully"
            else:
                return False, "Failed to create CAPA"
                
        except Exception as e:
            logger.error(f"Error creating CAPA: {e}")
            return False, f"Error creating CAPA: {e}"
    
    def update_capa(self, capa_id: UUID, update_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update an existing CAPA.
        
        Args:
            capa_id: UUID of the CAPA to update
            update_data: Dictionary containing updated fields
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.capa_service.update_capa(capa_id, update_data)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("CAPA updated successfully")
                return True, "CAPA updated successfully"
            else:
                return False, "Failed to update CAPA"
                
        except Exception as e:
            logger.error(f"Error updating CAPA: {e}")
            return False, f"Error updating CAPA: {e}"
    
    def update_capa_status(self, capa_id: UUID, new_status: str, updated_by: str) -> Tuple[bool, str]:
        """
        Update CAPA status.
        
        Args:
            capa_id: UUID of the CAPA
            new_status: New status
            updated_by: User making the change
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.capa_service.update_capa_status(capa_id, new_status, updated_by)
            
            if success:
                self._notify_data_changed()
                self._show_status_message(f"CAPA status updated to {new_status}")
                return True, f"CAPA status updated to {new_status}"
            else:
                return False, "Failed to update CAPA status"
                
        except Exception as e:
            logger.error(f"Error updating CAPA status: {e}")
            return False, f"Error updating CAPA status: {e}"
    
    def complete_capa(self, capa_id: UUID, completed_by: str) -> Tuple[bool, str]:
        """
        Complete a CAPA.
        
        Args:
            capa_id: UUID of the CAPA to complete
            completed_by: User completing the CAPA
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.capa_service.complete_capa(capa_id, completed_by)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("CAPA completed successfully")
                return True, "CAPA completed successfully"
            else:
                return False, "Failed to complete CAPA - may not be in progress"
                
        except Exception as e:
            logger.error(f"Error completing CAPA: {e}")
            return False, f"Error completing CAPA: {e}"
    
    def verify_capa(self, capa_id: UUID, verified_by: str, effectiveness_rating: float, effectiveness_notes: str = '') -> Tuple[bool, str]:
        """
        Verify a CAPA.
        
        Args:
            capa_id: UUID of the CAPA to verify
            verified_by: User verifying the CAPA
            effectiveness_rating: Effectiveness rating (1-5)
            effectiveness_notes: Optional effectiveness notes
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.capa_service.verify_capa(capa_id, verified_by, effectiveness_rating, effectiveness_notes)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("CAPA verified successfully")
                return True, "CAPA verified successfully"
            else:
                return False, "Failed to verify CAPA - may not be completed"
                
        except Exception as e:
            logger.error(f"Error verifying CAPA: {e}")
            return False, f"Error verifying CAPA: {e}"
    
    def get_capa_by_id(self, capa_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get CAPA details by ID.
        
        Args:
            capa_id: UUID of the CAPA
            
        Returns:
            CAPA dictionary or None if not found
        """
        try:
            capa = self.capa_service.get_capa_by_id(capa_id)
            if capa:
                return {
                    'id': str(capa.id),
                    'capa_number': capa.capa_number,
                    'title': capa.title,
                    'status': capa.status,
                    'priority': capa.priority,
                    'ncr_id': str(capa.ncr_id) if capa.ncr_id else None,
                    'source_type': capa.source_type,
                    'source_id': str(capa.source_id) if capa.source_id else None,
                    'description': capa.description,
                    'root_cause': capa.root_cause,
                    'corrective_action': capa.corrective_action,
                    'preventive_action': capa.preventive_action,
                    'assigned_to': capa.assigned_to,
                    'department': capa.department,
                    'created_date': capa.created_date.strftime('%Y-%m-%d') if capa.created_date else None,
                    'due_date': capa.due_date.strftime('%Y-%m-%d') if capa.due_date else None,
                    'completion_date': capa.completion_date.strftime('%Y-%m-%d') if capa.completion_date else None,
                    'verification_date': capa.verification_date.strftime('%Y-%m-%d') if capa.verification_date else None,
                    'effectiveness_rating': float(capa.effectiveness_rating) if capa.effectiveness_rating else 0,
                    'effectiveness_notes': capa.effectiveness_notes,
                    'created_by': capa.created_by,
                    'completed_by': capa.completed_by,
                    'verified_by': capa.verified_by
                }
            return None
        except Exception as e:
            logger.error(f"Error getting CAPA {capa_id}: {e}")
            return None
    
    def search_capas(self, search_term: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search CAPAs.
        
        Args:
            search_term: Search term
            status_filter: Optional status filter
            
        Returns:
            List of CAPA dictionaries
        """
        try:
            capas = self.capa_service.search_capas(search_term, status_filter)
            
            return [
                {
                    'id': str(capa.id),
                    'capa_number': capa.capa_number,
                    'title': capa.title,
                    'status': capa.status,
                    'priority': capa.priority,
                    'assigned_to': capa.assigned_to,
                    'created_date': capa.created_date.strftime('%Y-%m-%d') if capa.created_date else None,
                    'due_date': capa.due_date.strftime('%Y-%m-%d') if capa.due_date else None,
                    'days_overdue': capa.days_overdue
                }
                for capa in capas
            ]
        except Exception as e:
            logger.error(f"Error searching CAPAs: {e}")
            return []
    
    # Dashboard and Reporting Methods
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get dashboard data for quality module.
        
        Returns:
            Dictionary with dashboard information
        """
        try:
            return self.quality_service.get_dashboard_data()
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                'summary_cards': {
                    'pending_inspections': 0,
                    'open_ncrs': 0,
                    'active_capas': 0,
                    'quality_score': '0.0%'
                },
                'inspection_status_counts': {},
                'inspection_type_counts': {},
                'ncr_status_counts': {},
                'ncr_severity_counts': {},
                'capa_status_counts': {},
                'capa_priority_counts': {},
                'pending_inspections': [],
                'open_ncrs': [],
                'active_capas': [],
                'overdue_ncrs': [],
                'overdue_capas': [],
                'recent_inspections': [],
                'recent_ncrs': [],
                'recent_capas': []
            }
    
    def create_ncr_from_inspection(self, inspection_id: UUID, ncr_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create an NCR from a failed inspection.
        
        Args:
            inspection_id: UUID of the inspection
            ncr_data: Dictionary containing NCR information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success, message = self.quality_service.create_ncr_from_inspection(inspection_id, ncr_data)
            
            if success:
                self._notify_data_changed()
                self._show_status_message(message)
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error creating NCR from inspection: {e}")
            return False, f"Error creating NCR from inspection: {e}"
    
    def create_capa_from_ncr(self, ncr_id: UUID, capa_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a CAPA from an NCR.
        
        Args:
            ncr_id: UUID of the NCR
            capa_data: Dictionary containing CAPA information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success, message = self.quality_service.create_capa_from_ncr(ncr_id, capa_data)
            
            if success:
                self._notify_data_changed()
                self._show_status_message(message)
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error creating CAPA from NCR: {e}")
            return False, f"Error creating CAPA from NCR: {e}"
    
    def get_quality_alerts(self) -> List[Dict[str, Any]]:
        """
        Get quality alerts and warnings.
        
        Returns:
            List of quality alerts
        """
        try:
            return self.quality_service.get_quality_alerts()
        except Exception as e:
            logger.error(f"Error getting quality alerts: {e}")
            return []
    
    def get_quality_score_by_material(self, material_sku: str) -> Dict[str, Any]:
        """
        Get quality score for a specific material.
        
        Args:
            material_sku: Material SKU
            
        Returns:
            Dictionary with quality score information
        """
        try:
            return self.quality_service.get_quality_score_by_material(material_sku)
        except Exception as e:
            logger.error(f"Error getting quality score by material: {e}")
            return {
                'material_sku': material_sku,
                'quality_score': 0,
                'total_inspections': 0,
                'passed_inspections': 0,
                'failed_inspections': 0,
                'acceptance_rate': 0,
                'last_inspection_date': None
            }
    
    def get_material_quality_history(self, material_sku: str, limit: int = 20) -> Dict[str, List]:
        """
        Get quality history for a specific material.
        
        Args:
            material_sku: Material SKU
            limit: Maximum number of records to return
            
        Returns:
            Dictionary with quality history
        """
        try:
            return self.quality_service.get_material_quality_history(material_sku, limit)
        except Exception as e:
            logger.error(f"Error getting material quality history: {e}")
            return {
                'material_sku': material_sku,
                'inspection_history': [],
                'ncr_history': []
            }
    
    def get_quality_metrics_by_period(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Get quality metrics for a specific period.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with quality metrics
        """
        try:
            return self.quality_service.get_quality_metrics_by_period(start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting quality metrics by period: {e}")
            return {
                'period_start': start_date.strftime('%Y-%m-%d'),
                'period_end': end_date.strftime('%Y-%m-%d'),
                'total_inspections': 0,
                'passed_inspections': 0,
                'failed_inspections': 0,
                'acceptance_rate': 0,
                'total_ncrs': 0,
                'critical_ncrs': 0,
                'major_ncrs': 0,
                'minor_ncrs': 0,
                'total_capas': 0,
                'completed_capas': 0,
                'overdue_capas': 0,
                'avg_effectiveness_rating': 0
            }
    
    def get_quality_trends(self, days: int = 30) -> Dict[str, List]:
        """
        Get quality trends over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend data
        """
        try:
            return self.quality_service.get_quality_trends(days)
        except Exception as e:
            logger.error(f"Error getting quality trends: {e}")
            return {
                'dates': [],
                'acceptance_rates': [],
                'ncr_counts': [],
                'capa_counts': []
            }
    
    def get_inspection_statuses(self) -> List[str]:
        """
        Get all inspection status options.
        
        Returns:
            List of status names
        """
        try:
            from database.models.quality import InspectionStatus
            return [status.value for status in InspectionStatus]
        except Exception as e:
            logger.error(f"Error getting inspection statuses: {e}")
            return []
    
    def get_inspection_types(self) -> List[str]:
        """
        Get all inspection type options.
        
        Returns:
            List of type names
        """
        try:
            from database.models.quality import InspectionType
            return [inspection_type.value for inspection_type in InspectionType]
        except Exception as e:
            logger.error(f"Error getting inspection types: {e}")
            return []
    
    def get_ncr_statuses(self) -> List[str]:
        """
        Get all NCR status options.
        
        Returns:
            List of status names
        """
        try:
            from database.models.quality import NCRStatus
            return [status.value for status in NCRStatus]
        except Exception as e:
            logger.error(f"Error getting NCR statuses: {e}")
            return []
    
    def get_ncr_severities(self) -> List[str]:
        """
        Get all NCR severity options.
        
        Returns:
            List of severity names
        """
        try:
            from database.models.quality import NCRSeverity
            return [severity.value for severity in NCRSeverity]
        except Exception as e:
            logger.error(f"Error getting NCR severities: {e}")
            return []
    
    def get_capa_statuses(self) -> List[str]:
        """
        Get all CAPA status options.
        
        Returns:
            List of status names
        """
        try:
            from database.models.quality import CAPAStatus
            return [status.value for status in CAPAStatus]
        except Exception as e:
            logger.error(f"Error getting CAPA statuses: {e}")
            return []
    
    def get_capa_priorities(self) -> List[str]:
        """
        Get all CAPA priority options.
        
        Returns:
            List of priority names
        """
        try:
            from database.models.quality import CAPAPriority
            return [priority.value for priority in CAPAPriority]
        except Exception as e:
            logger.error(f"Error getting CAPA priorities: {e}")
            return []
