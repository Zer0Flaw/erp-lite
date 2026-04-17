"""
Production controller for XPanda ERP-Lite.
Bridges UI components with production services and handles business logic coordination.
"""

import logging
from typing import List, Optional, Dict, Any, Callable
from uuid import UUID
from datetime import date

from database.connection import DatabaseManager
from ..services.production_service import ProductionService
from ..services.bom_service import BOMService
from ..services.work_order_service import WorkOrderService

logger = logging.getLogger(__name__)


class ProductionController:
    """Controller class for production operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.production_service = ProductionService(db_manager)
        self.bom_service = BOMService(db_manager)
        self.work_order_service = WorkOrderService(db_manager)
        
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
    
    # BOM Management Methods
    
    def create_bom(self, bom_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a new Bill of Materials.
        
        Args:
            bom_data: Dictionary containing BOM information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate required fields
            required_fields = ['bom_code', 'name', 'finished_good_sku', 'finished_good_name', 'created_by']
            missing_fields = [field for field in required_fields if field not in bom_data]
            
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
            
            # Create BOM
            bom = self.bom_service.create_bom(bom_data)
            
            if bom:
                self._notify_data_changed()
                self._show_status_message(f"BOM '{bom.bom_code}' created successfully")
                return True, f"BOM '{bom.bom_code}' created successfully"
            else:
                return False, "Failed to create BOM"
                
        except Exception as e:
            logger.error(f"Error creating BOM: {e}")
            return False, f"Error creating BOM: {e}"
    
    def update_bom(self, bom_id: UUID, update_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update an existing BOM.
        
        Args:
            bom_id: UUID of the BOM to update
            update_data: Dictionary containing updated fields
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.bom_service.update_bom(bom_id, update_data)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("BOM updated successfully")
                return True, "BOM updated successfully"
            else:
                return False, "Failed to update BOM"
                
        except Exception as e:
            logger.error(f"Error updating BOM: {e}")
            return False, f"Error updating BOM: {e}"
    
    def delete_bom(self, bom_id: UUID, deleted_by: str) -> Tuple[bool, str]:
        """
        Delete a BOM.
        
        Args:
            bom_id: UUID of the BOM to delete
            deleted_by: User performing the deletion
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.bom_service.delete_bom(bom_id, deleted_by)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("BOM deleted successfully")
                return True, "BOM deleted successfully"
            else:
                return False, "Failed to delete BOM - may be in use by active work orders"
                
        except Exception as e:
            logger.error(f"Error deleting BOM: {e}")
            return False, f"Error deleting BOM: {e}"
    
    def get_bom_by_id(self, bom_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get BOM details by ID.
        
        Args:
            bom_id: UUID of the BOM
            
        Returns:
            BOM dictionary or None if not found
        """
        try:
            bom = self.bom_service.get_bom_by_id(bom_id)
            if bom:
                return {
                    'id': str(bom.id),
                    'bom_code': bom.bom_code,
                    'name': bom.name,
                    'description': bom.description or '',
                    'version': bom.version,
                    'finished_good_sku': bom.finished_good_sku,
                    'finished_good_name': bom.finished_good_name,
                    'standard_quantity': float(bom.standard_quantity),
                    'unit_of_measure': bom.unit_of_measure,
                    'standard_cycle_time': float(bom.standard_cycle_time) if bom.standard_cycle_time else None,
                    'setup_time': float(bom.setup_time) if bom.setup_time else None,
                    'yield_percentage': float(bom.yield_percentage) if bom.yield_percentage else None,
                    'effective_date': bom.effective_date.strftime('%Y-%m-%d') if bom.effective_date else None,
                    'expiry_date': bom.expiry_date.strftime('%Y-%m-%d') if bom.expiry_date else None,
                    'status': bom.status,
                    'bom_lines': [
                        {
                            'id': str(line.id),
                            'material_sku': line.material_sku,
                            'material_name': line.material_name,
                            'material_category': line.material_category,
                            'quantity_required': float(line.quantity_required),
                            'unit_of_measure': line.unit_of_measure,
                            'unit_cost': float(line.unit_cost) if line.unit_cost else None,
                            'waste_percentage': float(line.waste_percentage) if line.waste_percentage else None,
                            'is_optional': line.is_optional,
                            'substitution_sku': line.substitution_sku,
                            'notes': line.notes or '',
                            'line_cost': float(line.line_cost) if line.line_cost else None
                        }
                        for line in bom.bom_lines
                    ]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting BOM {bom_id}: {e}")
            return None
    
    def search_boms(self, search_term: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search BOMs.
        
        Args:
            search_term: Search term
            status_filter: Optional status filter
            
        Returns:
            List of BOM dictionaries
        """
        try:
            boms = self.bom_service.search_boms(search_term, status_filter)
            
            return [
                {
                    'id': str(bom.id),
                    'bom_code': bom.bom_code,
                    'name': bom.name,
                    'description': bom.description or '',
                    'finished_good_sku': bom.finished_good_sku,
                    'version': bom.version,
                    'status': bom.status,
                    'line_count': len(bom.bom_lines),
                    'updated_at': bom.updated_at.strftime('%Y-%m-%d') if bom.updated_at else None
                }
                for bom in boms
            ]
        except Exception as e:
            logger.error(f"Error searching BOMs: {e}")
            return []
    
    # Work Order Management Methods
    
    def create_work_order(self, work_order_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a new work order.
        
        Args:
            work_order_data: Dictionary containing work order information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate required fields
            required_fields = ['work_order_number', 'finished_good_sku', 'finished_good_name', 'quantity_ordered', 'created_by']
            missing_fields = [field for field in required_fields if field not in work_order_data]
            
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
            
            # Create work order
            work_order = self.work_order_service.create_work_order(work_order_data)
            
            if work_order:
                self._notify_data_changed()
                self._show_status_message(f"Work order '{work_order.work_order_number}' created successfully")
                return True, f"Work order '{work_order.work_order_number}' created successfully"
            else:
                return False, "Failed to create work order"
                
        except Exception as e:
            logger.error(f"Error creating work order: {e}")
            return False, f"Error creating work order: {e}"
    
    def update_work_order(self, work_order_id: UUID, update_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update an existing work order.
        
        Args:
            work_order_id: UUID of the work order to update
            update_data: Dictionary containing updated fields
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.work_order_service.update_work_order(work_order_id, update_data)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("Work order updated successfully")
                return True, "Work order updated successfully"
            else:
                return False, "Failed to update work order"
                
        except Exception as e:
            logger.error(f"Error updating work order: {e}")
            return False, f"Error updating work order: {e}"
    
    def update_work_order_status(self, work_order_id: UUID, new_status: str, updated_by: str) -> Tuple[bool, str]:
        """
        Update work order status.
        
        Args:
            work_order_id: UUID of the work order
            new_status: New status
            updated_by: User making the change
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.work_order_service.update_work_order_status(work_order_id, new_status, updated_by)
            
            if success:
                self._notify_data_changed()
                self._show_status_message(f"Work order status updated to {new_status}")
                return True, f"Work order status updated to {new_status}"
            else:
                return False, "Failed to update work order status"
                
        except Exception as e:
            logger.error(f"Error updating work order status: {e}")
            return False, f"Error updating work order status: {e}"
    
    def delete_work_order(self, work_order_id: UUID, deleted_by: str) -> Tuple[bool, str]:
        """
        Delete a work order.
        
        Args:
            work_order_id: UUID of the work order to delete
            deleted_by: User performing the deletion
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.work_order_service.delete_work_order(work_order_id, deleted_by)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("Work order deleted successfully")
                return True, "Work order deleted successfully"
            else:
                return False, "Failed to delete work order - may not be in planned status"
                
        except Exception as e:
            logger.error(f"Error deleting work order: {e}")
            return False, f"Error deleting work order: {e}"
    
    def get_work_order_by_id(self, work_order_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get work order details by ID.
        
        Args:
            work_order_id: UUID of the work order
            
        Returns:
            Work order dictionary or None if not found
        """
        try:
            work_order = self.work_order_service.get_work_order_by_id(work_order_id)
            if work_order:
                return {
                    'id': str(work_order.id),
                    'work_order_number': work_order.work_order_number,
                    'bom_id': str(work_order.bom_id) if work_order.bom_id else None,
                    'finished_good_sku': work_order.finished_good_sku,
                    'finished_good_name': work_order.finished_good_name,
                    'quantity_ordered': float(work_order.quantity_ordered),
                    'quantity_produced': float(work_order.quantity_produced),
                    'unit_of_measure': work_order.unit_of_measure,
                    'order_date': work_order.order_date.strftime('%Y-%m-%d') if work_order.order_date else None,
                    'start_date': work_order.start_date.strftime('%Y-%m-%d') if work_order.start_date else None,
                    'completion_date': work_order.completion_date.strftime('%Y-%m-%d') if work_order.completion_date else None,
                    'due_date': work_order.due_date.strftime('%Y-%m-%d') if work_order.due_date else None,
                    'status': work_order.status,
                    'priority': work_order.priority,
                    'estimated_hours': float(work_order.estimated_hours) if work_order.estimated_hours else None,
                    'actual_hours': float(work_order.actual_hours) if work_order.actual_hours else None,
                    'yield_percentage': float(work_order.yield_percentage) if work_order.yield_percentage else None,
                    'quality_status': work_order.quality_status,
                    'inspector': work_order.inspector,
                    'inspection_date': work_order.inspection_date.strftime('%Y-%m-%d') if work_order.inspection_date else None,
                    'notes': work_order.notes or ''
                }
            return None
        except Exception as e:
            logger.error(f"Error getting work order {work_order_id}: {e}")
            return None
    
    def search_work_orders(self, search_term: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search work orders.
        
        Args:
            search_term: Search term
            status_filter: Optional status filter
            
        Returns:
            List of work order dictionaries
        """
        try:
            work_orders = self.work_order_service.search_work_orders(search_term, status_filter)
            
            return [
                {
                    'id': str(wo.id),
                    'work_order_number': wo.work_order_number,
                    'finished_good_sku': wo.finished_good_sku,
                    'finished_good_name': wo.finished_good_name,
                    'status': wo.status,
                    'priority': wo.priority,
                    'quantity_ordered': float(wo.quantity_ordered),
                    'quantity_produced': float(wo.quantity_produced),
                    'completion_percentage': float(wo.completion_percentage),
                    'due_date': wo.due_date.strftime('%Y-%m-%d') if wo.due_date else None,
                    'start_date': wo.start_date.strftime('%Y-%m-%d') if wo.start_date else None
                }
                for wo in work_orders
            ]
        except Exception as e:
            logger.error(f"Error searching work orders: {e}")
            return []
    
    # Dashboard and Reporting Methods
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get dashboard data for production module.
        
        Returns:
            Dictionary with dashboard information
        """
        try:
            return self.production_service.get_dashboard_data()
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                'summary_cards': {
                    'active_boms': 0,
                    'total_work_orders': 0,
                    'in_progress_orders': 0,
                    'overdue_orders': 0
                },
                'bom_status_counts': {},
                'work_order_status_counts': {},
                'overdue_work_orders': [],
                'recent_work_orders': [],
                'recent_boms': []
            }
    
    def get_bom_options(self) -> List[Dict[str, str]]:
        """
        Get BOM options for dropdowns.
        
        Returns:
            List of BOM dictionaries with basic info
        """
        try:
            return self.bom_service.get_bom_options()
        except Exception as e:
            logger.error(f"Error getting BOM options: {e}")
            return []
    
    def create_work_order_from_bom(self, bom_id: UUID, work_order_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a work order from a BOM.
        
        Args:
            bom_id: UUID of the BOM
            work_order_data: Dictionary containing work order information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success, message = self.production_service.create_work_order_from_bom(bom_id, work_order_data)
            
            if success:
                self._notify_data_changed()
                self._show_status_message(message)
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error creating work order from BOM: {e}")
            return False, f"Error creating work order from BOM: {e}"
    
    def get_material_requirements(self, work_order_id: UUID) -> List[Dict[str, Any]]:
        """
        Get material requirements for a work order.
        
        Args:
            work_order_id: UUID of the work order
            
        Returns:
            List of material requirements
        """
        try:
            return self.production_service.get_material_requirements(work_order_id)
        except Exception as e:
            logger.error(f"Error getting material requirements: {e}")
            return []
    
    def get_production_schedule(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Get production schedule for date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of scheduled work orders
        """
        try:
            return self.production_service.get_production_schedule(start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting production schedule: {e}")
            return []
    
    def get_production_efficiency(self, work_order_id: UUID) -> Dict[str, Any]:
        """
        Get production efficiency metrics for a work order.
        
        Args:
            work_order_id: UUID of the work order
            
        Returns:
            Dictionary with efficiency metrics
        """
        try:
            return self.production_service.get_production_efficiency(work_order_id)
        except Exception as e:
            logger.error(f"Error getting production efficiency: {e}")
            return {}
    
    def get_bom_statuses(self) -> List[str]:
        """
        Get all BOM status options.
        
        Returns:
            List of status names
        """
        try:
            from database.models.production import BillOfMaterialStatus
            return [status.value for status in BillOfMaterialStatus]
        except Exception as e:
            logger.error(f"Error getting BOM statuses: {e}")
            return []
    
    def get_work_order_statuses(self) -> List[str]:
        """
        Get all work order status options.
        
        Returns:
            List of status names
        """
        try:
            from database.models.production import WorkOrderStatus
            return [status.value for status in WorkOrderStatus]
        except Exception as e:
            logger.error(f"Error getting work order statuses: {e}")
            return []
    
    def get_work_order_priorities(self) -> List[str]:
        """
        Get all work order priority options.
        
        Returns:
            List of priority names
        """
        try:
            from database.models.production import WorkOrderPriority
            return [priority.value for priority in WorkOrderPriority]
        except Exception as e:
            logger.error(f"Error getting work order priorities: {e}")
            return []
