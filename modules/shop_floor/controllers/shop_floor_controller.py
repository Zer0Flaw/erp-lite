"""
Shop Floor Controller for XPanda ERP-Lite.
Coordinates all shop floor services and provides unified interface.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from modules.shop_floor.services.time_entry_service import TimeEntryService
from modules.shop_floor.services.production_output_service import ProductionOutputService
from modules.shop_floor.services.batch_tracking_service import BatchTrackingService
from modules.shop_floor.services.station_management_service import StationManagementService

logger = logging.getLogger(__name__)


class ShopFloorController:
    """Main controller for shop floor operations."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # Initialize services
        self.time_entry_service = TimeEntryService(db_manager)
        self.production_output_service = ProductionOutputService(db_manager)
        self.batch_tracking_service = BatchTrackingService(db_manager)
        self.station_management_service = StationManagementService(db_manager)
        
        # Callbacks for UI updates
        self._data_changed_callbacks = []
        self._status_message_callbacks = []
    
    # Time Entry Operations
    def clock_in_operator(self, employee_id: str, employee_name: str,
                         work_order_id: Optional[int], operation: str,
                         station_id: Optional[str] = None,
                         badge_scan: Optional[str] = None,
                         notes: Optional[str] = None):
        """Clock in an operator to a work operation."""
        try:
            time_entry = self.time_entry_service.create_time_entry(
                employee_id=employee_id,
                employee_name=employee_name,
                work_order_id=work_order_id,
                operation=operation,
                station_id=station_id,
                badge_scan=badge_scan,
                notes=notes
            )
            
            self._notify_data_changed()
            self._notify_status_message(f"Clocked in {employee_name} to {operation}")
            return time_entry
            
        except Exception as e:
            logger.error(f"Error clocking in operator: {e}")
            self._notify_status_message(f"Error clocking in: {str(e)}")
            raise
    
    def clock_out_operator(self, time_entry_id: int):
        """Clock out an operator from a work operation."""
        try:
            time_entry = self.time_entry_service.clock_out(time_entry_id)
            
            self._notify_data_changed()
            self._notify_status_message(f"Clocked out {time_entry.employee_name}")
            return time_entry
            
        except Exception as e:
            logger.error(f"Error clocking out operator: {e}")
            self._notify_status_message(f"Error clocking out: {str(e)}")
            raise
    
    def get_active_entries_for_display(self, employee_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active time entries as serialized dicts (session-safe)."""
        try:
            return self.time_entry_service.get_active_entries_for_display(employee_id)
        except Exception as e:
            logger.error(f"Error getting active entries for display: {e}")
            raise

    def get_recent_completed_entries(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get completed entries from the last N hours as display dicts."""
        try:
            return self.time_entry_service.get_recent_completed_entries(hours)
        except Exception as e:
            logger.error(f"Error getting recent completed entries: {e}")
            raise

    def get_stations_for_clock_in(self) -> List[Dict[str, Any]]:
        """Get stations available or running, suitable for the clock-in dropdown."""
        try:
            return self.station_management_service.get_stations_for_clock_in()
        except Exception as e:
            logger.error(f"Error getting clock-in stations: {e}")
            raise

    def get_active_time_entries(self, employee_id: Optional[str] = None) -> List:
        """Get all active time entries."""
        try:
            return self.time_entry_service.get_active_time_entries(employee_id)
        except Exception as e:
            logger.error(f"Error getting active time entries: {e}")
            raise
    
    def get_time_entry_statistics(self, start_date: datetime, end_date: datetime,
                                employee_id: Optional[str] = None) -> Dict[str, Any]:
        """Get time entry statistics."""
        try:
            return self.time_entry_service.get_time_entry_statistics(start_date, end_date, employee_id)
        except Exception as e:
            logger.error(f"Error getting time entry statistics: {e}")
            raise
    
    # Production Output Operations
    def record_production_output(self, work_order_id: int, output_type: str,
                               quantity_produced: float, operator_id: str,
                               operator_name: str, **kwargs) -> Any:
        """Record production output."""
        try:
            from decimal import Decimal
            output = self.production_output_service.create_production_output(
                work_order_id=work_order_id,
                output_type=output_type,
                quantity_produced=Decimal(str(quantity_produced)),
                operator_id=operator_id,
                operator_name=operator_name,
                **kwargs
            )
            
            self._notify_data_changed()
            self._notify_status_message(f"Recorded {quantity_produced} units of {output_type}")
            return output
            
        except Exception as e:
            logger.error(f"Error recording production output: {e}")
            self._notify_status_message(f"Error recording output: {str(e)}")
            raise
    
    def get_work_order_yield(self, work_order_id: int) -> Dict[str, Any]:
        """Get yield statistics for a work order."""
        try:
            return self.production_output_service.calculate_work_order_yield(work_order_id)
        except Exception as e:
            logger.error(f"Error getting work order yield: {e}")
            raise
    
    def get_production_outputs_by_work_order(self, work_order_id: int) -> List:
        """Get production outputs for a work order."""
        try:
            return self.production_output_service.get_production_outputs_by_work_order(work_order_id)
        except Exception as e:
            logger.error(f"Error getting production outputs: {e}")
            raise
    
    # Batch Tracking Operations
    def create_production_batch(self, batch_type: str, operator_id: str, operator_name: str,
                              **kwargs) -> Any:
        """Create a new production batch."""
        try:
            batch = self.batch_tracking_service.create_production_batch(
                batch_type=batch_type,
                operator_id=operator_id,
                operator_name=operator_name,
                **kwargs
            )
            
            self._notify_data_changed()
            self._notify_status_message(f"Created batch {batch.batch_number}")
            return batch
            
        except Exception as e:
            logger.error(f"Error creating production batch: {e}")
            self._notify_status_message(f"Error creating batch: {str(e)}")
            raise
    
    def complete_batch(self, batch_id: int, output_quantity: float,
                      scrap_quantity: Optional[float] = None,
                      quality_notes: Optional[str] = None) -> Any:
        """Complete a production batch."""
        try:
            from decimal import Decimal
            batch = self.batch_tracking_service.complete_batch(
                batch_id=batch_id,
                output_quantity=Decimal(str(output_quantity)),
                scrap_quantity=Decimal(str(scrap_quantity)) if scrap_quantity else None,
                quality_notes=quality_notes
            )
            
            self._notify_data_changed()
            self._notify_status_message(f"Completed batch {batch.batch_number}")
            return batch
            
        except Exception as e:
            logger.error(f"Error completing batch: {e}")
            self._notify_status_message(f"Error completing batch: {str(e)}")
            raise
    
    def get_batch_chain(self, batch_id: int) -> Dict[str, Any]:
        """Get complete batch traceability chain."""
        try:
            return self.batch_tracking_service.get_batch_chain(batch_id)
        except Exception as e:
            logger.error(f"Error getting batch chain: {e}")
            raise
    
    def get_active_batches(self) -> List:
        """Get all active production batches."""
        try:
            return self.batch_tracking_service.get_active_batches()
        except Exception as e:
            logger.error(f"Error getting active batches: {e}")
            raise
    
    def trace_material_to_outputs(self, raw_material_lot: str) -> List[Dict[str, Any]]:
        """Trace raw material to final outputs."""
        try:
            return self.batch_tracking_service.trace_material_to_outputs(raw_material_lot)
        except Exception as e:
            logger.error(f"Error tracing material: {e}")
            raise
    
    # Station Management Operations
    def create_station(self, station_id: str, name: str, station_type: str,
                     **kwargs) -> Any:
        """Create a new production station."""
        try:
            station = self.station_management_service.create_station(
                station_id=station_id,
                name=name,
                station_type=station_type,
                **kwargs
            )
            
            self._notify_data_changed()
            self._notify_status_message(f"Created station {station_id}")
            return station
            
        except Exception as e:
            logger.error(f"Error creating station: {e}")
            self._notify_status_message(f"Error creating station: {str(e)}")
            raise
    
    def assign_work_to_station(self, station_id: str, work_order_id: int,
                              operator_id: str, operator_name: str,
                              batch_id: Optional[int] = None) -> Any:
        """Assign work to a station."""
        try:
            station = self.station_management_service.assign_work_to_station(
                station_id=station_id,
                work_order_id=work_order_id,
                operator_id=operator_id,
                operator_name=operator_name,
                batch_id=batch_id
            )
            
            self._notify_data_changed()
            self._notify_status_message(f"Assigned work to station {station_id}")
            return station
            
        except Exception as e:
            logger.error(f"Error assigning work to station: {e}")
            self._notify_status_message(f"Error assigning work: {str(e)}")
            raise
    
    def update_station_status(self, station_id: str, status: str,
                            reason: Optional[str] = None) -> Any:
        """Update station status."""
        try:
            station = self.station_management_service.update_station_status(
                station_id=station_id,
                status=status,
                reason=reason
            )
            
            self._notify_data_changed()
            self._notify_status_message(f"Updated station {station_id} to {status}")
            return station
            
        except Exception as e:
            logger.error(f"Error updating station status: {e}")
            self._notify_status_message(f"Error updating status: {str(e)}")
            raise
    
    def get_all_stations(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all stations serialized as dicts."""
        try:
            return self.station_management_service.get_all_stations(status_filter)
        except Exception as e:
            logger.error(f"Error getting all stations: {e}")
            raise

    def update_station(self, station_id: str, **kwargs) -> Any:
        """Update station details."""
        try:
            station = self.station_management_service.update_station(station_id, **kwargs)
            self._notify_data_changed()
            self._notify_status_message(f"Updated station {station_id}")
            return station
        except Exception as e:
            logger.error(f"Error updating station: {e}")
            self._notify_status_message(f"Error updating station: {str(e)}")
            raise

    def release_station_work(self, station_id: str) -> Any:
        """Release current work assignment from a station."""
        try:
            station = self.station_management_service.release_station_work(station_id)
            self._notify_data_changed()
            self._notify_status_message(f"Released work from station {station_id}")
            return station
        except Exception as e:
            logger.error(f"Error releasing station work: {e}")
            self._notify_status_message(f"Error releasing work: {str(e)}")
            raise

    def update_maintenance(self, station_id: str, maintenance_hours: int,
                           next_maintenance_date=None) -> Any:
        """Update maintenance records for a station."""
        try:
            station = self.station_management_service.update_maintenance(
                station_id=station_id,
                maintenance_hours=maintenance_hours,
                next_maintenance_date=next_maintenance_date
            )
            self._notify_data_changed()
            self._notify_status_message(f"Updated maintenance for station {station_id}")
            return station
        except Exception as e:
            logger.error(f"Error updating maintenance: {e}")
            self._notify_status_message(f"Error updating maintenance: {str(e)}")
            raise

    def seed_default_stations(self) -> int:
        """Seed default XPanda floor stations if none exist."""
        try:
            count = self.station_management_service.seed_default_stations()
            if count > 0:
                self._notify_data_changed()
                self._notify_status_message(f"Seeded {count} default stations")
            return count
        except Exception as e:
            logger.error(f"Error seeding default stations: {e}")
            self._notify_status_message(f"Error seeding stations: {str(e)}")
            raise

    def get_available_stations(self, station_type: Optional[str] = None) -> List:
        """Get available stations."""
        try:
            return self.station_management_service.get_available_stations(station_type)
        except Exception as e:
            logger.error(f"Error getting available stations: {e}")
            raise
    
    def get_station_summary(self) -> Dict[str, Any]:
        """Get station summary statistics."""
        try:
            return self.station_management_service.get_station_summary()
        except Exception as e:
            logger.error(f"Error getting station summary: {e}")
            raise
    
    def get_maintenance_schedule(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming maintenance schedule."""
        try:
            return self.station_management_service.get_maintenance_schedule(days_ahead)
        except Exception as e:
            logger.error(f"Error getting maintenance schedule: {e}")
            raise
    
    # Dashboard and Statistics
    def get_shop_floor_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for shop floor."""
        try:
            # Get active time entries
            active_time_entries = self.get_active_time_entries()
            
            # Get active batches
            active_batches = self.get_active_batches()
            
            # Get station summary
            station_summary = self.get_station_summary()
            
            # Get today's production summary
            from datetime import date
            today_start = datetime.combine(date.today(), datetime.min.time())
            today_end = today_start.replace(hour=23, minute=59, second=59)
            
            daily_production = self.production_output_service.get_daily_production_summary(today_start)
            
            # Get upcoming maintenance
            maintenance_schedule = self.get_maintenance_schedule(7)  # Next 7 days
            
            return {
                'active_time_entries': len(active_time_entries),
                'active_batches': len(active_batches),
                'station_summary': station_summary,
                'daily_production': daily_production,
                'upcoming_maintenance': len(maintenance_schedule),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            raise
    
    # Options and Lookups
    def get_operation_options(self) -> List[Dict[str, str]]:
        """Get operation type options."""
        return self.time_entry_service.get_operation_options()
    
    def get_output_type_options(self) -> List[Dict[str, str]]:
        """Get output type options."""
        return self.production_output_service.get_output_type_options()
    
    def get_batch_type_options(self) -> List[Dict[str, str]]:
        """Get batch type options."""
        return self.batch_tracking_service.get_batch_type_options()
    
    def get_station_type_options(self) -> List[Dict[str, str]]:
        """Get station type options."""
        return self.station_management_service.get_station_type_options()
    
    def get_station_status_options(self) -> List[Dict[str, str]]:
        """Get station status options."""
        return self.station_management_service.get_station_status_options()
    
    # Callback Management
    def register_data_changed_callback(self, callback):
        """Register callback for data change notifications."""
        self._data_changed_callbacks.append(callback)
    
    def register_status_message_callback(self, callback):
        """Register callback for status message notifications."""
        self._status_message_callbacks.append(callback)
    
    def _notify_data_changed(self):
        """Notify all registered callbacks of data changes."""
        for callback in self._data_changed_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in data changed callback: {e}")
    
    def _notify_status_message(self, message: str, timeout: int = 5000):
        """Notify all registered callbacks of status messages."""
        for callback in self._status_message_callbacks:
            try:
                callback(message, timeout)
            except Exception as e:
                logger.error(f"Error in status message callback: {e}")
    
    # Search and Lookup
    def search_time_entries(self, search_term: str, limit: int = 100) -> List:
        """Search time entries."""
        try:
            return self.time_entry_service.search_time_entries(search_term, limit)
        except Exception as e:
            logger.error(f"Error searching time entries: {e}")
            raise
    
    def search_production_outputs(self, search_term: str, limit: int = 100) -> List:
        """Search production outputs."""
        try:
            return self.production_output_service.search_production_outputs(search_term, limit)
        except Exception as e:
            logger.error(f"Error searching production outputs: {e}")
            raise
    
    def search_batches(self, search_term: str, limit: int = 100) -> List:
        """Search production batches."""
        try:
            return self.batch_tracking_service.search_batches(search_term, limit)
        except Exception as e:
            logger.error(f"Error searching batches: {e}")
            raise
    
    def search_stations(self, search_term: str, limit: int = 100) -> List:
        """Search production stations."""
        try:
            return self.station_management_service.search_stations(search_term, limit)
        except Exception as e:
            logger.error(f"Error searching stations: {e}")
            raise
