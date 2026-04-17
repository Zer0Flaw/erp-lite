"""
Material service layer for XPanda ERP-Lite.
Provides business logic for material management operations.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from database.models.inventory import Material, MaterialCategory, InventoryTransaction, TransactionType
from database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class MaterialService:
    """Service class for material operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_material(self, material_data: Dict[str, Any]) -> Optional[Material]:
        """
        Create a new material record.
        
        Args:
            material_data: Dictionary containing material information
            
        Returns:
            Created Material object or None if failed
        """
        try:
            with self.db_manager.get_session() as session:
                # Check if SKU already exists
                existing = session.query(Material).filter(
                    Material.sku == material_data['sku'].upper()
                ).first()
                
                if existing:
                    logger.warning(f"Material with SKU {material_data['sku']} already exists")
                    return None
                
                # Create new material
                material = Material(
                    sku=material_data['sku'].upper(),
                    name=material_data['name'],
                    description=material_data.get('description', ''),
                    category=material_data.get('category', MaterialCategory.RAW_MATERIAL.value),
                    unit_of_measure=material_data.get('unit_of_measure', 'EA'),
                    weight_per_unit=material_data.get('weight_per_unit'),
                    dimensions=material_data.get('dimensions'),
                    reorder_point=material_data.get('reorder_point', 0),
                    max_stock_level=material_data.get('max_stock_level'),
                    preferred_supplier=material_data.get('preferred_supplier'),
                    storage_location=material_data.get('storage_location'),
                    standard_cost=material_data.get('standard_cost'),
                    average_cost=material_data.get('average_cost'),
                    last_cost=material_data.get('last_cost'),
                    expansion_ratio=material_data.get('expansion_ratio'),
                    density_target=material_data.get('density_target'),
                    mold_id=material_data.get('mold_id'),
                    notes=material_data.get('notes', ''),
                    created_by=material_data.get('created_by', 'System')
                )
                
                session.add(material)
                session.flush()  # Get the ID without committing
                
                logger.info(f"Created material: {material.sku}")
                return material
                
        except Exception as e:
            logger.error(f"Failed to create material: {e}")
            return None
    
    def get_material_by_id(self, material_id: UUID) -> Optional[Material]:
        """
        Get material by ID.
        
        Args:
            material_id: UUID of the material
            
        Returns:
            Material object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(Material).filter(
                    Material.id == material_id,
                    Material.deleted_at.is_(None)
                ).first()
        except Exception as e:
            logger.error(f"Failed to get material {material_id}: {e}")
            return None
    
    def get_material_by_sku(self, sku: str) -> Optional[Material]:
        """
        Get material by SKU.
        
        Args:
            sku: Material SKU
            
        Returns:
            Material object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(Material).filter(
                    Material.sku == sku.upper(),
                    Material.deleted_at.is_(None)
                ).first()
        except Exception as e:
            logger.error(f"Failed to get material {sku}: {e}")
            return None
    
    def get_all_materials(self, active_only: bool = True) -> List[Material]:
        """
        Get all materials.
        
        Args:
            active_only: Whether to return only active materials
            
        Returns:
            List of Material objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Material).filter(Material.deleted_at.is_(None))
                
                if active_only:
                    query = query.filter(Material.active == True)
                
                return query.order_by(Material.sku).all()
        except Exception as e:
            logger.error(f"Failed to get materials: {e}")
            return []
    
    def search_materials(self, search_term: str, category: Optional[str] = None) -> List[Material]:
        """
        Search materials by SKU, name, or description.
        
        Args:
            search_term: Search term
            category: Optional category filter
            
        Returns:
            List of matching Material objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Material).filter(Material.deleted_at.is_(None))
                
                # Add search conditions
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    (Material.sku.ilike(search_pattern)) |
                    (Material.name.ilike(search_pattern)) |
                    (Material.description.ilike(search_pattern))
                )
                
                # Add category filter if specified
                if category:
                    query = query.filter(Material.category == category)
                
                return query.order_by(Material.sku).all()
        except Exception as e:
            logger.error(f"Failed to search materials: {e}")
            return []
    
    def update_material(self, material_id: UUID, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing material.
        
        Args:
            material_id: UUID of the material to update
            update_data: Dictionary containing updated fields
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                material = session.query(Material).filter(
                    Material.id == material_id,
                    Material.deleted_at.is_(None)
                ).first()
                
                if not material:
                    logger.warning(f"Material {material_id} not found")
                    return False
                
                # Update fields
                for field, value in update_data.items():
                    if hasattr(material, field) and field not in ['id', 'created_at', 'created_by']:
                        if field == 'sku':
                            material.sku = value.upper()
                        else:
                            setattr(material, field, value)
                
                material.updated_at = datetime.utcnow()
                
                logger.info(f"Updated material: {material.sku}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update material {material_id}: {e}")
            return False
    
    def delete_material(self, material_id: UUID, deleted_by: str) -> bool:
        """
        Soft delete a material.
        
        Args:
            material_id: UUID of the material to delete
            deleted_by: User performing the deletion
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                material = session.query(Material).filter(
                    Material.id == material_id,
                    Material.deleted_at.is_(None)
                ).first()
                
                if not material:
                    logger.warning(f"Material {material_id} not found")
                    return False
                
                material.deleted_at = datetime.utcnow()
                material.active = False
                
                logger.info(f"Deleted material: {material.sku}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete material {material_id}: {e}")
            return False
    
    def get_material_categories(self) -> List[str]:
        """
        Get all unique material categories.
        
        Returns:
            List of category names
        """
        try:
            with self.db_manager.get_session() as session:
                categories = session.query(Material.category).filter(
                    Material.deleted_at.is_(None)
                ).distinct().all()
                
                return [cat[0] for cat in categories]
        except Exception as e:
            logger.error(f"Failed to get material categories: {e}")
            return []
    
    def get_low_stock_materials(self) -> List[Material]:
        """
        Get materials that are below their reorder point.
        
        Returns:
            List of low stock Material objects
        """
        try:
            with self.db_manager.get_session() as session:
                # This would require joining with inventory summary
                # For now, return materials with reorder point > 0
                return session.query(Material).filter(
                    Material.deleted_at.is_(None),
                    Material.active == True,
                    Material.reorder_point > 0
                ).all()
        except Exception as e:
            logger.error(f"Failed to get low stock materials: {e}")
            return []
    
    def get_material_statistics(self) -> Dict[str, Any]:
        """
        Get material statistics for dashboard.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.db_manager.get_session() as session:
                # Total materials
                total_materials = session.query(Material).filter(
                    Material.deleted_at.is_(None),
                    Material.active == True
                ).count()
                
                # Materials by category
                category_counts = {}
                categories = session.query(Material.category).filter(
                    Material.deleted_at.is_(None),
                    Material.active == True
                ).distinct().all()
                
                for category in categories:
                    count = session.query(Material).filter(
                        Material.category == category[0],
                        Material.deleted_at.is_(None),
                        Material.active == True
                    ).count()
                    category_counts[category[0]] = count
                
                # Low stock count (placeholder)
                low_stock_count = len(self.get_low_stock_materials())
                
                return {
                    'total_materials': total_materials,
                    'low_stock_count': low_stock_count,
                    'category_counts': category_counts
                }
                
        except Exception as e:
            logger.error(f"Failed to get material statistics: {e}")
            return {
                'total_materials': 0,
                'low_stock_count': 0,
                'category_counts': {}
            }
