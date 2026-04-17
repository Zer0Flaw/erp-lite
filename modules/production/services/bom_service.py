"""
BOM service for XPanda ERP-Lite.
Provides business logic for Bill of Materials management operations.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from database.models.production import BillOfMaterial, BillOfMaterialLine, BillOfMaterialStatus
from database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class BOMService:
    """Service class for BOM operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_bom(self, bom_data: Dict[str, Any]) -> Optional[BillOfMaterial]:
        """
        Create a new Bill of Materials.
        
        Args:
            bom_data: Dictionary containing BOM information
            
        Returns:
            Created BillOfMaterial object or None if failed
        """
        try:
            with self.db_manager.get_session() as session:
                # Check if BOM code already exists
                existing = session.query(BillOfMaterial).filter(
                    BillOfMaterial.bom_code == bom_data['bom_code'].upper(),
                    BillOfMaterial.deleted_at.is_(None)
                ).first()
                
                if existing:
                    logger.warning(f"BOM with code {bom_data['bom_code']} already exists")
                    return None
                
                # Create new BOM
                bom = BillOfMaterial(
                    bom_code=bom_data['bom_code'].upper(),
                    name=bom_data['name'],
                    description=bom_data.get('description', ''),
                    version=bom_data.get('version', '1.0'),
                    finished_good_sku=bom_data['finished_good_sku'],
                    finished_good_name=bom_data['finished_good_name'],
                    standard_quantity=Decimal(str(bom_data.get('standard_quantity', 1.0))),
                    unit_of_measure=bom_data.get('unit_of_measure', 'EA'),
                    standard_cycle_time=Decimal(str(bom_data.get('standard_cycle_time', 0))),
                    setup_time=Decimal(str(bom_data.get('setup_time', 0))),
                    yield_percentage=Decimal(str(bom_data.get('yield_percentage', 100.0))),
                    effective_date=self._parse_date(bom_data.get('effective_date')),
                    expiry_date=self._parse_date(bom_data.get('expiry_date')),
                    status=bom_data.get('status', BillOfMaterialStatus.DRAFT.value),
                    created_by=bom_data.get('created_by', 'System')
                )
                
                session.add(bom)
                session.flush()  # Get the ID without committing
                
                # Create BOM lines
                bom_lines_data = bom_data.get('bom_lines', [])
                for line_data in bom_lines_data:
                    bom_line = BillOfMaterialLine(
                        bom_id=bom.id,
                        material_sku=line_data['material_sku'],
                        material_name=line_data.get('material_name', ''),
                        material_category=line_data.get('material_category', ''),
                        quantity_required=Decimal(str(line_data['quantity_required'])),
                        unit_of_measure=line_data.get('unit_of_measure', 'EA'),
                        unit_cost=Decimal(str(line_data.get('unit_cost', 0))),
                        waste_percentage=Decimal(str(line_data.get('waste_percentage', 0))),
                        is_optional=line_data.get('is_optional', False),
                        substitution_sku=line_data.get('substitution_sku'),
                        notes=line_data.get('notes', '')
                    )
                    session.add(bom_line)
                
                logger.info(f"Created BOM: {bom.bom_code}")
                return bom
                
        except Exception as e:
            logger.error(f"Failed to create BOM: {e}")
            return None
    
    def get_bom_by_id(self, bom_id: UUID) -> Optional[BillOfMaterial]:
        """
        Get BOM by ID.
        
        Args:
            bom_id: UUID of the BOM
            
        Returns:
            BillOfMaterial object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(BillOfMaterial).filter(
                    BillOfMaterial.id == bom_id,
                    BillOfMaterial.deleted_at.is_(None)
                ).first()
        except Exception as e:
            logger.error(f"Failed to get BOM {bom_id}: {e}")
            return None
    
    def get_bom_by_code(self, bom_code: str) -> Optional[BillOfMaterial]:
        """
        Get BOM by code.
        
        Args:
            bom_code: BOM code
            
        Returns:
            BillOfMaterial object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(BillOfMaterial).filter(
                    BillOfMaterial.bom_code == bom_code.upper(),
                    BillOfMaterial.deleted_at.is_(None)
                ).first()
        except Exception as e:
            logger.error(f"Failed to get BOM {bom_code}: {e}")
            return None
    
    def get_all_boms(self, active_only: bool = False) -> List[BillOfMaterial]:
        """
        Get all BOMs.
        
        Args:
            active_only: Whether to return only active BOMs
            
        Returns:
            List of BillOfMaterial objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(BillOfMaterial).filter(
                    BillOfMaterial.deleted_at.is_(None)
                )
                
                if active_only:
                    today = date.today()
                    query = query.filter(
                        BillOfMaterial.status == BillOfMaterialStatus.ACTIVE.value,
                        BillOfMaterial.effective_date <= today,
                        (BillOfMaterial.expiry_date.is_(None) | BillOfMaterial.expiry_date >= today)
                    )
                
                return query.order_by(BillOfMaterial.bom_code).all()
        except Exception as e:
            logger.error(f"Failed to get BOMs: {e}")
            return []
    
    def search_boms(self, search_term: str, status_filter: Optional[str] = None) -> List[BillOfMaterial]:
        """
        Search BOMs by code, name, or product SKU.
        
        Args:
            search_term: Search term
            status_filter: Optional status filter
            
        Returns:
            List of matching BillOfMaterial objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(BillOfMaterial).filter(
                    BillOfMaterial.deleted_at.is_(None)
                )
                
                # Add search conditions
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    (BillOfMaterial.bom_code.ilike(search_pattern)) |
                    (BillOfMaterial.name.ilike(search_pattern)) |
                    (BillOfMaterial.finished_good_sku.ilike(search_pattern)) |
                    (BillOfMaterial.finished_good_name.ilike(search_pattern))
                )
                
                # Add status filter if specified
                if status_filter:
                    query = query.filter(BillOfMaterial.status == status_filter)
                
                return query.order_by(BillOfMaterial.bom_code).all()
        except Exception as e:
            logger.error(f"Failed to search BOMs: {e}")
            return []
    
    def update_bom(self, bom_id: UUID, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing BOM.
        
        Args:
            bom_id: UUID of the BOM to update
            update_data: Dictionary containing updated fields
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                bom = session.query(BillOfMaterial).filter(
                    BillOfMaterial.id == bom_id,
                    BillOfMaterial.deleted_at.is_(None)
                ).first()
                
                if not bom:
                    logger.warning(f"BOM {bom_id} not found")
                    return False
                
                # Update BOM fields
                for field, value in update_data.items():
                    if hasattr(bom, field) and field not in ['id', 'created_at', 'created_by', 'bom_lines']:
                        if field == 'bom_code':
                            bom.bom_code = value.upper()
                        elif field in ['standard_quantity', 'standard_cycle_time', 'setup_time', 'yield_percentage']:
                            setattr(bom, field, Decimal(str(value)))
                        elif field in ['effective_date', 'expiry_date']:
                            setattr(bom, field, self._parse_date(value))
                        else:
                            setattr(bom, field, value)
                
                bom.updated_at = datetime.utcnow()
                
                # Update BOM lines if provided
                if 'bom_lines' in update_data:
                    # Remove existing lines
                    session.query(BillOfMaterialLine).filter(
                        BillOfMaterialLine.bom_id == bom_id
                    ).delete()
                    
                    # Add new lines
                    for line_data in update_data['bom_lines']:
                        bom_line = BillOfMaterialLine(
                            bom_id=bom.id,
                            material_sku=line_data['material_sku'],
                            material_name=line_data.get('material_name', ''),
                            material_category=line_data.get('material_category', ''),
                            quantity_required=Decimal(str(line_data['quantity_required'])),
                            unit_of_measure=line_data.get('unit_of_measure', 'EA'),
                            unit_cost=Decimal(str(line_data.get('unit_cost', 0))),
                            waste_percentage=Decimal(str(line_data.get('waste_percentage', 0))),
                            is_optional=line_data.get('is_optional', False),
                            substitution_sku=line_data.get('substitution_sku'),
                            notes=line_data.get('notes', '')
                        )
                        session.add(bom_line)
                
                logger.info(f"Updated BOM: {bom.bom_code}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update BOM {bom_id}: {e}")
            return False
    
    def delete_bom(self, bom_id: UUID, deleted_by: str) -> bool:
        """
        Soft delete a BOM.
        
        Args:
            bom_id: UUID of the BOM to delete
            deleted_by: User performing the deletion
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                bom = session.query(BillOfMaterial).filter(
                    BillOfMaterial.id == bom_id,
                    BillOfMaterial.deleted_at.is_(None)
                ).first()
                
                if not bom:
                    logger.warning(f"BOM {bom_id} not found")
                    return False
                
                # Check if BOM is used in any active work orders
                from database.models.production import WorkOrder
                active_work_orders = session.query(WorkOrder).filter(
                    WorkOrder.bom_id == bom_id,
                    WorkOrder.status.in_(['Planned', 'Released', 'In Progress'])
                ).count()
                
                if active_work_orders > 0:
                    logger.warning(f"Cannot delete BOM {bom.bom_code} - used in {active_work_orders} active work orders")
                    return False
                
                bom.deleted_at = datetime.utcnow()
                
                logger.info(f"Deleted BOM: {bom.bom_code}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete BOM {bom_id}: {e}")
            return False
    
    def get_bom_statistics(self) -> Dict[str, Any]:
        """
        Get BOM statistics for dashboard.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.db_manager.get_session() as session:
                # Total BOMs
                total_boms = session.query(BillOfMaterial).filter(
                    BillOfMaterial.deleted_at.is_(None)
                ).count()
                
                # Active BOMs
                today = date.today()
                active_boms = session.query(BillOfMaterial).filter(
                    BillOfMaterial.deleted_at.is_(None),
                    BillOfMaterial.status == BillOfMaterialStatus.ACTIVE.value,
                    BillOfMaterial.effective_date <= today,
                    (BillOfMaterial.expiry_date.is_(None) | BillOfMaterial.expiry_date >= today)
                ).count()
                
                # BOMs by status
                status_counts = {}
                for status in BillOfMaterialStatus:
                    count = session.query(BillOfMaterial).filter(
                        BillOfMaterial.status == status.value,
                        BillOfMaterial.deleted_at.is_(None)
                    ).count()
                    status_counts[status.value] = count
                
                return {
                    'total_boms': total_boms,
                    'active_boms': active_boms,
                    'status_counts': status_counts
                }
                
        except Exception as e:
            logger.error(f"Failed to get BOM statistics: {e}")
            return {
                'total_boms': 0,
                'active_boms': 0,
                'status_counts': {}
            }
    
    def get_bom_options(self) -> List[Dict[str, str]]:
        """
        Get BOM options for dropdowns.
        
        Returns:
            List of BOM dictionaries with basic info
        """
        try:
            boms = self.get_all_boms(active_only=True)
            
            return [
                {
                    'id': str(bom.id),
                    'bom_code': bom.bom_code,
                    'name': bom.name,
                    'finished_good_sku': bom.finished_good_sku,
                    'finished_good_name': bom.finished_good_name,
                    'version': bom.version
                }
                for bom in boms
            ]
            
        except Exception as e:
            logger.error(f"Failed to get BOM options: {e}")
            return []
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}")
            return None
    
    def calculate_bom_cost(self, bom_id: UUID) -> Optional[Decimal]:
        """
        Calculate total cost of a BOM.
        
        Args:
            bom_id: UUID of the BOM
            
        Returns:
            Total cost or None if failed
        """
        try:
            with self.db_manager.get_session() as session:
                bom = session.query(BillOfMaterial).filter(
                    BillOfMaterial.id == bom_id,
                    BillOfMaterial.deleted_at.is_(None)
                ).first()
                
                if not bom:
                    return None
                
                total_cost = Decimal('0')
                for line in bom.bom_lines:
                    if line.unit_cost:
                        effective_quantity = line.effective_quantity
                        line_cost = effective_quantity * line.unit_cost
                        total_cost += line_cost
                
                return total_cost
                
        except Exception as e:
            logger.error(f"Failed to calculate BOM cost {bom_id}: {e}")
            return None
