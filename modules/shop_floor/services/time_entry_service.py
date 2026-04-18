"""
Time Entry Service for XPanda ERP-Lite.
Handles time tracking for shop floor operations.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from database.models.shop_floor import TimeEntry, TimeEntryStatus, OperationType
from database.models.production import WorkOrder
from database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class TimeEntryService:
    """Service for managing time entries and job clock operations."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def create_time_entry(self, employee_id: str, employee_name: str, 
                         work_order_id: Optional[int], operation: str,
                         station_id: Optional[str] = None, 
                         badge_scan: Optional[str] = None,
                         notes: Optional[str] = None) -> TimeEntry:
        """Create a new time entry (clock in)."""
        try:
            with self.db_manager.get_session() as session:
                # Validate work order if provided
                if work_order_id:
                    work_order = session.query(WorkOrder).filter(
                        WorkOrder.id == work_order_id
                    ).first()
                    if not work_order:
                        raise ValueError(f"Work Order {work_order_id} not found")
                
                # Check for existing active time entries for this employee
                active_entries = session.query(TimeEntry).filter(
                    TimeEntry.employee_id == employee_id,
                    TimeEntry.status == TimeEntryStatus.ACTIVE.value
                ).all()
                
                # Allow multiple active entries for different operations (e.g., monitoring aging while cutting)
                # But warn if same operation
                for entry in active_entries:
                    if entry.operation == operation:
                        logger.warning(f"Employee {employee_id} already has active time entry for {operation}")
                
                time_entry = TimeEntry(
                    employee_id=employee_id,
                    employee_name=employee_name,
                    work_order_id=work_order_id,
                    operation=operation,
                    station_id=station_id,
                    badge_scan=badge_scan,
                    notes=notes,
                    start_time=datetime.now(),
                    status=TimeEntryStatus.ACTIVE.value
                )
                
                session.add(time_entry)
                session.commit()
                session.refresh(time_entry)
                
                logger.info(f"Created time entry for {employee_name} - {operation}")
                return time_entry
                
        except Exception as e:
            logger.error(f"Error creating time entry: {e}")
            raise
    
    def clock_out(self, time_entry_id: int) -> TimeEntry:
        """Clock out a time entry."""
        try:
            with self.db_manager.get_session() as session:
                time_entry = session.query(TimeEntry).filter(
                    TimeEntry.id == time_entry_id
                ).first()
                
                if not time_entry:
                    raise ValueError(f"Time entry {time_entry_id} not found")
                
                if time_entry.status != TimeEntryStatus.ACTIVE.value:
                    raise ValueError(f"Time entry {time_entry_id} is not active")
                
                time_entry.end_time = datetime.now()
                time_entry.status = TimeEntryStatus.COMPLETED.value
                time_entry.calculate_total_hours()
                
                session.commit()
                session.refresh(time_entry)
                
                logger.info(f"Clocked out time entry {time_entry_id} for {time_entry.employee_name}")
                return time_entry
                
        except Exception as e:
            logger.error(f"Error clocking out time entry: {e}")
            raise
    
    def pause_time_entry(self, time_entry_id: int) -> TimeEntry:
        """Pause a time entry."""
        try:
            with self.db_manager.get_session() as session:
                time_entry = session.query(TimeEntry).filter(
                    TimeEntry.id == time_entry_id
                ).first()
                
                if not time_entry:
                    raise ValueError(f"Time entry {time_entry_id} not found")
                
                if time_entry.status != TimeEntryStatus.ACTIVE.value:
                    raise ValueError(f"Time entry {time_entry_id} is not active")
                
                time_entry.status = TimeEntryStatus.PAUSED.value
                time_entry.calculate_total_hours()  # Calculate partial hours
                
                session.commit()
                session.refresh(time_entry)
                
                logger.info(f"Paused time entry {time_entry_id} for {time_entry.employee_name}")
                return time_entry
                
        except Exception as e:
            logger.error(f"Error pausing time entry: {e}")
            raise
    
    def resume_time_entry(self, time_entry_id: int) -> TimeEntry:
        """Resume a paused time entry."""
        try:
            with self.db_manager.get_session() as session:
                time_entry = session.query(TimeEntry).filter(
                    TimeEntry.id == time_entry_id
                ).first()
                
                if not time_entry:
                    raise ValueError(f"Time entry {time_entry_id} not found")
                
                if time_entry.status != TimeEntryStatus.PAUSED.value:
                    raise ValueError(f"Time entry {time_entry_id} is not paused")
                
                # Store the partial hours and reset start time
                partial_hours = time_entry.total_hours or Decimal('0')
                time_entry.start_time = datetime.now()
                time_entry.status = TimeEntryStatus.ACTIVE.value
                time_entry.total_hours = partial_hours
                
                session.commit()
                session.refresh(time_entry)
                
                logger.info(f"Resumed time entry {time_entry_id} for {time_entry.employee_name}")
                return time_entry
                
        except Exception as e:
            logger.error(f"Error resuming time entry: {e}")
            raise
    
    def get_active_time_entries(self, employee_id: Optional[str] = None) -> List[TimeEntry]:
        """Get all active time entries, optionally filtered by employee."""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(TimeEntry).filter(
                    TimeEntry.status == TimeEntryStatus.ACTIVE.value
                )
                
                if employee_id:
                    query = query.filter(TimeEntry.employee_id == employee_id)
                
                return query.order_by(TimeEntry.start_time.desc()).all()
                
        except Exception as e:
            logger.error(f"Error getting active time entries: {e}")
            raise
    
    def get_time_entries_by_date_range(self, start_date: datetime, end_date: datetime,
                                     employee_id: Optional[str] = None,
                                     work_order_id: Optional[int] = None) -> List[TimeEntry]:
        """Get time entries within a date range."""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(TimeEntry).filter(
                    TimeEntry.start_time >= start_date,
                    TimeEntry.start_time <= end_date
                )
                
                if employee_id:
                    query = query.filter(TimeEntry.employee_id == employee_id)
                
                if work_order_id:
                    query = query.filter(TimeEntry.work_order_id == work_order_id)
                
                return query.order_by(TimeEntry.start_time.desc()).all()
                
        except Exception as e:
            logger.error(f"Error getting time entries by date range: {e}")
            raise
    
    def calculate_elapsed_time(self, time_entry: TimeEntry) -> Dict[str, Any]:
        """Calculate elapsed time for an active time entry."""
        if time_entry.status != TimeEntryStatus.ACTIVE.value:
            return {
                'elapsed_hours': float(time_entry.total_hours or 0),
                'elapsed_minutes': int((time_entry.total_hours or 0) * 60),
                'elapsed_seconds': int((time_entry.total_hours or 0) * 3600)
            }
        
        now = datetime.now()
        elapsed = now - time_entry.start_time
        elapsed_hours = Decimal(elapsed.total_seconds() / 3600).quantize(Decimal('0.01'))
        
        return {
            'elapsed_hours': float(elapsed_hours),
            'elapsed_minutes': int(elapsed.total_seconds() / 60),
            'elapsed_seconds': int(elapsed.total_seconds()),
            'start_time': time_entry.start_time,
            'current_time': now
        }
    
    def get_time_entry_statistics(self, start_date: datetime, end_date: datetime,
                                employee_id: Optional[str] = None) -> Dict[str, Any]:
        """Get time entry statistics for a date range."""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(TimeEntry).filter(
                    TimeEntry.start_time >= start_date,
                    TimeEntry.start_time <= end_date,
                    TimeEntry.status == TimeEntryStatus.COMPLETED.value
                )
                
                if employee_id:
                    query = query.filter(TimeEntry.employee_id == employee_id)
                
                entries = query.all()
                
                total_hours = sum(entry.total_hours or 0 for entry in entries)
                
                # Group by operation
                operation_hours = {}
                for entry in entries:
                    operation = entry.operation
                    if operation not in operation_hours:
                        operation_hours[operation] = Decimal('0')
                    operation_hours[operation] += entry.total_hours or 0
                
                # Group by employee
                employee_hours = {}
                for entry in entries:
                    emp = entry.employee_name
                    if emp not in employee_hours:
                        employee_hours[emp] = Decimal('0')
                    employee_hours[emp] += entry.total_hours or 0
                
                return {
                    'total_hours': float(total_hours),
                    'total_entries': len(entries),
                    'average_hours_per_entry': float(total_hours / len(entries)) if entries else 0,
                    'operation_breakdown': {k: float(v) for k, v in operation_hours.items()},
                    'employee_breakdown': {k: float(v) for k, v in employee_hours.items()},
                    'date_range': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting time entry statistics: {e}")
            raise
    
    def get_active_entries_for_display(self, employee_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active entries serialized as dicts (safe after session close)."""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(TimeEntry).filter(
                    TimeEntry.status == TimeEntryStatus.ACTIVE.value
                )
                if employee_id:
                    query = query.filter(TimeEntry.employee_id == employee_id)
                entries = query.order_by(TimeEntry.start_time.asc()).all()
                return [
                    {
                        'id': e.id,
                        'employee_id': e.employee_id,
                        'employee_name': e.employee_name,
                        'operation': e.operation,
                        'station_id': e.station_id or '',
                        'start_time': e.start_time,
                        'work_order_id': e.work_order_id,
                        'notes': e.notes or '',
                    }
                    for e in entries
                ]
        except Exception as e:
            logger.error(f"Error getting active entries for display: {e}")
            raise

    def get_recent_completed_entries(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get completed time entries from the last N hours, serialized as display dicts."""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            with self.db_manager.get_session() as session:
                entries = session.query(TimeEntry).filter(
                    TimeEntry.status == TimeEntryStatus.COMPLETED.value,
                    TimeEntry.end_time >= cutoff
                ).order_by(TimeEntry.end_time.desc()).limit(100).all()
                return [
                    {
                        'employee_name': e.employee_name,
                        'operation': e.operation.replace('_', ' ').title(),
                        'station_id': e.station_id or '',
                        'start_time': e.start_time.strftime('%H:%M') if e.start_time else '',
                        'end_time': e.end_time.strftime('%H:%M') if e.end_time else '',
                        'total_hours': f"{float(e.total_hours):.2f}h" if e.total_hours else '—',
                        'status': 'Completed',
                    }
                    for e in entries
                ]
        except Exception as e:
            logger.error(f"Error getting recent completed entries: {e}")
            raise

    def get_operation_options(self) -> List[Dict[str, str]]:
        """Get available operation options for dropdown."""
        return [
            {'value': OperationType.EXPANSION.value, 'label': 'Expansion'},
            {'value': OperationType.MOLDING.value, 'label': 'Molding'},
            {'value': OperationType.AGING.value, 'label': 'Aging'},
            {'value': OperationType.CUTTING.value, 'label': 'Cutting'},
            {'value': OperationType.FABRICATION.value, 'label': 'Fabrication'},
            {'value': OperationType.PACKAGING.value, 'label': 'Packaging'},
            {'value': OperationType.INSPECTION.value, 'label': 'Inspection'},
            {'value': OperationType.MAINTENANCE.value, 'label': 'Maintenance'}
        ]
    
    def search_time_entries(self, search_term: str, limit: int = 100) -> List[TimeEntry]:
        """Search time entries by employee name, work order, or operation."""
        try:
            with self.db_manager.get_session() as session:
                search_pattern = f"%{search_term}%"
                
                return session.query(TimeEntry).filter(
                    (TimeEntry.employee_name.ilike(search_pattern)) |
                    (TimeEntry.operation.ilike(search_pattern)) |
                    (TimeEntry.notes.ilike(search_pattern))
                ).limit(limit).all()
                
        except Exception as e:
            logger.error(f"Error searching time entries: {e}")
            raise
