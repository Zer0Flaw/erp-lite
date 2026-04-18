"""
Station Management Service for XPanda ERP-Lite.
Handles production stations and equipment status tracking.
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from database.models.shop_floor import ProductionStation, StationStatus, StationType
from database.models.production import WorkOrder
from database.models.shop_floor import ProductionBatch
from database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class StationManagementService:
    """Service for managing production stations and equipment."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def create_station(self, station_id: str, name: str, station_type: str,
                      location: Optional[str] = None, department: Optional[str] = None,
                      capacity_per_hour: Optional[Decimal] = None,
                      max_block_size: Optional[str] = None,
                      temperature_range: Optional[str] = None,
                      notes: Optional[str] = None) -> ProductionStation:
        """Create a new production station."""
        try:
            with self.db_manager.get_session() as session:
                # Check if station ID already exists
                existing = session.query(ProductionStation).filter(
                    ProductionStation.station_id == station_id
                ).first()
                if existing:
                    raise ValueError(f"Station ID {station_id} already exists")
                
                station = ProductionStation(
                    station_id=station_id,
                    name=name,
                    station_type=station_type,
                    status=StationStatus.AVAILABLE.value,
                    location=location,
                    department=department,
                    capacity_per_hour=capacity_per_hour,
                    max_block_size=max_block_size,
                    temperature_range=temperature_range,
                    notes=notes
                )
                
                session.add(station)
                session.commit()
                session.refresh(station)
                
                logger.info(f"Created production station {station_id}")
                return station
                
        except Exception as e:
            logger.error(f"Error creating production station: {e}")
            raise
    
    def update_station_status(self, station_id: str, status: str, 
                            reason: Optional[str] = None) -> ProductionStation:
        """Update station status."""
        try:
            with self.db_manager.get_session() as session:
                station = session.query(ProductionStation).filter(
                    ProductionStation.station_id == station_id
                ).first()
                
                if not station:
                    raise ValueError(f"Station {station_id} not found")
                
                station.set_status(status, reason)
                session.commit()
                session.refresh(station)
                
                logger.info(f"Updated station {station_id} status to {status}")
                return station
                
        except Exception as e:
            logger.error(f"Error updating station status: {e}")
            raise
    
    def assign_work_to_station(self, station_id: str, work_order_id: int,
                              operator_id: str, operator_name: str,
                              batch_id: Optional[int] = None) -> ProductionStation:
        """Assign work to a station."""
        try:
            with self.db_manager.get_session() as session:
                station = session.query(ProductionStation).filter(
                    ProductionStation.station_id == station_id
                ).first()
                
                if not station:
                    raise ValueError(f"Station {station_id} not found")
                
                # Validate work order
                work_order = session.query(WorkOrder).filter(
                    WorkOrder.id == work_order_id
                ).first()
                if not work_order:
                    raise ValueError(f"Work Order {work_order_id} not found")
                
                # Validate batch if provided
                if batch_id:
                    batch = session.query(ProductionBatch).filter(
                        ProductionBatch.id == batch_id
                    ).first()
                    if not batch:
                        raise ValueError(f"Batch {batch_id} not found")
                
                station.assign_work(work_order_id, operator_id, operator_name)
                if batch_id:
                    station.current_batch_id = batch_id
                
                session.commit()
                session.refresh(station)
                
                logger.info(f"Assigned work order {work_order_id} to station {station_id}")
                return station
                
        except Exception as e:
            logger.error(f"Error assigning work to station: {e}")
            raise
    
    def release_station_work(self, station_id: str) -> ProductionStation:
        """Release current work assignment from a station."""
        try:
            with self.db_manager.get_session() as session:
                station = session.query(ProductionStation).filter(
                    ProductionStation.station_id == station_id
                ).first()
                
                if not station:
                    raise ValueError(f"Station {station_id} not found")
                
                station.release_work()
                session.commit()
                session.refresh(station)
                
                logger.info(f"Released work from station {station_id}")
                return station
                
        except Exception as e:
            logger.error(f"Error releasing station work: {e}")
            raise
    
    def get_station_by_id(self, station_id: str) -> Optional[ProductionStation]:
        """Get a station by its ID."""
        try:
            with self.db_manager.get_session() as session:
                return session.query(ProductionStation).filter(
                    ProductionStation.station_id == station_id
                ).first()
                
        except Exception as e:
            logger.error(f"Error getting station by ID: {e}")
            raise
    
    def get_stations_by_status(self, status: str) -> List[ProductionStation]:
        """Get all stations with a specific status."""
        try:
            with self.db_manager.get_session() as session:
                return session.query(ProductionStation).filter(
                    ProductionStation.status == status
                ).order_by(ProductionStation.station_id).all()
                
        except Exception as e:
            logger.error(f"Error getting stations by status: {e}")
            raise
    
    def get_stations_by_type(self, station_type: str) -> List[ProductionStation]:
        """Get all stations of a specific type."""
        try:
            with self.db_manager.get_session() as session:
                return session.query(ProductionStation).filter(
                    ProductionStation.station_type == station_type
                ).order_by(ProductionStation.station_id).all()
                
        except Exception as e:
            logger.error(f"Error getting stations by type: {e}")
            raise
    
    def get_available_stations(self, station_type: Optional[str] = None) -> List[ProductionStation]:
        """Get all available stations, optionally filtered by type."""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(ProductionStation).filter(
                    ProductionStation.status == StationStatus.AVAILABLE.value
                )
                
                if station_type:
                    query = query.filter(ProductionStation.station_type == station_type)
                
                return query.order_by(ProductionStation.station_id).all()
                
        except Exception as e:
            logger.error(f"Error getting available stations: {e}")
            raise
    
    def get_station_utilization(self, start_date: datetime, 
                             end_date: datetime) -> Dict[str, Any]:
        """Get station utilization statistics."""
        try:
            with self.db_manager.get_session() as session:
                stations = session.query(ProductionStation).all()
                
                utilization_data = []
                total_available_hours = Decimal('0')
                total_running_hours = Decimal('0')
                
                for station in stations:
                    # Calculate available hours (assuming 24/7 operation)
                    total_hours = Decimal((end_date - start_date).total_seconds() / 3600)
                    total_available_hours += total_hours
                    
                    # For this implementation, we'll estimate running hours
                    # In a real system, this would be calculated from actual time entries
                    if station.status == StationStatus.RUNNING.value:
                        # Estimate based on current status
                        running_hours = total_hours * Decimal('0.8')  # Assume 80% utilization
                    else:
                        running_hours = total_hours * Decimal('0.3')  # Assume 30% utilization for available stations
                    
                    total_running_hours += running_hours
                    utilization_percentage = (running_hours / total_hours * 100) if total_hours > 0 else 0
                    
                    utilization_data.append({
                        'station_id': station.station_id,
                        'name': station.name,
                        'station_type': station.station_type,
                        'status': station.status,
                        'total_hours': float(total_hours),
                        'running_hours': float(running_hours),
                        'utilization_percentage': float(utilization_percentage)
                    })
                
                overall_utilization = (total_running_hours / total_available_hours * 100) if total_available_hours > 0 else 0
                
                return {
                    'overall_utilization_percentage': float(overall_utilization),
                    'total_available_hours': float(total_available_hours),
                    'total_running_hours': float(total_running_hours),
                    'station_count': len(stations),
                    'station_breakdown': utilization_data
                }
                
        except Exception as e:
            logger.error(f"Error getting station utilization: {e}")
            raise
    
    def get_maintenance_schedule(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming maintenance schedule."""
        try:
            with self.db_manager.get_session() as session:
                target_date = date.today() + timedelta(days=days_ahead)
                
                stations = session.query(ProductionStation).filter(
                    ProductionStation.next_maintenance_date <= target_date
                ).order_by(ProductionStation.next_maintenance_date).all()
                
                schedule = []
                for station in stations:
                    days_until_maintenance = (station.next_maintenance_date - date.today()).days if station.next_maintenance_date else None
                    
                    schedule.append({
                        'station_id': station.station_id,
                        'name': station.name,
                        'station_type': station.station_type,
                        'last_maintenance_date': station.last_maintenance_date,
                        'next_maintenance_date': station.next_maintenance_date,
                        'days_until_maintenance': days_until_maintenance,
                        'maintenance_hours': station.maintenance_hours,
                        'total_runtime_hours': float(station.total_runtime_hours),
                        'status': station.status
                    })
                
                return schedule
                
        except Exception as e:
            logger.error(f"Error getting maintenance schedule: {e}")
            raise
    
    def update_maintenance(self, station_id: str, maintenance_hours: int,
                          next_maintenance_date: Optional[date] = None) -> ProductionStation:
        """Update maintenance records for a station."""
        try:
            with self.db_manager.get_session() as session:
                station = session.query(ProductionStation).filter(
                    ProductionStation.station_id == station_id
                ).first()
                
                if not station:
                    raise ValueError(f"Station {station_id} not found")
                
                station.last_maintenance_date = date.today()
                station.maintenance_hours += maintenance_hours
                station.total_runtime_hours = Decimal('0')  # Reset runtime after maintenance
                
                if next_maintenance_date:
                    station.next_maintenance_date = next_maintenance_date
                else:
                    # Default to 30 days from now
                    station.next_maintenance_date = date.today() + timedelta(days=30)
                
                session.commit()
                session.refresh(station)
                
                logger.info(f"Updated maintenance for station {station_id}")
                return station
                
        except Exception as e:
            logger.error(f"Error updating maintenance: {e}")
            raise
    
    def get_station_type_options(self) -> List[Dict[str, str]]:
        """Get available station type options."""
        return [
            {'value': StationType.PRE_EXPANDER.value, 'label': 'Pre-Expander'},
            {'value': StationType.BLOCK_MOLD.value, 'label': 'Block Mold'},
            {'value': StationType.AGING_SILO.value, 'label': 'Aging Silo'},
            {'value': StationType.HOT_WIRE_CUTTER.value, 'label': 'Hot Wire Cutter'},
            {'value': StationType.CNC_ROUTER.value, 'label': 'CNC Router'},
            {'value': StationType.BAND_SAW.value, 'label': 'Band Saw'},
            {'value': StationType.PACKAGING.value, 'label': 'Packaging'},
            {'value': StationType.INSPECTION.value, 'label': 'Inspection'},
            {'value': StationType.GENERAL.value, 'label': 'General'}
        ]
    
    def get_station_status_options(self) -> List[Dict[str, str]]:
        """Get available station status options."""
        return [
            {'value': StationStatus.AVAILABLE.value, 'label': 'Available'},
            {'value': StationStatus.RUNNING.value, 'label': 'Running'},
            {'value': StationStatus.MAINTENANCE.value, 'label': 'Maintenance'},
            {'value': StationStatus.OFFLINE.value, 'label': 'Offline'},
            {'value': StationStatus.CLEANUP.value, 'label': 'Cleanup'}
        ]
    
    def get_all_stations(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all stations serialized as dicts (session-safe), optionally filtered by status."""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(ProductionStation).order_by(ProductionStation.station_id)
                if status_filter:
                    query = query.filter(ProductionStation.status == status_filter)
                stations = query.all()
                return [
                    {
                        'station_id': s.station_id,
                        'name': s.name,
                        'station_type': s.station_type,
                        'status': s.status,
                        'location': s.location or '',
                        'department': s.department or '',
                        'capacity_per_hour': float(s.capacity_per_hour) if s.capacity_per_hour else 0.0,
                        'current_operator_name': s.current_operator_name or '',
                        'total_runtime_hours': float(s.total_runtime_hours) if s.total_runtime_hours else 0.0,
                        'notes': s.notes or '',
                        'max_block_size': s.max_block_size or '',
                        'temperature_range': s.temperature_range or '',
                    }
                    for s in stations
                ]
        except Exception as e:
            logger.error(f"Error getting all stations: {e}")
            raise

    def update_station(self, station_id: str, **kwargs) -> ProductionStation:
        """Update editable fields of an existing station."""
        try:
            with self.db_manager.get_session() as session:
                station = session.query(ProductionStation).filter(
                    ProductionStation.station_id == station_id
                ).first()
                if not station:
                    raise ValueError(f"Station {station_id} not found")

                allowed = {'name', 'station_type', 'location', 'department',
                           'capacity_per_hour', 'max_block_size', 'temperature_range', 'notes', 'status'}
                for key, value in kwargs.items():
                    if key in allowed:
                        setattr(station, key, value)

                session.commit()
                session.refresh(station)
                logger.info(f"Updated station {station_id}")
                return station
        except Exception as e:
            logger.error(f"Error updating station: {e}")
            raise

    def seed_default_stations(self) -> int:
        """Seed default XPanda floor stations if none exist. Returns number of stations created."""
        try:
            with self.db_manager.get_session() as session:
                if session.query(ProductionStation).count() > 0:
                    return 0

                defaults = [
                    ('PRE-EXP-01', 'Pre-Expander',    StationType.PRE_EXPANDER.value,   'Production Floor'),
                    ('MOLD-01',    'Block Mold 1',     StationType.BLOCK_MOLD.value,      'Production Floor'),
                    ('MOLD-02',    'Block Mold 2',     StationType.BLOCK_MOLD.value,      'Production Floor'),
                    ('SILO-01',    'Aging Silo 1',     StationType.AGING_SILO.value,      'Production Floor'),
                    ('SILO-02',    'Aging Silo 2',     StationType.AGING_SILO.value,      'Production Floor'),
                    ('CUT-01',     'Hot Wire Cutter',  StationType.HOT_WIRE_CUTTER.value, 'Cutting Area'),
                    ('CNC-01',     'CNC Router',       StationType.CNC_ROUTER.value,      'Cutting Area'),
                    ('SAW-01',     'Band Saw',         StationType.BAND_SAW.value,        'Cutting Area'),
                    ('PKG-01',     'Packaging',        StationType.PACKAGING.value,       'Packaging Area'),
                    ('QC-01',      'Inspection',       StationType.INSPECTION.value,      'Quality Area'),
                ]

                for station_id, name, station_type, location in defaults:
                    session.add(ProductionStation(
                        station_id=station_id,
                        name=name,
                        station_type=station_type,
                        status=StationStatus.AVAILABLE.value,
                        location=location,
                    ))

                session.commit()
                logger.info(f"Seeded {len(defaults)} default stations")
                return len(defaults)
        except Exception as e:
            logger.error(f"Error seeding default stations: {e}")
            raise

    def get_stations_for_clock_in(self) -> List[Dict[str, Any]]:
        """Get stations with available or running status for the clock-in dropdown."""
        try:
            with self.db_manager.get_session() as session:
                stations = session.query(ProductionStation).filter(
                    ProductionStation.status.in_([
                        StationStatus.AVAILABLE.value,
                        StationStatus.RUNNING.value,
                    ])
                ).order_by(ProductionStation.station_id).all()
                return [
                    {
                        'station_id': s.station_id,
                        'name': s.name,
                        'status': s.status,
                    }
                    for s in stations
                ]
        except Exception as e:
            logger.error(f"Error getting clock-in stations: {e}")
            raise

    def search_stations(self, search_term: str, limit: int = 100) -> List[ProductionStation]:
        """Search stations by name, location, or station ID."""
        try:
            with self.db_manager.get_session() as session:
                search_pattern = f"%{search_term}%"
                
                return session.query(ProductionStation).filter(
                    (ProductionStation.station_id.ilike(search_pattern)) |
                    (ProductionStation.name.ilike(search_pattern)) |
                    (ProductionStation.location.ilike(search_pattern)) |
                    (ProductionStation.department.ilike(search_pattern))
                ).limit(limit).all()
                
        except Exception as e:
            logger.error(f"Error searching stations: {e}")
            raise
    
    def get_station_summary(self) -> Dict[str, Any]:
        """Get summary of all stations."""
        try:
            with self.db_manager.get_session() as session:
                stations = session.query(ProductionStation).all()
                
                status_counts = {}
                type_counts = {}
                
                for station in stations:
                    # Count by status
                    status = station.status
                    if status not in status_counts:
                        status_counts[status] = 0
                    status_counts[status] += 1
                    
                    # Count by type
                    station_type = station.station_type
                    if station_type not in type_counts:
                        type_counts[station_type] = 0
                    type_counts[station_type] += 1
                
                return {
                    'total_stations': len(stations),
                    'status_breakdown': status_counts,
                    'type_breakdown': type_counts,
                    'available_count': status_counts.get(StationStatus.AVAILABLE.value, 0),
                    'running_count': status_counts.get(StationStatus.RUNNING.value, 0),
                    'maintenance_count': status_counts.get(StationStatus.MAINTENANCE.value, 0),
                    'offline_count': status_counts.get(StationStatus.OFFLINE.value, 0)
                }
                
        except Exception as e:
            logger.error(f"Error getting station summary: {e}")
            raise
