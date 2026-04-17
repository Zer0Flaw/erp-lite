"""
Orders controller for XPanda ERP-Lite.
Bridges UI components with orders services and handles business logic coordination.
"""

import logging
from typing import List, Optional, Dict, Any, Callable
from uuid import UUID
from datetime import date

from database.connection import DatabaseManager
from ..services.orders_service import OrdersService
from ..services.customer_service import CustomerService
from ..services.sales_order_service import SalesOrderService

logger = logging.getLogger(__name__)


class OrdersController:
    """Controller class for orders operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.orders_service = OrdersService(db_manager)
        self.customer_service = CustomerService(db_manager)
        self.sales_order_service = SalesOrderService(db_manager)
        
        # Callbacks for UI updates
        self._data_changed_callbacks: List[Callable] = []
        self._status_message_callbacks: List[Callable[[str, int], None]] = []
    
    def register_data_changed_callback(self, callback: Callable) -> None:
        """Register a callback for data change notifications."""
        self._data_changed_callbacks.append(callback)
    
    def register_status_message_callback(self, callback: Callable[[str, int], None]) -> None:
        """Register a callback for status message notifications."""
        self._status_message_callbacks.append(callback)
    
    def _notify_data_changed(self) -> None:
        """Notify all registered callbacks that data has changed."""
        for callback in self._data_changed_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in data changed callback: {e}")
    
    def _show_status_message(self, message: str, timeout: int = 3000) -> None:
        """Show status message through registered callbacks."""
        for callback in self._status_message_callbacks:
            try:
                callback(message, timeout)
            except Exception as e:
                logger.error(f"Error in status message callback: {e}")
    
    # Customer Management Methods
    
    def create_customer(self, customer_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a new customer.
        
        Args:
            customer_data: Dictionary containing customer information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate required fields
            required_fields = ['customer_code', 'name', 'billing_address_line1', 'billing_city', 'billing_state', 'billing_postal_code', 'created_by']
            missing_fields = [field for field in required_fields if field not in customer_data]
            
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
            
            # Create customer
            customer = self.customer_service.create_customer(customer_data)
            
            if customer:
                self._notify_data_changed()
                self._show_status_message(f"Customer '{customer.customer_code}' created successfully")
                return True, f"Customer '{customer.customer_code}' created successfully"
            else:
                return False, "Failed to create customer"
                
        except Exception as e:
            logger.error(f"Error creating customer: {e}")
            return False, f"Error creating customer: {e}"
    
    def update_customer(self, customer_id: UUID, update_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update an existing customer.
        
        Args:
            customer_id: UUID of the customer to update
            update_data: Dictionary containing updated fields
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.customer_service.update_customer(customer_id, update_data)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("Customer updated successfully")
                return True, "Customer updated successfully"
            else:
                return False, "Failed to update customer"
                
        except Exception as e:
            logger.error(f"Error updating customer: {e}")
            return False, f"Error updating customer: {e}"
    
    def delete_customer(self, customer_id: UUID, deleted_by: str) -> Tuple[bool, str]:
        """
        Delete a customer.
        
        Args:
            customer_id: UUID of the customer to delete
            deleted_by: User performing the deletion
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.customer_service.delete_customer(customer_id, deleted_by)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("Customer deleted successfully")
                return True, "Customer deleted successfully"
            else:
                return False, "Failed to delete customer - may have active orders"
                
        except Exception as e:
            logger.error(f"Error deleting customer: {e}")
            return False, f"Error deleting customer: {e}"
    
    def get_customer_by_id(self, customer_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get customer details by ID.
        
        Args:
            customer_id: UUID of the customer
            
        Returns:
            Customer dictionary or None if not found
        """
        try:
            customer = self.customer_service.get_customer_by_id(customer_id)
            if customer:
                return {
                    'id': str(customer.id),
                    'customer_code': customer.customer_code,
                    'name': customer.name,
                    'company_name': customer.company_name or '',
                    'contact_person': customer.contact_person or '',
                    'phone': customer.phone or '',
                    'email': customer.email or '',
                    'website': customer.website or '',
                    'billing_address_line1': customer.billing_address_line1,
                    'billing_address_line2': customer.billing_address_line2 or '',
                    'billing_city': customer.billing_city,
                    'billing_state': customer.billing_state,
                    'billing_postal_code': customer.billing_postal_code,
                    'billing_country': customer.billing_country,
                    'shipping_address_line1': customer.shipping_address_line1 or '',
                    'shipping_address_line2': customer.shipping_address_line2 or '',
                    'shipping_city': customer.shipping_city or '',
                    'shipping_state': customer.shipping_state or '',
                    'shipping_postal_code': customer.shipping_postal_code or '',
                    'shipping_country': customer.shipping_country or '',
                    'customer_type': customer.customer_type or '',
                    'tax_exempt': customer.tax_exempt,
                    'tax_id': customer.tax_id or '',
                    'credit_limit': float(customer.credit_limit) if customer.credit_limit else 0,
                    'payment_terms': customer.payment_terms or '',
                    'status': customer.status,
                    'notes': customer.notes or ''
                }
            return None
        except Exception as e:
            logger.error(f"Error getting customer {customer_id}: {e}")
            return None
    
    def search_customers(self, search_term: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search customers.
        
        Args:
            search_term: Search term
            status_filter: Optional status filter
            
        Returns:
            List of customer dictionaries
        """
        try:
            customers = self.customer_service.search_customers(search_term, status_filter)
            
            return [
                {
                    'id': str(customer.id),
                    'customer_code': customer.customer_code,
                    'name': customer.name,
                    'company_name': customer.company_name or '',
                    'contact_person': customer.contact_person or '',
                    'phone': customer.phone or '',
                    'email': customer.email or '',
                    'status': customer.status,
                    'customer_type': customer.customer_type or '',
                    'updated_at': customer.updated_at.strftime('%Y-%m-%d') if customer.updated_at else None
                }
                for customer in customers
            ]
        except Exception as e:
            logger.error(f"Error searching customers: {e}")
            return []
    
    # Sales Order Management Methods
    
    def create_sales_order(self, order_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create a new sales order.
        
        Args:
            order_data: Dictionary containing sales order information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate required fields
            required_fields = ['order_number', 'customer_name', 'order_lines', 'created_by']
            missing_fields = [field for field in required_fields if field not in order_data]
            
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
            
            # Create sales order
            sales_order = self.sales_order_service.create_sales_order(order_data)
            
            if sales_order:
                self._notify_data_changed()
                self._show_status_message(f"Sales order '{sales_order.order_number}' created successfully")
                return True, f"Sales order '{sales_order.order_number}' created successfully"
            else:
                return False, "Failed to create sales order"
                
        except Exception as e:
            logger.error(f"Error creating sales order: {e}")
            return False, f"Error creating sales order: {e}"
    
    def update_sales_order(self, order_id: UUID, update_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update an existing sales order.
        
        Args:
            order_id: UUID of the sales order to update
            update_data: Dictionary containing updated fields
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.sales_order_service.update_sales_order(order_id, update_data)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("Sales order updated successfully")
                return True, "Sales order updated successfully"
            else:
                return False, "Failed to update sales order"
                
        except Exception as e:
            logger.error(f"Error updating sales order: {e}")
            return False, f"Error updating sales order: {e}"
    
    def update_order_status(self, order_id: UUID, new_status: str, updated_by: str) -> Tuple[bool, str]:
        """
        Update sales order status.
        
        Args:
            order_id: UUID of the sales order
            new_status: New status
            updated_by: User making the change
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.sales_order_service.update_order_status(order_id, new_status, updated_by)
            
            if success:
                self._notify_data_changed()
                self._show_status_message(f"Order status updated to {new_status}")
                return True, f"Order status updated to {new_status}"
            else:
                return False, "Failed to update order status"
                
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            return False, f"Error updating order status: {e}"
    
    def delete_sales_order(self, order_id: UUID, deleted_by: str) -> Tuple[bool, str]:
        """
        Delete a sales order.
        
        Args:
            order_id: UUID of the sales order to delete
            deleted_by: User performing the deletion
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            success = self.sales_order_service.delete_sales_order(order_id, deleted_by)
            
            if success:
                self._notify_data_changed()
                self._show_status_message("Sales order deleted successfully")
                return True, "Sales order deleted successfully"
            else:
                return False, "Failed to delete sales order - may not be in draft status"
                
        except Exception as e:
            logger.error(f"Error deleting sales order: {e}")
            return False, f"Error deleting sales order: {e}"
    
    def get_sales_order_by_id(self, order_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get sales order details by ID.
        
        Args:
            order_id: UUID of the sales order
            
        Returns:
            Sales order dictionary or None if not found
        """
        try:
            sales_order = self.sales_order_service.get_sales_order_by_id(order_id)
            if sales_order:
                return {
                    'id': str(sales_order.id),
                    'order_number': sales_order.order_number,
                    'customer_id': str(sales_order.customer_id) if sales_order.customer_id else None,
                    'customer_name': sales_order.customer.name if sales_order.customer else 'Unknown',
                    'customer_purchase_order': sales_order.customer_purchase_order or '',
                    'order_date': sales_order.order_date.strftime('%Y-%m-%d') if sales_order.order_date else None,
                    'requested_ship_date': sales_order.requested_ship_date.strftime('%Y-%m-%d') if sales_order.requested_ship_date else None,
                    'promised_ship_date': sales_order.promised_ship_date.strftime('%Y-%m-%d') if sales_order.promised_ship_date else None,
                    'actual_ship_date': sales_order.actual_ship_date.strftime('%Y-%m-%d') if sales_order.actual_ship_date else None,
                    'delivery_date': sales_order.delivery_date.strftime('%Y-%m-%d') if sales_order.delivery_date else None,
                    'status': sales_order.status,
                    'priority': sales_order.priority,
                    'subtotal': float(sales_order.subtotal),
                    'tax_amount': float(sales_order.tax_amount),
                    'shipping_amount': float(sales_order.shipping_amount),
                    'total_amount': float(sales_order.total_amount),
                    'paid_amount': float(sales_order.paid_amount),
                    'payment_status': sales_order.payment_status,
                    'payment_method': sales_order.payment_method or '',
                    'payment_terms': sales_order.payment_terms or '',
                    'fulfillment_status': sales_order.fulfillment_status,
                    'tracking_number': sales_order.tracking_number or '',
                    'carrier': sales_order.carrier or '',
                    'sales_rep': sales_order.sales_rep or '',
                    'notes': sales_order.notes or '',
                    'internal_notes': sales_order.internal_notes or '',
                    'order_lines': [
                        {
                            'id': str(line.id),
                            'product_sku': line.product_sku,
                            'product_name': line.product_name,
                            'product_description': line.product_description or '',
                            'quantity': float(line.quantity),
                            'quantity_shipped': float(line.quantity_shipped),
                            'quantity_backordered': float(line.quantity_backordered),
                            'unit_of_measure': line.unit_of_measure,
                            'unit_price': float(line.unit_price),
                            'discount_percentage': float(line.discount_percentage),
                            'line_total': float(line.line_total),
                            'notes': line.notes or ''
                        }
                        for line in sales_order.order_lines
                    ]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting sales order {order_id}: {e}")
            return None
    
    def search_sales_orders(self, search_term: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search sales orders.
        
        Args:
            search_term: Search term
            status_filter: Optional status filter
            
        Returns:
            List of sales order dictionaries
        """
        try:
            sales_orders = self.sales_order_service.search_sales_orders(search_term, status_filter)
            
            return [
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
                    'order_date': order.order_date.strftime('%Y-%m-%d') if order.order_date else None,
                    'promised_ship_date': order.promised_ship_date.strftime('%Y-%m-%d') if order.promised_ship_date else None
                }
                for order in sales_orders
            ]
        except Exception as e:
            logger.error(f"Error searching sales orders: {e}")
            return []
    
    # Dashboard and Reporting Methods
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get dashboard data for orders module.
        
        Returns:
            Dictionary with dashboard information
        """
        try:
            return self.orders_service.get_dashboard_data()
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
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
    
    def get_customer_options(self) -> List[Dict[str, str]]:
        """
        Get customer options for dropdowns.
        
        Returns:
            List of customer dictionaries with basic info
        """
        try:
            return self.customer_service.get_customer_options()
        except Exception as e:
            logger.error(f"Error getting customer options: {e}")
            return []
    
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
            success, message = self.orders_service.create_sales_order_for_customer(customer_id, order_data)
            
            if success:
                self._notify_data_changed()
                self._show_status_message(message)
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error creating sales order for customer: {e}")
            return False, f"Error creating sales order for customer: {e}"
    
    def get_order_statistics(self, order_id: UUID) -> Dict[str, Any]:
        """
        Get order statistics for a sales order.
        
        Args:
            order_id: UUID of the sales order
            
        Returns:
            Dictionary with order statistics
        """
        try:
            return self.orders_service.get_order_statistics(order_id)
        except Exception as e:
            logger.error(f"Error getting order statistics: {e}")
            return {}
    
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
            return self.orders_service.get_orders_by_date_range(start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting orders by date range: {e}")
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
            return self.orders_service.get_sales_by_period(start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting sales by period: {e}")
            return {
                'period_start': start_date.strftime('%Y-%m-%d'),
                'period_end': end_date.strftime('%Y-%m-%d'),
                'total_sales': 0,
                'order_count': 0,
                'avg_order_value': 0,
                'top_customers': []
            }
    
    def get_customer_statuses(self) -> List[str]:
        """
        Get all customer status options.
        
        Returns:
            List of status names
        """
        try:
            return self.customer_service.get_customer_statuses()
        except Exception as e:
            logger.error(f"Error getting customer statuses: {e}")
            return []
    
    def get_order_statuses(self) -> List[str]:
        """
        Get all sales order status options.
        
        Returns:
            List of status names
        """
        try:
            from database.models.orders import OrderStatus
            return [status.value for status in OrderStatus]
        except Exception as e:
            logger.error(f"Error getting order statuses: {e}")
            return []
    
    def get_order_priorities(self) -> List[str]:
        """
        Get all sales order priority options.
        
        Returns:
            List of priority names
        """
        try:
            from database.models.orders import OrderPriority
            return [priority.value for priority in OrderPriority]
        except Exception as e:
            logger.error(f"Error getting order priorities: {e}")
            return []
    
    def get_payment_statuses(self) -> List[str]:
        """
        Get all payment status options.
        
        Returns:
            List of payment status names
        """
        try:
            from database.models.orders import PaymentStatus
            return [status.value for status in PaymentStatus]
        except Exception as e:
            logger.error(f"Error getting payment statuses: {e}")
            return []
    
    def get_fulfillment_statuses(self) -> List[str]:
        """
        Get all fulfillment status options.
        
        Returns:
            List of fulfillment status names
        """
        try:
            from database.models.orders import FulfillmentStatus
            return [status.value for status in FulfillmentStatus]
        except Exception as e:
            logger.error(f"Error getting fulfillment statuses: {e}")
            return []
