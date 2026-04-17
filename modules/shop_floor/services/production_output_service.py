"""
Production Output Service for XPanda ERP-Lite.
Handles production recording and yield tracking.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from database.models.shop_floor import ProductionOutput, ProductionOutputType
from database.models.production import WorkOrder
from database.models.inventory import Material
from database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class ProductionOutputService:
    """Service for managing production outputs and yield calculations."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def create_production_output(self, work_order_id: int, output_type: str,
                               quantity_produced: Decimal, operator_id: str,
                               operator_name: str, station_id: Optional[str] = None,
                               batch_id: Optional[int] = None,
                               quantity_scrapped: Optional[Decimal] = None,
                               length: Optional[Decimal] = None,
                               width: Optional[Decimal] = None,
                               height: Optional[Decimal] = None,
                               density: Optional[Decimal] = None,
                               lot_number: Optional[str] = None,
                               bead_batch: Optional[str] = None,
                               bead_lot_number: Optional[str] = None,
                               expansion_batch: Optional[str] = None,
                               mold_id: Optional[str] = None,
                               theoretical_yield: Optional[Decimal] = None,
                               notes: Optional[str] = None) -> ProductionOutput:
        """Create a new production output record."""
        try:
            with self.db_manager.get_session() as session:
                # Validate work order
                work_order = session.query(WorkOrder).filter(
                    WorkOrder.id == work_order_id
                ).first()
                if not work_order:
                    raise ValueError(f"Work Order {work_order_id} not found")
                
                # Set default scrap quantity
                if quantity_scrapped is None:
                    quantity_scrapped = Decimal('0')
                
                production_output = ProductionOutput(
                    work_order_id=work_order_id,
                    batch_id=batch_id,
                    output_type=output_type,
                    quantity_produced=quantity_produced,
                    quantity_scrapped=quantity_scrapped,
                    theoretical_yield=theoretical_yield,
                    length=length,
                    width=width,
                    height=height,
                    density=density,
                    lot_number=lot_number,
                    bead_batch=bead_batch,
                    bead_lot_number=bead_lot_number,
                    expansion_batch=expansion_batch,
                    mold_id=mold_id,
                    operator_id=operator_id,
                    operator_name=operator_name,
                    station_id=station_id,
                    timestamp=datetime.now(),
                    notes=notes
                )
                
                # Calculate yield if theoretical yield is provided
                if theoretical_yield:
                    production_output.calculate_yield()
                
                session.add(production_output)
                session.commit()
                session.refresh(production_output)
                
                logger.info(f"Created production output for work order {work_order_id}")
                return production_output
                
        except Exception as e:
            logger.error(f"Error creating production output: {e}")
            raise
    
    def update_production_output(self, output_id: int, **kwargs) -> ProductionOutput:
        """Update an existing production output."""
        try:
            with self.db_manager.get_session() as session:
                production_output = session.query(ProductionOutput).filter(
                    ProductionOutput.id == output_id
                ).first()
                
                if not production_output:
                    raise ValueError(f"Production output {output_id} not found")
                
                # Update allowed fields
                allowed_fields = [
                    'quantity_produced', 'quantity_scrapped', 'theoretical_yield',
                    'length', 'width', 'height', 'density', 'lot_number',
                    'bead_batch', 'bead_lot_number', 'expansion_batch', 'mold_id',
                    'notes', 'quality_status'
                ]
                
                for field, value in kwargs.items():
                    if field in allowed_fields:
                        setattr(production_output, field, value)
                
                # Recalculate yield if theoretical yield is available
                if production_output.theoretical_yield:
                    production_output.calculate_yield()
                
                session.commit()
                session.refresh(production_output)
                
                logger.info(f"Updated production output {output_id}")
                return production_output
                
        except Exception as e:
            logger.error(f"Error updating production output: {e}")
            raise
    
    def get_production_outputs_by_work_order(self, work_order_id: int) -> List[ProductionOutput]:
        """Get all production outputs for a work order."""
        try:
            with self.db_manager.get_session() as session:
                return session.query(ProductionOutput).filter(
                    ProductionOutput.work_order_id == work_order_id
                ).order_by(ProductionOutput.timestamp.desc()).all()
                
        except Exception as e:
            logger.error(f"Error getting production outputs for work order: {e}")
            raise
    
    def get_production_outputs_by_batch(self, batch_id: int) -> List[ProductionOutput]:
        """Get all production outputs for a batch."""
        try:
            with self.db_manager.get_session() as session:
                return session.query(ProductionOutput).filter(
                    ProductionOutput.batch_id == batch_id
                ).order_by(ProductionOutput.timestamp.desc()).all()
                
        except Exception as e:
            logger.error(f"Error getting production outputs for batch: {e}")
            raise
    
    def get_production_outputs_by_date_range(self, start_date: datetime, 
                                           end_date: datetime,
                                           output_type: Optional[str] = None,
                                           operator_id: Optional[str] = None) -> List[ProductionOutput]:
        """Get production outputs within a date range."""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(ProductionOutput).filter(
                    ProductionOutput.timestamp >= start_date,
                    ProductionOutput.timestamp <= end_date
                )
                
                if output_type:
                    query = query.filter(ProductionOutput.output_type == output_type)
                
                if operator_id:
                    query = query.filter(ProductionOutput.operator_id == operator_id)
                
                return query.order_by(ProductionOutput.timestamp.desc()).all()
                
        except Exception as e:
            logger.error(f"Error getting production outputs by date range: {e}")
            raise
    
    def calculate_work_order_yield(self, work_order_id: int) -> Dict[str, Any]:
        """Calculate yield statistics for a work order."""
        try:
            with self.db_manager.get_session() as session:
                outputs = session.query(ProductionOutput).filter(
                    ProductionOutput.work_order_id == work_order_id
                ).all()
                
                if not outputs:
                    return {
                        'total_produced': 0,
                        'total_scrapped': 0,
                        'total_actual': 0,
                        'total_theoretical': 0,
                        'overall_yield_percentage': 0,
                        'output_count': 0
                    }
                
                total_produced = sum(output.quantity_produced for output in outputs)
                total_scrapped = sum(output.quantity_scrapped for output in outputs)
                total_actual = sum(output.actual_yield or 0 for output in outputs)
                total_theoretical = sum(output.theoretical_yield or 0 for output in outputs)
                
                overall_yield = (total_actual / total_theoretical * 100) if total_theoretical > 0 else 0
                
                # Group by output type
                type_breakdown = {}
                for output in outputs:
                    output_type = output.output_type
                    if output_type not in type_breakdown:
                        type_breakdown[output_type] = {
                            'produced': Decimal('0'),
                            'scrapped': Decimal('0'),
                            'actual': Decimal('0'),
                            'theoretical': Decimal('0'),
                            'yield_percentage': Decimal('0')
                        }
                    
                    type_breakdown[output_type]['produced'] += output.quantity_produced
                    type_breakdown[output_type]['scrapped'] += output.quantity_scrapped
                    type_breakdown[output_type]['actual'] += output.actual_yield or 0
                    type_breakdown[output_type]['theoretical'] += output.theoretical_yield or 0
                
                # Calculate yield percentages for each type
                for output_type in type_breakdown:
                    theoretical = type_breakdown[output_type]['theoretical']
                    actual = type_breakdown[output_type]['actual']
                    type_breakdown[output_type]['yield_percentage'] = (
                        (actual / theoretical * 100) if theoretical > 0 else 0
                    )
                
                return {
                    'total_produced': float(total_produced),
                    'total_scrapped': float(total_scrapped),
                    'total_actual': float(total_actual),
                    'total_theoretical': float(total_theoretical),
                    'overall_yield_percentage': float(overall_yield),
                    'output_count': len(outputs),
                    'type_breakdown': {
                        k: {
                            'produced': float(v['produced']),
                            'scrapped': float(v['scrapped']),
                            'actual': float(v['actual']),
                            'theoretical': float(v['theoretical']),
                            'yield_percentage': float(v['yield_percentage'])
                        }
                        for k, v in type_breakdown.items()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error calculating work order yield: {e}")
            raise
    
    def get_foam_block_statistics(self, start_date: datetime, 
                                 end_date: datetime) -> Dict[str, Any]:
        """Get foam block production statistics."""
        try:
            with self.db_manager.get_session() as session:
                outputs = session.query(ProductionOutput).filter(
                    ProductionOutput.output_type == ProductionOutputType.FOAM_BLOCK.value,
                    ProductionOutput.timestamp >= start_date,
                    ProductionOutput.timestamp <= end_date
                ).all()
                
                if not outputs:
                    return {
                        'total_blocks': 0,
                        'total_volume_cubic_feet': 0,
                        'average_density': 0,
                        'density_range': {'min': 0, 'max': 0},
                        'size_distribution': {}
                    }
                
                total_blocks = len(outputs)
                total_volume = sum(output.calculate_volume() or 0 for output in outputs)
                
                # Density statistics
                densities = [output.density for output in outputs if output.density]
                average_density = sum(densities) / len(densities) if densities else 0
                min_density = min(densities) if densities else 0
                max_density = max(densities) if densities else 0
                
                # Size distribution (group by volume ranges)
                size_distribution = {}
                for output in outputs:
                    volume = output.calculate_volume() or 0
                    if volume < 10:
                        size_category = 'Small (<10 ft³)'
                    elif volume < 50:
                        size_category = 'Medium (10-50 ft³)'
                    elif volume < 100:
                        size_category = 'Large (50-100 ft³)'
                    else:
                        size_category = 'X-Large (>100 ft³)'
                    
                    if size_category not in size_distribution:
                        size_distribution[size_category] = 0
                    size_distribution[size_category] += 1
                
                return {
                    'total_blocks': total_blocks,
                    'total_volume_cubic_feet': float(total_volume),
                    'average_density': float(average_density),
                    'density_range': {'min': float(min_density), 'max': float(max_density)},
                    'size_distribution': size_distribution
                }
                
        except Exception as e:
            logger.error(f"Error getting foam block statistics: {e}")
            raise
    
    def get_output_type_options(self) -> List[Dict[str, str]]:
        """Get available output type options."""
        return [
            {'value': ProductionOutputType.FOAM_BLOCK.value, 'label': 'Foam Block'},
            {'value': ProductionOutputType.FABRICATED_PART.value, 'label': 'Fabricated Part'},
            {'value': ProductionOutputType.SCRAP.value, 'label': 'Scrap'},
            {'value': ProductionOutputType.REWORK.value, 'label': 'Rework'}
        ]
    
    def search_production_outputs(self, search_term: str, limit: int = 100) -> List[ProductionOutput]:
        """Search production outputs by various fields."""
        try:
            with self.db_manager.get_session() as session:
                search_pattern = f"%{search_term}%"
                
                return session.query(ProductionOutput).filter(
                    (ProductionOutput.lot_number.ilike(search_pattern)) |
                    (ProductionOutput.bead_batch.ilike(search_pattern)) |
                    (ProductionOutput.expansion_batch.ilike(search_pattern)) |
                    (ProductionOutput.mold_id.ilike(search_pattern)) |
                    (ProductionOutput.operator_name.ilike(search_pattern)) |
                    (ProductionOutput.notes.ilike(search_pattern))
                ).limit(limit).all()
                
        except Exception as e:
            logger.error(f"Error searching production outputs: {e}")
            raise
    
    def get_daily_production_summary(self, date: datetime) -> Dict[str, Any]:
        """Get daily production summary."""
        try:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            with self.db_manager.get_session() as session:
                outputs = session.query(ProductionOutput).filter(
                    ProductionOutput.timestamp >= start_of_day,
                    ProductionOutput.timestamp < end_of_day
                ).all()
                
                # Group by output type
                type_summary = {}
                for output in outputs:
                    output_type = output.output_type
                    if output_type not in type_summary:
                        type_summary[output_type] = {
                            'count': 0,
                            'produced': Decimal('0'),
                            'scrapped': Decimal('0')
                        }
                    
                    type_summary[output_type]['count'] += 1
                    type_summary[output_type]['produced'] += output.quantity_produced
                    type_summary[output_type]['scrapped'] += output.quantity_scrapped
                
                return {
                    'date': date.date().isoformat(),
                    'total_outputs': len(outputs),
                    'type_summary': {
                        k: {
                            'count': v['count'],
                            'produced': float(v['produced']),
                            'scrapped': float(v['scrapped'])
                        }
                        for k, v in type_summary.items()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting daily production summary: {e}")
            raise
