"""
Batch Tracking Service for XPanda ERP-Lite.
Handles lot traceability and material chain tracking.
"""

import logging
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from database.models.shop_floor import ProductionBatch, BatchType, ProductionOutput
from database.models.production import WorkOrder
from database.models.inventory import Material
from database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class BatchTrackingService:
    """Service for managing production batches and traceability."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def create_production_batch(self, batch_type: str, operator_id: str, operator_name: str,
                              station_id: Optional[str] = None,
                              raw_material_lot: Optional[str] = None,
                              input_batch_id: Optional[int] = None,
                              work_order_id: Optional[int] = None,
                              parameters: Optional[Dict[str, Any]] = None,
                              input_quantity: Optional[Decimal] = None,
                              notes: Optional[str] = None) -> ProductionBatch:
        """Create a new production batch."""
        try:
            with self.db_manager.get_session() as session:
                # Validate input batch if provided
                if input_batch_id:
                    input_batch = session.query(ProductionBatch).filter(
                        ProductionBatch.id == input_batch_id
                    ).first()
                    if not input_batch:
                        raise ValueError(f"Input batch {input_batch_id} not found")
                
                # Validate work order if provided
                if work_order_id:
                    work_order = session.query(WorkOrder).filter(
                        WorkOrder.id == work_order_id
                    ).first()
                    if not work_order:
                        raise ValueError(f"Work Order {work_order_id} not found")
                
                # Generate batch number
                batch_number = self._generate_batch_number(batch_type, date.today(), session)
                
                # Convert parameters to JSON string
                parameters_json = json.dumps(parameters) if parameters else None
                
                production_batch = ProductionBatch(
                    batch_number=batch_number,
                    batch_type=batch_type,
                    raw_material_lot=raw_material_lot,
                    input_batch_id=input_batch_id,
                    work_order_id=work_order_id,
                    start_time=datetime.now(),
                    operator_id=operator_id,
                    operator_name=operator_name,
                    station_id=station_id,
                    parameters=parameters_json,
                    input_quantity=input_quantity,
                    status="active",
                    notes=notes
                )
                
                session.add(production_batch)
                session.commit()
                session.refresh(production_batch)
                
                logger.info(f"Created production batch {batch_number}")
                return production_batch
                
        except Exception as e:
            logger.error(f"Error creating production batch: {e}")
            raise
    
    def complete_batch(self, batch_id: int, output_quantity: Decimal,
                      scrap_quantity: Optional[Decimal] = None,
                      quality_notes: Optional[str] = None) -> ProductionBatch:
        """Complete a production batch."""
        try:
            with self.db_manager.get_session() as session:
                batch = session.query(ProductionBatch).filter(
                    ProductionBatch.id == batch_id
                ).first()
                
                if not batch:
                    raise ValueError(f"Production batch {batch_id} not found")
                
                if batch.status != "active":
                    raise ValueError(f"Batch {batch_id} is not active")
                
                batch.end_time = datetime.now()
                batch.output_quantity = output_quantity
                batch.scrap_quantity = scrap_quantity or Decimal('0')
                batch.status = "completed"
                batch.quality_notes = quality_notes
                batch.calculate_duration()
                
                session.commit()
                session.refresh(batch)
                
                logger.info(f"Completed production batch {batch.batch_number}")
                return batch
                
        except Exception as e:
            logger.error(f"Error completing production batch: {e}")
            raise
    
    def get_batch_by_number(self, batch_number: str) -> Optional[ProductionBatch]:
        """Get a batch by its batch number."""
        try:
            with self.db_manager.get_session() as session:
                return session.query(ProductionBatch).filter(
                    ProductionBatch.batch_number == batch_number
                ).first()
                
        except Exception as e:
            logger.error(f"Error getting batch by number: {e}")
            raise
    
    def get_batch_chain(self, batch_id: int) -> Dict[str, Any]:
        """Get the complete chain of batches for traceability."""
        try:
            with self.db_manager.get_session() as session:
                batch = session.query(ProductionBatch).filter(
                    ProductionBatch.id == batch_id
                ).first()
                
                if not batch:
                    raise ValueError(f"Production batch {batch_id} not found")
                
                # Build chain going backwards (raw materials -> current batch)
                chain = []
                current_batch = batch
                
                while current_batch:
                    chain.append({
                        'id': current_batch.id,
                        'batch_number': current_batch.batch_number,
                        'batch_type': current_batch.batch_type,
                        'raw_material_lot': current_batch.raw_material_lot,
                        'start_time': current_batch.start_time,
                        'end_time': current_batch.end_time,
                        'operator_name': current_batch.operator_name,
                        'station_id': current_batch.station_id,
                        'input_quantity': float(current_batch.input_quantity or 0),
                        'output_quantity': float(current_batch.output_quantity or 0),
                        'scrap_quantity': float(current_batch.scrap_quantity or 0)
                    })
                    
                    # Move to input batch
                    if current_batch.input_batch_id:
                        current_batch = session.query(ProductionBatch).filter(
                            ProductionBatch.id == current_batch.input_batch_id
                        ).first()
                    else:
                        break
                
                # Get outputs from this batch
                outputs = session.query(ProductionOutput).filter(
                    ProductionOutput.batch_id == batch_id
                ).all()
                
                output_info = []
                for output in outputs:
                    output_info.append({
                        'id': output.id,
                        'output_type': output.output_type,
                        'quantity_produced': float(output.quantity_produced),
                        'quantity_scrapped': float(output.quantity_scrapped),
                        'lot_number': output.lot_number,
                        'operator_name': output.operator_name,
                        'timestamp': output.timestamp
                    })
                
                return {
                    'current_batch': {
                        'id': batch.id,
                        'batch_number': batch.batch_number,
                        'batch_type': batch.batch_type,
                        'status': batch.status,
                        'raw_material_lot': batch.raw_material_lot,
                        'work_order_id': batch.work_order_id
                    },
                    'chain': list(reversed(chain)),  # Show from raw materials to current
                    'outputs': output_info
                }
                
        except Exception as e:
            logger.error(f"Error getting batch chain: {e}")
            raise
    
    def trace_material_to_outputs(self, raw_material_lot: str) -> List[Dict[str, Any]]:
        """Trace a raw material lot through to final outputs."""
        try:
            with self.db_manager.get_session() as session:
                # Find all batches that used this raw material
                batches = session.query(ProductionBatch).filter(
                    ProductionBatch.raw_material_lot == raw_material_lot
                ).all()
                
                trace_results = []
                
                for batch in batches:
                    # Get outputs from this batch and any downstream batches
                    outputs = self._get_downstream_outputs(batch.id, session)
                    
                    trace_results.append({
                        'batch_id': batch.id,
                        'batch_number': batch.batch_number,
                        'batch_type': batch.batch_type,
                        'start_time': batch.start_time,
                        'operator_name': batch.operator_name,
                        'outputs': outputs
                    })
                
                return trace_results
                
        except Exception as e:
            logger.error(f"Error tracing material to outputs: {e}")
            raise
    
    def get_batches_by_date_range(self, start_date: datetime, end_date: datetime,
                                 batch_type: Optional[str] = None,
                                 operator_id: Optional[str] = None) -> List[ProductionBatch]:
        """Get batches within a date range."""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(ProductionBatch).filter(
                    ProductionBatch.start_time >= start_date,
                    ProductionBatch.start_time <= end_date
                )
                
                if batch_type:
                    query = query.filter(ProductionBatch.batch_type == batch_type)
                
                if operator_id:
                    query = query.filter(ProductionBatch.operator_id == operator_id)
                
                return query.order_by(ProductionBatch.start_time.desc()).all()
                
        except Exception as e:
            logger.error(f"Error getting batches by date range: {e}")
            raise
    
    def get_batch_statistics(self, start_date: datetime, 
                           end_date: datetime) -> Dict[str, Any]:
        """Get batch statistics for a date range."""
        try:
            with self.db_manager.get_session() as session:
                batches = session.query(ProductionBatch).filter(
                    ProductionBatch.start_time >= start_date,
                    ProductionBatch.start_time <= end_date
                ).all()
                
                if not batches:
                    return {
                        'total_batches': 0,
                        'completed_batches': 0,
                        'active_batches': 0,
                        'average_duration_minutes': 0,
                        'total_input_quantity': 0,
                        'total_output_quantity': 0,
                        'total_scrap_quantity': 0,
                        'overall_yield_percentage': 0,
                        'type_breakdown': {}
                    }
                
                total_batches = len(batches)
                completed_batches = len([b for b in batches if b.status == "completed"])
                active_batches = len([b for b in batches if b.status == "active"])
                
                # Calculate durations for completed batches
                completed_batch_objs = [b for b in batches if b.duration_minutes is not None]
                avg_duration = sum(b.duration_minutes for b in completed_batch_objs) / len(completed_batch_objs) if completed_batch_objs else 0
                
                total_input = sum(b.input_quantity or 0 for b in batches)
                total_output = sum(b.output_quantity or 0 for b in batches)
                total_scrap = sum(b.scrap_quantity or 0 for b in batches)
                
                overall_yield = (total_output / total_input * 100) if total_input > 0 else 0
                
                # Type breakdown
                type_breakdown = {}
                for batch in batches:
                    batch_type = batch.batch_type
                    if batch_type not in type_breakdown:
                        type_breakdown[batch_type] = {
                            'count': 0,
                            'completed': 0,
                            'input_quantity': Decimal('0'),
                            'output_quantity': Decimal('0'),
                            'scrap_quantity': Decimal('0')
                        }
                    
                    type_breakdown[batch_type]['count'] += 1
                    if batch.status == "completed":
                        type_breakdown[batch_type]['completed'] += 1
                    type_breakdown[batch_type]['input_quantity'] += batch.input_quantity or 0
                    type_breakdown[batch_type]['output_quantity'] += batch.output_quantity or 0
                    type_breakdown[batch_type]['scrap_quantity'] += batch.scrap_quantity or 0
                
                return {
                    'total_batches': total_batches,
                    'completed_batches': completed_batches,
                    'active_batches': active_batches,
                    'average_duration_minutes': avg_duration,
                    'total_input_quantity': float(total_input),
                    'total_output_quantity': float(total_output),
                    'total_scrap_quantity': float(total_scrap),
                    'overall_yield_percentage': float(overall_yield),
                    'type_breakdown': {
                        k: {
                            'count': v['count'],
                            'completed': v['completed'],
                            'input_quantity': float(v['input_quantity']),
                            'output_quantity': float(v['output_quantity']),
                            'scrap_quantity': float(v['scrap_quantity'])
                        }
                        for k, v in type_breakdown.items()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting batch statistics: {e}")
            raise
    
    def _generate_batch_number(self, batch_type: str, batch_date: date, session) -> str:
        """Generate a unique batch number."""
        try:
            date_str = batch_date.strftime("%Y%m%d")
            prefix = batch_type.upper()
            
            # Find existing batches for this date and type
            existing_count = session.query(ProductionBatch).filter(
                ProductionBatch.batch_type == batch_type,
                ProductionBatch.start_time >= batch_date,
                ProductionBatch.start_time < batch_date + timedelta(days=1)
            ).count()
            
            sequence = existing_count + 1
            return f"{prefix}-{date_str}-{sequence:03d}"
            
        except Exception as e:
            logger.error(f"Error generating batch number: {e}")
            # Fallback to simple format
            return f"{prefix}-{date_str}-001"
    
    def _get_downstream_outputs(self, batch_id: int, session) -> List[Dict[str, Any]]:
        """Get all outputs from this batch and downstream batches."""
        outputs = []
        
        # Get direct outputs from this batch
        direct_outputs = session.query(ProductionOutput).filter(
            ProductionOutput.batch_id == batch_id
        ).all()
        
        for output in direct_outputs:
            outputs.append({
                'id': output.id,
                'output_type': output.output_type,
                'quantity_produced': float(output.quantity_produced),
                'lot_number': output.lot_number,
                'timestamp': output.timestamp,
                'direct': True
            })
        
        # Get outputs from downstream batches
        downstream_batches = session.query(ProductionBatch).filter(
            ProductionBatch.input_batch_id == batch_id
        ).all()
        
        for downstream_batch in downstream_batches:
            downstream_outputs = self._get_downstream_outputs(downstream_batch.id, session)
            outputs.extend(downstream_outputs)
        
        return outputs
    
    def get_batch_type_options(self) -> List[Dict[str, str]]:
        """Get available batch type options."""
        return [
            {'value': BatchType.EXPANSION.value, 'label': 'Expansion'},
            {'value': BatchType.MOLDING.value, 'label': 'Molding'},
            {'value': BatchType.FABRICATION.value, 'label': 'Fabrication'},
            {'value': BatchType.AGING.value, 'label': 'Aging'}
        ]
    
    def search_batches(self, search_term: str, limit: int = 100) -> List[ProductionBatch]:
        """Search batches by batch number, operator, or notes."""
        try:
            with self.db_manager.get_session() as session:
                search_pattern = f"%{search_term}%"
                
                return session.query(ProductionBatch).filter(
                    (ProductionBatch.batch_number.ilike(search_pattern)) |
                    (ProductionBatch.raw_material_lot.ilike(search_pattern)) |
                    (ProductionBatch.operator_name.ilike(search_pattern)) |
                    (ProductionBatch.notes.ilike(search_pattern))
                ).limit(limit).all()
                
        except Exception as e:
            logger.error(f"Error searching batches: {e}")
            raise
    
    def get_active_batches(self) -> List[ProductionBatch]:
        """Get all currently active batches."""
        try:
            with self.db_manager.get_session() as session:
                return session.query(ProductionBatch).filter(
                    ProductionBatch.status == "active"
                ).order_by(ProductionBatch.start_time.desc()).all()
                
        except Exception as e:
            logger.error(f"Error getting active batches: {e}")
            raise
