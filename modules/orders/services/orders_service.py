"""
Orders service for XPanda ERP-Lite.
Coordinates customer and sales order operations for complete order management.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from database.connection import DatabaseManager
from sqlalchemy import func
from .customer_service import CustomerService
from .sales_order_service import SalesOrderService

logger = logging.getLogger(__name__)


class OrdersService:
    """Main service class for orders operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.customer_service = CustomerService(db_manager)
        self.sales_order_service = SalesOrderService(db_manager)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get dashboard data for orders module.
        
        Returns:
            Dictionary with dashboard information
        """
        try:
            # Get customer statistics
            customer_stats = self.customer_service.get_customer_statistics()
            
            # Get sales order statistics
            order_stats = self.sales_order_service.get_sales_order_statistics()
            
            # Get overdue orders
            overdue_orders = self.sales_order_service.get_overdue_orders()
            
            # Get recent orders
            recent_orders = self.get_recent_orders_with_customers(10)
            
            # Get recent customers
            recent_customers = self.get_recent_customers(10)
            
            # Calculate summary cards
            summary_cards = {
                'active_customers': customer_stats['active_customers'],
                'total_orders': order_stats['total_orders'],
                'pending_shipment': order_stats['status_counts'].get('Ready to Ship', 0),
                'overdue_payments': order_stats['overdue_count']
            }
            
            return {
                'summary_cards': summary_cards,
                'customer_status_counts': customer_stats['status_counts'],
                'order_status_counts': order_stats['status_counts'],
                'overdue_orders': [
                    {
                        'order_number': order.order_number,
                        'customer_name': order.customer.name if order.customer else 'Unknown',
                        'total_amount': float(order.total_amount),
                        'due_date': order.order_date.strftime('%Y-%m-%d') if order.order_date else '',
                        'days_overdue': (date.today() - order.order_date).days if order.order_date else 0
                    }
                    for order in overdue_orders
                ],
                'recent_orders': [
                    {
                        'order_number': order.order_number,
                        'customer_name': order.customer.name if order.customer else 'Unknown',
                        'status': order.status,
                        'priority': order.priority,
                        'total_amount': float(order.total_amount),
                        'payment_status': order.payment_status,
                        'fulfillment_status': order.fulfillment_status,
                        'order_date': order.order_date.strftime('%Y-%m-%d') if order.order_date else ''
                    }
                    for order in recent_orders
                ],
                'recent_customers': [
                    {
                        'customer_code': customer.customer_code,
                        'name': customer.name,
                        'company_name': customer.company_name,
                        'status': customer.status,
                        'customer_type': customer.customer_type,
                        'total_orders': self.get_customer_order_count(customer.id)
                    }
                    for customer in recent_customers
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {
                'summary_cards': {
                    'active_customers': 0,
                    'total_orders': 0,
                    'pending_shipment': 0,
                    'overdue_payments': 0
                },
                'customer_status_counts': {},
                'order_status_counts': {},
                'overdue_orders': [],
                'recent_orders': [],
                'recent_customers': []
            }
    
    def create_sales_order_for_customer(self, customer_id: UUID, order_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a sales order for a customer.
        
        Args:
            customer_id: UUID of the customer
            order_data: Dictionary containing order information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Get customer
            customer = self.customer_service.get_customer_by_id(customer_id)
            if not customer:
                return False, "Customer not found"
            
            # Check if customer is active
            if not customer.is_active:
                return False, "Customer is not active"
            
            # Set customer-related fields in order data
            order_data['customer_name'] = customer.customer_code
            
            # Set default payment terms if not provided
            if not order_data.get('payment_terms'):
                order_data['payment_terms'] = customer.payment_terms or 'NET30'
            
            # Create sales order
            sales_order = self.sales_order_service.create_sales_order(order_data)
            
            if sales_order:
                return True, f"Sales order {sales_order.order_number} created successfully for customer {customer.name}"
            else:
                return False, "Failed to create sales order"
                
        except Exception as e:
            logger.error(f"Failed to create sales order for customer: {e}")
            return False, f"Error creating sales order: {e}"
    
    def get_recent_orders_with_customers(self, limit: int = 10) -> List[Any]:
        """
        Get recent sales orders with customer information.
        
        Args:
            limit: Maximum number of orders to return
            
        Returns:
            List of SalesOrder objects with customer relationships
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(SalesOrder).join(Customer).order_by(
                    SalesOrder.created_at.desc()
                ).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get recent orders: {e}")
            return []
    
    def get_recent_customers(self, limit: int = 10) -> List[Any]:
        """
        Get recent customers.
        
        Args:
            limit: Maximum number of customers to return
            
        Returns:
            List of Customer objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(Customer).filter(
                    Customer.deleted_at.is_(None)
                ).order_by(
                    Customer.created_at.desc()
                ).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get recent customers: {e}")
            return []
    
    def get_customer_order_count(self, customer_id: UUID) -> int:
        """
        Get total number of orders for a customer.
        
        Args:
            customer_id: UUID of the customer
            
        Returns:
            Number of orders
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(SalesOrder).filter(
                    SalesOrder.customer_id == customer_id
                ).count()
        except Exception as e:
            logger.error(f"Failed to get customer order count: {e}")
            return 0
    
    def get_orders_by_date_range(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Get orders within a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of order dictionaries
        """
        try:
            with self.db_manager.get_session() as session:
                orders = session.query(SalesOrder).join(Customer).filter(
                    SalesOrder.order_date >= start_date,
                    SalesOrder.order_date <= end_date
                ).order_by(SalesOrder.order_date).all()
                
                return [
                    {
                        'order_number': order.order_number,
                        'customer_name': order.customer.name if order.customer else 'Unknown',
                        'customer_code': order.customer.customer_code if order.customer else 'Unknown',
                        'status': order.status,
                        'priority': order.priority,
                        'total_amount': float(order.total_amount),
                        'order_date': order.order_date.strftime('%Y-%m-%d') if order.order_date else '',
                        'promised_ship_date': order.promised_ship_date.strftime('%Y-%m-%d') if order.promised_ship_date else '',
                        'payment_status': order.payment_status,
                        'fulfillment_status': order.fulfillment_status
                    }
                    for order in orders
                ]
        except Exception as e:
            logger.error(f"Failed to get orders by date range: {e}")
            return []
    
    def get_sales_by_period(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Get sales statistics for a period.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with sales statistics
        """
        try:
            with self.db_manager.get_session() as session:
                # Total sales amount
                total_sales = session.query(SalesOrder.total_amount).filter(
                    SalesOrder.order_date >= start_date,
                    SalesOrder.order_date <= end_date
                ).scalar() or 0
                
                # Number of orders
                order_count = session.query(SalesOrder).filter(
                    SalesOrder.order_date >= start_date,
                    SalesOrder.order_date <= end_date
                ).count()
                
                # Average order value
                avg_order_value = float(total_sales) / order_count if order_count > 0 else 0
                
                # Top customers (by order count)
                top_customers = session.query(
                    Customer.customer_code,
                    Customer.name,
                    func.count(SalesOrder.id).label('order_count'),
                    func.sum(SalesOrder.total_amount).label('total_sales')
                ).join(SalesOrder).filter(
                    SalesOrder.order_date >= start_date,
                    SalesOrder.order_date <= end_date
                ).group_by(
                    Customer.customer_code,
                    Customer.name
                ).order_by(
                    func.count(SalesOrder.id).desc()
                ).limit(5).all()
                
                return {
                    'period_start': start_date.strftime('%Y-%m-%d'),
                    'period_end': end_date.strftime('%Y-%m-%d'),
                    'total_sales': float(total_sales),
                    'order_count': order_count,
                    'avg_order_value': avg_order_value,
                    'top_customers': [
                        {
                            'customer_code': customer.customer_code,
                            'customer_name': customer.name,
                            'order_count': customer.order_count,
                            'total_sales': float(customer.total_sales)
                        }
                        for customer in top_customers
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get sales by period: {e}")
            return {
                'period_start': start_date.strftime('%Y-%m-%d'),
                'period_end': end_date.strftime('%Y-%m-%d'),
                'total_sales': 0,
                'order_count': 0,
                'avg_order_value': 0,
                'top_customers': []
            }
    
    def get_customer_sales_history(self, customer_id: UUID, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get sales history for a customer.
        
        Args:
            customer_id: UUID of the customer
            limit: Maximum number of orders to return
            
        Returns:
            List of order dictionaries
        """
        try:
            with self.db_manager.get_session() as session:
                orders = session.query(SalesOrder).filter(
                    SalesOrder.customer_id == customer_id
                ).order_by(
                    SalesOrder.order_date.desc()
                ).limit(limit).all()
                
                return [
                    {
                        'order_number': order.order_number,
                        'status': order.status,
                        'total_amount': float(order.total_amount),
                        'order_date': order.order_date.strftime('%Y-%m-%d') if order.order_date else '',
                        'promised_ship_date': order.promised_ship_date.strftime('%Y-%m-%d') if order.promised_ship_date else '',
                        'actual_ship_date': order.actual_ship_date.strftime('%Y-%m-%d') if order.actual_ship_date else '',
                        'payment_status': order.payment_status,
                        'fulfillment_status': order.fulfillment_status,
                        'tracking_number': order.tracking_number
                    }
                    for order in orders
                ]
        except Exception as e:
            logger.error(f"Failed to get customer sales history: {e}")
            return []
    
    def search_orders(self, search_term: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search orders data (customers and sales orders).
        
        Args:
            search_term: Search term
            filters: Optional filters
            
        Returns:
            Dictionary with search results
        """
        try:
            filters = filters or {}
            
            # Search customers
            customer_status_filter = filters.get('customer_status')
            customers = self.customer_service.search_customers(search_term, customer_status_filter)
            
            customer_results = [
                {
                    'id': str(customer.id),
                    'customer_code': customer.customer_code,
                    'name': customer.name,
                    'company_name': customer.company_name,
                    'contact_person': customer.contact_person,
                    'phone': customer.phone,
                    'email': customer.email,
                    'status': customer.status,
                    'customer_type': customer.customer_type
                }
                for customer in customers
            ]
            
            # Search sales orders
            order_status_filter = filters.get('order_status')
            sales_orders = self.sales_order_service.search_sales_orders(search_term, order_status_filter)
            
            sales_order_results = [
                {
                    'id': str(order.id),
                    'order_number': order.order_number,
                    'customer_name': order.customer.name if order.customer else 'Unknown',
                    'customer_code': order.customer.customer_code if order.customer else 'Unknown',
                    'status': order.status,
                    'priority': order.priority,
                    'total_amount': float(order.total_amount),
                    'payment_status': order.payment_status,
                    'fulfillment_status': order.fulfillment_status,
                    'order_date': order.order_date.strftime('%Y-%m-%d') if order.order_date else '',
                    'promised_ship_date': order.promised_ship_date.strftime('%Y-%m-%d') if order.promised_ship_date else ''
                }
                for order in sales_orders
            ]
            
            return {
                'customers': customer_results,
                'sales_orders': sales_order_results
            }
            
        except Exception as e:
            logger.error(f"Failed to search orders data: {e}")
            return {'customers': [], 'sales_orders': []}
    
    def get_customer_options(self) -> List[Dict[str, str]]:
        """
        Get customer options for dropdowns.
        
        Returns:
            List of customer dictionaries with basic info
        """
        try:
            return self.customer_service.get_customer_options()
        except Exception as e:
            logger.error(f"Failed to get customer options: {e}")
            return []
    
    def get_order_statistics(self, order_id: UUID) -> Dict[str, Any]:
        """
        Get detailed statistics for a sales order.
        
        Args:
            order_id: UUID of the sales order
            
        Returns:
            Dictionary with order statistics
        """
        try:
            with self.db_manager.get_session() as session:
                order = session.query(SalesOrder).filter(
                    SalesOrder.id == order_id
                ).first()
                
                if not order:
                    return {}
                
                # Order line statistics
                order_lines = session.query(OrderLine).filter(
                    OrderLine.sales_order_id == order_id
                ).all()
                
                total_quantity = sum(line.quantity for line in order_lines)
                total_shipped = sum(line.quantity_shipped for line in order_lines)
                total_backordered = sum(line.quantity_backordered for line in order_lines)
                
                # Calculate fulfillment percentage
                fulfillment_percentage = (total_shipped / total_quantity * 100) if total_quantity > 0 else 0
                
                return {
                    'order_number': order.order_number,
                    'total_amount': float(order.total_amount),
                    'balance_due': float(order.balance_due),
                    'total_lines': len(order_lines),
                    'total_quantity': float(total_quantity),
                    'total_shipped': float(total_shipped),
                    'total_backordered': float(total_backordered),
                    'fulfillment_percentage': fulfillment_percentage,
                    'days_since_order': (date.today() - order.order_date).days if order.order_date else 0,
                    'days_overdue': (date.today() - order.order_date).days if order.is_overdue and order.order_date else 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get order statistics: {e}")
            return {}
    
    def update_order_fulfillment(self, order_id: UUID, fulfillment_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update order fulfillment information.
        
        Args:
            order_id: UUID of the order
            fulfillment_data: Dictionary containing fulfillment information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with self.db_manager.get_session() as session:
                order = session.query(SalesOrder).filter(
                    SalesOrder.id == order_id
                ).first()
                
                if not order:
                    return False, "Order not found"
                
                # Update fulfillment information
                order.tracking_number = fulfillment_data.get('tracking_number', order.tracking_number)
                order.carrier = fulfillment_data.get('carrier', order.carrier)
                order.fulfillment_status = fulfillment_data.get('fulfillment_status', order.fulfillment_status)
                order.actual_ship_date = self._parse_date(fulfillment_data.get('actual_ship_date'))
                
                # Update order lines if provided
                if 'order_lines' in fulfillment_data:
                    for line_update in fulfillment_data['order_lines']:
                        order_line = session.query(OrderLine).filter(
                            OrderLine.id == line_update.get('id')
                        ).first()
                        
                        if order_line:
                            order_line.quantity_shipped = Decimal(str(line_update.get('quantity_shipped', order_line.quantity_shipped)))
                            order_line.quantity_backordered = Decimal(str(line_update.get('quantity_backordered', order_line.quantity_backordered)))
                
                # Update order status if fully shipped
                if order.fulfillment_status == FulfillmentStatus.FULFILLED.value:
                    order.status = OrderStatus.SHIPPED.value
                
                logger.info(f"Updated fulfillment for order {order.order_number}")
                return True, f"Fulfillment updated for order {order.order_number}"
                
        except Exception as e:
            logger.error(f"Failed to update order fulfillment: {e}")
            return False, f"Error updating fulfillment: {e}"
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}")
            return None
