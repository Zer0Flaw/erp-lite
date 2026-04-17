"""
Quality service for XPanda ERP-Lite.
Coordinates inspection, NCR, and CAPA operations for complete quality management.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from database.connection import DatabaseManager
from .inspection_service import InspectionService
from .ncr_service import NCRService
from .capa_service import CAPAService

logger = logging.getLogger(__name__)


class QualityService:
    """Main service class for quality operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.inspection_service = InspectionService(db_manager)
        self.ncr_service = NCRService(db_manager)
        self.capa_service = CAPAService(db_manager)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get dashboard data for quality module.
        
        Returns:
            Dictionary with dashboard information
        """
        try:
            # Get inspection statistics
            inspection_stats = self.inspection_service.get_inspection_statistics()
            
            # Get NCR statistics
            ncr_stats = self.ncr_service.get_ncr_statistics()
            
            # Get CAPA statistics
            capa_stats = self.capa_service.get_capa_statistics()
            
            # Get pending items
            pending_inspections = self.inspection_service.get_pending_inspections()
            open_ncrs = self.ncr_service.get_open_ncrs()
            active_capas = self.capa_service.get_active_capas()
            
            # Get overdue items
            overdue_ncrs = self.ncr_service.get_overdue_ncrs()
            overdue_capas = self.capa_service.get_overdue_capas()
            
            # Calculate quality score (simple metric based on recent performance)
            quality_score = self._calculate_quality_score()
            
            # Get recent items
            recent_inspections = self.get_recent_inspections_with_details(5)
            recent_ncrs = self.get_recent_ncrs_with_details(5)
            recent_capas = self.get_recent_capas_with_details(5)
            
            # Calculate summary cards
            summary_cards = {
                'pending_inspections': len(pending_inspections),
                'open_ncrs': ncr_stats['open_ncrs'],
                'active_capas': capa_stats['active_capas'],
                'quality_score': f"{quality_score:.1f}%"
            }
            
            return {
                'summary_cards': summary_cards,
                'inspection_status_counts': inspection_stats['status_counts'],
                'inspection_type_counts': inspection_stats['type_counts'],
                'ncr_status_counts': ncr_stats['status_counts'],
                'ncr_severity_counts': ncr_stats['severity_counts'],
                'capa_status_counts': capa_stats['status_counts'],
                'capa_priority_counts': capa_stats['priority_counts'],
                'pending_inspections': [
                    {
                        'inspection_number': inspection.inspection_number,
                        'inspection_type': inspection.inspection_type,
                        'material_sku': inspection.material_sku,
                        'batch_number': inspection.batch_number,
                        'inspector': inspection.inspector,
                        'inspection_date': inspection.inspection_date.strftime('%Y-%m-%d') if inspection.inspection_date else ''
                    }
                    for inspection in pending_inspections
                ],
                'open_ncrs': [
                    {
                        'ncr_number': ncr.ncr_number,
                        'severity': ncr.severity,
                        'material_sku': ncr.material_sku,
                        'batch_number': ncr.batch_number,
                        'discovery_date': ncr.discovery_date.strftime('%Y-%m-%d') if ncr.discovery_date else '',
                        'reported_by': ncr.reported_by,
                        'days_open': ncr.days_open
                    }
                    for ncr in open_ncrs
                ],
                'active_capas': [
                    {
                        'capa_number': capa.capa_number,
                        'title': capa.title,
                        'status': capa.status,
                        'priority': capa.priority,
                        'assigned_to': capa.assigned_to,
                        'due_date': capa.due_date.strftime('%Y-%m-%d') if capa.due_date else '',
                        'days_overdue': capa.days_overdue
                    }
                    for capa in active_capas
                ],
                'overdue_ncrs': [
                    {
                        'ncr_number': ncr.ncr_number,
                        'severity': ncr.severity,
                        'material_sku': ncr.material_sku,
                        'days_open': ncr.days_open
                    }
                    for ncr in overdue_ncrs
                ],
                'overdue_capas': [
                    {
                        'capa_number': capa.capa_number,
                        'title': capa.title,
                        'priority': capa.priority,
                        'assigned_to': capa.assigned_to,
                        'days_overdue': capa.days_overdue
                    }
                    for capa in overdue_capas
                ],
                'recent_inspections': [
                    {
                        'inspection_number': inspection.inspection_number,
                        'inspection_type': inspection.inspection_type,
                        'status': inspection.status,
                        'material_sku': inspection.material_sku,
                        'batch_number': inspection.batch_number,
                        'inspector': inspection.inspector,
                        'overall_result': inspection.overall_result,
                        'inspection_date': inspection.inspection_date.strftime('%Y-%m-%d') if inspection.inspection_date else ''
                    }
                    for inspection in recent_inspections
                ],
                'recent_ncrs': [
                    {
                        'ncr_number': ncr.ncr_number,
                        'severity': ncr.severity,
                        'status': ncr.status,
                        'material_sku': ncr.material_sku,
                        'batch_number': ncr.batch_number,
                        'discovery_date': ncr.discovery_date.strftime('%Y-%m-%d') if ncr.discovery_date else '',
                        'reported_by': ncr.reported_by,
                        'days_open': ncr.days_open
                    }
                    for ncr in recent_ncrs
                ],
                'recent_capas': [
                    {
                        'capa_number': capa.capa_number,
                        'title': capa.title,
                        'status': capa.status,
                        'priority': capa.priority,
                        'assigned_to': capa.assigned_to,
                        'created_date': capa.created_date.strftime('%Y-%m-%d') if capa.created_date else '',
                        'due_date': capa.due_date.strftime('%Y-%m-%d') if capa.due_date else '',
                        'days_overdue': capa.days_overdue
                    }
                    for capa in recent_capas
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {
                'summary_cards': {
                    'pending_inspections': 0,
                    'open_ncrs': 0,
                    'active_capas': 0,
                    'quality_score': '0.0%'
                },
                'inspection_status_counts': {},
                'inspection_type_counts': {},
                'ncr_status_counts': {},
                'ncr_severity_counts': {},
                'capa_status_counts': {},
                'capa_priority_counts': {},
                'pending_inspections': [],
                'open_ncrs': [],
                'active_capas': [],
                'overdue_ncrs': [],
                'overdue_capas': [],
                'recent_inspections': [],
                'recent_ncrs': [],
                'recent_capas': []
            }
    
    def create_ncr_from_inspection(self, inspection_id: UUID, ncr_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create an NCR from a failed inspection.
        
        Args:
            inspection_id: UUID of the inspection
            ncr_data: Dictionary containing NCR information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Get inspection
            inspection = self.inspection_service.get_inspection_by_id(inspection_id)
            if not inspection:
                return False, "Inspection not found"
            
            # Check if inspection failed
            if inspection.overall_result != 'FAIL':
                return False, "Inspection did not fail - cannot create NCR"
            
            # Set inspection-related fields in NCR data
            ncr_data['inspection_id'] = inspection_id
            ncr_data['material_sku'] = inspection.material_sku
            ncr_data['batch_number'] = inspection.batch_number
            
            # Create NCR
            ncr = self.ncr_service.create_ncr(ncr_data)
            
            if ncr:
                return True, f"NCR {ncr.ncr_number} created successfully from inspection {inspection.inspection_number}"
            else:
                return False, "Failed to create NCR from inspection"
                
        except Exception as e:
            logger.error(f"Failed to create NCR from inspection: {e}")
            return False, f"Error creating NCR from inspection: {e}"
    
    def create_capa_from_ncr(self, ncr_id: UUID, capa_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a CAPA from an NCR.
        
        Args:
            ncr_id: UUID of the NCR
            capa_data: Dictionary containing CAPA information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Get NCR
            ncr = self.ncr_service.get_ncr_by_id(ncr_id)
            if not ncr:
                return False, "NCR not found"
            
            # Set NCR-related fields in CAPA data
            capa_data['ncr_id'] = ncr_id
            capa_data['source_type'] = 'NCR'
            capa_data['source_id'] = ncr_id
            
            # Create CAPA
            capa = self.capa_service.create_capa(capa_data)
            
            if capa:
                return True, f"CAPA {capa.capa_number} created successfully from NCR {ncr.ncr_number}"
            else:
                return False, "Failed to create CAPA from NCR"
                
        except Exception as e:
            logger.error(f"Failed to create CAPA from NCR: {e}")
            return False, f"Error creating CAPA from NCR: {e}"
    
    def get_recent_inspections_with_details(self, limit: int = 10) -> List[Any]:
        """
        Get recent inspections with related information.
        
        Args:
            limit: Maximum number of inspections to return
            
        Returns:
            List of Inspection objects with relationships
        """
        try:
            return self.inspection_service.get_recent_inspections(limit)
        except Exception as e:
            logger.error(f"Failed to get recent inspections: {e}")
            return []
    
    def get_recent_ncrs_with_details(self, limit: int = 10) -> List[Any]:
        """
        Get recent NCRs with related information.
        
        Args:
            limit: Maximum number of NCRs to return
            
        Returns:
            List of NonConformanceReport objects with relationships
        """
        try:
            return self.ncr_service.get_recent_ncrs(limit)
        except Exception as e:
            logger.error(f"Failed to get recent NCRs: {e}")
            return []
    
    def get_recent_capas_with_details(self, limit: int = 10) -> List[Any]:
        """
        Get recent CAPAs with related information.
        
        Args:
            limit: Maximum number of CAPAs to return
            
        Returns:
            List of CAPAAction objects with relationships
        """
        try:
            return self.capa_service.get_recent_capas(limit)
        except Exception as e:
            logger.error(f"Failed to get recent CAPAs: {e}")
            return []
    
    def get_quality_metrics_by_period(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Get quality metrics for a specific period.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with quality metrics
        """
        try:
            # This would calculate various quality metrics for the period
            # For now, return placeholder data
            
            return {
                'period_start': start_date.strftime('%Y-%m-%d'),
                'period_end': end_date.strftime('%Y-%m-%d'),
                'total_inspections': 0,
                'passed_inspections': 0,
                'failed_inspections': 0,
                'acceptance_rate': 0,
                'total_ncrs': 0,
                'critical_ncrs': 0,
                'major_ncrs': 0,
                'minor_ncrs': 0,
                'total_capas': 0,
                'completed_capas': 0,
                'overdue_capas': 0,
                'avg_effectiveness_rating': 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get quality metrics by period: {e}")
            return {
                'period_start': start_date.strftime('%Y-%m-%d'),
                'period_end': end_date.strftime('%Y-%m-%d'),
                'total_inspections': 0,
                'passed_inspections': 0,
                'failed_inspections': 0,
                'acceptance_rate': 0,
                'total_ncrs': 0,
                'critical_ncrs': 0,
                'major_ncrs': 0,
                'minor_ncrs': 0,
                'total_capas': 0,
                'completed_capas': 0,
                'overdue_capas': 0,
                'avg_effectiveness_rating': 0
            }
    
    def get_quality_trends(self, days: int = 30) -> Dict[str, List]:
        """
        Get quality trends over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend data
        """
        try:
            # This would calculate trend data over the specified period
            # For now, return placeholder data
            
            return {
                'dates': [],
                'acceptance_rates': [],
                'ncr_counts': [],
                'capa_counts': []
            }
            
        except Exception as e:
            logger.error(f"Failed to get quality trends: {e}")
            return {
                'dates': [],
                'acceptance_rates': [],
                'ncr_counts': [],
                'capa_counts': []
            }
    
    def get_material_quality_history(self, material_sku: str, limit: int = 20) -> Dict[str, List]:
        """
        Get quality history for a specific material.
        
        Args:
            material_sku: Material SKU
            limit: Maximum number of records to return
            
        Returns:
            Dictionary with quality history
        """
        try:
            # Get inspection history
            inspections = self.inspection_service.search_inspections(material_sku)
            inspection_history = [
                {
                    'inspection_number': insp.inspection_number,
                    'inspection_type': insp.inspection_type,
                    'status': insp.status,
                    'overall_result': insp.overall_result,
                    'acceptance_rate': float(insp.acceptance_rate) if insp.acceptance_rate else 0,
                    'inspection_date': insp.inspection_date.strftime('%Y-%m-%d') if insp.inspection_date else '',
                    'inspector': insp.inspector,
                    'batch_number': insp.batch_number
                }
                for insp in inspections[:limit]
            ]
            
            # Get NCR history
            ncrs = self.ncr_service.get_ncrs_by_material(material_sku)
            ncr_history = [
                {
                    'ncr_number': ncr.ncr_number,
                    'severity': ncr.severity,
                    'status': ncr.status,
                    'discovery_date': ncr.discovery_date.strftime('%Y-%m-%d') if ncr.discovery_date else '',
                    'reported_by': ncr.reported_by,
                    'description': ncr.description[:100] + '...' if len(ncr.description) > 100 else ncr.description,
                    'batch_number': ncr.batch_number
                }
                for ncr in ncrs[:limit]
            ]
            
            return {
                'material_sku': material_sku,
                'inspection_history': inspection_history,
                'ncr_history': ncr_history
            }
            
        except Exception as e:
            logger.error(f"Failed to get material quality history: {e}")
            return {
                'material_sku': material_sku,
                'inspection_history': [],
                'ncr_history': []
            }
    
    def get_quality_score_by_material(self, material_sku: str) -> Dict[str, Any]:
        """
        Get quality score for a specific material.
        
        Args:
            material_sku: Material SKU
            
        Returns:
            Dictionary with quality score information
        """
        try:
            # Get material quality history
            history = self.get_material_quality_history(material_sku, 50)
            
            # Calculate quality score based on recent performance
            inspections = history['inspection_history']
            
            if not inspections:
                return {
                    'material_sku': material_sku,
                    'quality_score': 0,
                    'total_inspections': 0,
                    'passed_inspections': 0,
                    'failed_inspections': 0,
                    'acceptance_rate': 0,
                    'last_inspection_date': None
                }
            
            total_inspections = len(inspections)
            passed_inspections = len([insp for insp in inspections if insp['overall_result'] == 'PASS'])
            failed_inspections = len([insp for insp in inspections if insp['overall_result'] == 'FAIL'])
            
            # Calculate acceptance rate
            acceptance_rate = (passed_inspections / total_inspections * 100) if total_inspections > 0 else 0
            
            # Calculate quality score (acceptance rate is the quality score)
            quality_score = acceptance_rate
            
            # Get last inspection date
            last_inspection_date = inspections[0]['inspection_date'] if inspections else None
            
            return {
                'material_sku': material_sku,
                'quality_score': quality_score,
                'total_inspections': total_inspections,
                'passed_inspections': passed_inspections,
                'failed_inspections': failed_inspections,
                'acceptance_rate': acceptance_rate,
                'last_inspection_date': last_inspection_date
            }
            
        except Exception as e:
            logger.error(f"Failed to get quality score by material: {e}")
            return {
                'material_sku': material_sku,
                'quality_score': 0,
                'total_inspections': 0,
                'passed_inspections': 0,
                'failed_inspections': 0,
                'acceptance_rate': 0,
                'last_inspection_date': None
            }
    
    def _calculate_quality_score(self) -> float:
        """
        Calculate overall quality score.
        
        Returns:
            Quality score as percentage
        """
        try:
            # Get inspection statistics
            inspection_stats = self.inspection_service.get_inspection_statistics()
            
            # Simple quality score based on recent acceptance rate
            acceptance_rate = inspection_stats.get('acceptance_rate', 0)
            
            # Adjust score based on open NCRs and overdue CAPAs
            ncr_stats = self.ncr_service.get_ncr_statistics()
            capa_stats = self.capa_service.get_capa_statistics()
            
            # Deduct points for open issues
            open_ncrs = ncr_stats.get('open_ncrs', 0)
            overdue_capas = capa_stats.get('overdue_capas', 0)
            
            # Simple scoring formula
            quality_score = acceptance_rate
            
            # Deduct points for open issues (max 10 points each)
            quality_score -= min(open_ncrs * 2, 10)
            quality_score -= min(overdue_capas * 3, 10)
            
            # Ensure score is within 0-100 range
            quality_score = max(0, min(100, quality_score))
            
            return quality_score
            
        except Exception as e:
            logger.error(f"Failed to calculate quality score: {e}")
            return 0.0
    
    def get_quality_alerts(self) -> List[Dict[str, Any]]:
        """
        Get quality alerts and warnings.
        
        Returns:
            List of quality alerts
        """
        try:
            alerts = []
            
            # Check for overdue NCRs
            overdue_ncrs = self.ncr_service.get_overdue_ncrs()
            if overdue_ncrs:
                alerts.append({
                    'type': 'warning',
                    'message': f"{len(overdue_ncrs)} overdue NCRs require attention",
                    'severity': 'high',
                    'count': len(overdue_ncrs)
                })
            
            # Check for overdue CAPAs
            overdue_capas = self.capa_service.get_overdue_capas()
            if overdue_capas:
                alerts.append({
                    'type': 'warning',
                    'message': f"{len(overdue_capas)} overdue CAPAs require attention",
                    'severity': 'medium',
                    'count': len(overdue_capas)
                })
            
            # Check for critical NCRs
            critical_ncrs = self.ncr_service.get_ncrs_by_severity('Critical')
            open_critical_ncrs = [ncr for ncr in critical_ncrs if ncr.status == 'Open']
            if open_critical_ncrs:
                alerts.append({
                    'type': 'error',
                    'message': f"{len(open_critical_ncrs)} critical NCRs are open",
                    'severity': 'critical',
                    'count': len(open_critical_ncrs)
                })
            
            # Check for failed inspections
            failed_inspections = self.inspection_service.search_inspections('FAIL')
            recent_failed = [insp for insp in failed_inspections if insp.inspection_date >= date.today()]
            if recent_failed:
                alerts.append({
                    'type': 'warning',
                    'message': f"{len(recent_failed)} inspections failed today",
                    'severity': 'medium',
                    'count': len(recent_failed)
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get quality alerts: {e}")
            return []
