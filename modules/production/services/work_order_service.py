"""
Work Order service for XPanda ERP-Lite.
Provides business logic for work order management operations.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from database.models.production import (
    WorkOrder, WorkOrderStatus, WorkOrderPriority,
    ProductionStep, ProductionStepStatus,
    MaterialConsumption
)
from database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class WorkOrderService:
    """Service class for work order operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_work_order(self, work_order_data: Dict[str, Any]) -> Optional[WorkOrder]:
        """
        Create a new work order.
        
        Args:
            work_order_data: Dictionary containing work order information
            
        Returns:
            Created WorkOrder object or None if failed
        """
        try:
            with self.db_manager.get_session() as session:
                # Check if work order number already exists
                existing = session.query(WorkOrder).filter(
                    WorkOrder.work_order_number == work_order_data['work_order_number'].upper()
                ).first()
                
                if existing:
                    logger.warning(f"Work order {work_order_data['work_order_number']} already exists")
                    return None
                
                # Create new work order
                work_order = WorkOrder(
                    work_order_number=work_order_data['work_order_number'].upper(),
                    bom_id=work_order_data.get('bom_id'),
                    finished_good_sku=work_order_data['finished_good_sku'],
                    finished_good_name=work_order_data['finished_good_name'],
                    quantity_ordered=Decimal(str(work_order_data['quantity_ordered'])),
                    quantity_produced=Decimal(str(work_order_data.get('quantity_produced', 0))),
                    unit_of_measure=work_order_data.get('unit_of_measure', 'EA'),
                    order_date=self._parse_date(work_order_data.get('order_date', date.today())),
                    start_date=self._parse_date(work_order_data.get('start_date')),
                    completion_date=self._parse_date(work_order_data.get('completion_date')),
                    due_date=self._parse_date(work_order_data.get('due_date')),
                    status=work_order_data.get('status', WorkOrderStatus.PLANNED.value),
                    priority=work_order_data.get('priority', WorkOrderPriority.NORMAL.value),
                    estimated_hours=Decimal(str(work_order_data.get('estimated_hours', 0))),
                    actual_hours=Decimal(str(work_order_data.get('actual_hours', 0))),
                    yield_percentage=Decimal(str(work_order_data.get('yield_percentage', 100))),
                    quality_status=work_order_data.get('quality_status'),
                    inspector=work_order_data.get('inspector'),
                    inspection_date=self._parse_datetime(work_order_data.get('inspection_date')),
                    notes=work_order_data.get('notes', ''),
                    created_by=work_order_data.get('created_by', 'System')
                )
                
                session.add(work_order)
                session.flush()
                
                # Create production steps if BOM is provided
                if work_order.bom_id:
                    self._create_production_steps(session, work_order)
                
                # Create material consumptions if BOM is provided
                if work_order.bom_id:
                    self._create_material_consumptions(session, work_order)
                
                logger.info(f"Created work order: {work_order.work_order_number}")
                return work_order
                
        except Exception as e:
            logger.error(f"Failed to create work order: {e}")
            return None
    
    def get_work_order_by_id(self, work_order_id: UUID) -> Optional[WorkOrder]:
        """
        Get work order by ID.
        
        Args:
            work_order_id: UUID of the work order
            
        Returns:
            WorkOrder object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(WorkOrder).filter(
                    WorkOrder.id == work_order_id
                ).first()
        except Exception as e:
            logger.error(f"Failed to get work order {work_order_id}: {e}")
            return None
    
    def get_work_order_by_number(self, work_order_number: str) -> Optional[WorkOrder]:
        """
        Get work order by number.
        
        Args:
            work_order_number: Work order number
            
        Returns:
            WorkOrder object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(WorkOrder).filter(
                    WorkOrder.work_order_number == work_order_number.upper()
                ).first()
        except Exception as e:
            logger.error(f"Failed to get work order {work_order_number}: {e}")
            return None
    
    def get_all_work_orders(self, status_filter: Optional[str] = None) -> List[WorkOrder]:
        """
        Get all work orders.
        
        Args:
            status_filter: Optional status filter
            
        Returns:
            List of WorkOrder objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(WorkOrder)
                
                if status_filter:
                    query = query.filter(WorkOrder.status == status_filter)
                
                return query.order_by(WorkOrder.work_order_number).all()
        except Exception as e:
            logger.error(f"Failed to get work orders: {e}")
            return []
    
    def search_work_orders(self, search_term: str, status_filter: Optional[str] = None) -> List[WorkOrder]:
        """
        Search work orders by number, product SKU, or name.
        
        Args:
            search_term: Search term
            status_filter: Optional status filter
            
        Returns:
            List of matching WorkOrder objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(WorkOrder)
                
                # Add search conditions
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    (WorkOrder.work_order_number.ilike(search_pattern)) |
                    (WorkOrder.finished_good_sku.ilike(search_pattern)) |
                    (WorkOrder.finished_good_name.ilike(search_pattern))
                )
                
                # Add status filter if specified
                if status_filter:
                    query = query.filter(WorkOrder.status == status_filter)
                
                return query.order_by(WorkOrder.work_order_number).all()
        except Exception as e:
            logger.error(f"Failed to search work orders: {e}")
            return []
    
    def update_work_order(self, work_order_id: UUID, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing work order.
        
        Args:
            work_order_id: UUID of the work order to update
            update_data: Dictionary containing updated fields
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                work_order = session.query(WorkOrder).filter(
                    WorkOrder.id == work_order_id
                ).first()
                
                if not work_order:
                    logger.warning(f"Work order {work_order_id} not found")
                    return False
                
                # Update work order fields
                for field, value in update_data.items():
                    if hasattr(work_order, field) and field not in ['id', 'created_at', 'created_by']:
                        if field == 'work_order_number':
                            work_order.work_order_number = value.upper()
                        elif field in ['quantity_ordered', 'quantity_produced', 'estimated_hours', 'actual_hours', 'yield_percentage']:
                            setattr(work_order, field, Decimal(str(value)))
                        elif field in ['order_date', 'start_date', 'completion_date', 'due_date']:
                            setattr(work_order, field, self._parse_date(value))
                        elif field == 'inspection_date':
                            setattr(work_order, field, self._parse_datetime(value))
                        else:
                            setattr(work_order, field, value)
                
                work_order.updated_at = datetime.utcnow()
                
                logger.info(f"Updated work order: {work_order.work_order_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update work order {work_order_id}: {e}")
            return False
    
    def update_work_order_status(self, work_order_id: UUID, new_status: str, updated_by: str) -> bool:
        """
        Update work order status with proper validation.
        
        Args:
            work_order_id: UUID of the work order
            new_status: New status
            updated_by: User making the change
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                work_order = session.query(WorkOrder).filter(
                    WorkOrder.id == work_order_id
                ).first()
                
                if not work_order:
                    logger.warning(f"Work order {work_order_id} not found")
                    return False
                
                # Validate status transition
                if not self._is_valid_status_transition(work_order.status, new_status):
                    logger.warning(f"Invalid status transition from {work_order.status} to {new_status}")
                    return False
                
                # Update status and related fields
                old_status = work_order.status
                work_order.status = new_status
                work_order.updated_at = datetime.utcnow()
                
                # Handle status-specific updates
                if new_status == WorkOrderStatus.RELEASED.value:
                    if not work_order.start_date:
                        work_order.start_date = date.today()
                elif new_status == WorkOrderStatus.COMPLETED.value:
                    work_order.completion_date = date.today()
                    work_order.completed_by = updated_by
                    work_order.completed_at = datetime.utcnow()
                    # Set quantity produced to ordered quantity if not already set
                    if work_order.quantity_produced == 0:
                        work_order.quantity_produced = work_order.quantity_ordered
                elif new_status == WorkOrderStatus.IN_PROGRESS.value:
                    if not work_order.start_date:
                        work_order.start_date = date.today()
                
                logger.info(f"Updated work order {work_order.work_order_number} status from {old_status} to {new_status}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update work order status {work_order_id}: {e}")
            return False
    
    def delete_work_order(self, work_order_id: UUID, deleted_by: str) -> bool:
        """
        Delete a work order (only if in planned status).
        
        Args:
            work_order_id: UUID of the work order to delete
            deleted_by: User performing the deletion
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                work_order = session.query(WorkOrder).filter(
                    WorkOrder.id == work_order_id
                ).first()
                
                if not work_order:
                    logger.warning(f"Work order {work_order_id} not found")
                    return False
                
                # Only allow deletion of planned work orders
                if work_order.status != WorkOrderStatus.PLANNED.value:
                    logger.warning(f"Cannot delete work order {work_order.work_order_number} - status is {work_order.status}")
                    return False
                
                # Delete related records
                session.query(ProductionStep).filter(
                    ProductionStep.work_order_id == work_order_id
                ).delete()
                
                session.query(MaterialConsumption).filter(
                    MaterialConsumption.work_order_id == work_order_id
                ).delete()
                
                # Delete work order
                session.delete(work_order)
                
                logger.info(f"Deleted work order: {work_order.work_order_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete work order {work_order_id}: {e}")
            return False
    
    def get_work_order_statistics(self) -> Dict[str, Any]:
        """
        Get work order statistics for dashboard.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.db_manager.get_session() as session:
                # Total work orders
                total_work_orders = session.query(WorkOrder).count()
                
                # Work orders by status
                status_counts = {}
                for status in WorkOrderStatus:
                    count = session.query(WorkOrder).filter(
                        WorkOrder.status == status.value
                    ).count()
                    status_counts[status.value] = count
                
                # Overdue work orders
                today = date.today()
                overdue_count = session.query(WorkOrder).filter(
                    WorkOrder.due_date < today,
                    WorkOrder.status.in_([WorkOrderStatus.PLANNED.value, WorkOrderStatus.RELEASED.value, WorkOrderStatus.IN_PROGRESS.value])
                ).count()
                
                # Work orders due this week
                week_end = today + datetime.timedelta(days=7)
                due_this_week = session.query(WorkOrder).filter(
                    WorkOrder.due_date <= week_end,
                    WorkOrder.due_date >= today,
                    WorkOrder.status.in_([WorkOrderStatus.PLANNED.value, WorkOrderStatus.RELEASED.value, WorkOrderStatus.IN_PROGRESS.value])
                ).count()
                
                return {
                    'total_work_orders': total_work_orders,
                    'status_counts': status_counts,
                    'overdue_count': overdue_count,
                    'due_this_week': due_this_week
                }
                
        except Exception as e:
            logger.error(f"Failed to get work order statistics: {e}")
            return {
                'total_work_orders': 0,
                'status_counts': {},
                'overdue_count': 0,
                'due_this_week': 0
            }
    
    def get_overdue_work_orders(self) -> List[WorkOrder]:
        """
        Get overdue work orders.
        
        Returns:
            List of overdue WorkOrder objects
        """
        try:
            with self.db_manager.get_session() as session:
                today = date.today()
                return session.query(WorkOrder).filter(
                    WorkOrder.due_date < today,
                    WorkOrder.status.in_([WorkOrderStatus.PLANNED.value, WorkOrderStatus.RELEASED.value, WorkOrderStatus.IN_PROGRESS.value])
                ).order_by(WorkOrder.due_date).all()
        except Exception as e:
            logger.error(f"Failed to get overdue work orders: {e}")
            return []
    
    def _create_production_steps(self, session, work_order: WorkOrder) -> None:
        """Create production steps based on BOM."""
        # This would create production steps based on the BOM
        # For now, create a basic production step
        step = ProductionStep(
            work_order_id=work_order.id,
            step_number=1,
            step_name="Production",
            step_description="Main production process",
            estimated_minutes=work_order.estimated_hours * 60 if work_order.estimated_hours else 60,
            status=ProductionStepStatus.PENDING.value
        )
        session.add(step)
    
    def _create_material_consumptions(self, session, work_order: WorkOrder) -> None:
        """Create material consumptions based on BOM."""
        # This would create material consumptions based on BOM lines
        # For now, create a placeholder consumption
        consumption = MaterialConsumption(
            work_order_id=work_order.id,
            material_sku=work_order.finished_good_sku,
            material_name=work_order.finished_good_name,
            quantity_planned=work_order.quantity_ordered,
            unit_of_measure=work_order.unit_of_measure
        )
        session.add(consumption)
    
    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """Validate work order status transitions."""
        valid_transitions = {
            WorkOrderStatus.PLANNED.value: [WorkOrderStatus.RELEASED.value, WorkOrderStatus.CANCELLED.value],
            WorkOrderStatus.RELEASED.value: [WorkOrderStatus.IN_PROGRESS.value, WorkOrderStatus.CANCELLED.value, WorkOrderStatus.ON_HOLD.value],
            WorkOrderStatus.IN_PROGRESS.value: [WorkOrderStatus.COMPLETED.value, WorkOrderStatus.ON_HOLD.value, WorkOrderStatus.CANCELLED.value],
            WorkOrderStatus.ON_HOLD.value: [WorkOrderStatus.IN_PROGRESS.value, WorkOrderStatus.CANCELLED.value],
            WorkOrderStatus.COMPLETED.value: [],  # No transitions from completed
            WorkOrderStatus.CANCELLED.value: []   # No transitions from cancelled
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
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object."""
        if not datetime_str:
            return None
        
        try:
            return datetime.strptime(datetime_str, '%Y-%m-%d')
        except ValueError:
            logger.warning(f"Invalid datetime format: {datetime_str}")
            return None
