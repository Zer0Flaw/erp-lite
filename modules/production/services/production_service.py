"""
Production service for XPanda ERP-Lite.
Coordinates BOM and work order operations for complete production management.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from database.connection import DatabaseManager
from database.models.production import WorkOrder, BillOfMaterial, BillOfMaterialLine
from .bom_service import BOMService
from .work_order_service import WorkOrderService

logger = logging.getLogger(__name__)


class ProductionService:
    """Main service class for production operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.bom_service = BOMService(db_manager)
        self.work_order_service = WorkOrderService(db_manager)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get dashboard data for production module.
        
        Returns:
            Dictionary with dashboard information
        """
        try:
            # Get BOM statistics
            bom_stats = self.bom_service.get_bom_statistics()
            
            # Get work order statistics
            work_order_stats = self.work_order_service.get_work_order_statistics()
            
            # Get overdue work orders
            overdue_work_orders = self.work_order_service.get_overdue_work_orders()
            
            # Get recent work orders
            recent_work_orders = self.get_recent_work_orders(10)
            
            # Get recent BOMs
            recent_boms = self.get_recent_boms(10)
            
            # Calculate summary cards
            summary_cards = {
                'active_boms': bom_stats['active_boms'],
                'total_work_orders': work_order_stats['total_work_orders'],
                'in_progress_orders': work_order_status_counts.get('In Progress', 0),
                'overdue_orders': work_order_stats['overdue_count']
            }
            
            return {
                'summary_cards': summary_cards,
                'bom_status_counts': bom_stats['status_counts'],
                'work_order_status_counts': work_order_stats['status_counts'],
                'overdue_work_orders': [
                    {
                        'work_order_number': wo.work_order_number,
                        'finished_good_sku': wo.finished_good_sku,
                        'finished_good_name': wo.finished_good_name,
                        'due_date': wo.due_date.strftime('%Y-%m-%d') if wo.due_date else '',
                        'priority': wo.priority,
                        'days_overdue': (date.today() - wo.due_date).days if wo.due_date else 0
                    }
                    for wo in overdue_work_orders
                ],
                'recent_work_orders': [
                    {
                        'work_order_number': wo.work_order_number,
                        'finished_good_sku': wo.finished_good_sku,
                        'status': wo.status,
                        'priority': wo.priority,
                        'quantity_ordered': float(wo.quantity_ordered),
                        'quantity_produced': float(wo.quantity_produced),
                        'completion_percentage': float(wo.completion_percentage),
                        'due_date': wo.due_date.strftime('%Y-%m-%d') if wo.due_date else ''
                    }
                    for wo in recent_work_orders
                ],
                'recent_boms': [
                    {
                        'bom_code': bom.bom_code,
                        'name': bom.name,
                        'finished_good_sku': bom.finished_good_sku,
                        'version': bom.version,
                        'status': bom.status,
                        'line_count': len(bom.bom_lines),
                        'updated_at': bom.updated_at.strftime('%Y-%m-%d') if bom.updated_at else ''
                    }
                    for bom in recent_boms
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
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
            # Get BOM
            bom = self.bom_service.get_bom_by_id(bom_id)
            if not bom:
                return False, "BOM not found"
            
            # Check if BOM is active
            if not bom.is_active:
                return False, "BOM is not active"
            
            # Set BOM-related fields in work order data
            work_order_data['bom_id'] = bom_id
            work_order_data['finished_good_sku'] = bom.finished_good_sku
            work_order_data['finished_good_name'] = bom.finished_good_name
            
            # Set standard production times if not provided
            if not work_order_data.get('estimated_hours'):
                if bom.standard_cycle_time:
                    work_order_data['estimated_hours'] = float(bom.standard_cycle_time) / 60
                else:
                    work_order_data['estimated_hours'] = 1.0
            
            # Set yield percentage if not provided
            if not work_order_data.get('yield_percentage'):
                work_order_data['yield_percentage'] = float(bom.yield_percentage) if bom.yield_percentage else 100.0
            
            # Create work order
            work_order = self.work_order_service.create_work_order(work_order_data)
            
            if work_order:
                return True, f"Work order {work_order.work_order_number} created successfully from BOM {bom.bom_code}"
            else:
                return False, "Failed to create work order"
                
        except Exception as e:
            logger.error(f"Failed to create work order from BOM: {e}")
            return False, f"Error creating work order: {e}"
    
    def get_recent_work_orders(self, limit: int = 10) -> List[Any]:
        """
        Get recent work orders.
        
        Args:
            limit: Maximum number of work orders to return
            
        Returns:
            List of WorkOrder objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(WorkOrder).order_by(
                    WorkOrder.created_at.desc()
                ).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get recent work orders: {e}")
            return []
    
    def get_recent_boms(self, limit: int = 10) -> List[Any]:
        """
        Get recent BOMs.
        
        Args:
            limit: Maximum number of BOMs to return
            
        Returns:
            List of BillOfMaterial objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(BillOfMaterial).filter(
                    BillOfMaterial.deleted_at.is_(None)
                ).order_by(
                    BillOfMaterial.updated_at.desc()
                ).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get recent BOMs: {e}")
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
            with self.db_manager.get_session() as session:
                work_orders = session.query(WorkOrder).filter(
                    WorkOrder.start_date >= start_date,
                    WorkOrder.start_date <= end_date,
                    WorkOrder.status.in_(['Planned', 'Released', 'In Progress'])
                ).order_by(WorkOrder.start_date, WorkOrder.priority).all()
                
                return [
                    {
                        'work_order_number': wo.work_order_number,
                        'finished_good_sku': wo.finished_good_sku,
                        'finished_good_name': wo.finished_good_name,
                        'start_date': wo.start_date.strftime('%Y-%m-%d') if wo.start_date else '',
                        'due_date': wo.due_date.strftime('%Y-%m-%d') if wo.due_date else '',
                        'status': wo.status,
                        'priority': wo.priority,
                        'quantity_ordered': float(wo.quantity_ordered),
                        'estimated_hours': float(wo.estimated_hours) if wo.estimated_hours else 0
                    }
                    for wo in work_orders
                ]
        except Exception as e:
            logger.error(f"Failed to get production schedule: {e}")
            return []
    
    def get_material_requirements(self, work_order_id: UUID) -> List[Dict[str, Any]]:
        """
        Get material requirements for a work order.
        
        Args:
            work_order_id: UUID of the work order
            
        Returns:
            List of material requirements
        """
        try:
            with self.db_manager.get_session() as session:
                work_order = session.query(WorkOrder).filter(
                    WorkOrder.id == work_order_id
                ).first()
                
                if not work_order or not work_order.bom_id:
                    return []
                
                # Get BOM lines
                bom_lines = session.query(BillOfMaterialLine).filter(
                    BillOfMaterialLine.bom_id == work_order.bom_id
                ).all()
                
                requirements = []
                for line in bom_lines:
                    effective_quantity = line.effective_quantity
                    required_quantity = effective_quantity * work_order.quantity_ordered
                    
                    requirements.append({
                        'material_sku': line.material_sku,
                        'material_name': line.material_name,
                        'quantity_required': float(required_quantity),
                        'unit_of_measure': line.unit_of_measure,
                        'unit_cost': float(line.unit_cost) if line.unit_cost else 0,
                        'total_cost': float(required_quantity * line.unit_cost) if line.unit_cost else 0,
                        'is_optional': line.is_optional
                    })
                
                return requirements
                
        except Exception as e:
            logger.error(f"Failed to get material requirements: {e}")
            return []
    
    def calculate_production_capacity(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Calculate production capacity for date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with capacity information
        """
        try:
            with self.db_manager.get_session() as session:
                # Get scheduled work orders for the period
                work_orders = session.query(WorkOrder).filter(
                    WorkOrder.start_date >= start_date,
                    WorkOrder.start_date <= end_date,
                    WorkOrder.status.in_(['Planned', 'Released', 'In Progress'])
                ).all()
                
                total_scheduled_hours = sum(
                    float(wo.estimated_hours) for wo in work_orders if wo.estimated_hours
                )
                
                # Get work days in period (excluding weekends)
                work_days = 0
                current_date = start_date
                while current_date <= end_date:
                    if current_date.weekday() < 5:  # Monday to Friday
                        work_days += 1
                    current_date += datetime.timedelta(days=1)
                
                # Assume 8 hours per day, 1 machine
                total_available_hours = work_days * 8
                
                capacity_utilization = (total_scheduled_hours / total_available_hours * 100) if total_available_hours > 0 else 0
                
                return {
                    'period_start': start_date.strftime('%Y-%m-%d'),
                    'period_end': end_date.strftime('%Y-%m-%d'),
                    'work_days': work_days,
                    'total_available_hours': total_available_hours,
                    'total_scheduled_hours': total_scheduled_hours,
                    'capacity_utilization': capacity_utilization,
                    'remaining_capacity': total_available_hours - total_scheduled_hours,
                    'scheduled_work_orders': len(work_orders)
                }
                
        except Exception as e:
            logger.error(f"Failed to calculate production capacity: {e}")
            return {
                'period_start': start_date.strftime('%Y-%m-%d'),
                'period_end': end_date.strftime('%Y-%m-%d'),
                'work_days': 0,
                'total_available_hours': 0,
                'total_scheduled_hours': 0,
                'capacity_utilization': 0,
                'remaining_capacity': 0,
                'scheduled_work_orders': 0
            }
    
    def get_production_efficiency(self, work_order_id: UUID) -> Dict[str, Any]:
        """
        Calculate production efficiency for a work order.
        
        Args:
            work_order_id: UUID of the work order
            
        Returns:
            Dictionary with efficiency metrics
        """
        try:
            with self.db_manager.get_session() as session:
                work_order = session.query(WorkOrder).filter(
                    WorkOrder.id == work_order_id
                ).first()
                
                if not work_order:
                    return {}
                
                # Calculate efficiency metrics
                completion_percentage = float(work_order.completion_percentage)
                
                # Time efficiency
                time_efficiency = 0
                if work_order.estimated_hours and work_order.estimated_hours > 0:
                    if work_order.actual_hours:
                        time_efficiency = (work_order.estimated_hours / work_order.actual_hours) * 100
                    else:
                        time_efficiency = 100  # Not completed yet
                
                # Yield efficiency
                yield_efficiency = float(work_order.yield_percentage) if work_order.yield_percentage else 100
                
                # Overall efficiency (average of completion, time, and yield)
                overall_efficiency = (completion_percentage + min(time_efficiency, 100) + yield_efficiency) / 3
                
                return {
                    'work_order_number': work_order.work_order_number,
                    'completion_percentage': completion_percentage,
                    'time_efficiency': min(time_efficiency, 100),
                    'yield_efficiency': yield_efficiency,
                    'overall_efficiency': overall_efficiency,
                    'estimated_hours': float(work_order.estimated_hours) if work_order.estimated_hours else 0,
                    'actual_hours': float(work_order.actual_hours) if work_order.actual_hours else 0,
                    'quantity_ordered': float(work_order.quantity_ordered),
                    'quantity_produced': float(work_order.quantity_produced)
                }
                
        except Exception as e:
            logger.error(f"Failed to get production efficiency: {e}")
            return {}
    
    def search_production(self, search_term: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search production data (BOMs and work orders).
        
        Args:
            search_term: Search term
            filters: Optional filters
            
        Returns:
            Dictionary with search results
        """
        try:
            filters = filters or {}
            
            # Search BOMs
            bom_status_filter = filters.get('bom_status')
            boms = self.bom_service.search_boms(search_term, bom_status_filter)
            
            bom_results = [
                {
                    'id': str(bom.id),
                    'bom_code': bom.bom_code,
                    'name': bom.name,
                    'finished_good_sku': bom.finished_good_sku,
                    'version': bom.version,
                    'status': bom.status,
                    'line_count': len(bom.bom_lines),
                    'updated_at': bom.updated_at.strftime('%Y-%m-%d') if bom.updated_at else ''
                }
                for bom in boms
            ]
            
            # Search work orders
            wo_status_filter = filters.get('work_order_status')
            work_orders = self.work_order_service.search_work_orders(search_term, wo_status_filter)
            
            work_order_results = [
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
                    'due_date': wo.due_date.strftime('%Y-%m-%d') if wo.due_date else ''
                }
                for wo in work_orders
            ]
            
            return {
                'boms': bom_results,
                'work_orders': work_order_results
            }
            
        except Exception as e:
            logger.error(f"Failed to search production data: {e}")
            return {'boms': [], 'work_orders': []}
