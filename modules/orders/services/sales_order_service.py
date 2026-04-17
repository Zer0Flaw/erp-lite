"""
Sales Order service for XPanda ERP-Lite.
Provides business logic for sales order management operations.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from database.models.orders import (
    SalesOrder, OrderLine, OrderStatus, OrderPriority, 
    PaymentStatus, FulfillmentStatus
)
from database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class SalesOrderService:
    """Service class for sales order operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_sales_order(self, order_data: Dict[str, Any]) -> Optional[SalesOrder]:
        """
        Create a new sales order.
        
        Args:
            order_data: Dictionary containing sales order information
            
        Returns:
            Created SalesOrder object or None if failed
        """
        try:
            with self.db_manager.get_session() as session:
                # Check if order number already exists
                existing = session.query(SalesOrder).filter(
                    SalesOrder.order_number == order_data['order_number'].upper()
                ).first()
                
                if existing:
                    logger.warning(f"Sales order {order_data['order_number']} already exists")
                    return None
                
                # Get customer
                from database.models.orders import Customer
                customer = session.query(Customer).filter(
                    Customer.customer_code == order_data['customer_name'],
                    Customer.deleted_at.is_(None)
                ).first()
                
                if not customer:
                    logger.warning(f"Customer {order_data['customer_name']} not found")
                    return None
                
                # Calculate financial amounts
                subtotal = Decimal(str(order_data.get('subtotal', 0)))
                tax_amount = Decimal(str(order_data.get('tax_amount', 0)))
                shipping_amount = Decimal(str(order_data.get('shipping_amount', 0)))
                total_amount = subtotal + tax_amount + shipping_amount
                
                # Create new sales order
                sales_order = SalesOrder(
                    order_number=order_data['order_number'].upper(),
                    customer_id=customer.id,
                    customer_purchase_order=order_data.get('customer_purchase_order', ''),
                    order_date=self._parse_date(order_data.get('order_date', date.today())),
                    requested_ship_date=self._parse_date(order_data.get('requested_ship_date')),
                    promised_ship_date=self._parse_date(order_data.get('promised_ship_date')),
                    status=order_data.get('status', OrderStatus.DRAFT.value),
                    priority=order_data.get('priority', OrderPriority.NORMAL.value),
                    subtotal=subtotal,
                    tax_amount=tax_amount,
                    shipping_amount=shipping_amount,
                    total_amount=total_amount,
                    paid_amount=Decimal(str(order_data.get('paid_amount', 0))),
                    payment_status=order_data.get('payment_status', PaymentStatus.PENDING.value),
                    payment_method=order_data.get('payment_method', ''),
                    payment_terms=order_data.get('payment_terms', ''),
                    fulfillment_status=order_data.get('fulfillment_status', FulfillmentStatus.PENDING.value),
                    tracking_number=order_data.get('tracking_number', ''),
                    carrier=order_data.get('carrier', ''),
                    sales_rep=order_data.get('sales_rep', ''),
                    notes=order_data.get('notes', ''),
                    internal_notes=order_data.get('internal_notes', ''),
                    created_by=order_data.get('created_by', 'System')
                )
                
                session.add(sales_order)
                session.flush()  # Get the ID without committing
                
                # Create order lines
                order_lines_data = order_data.get('order_lines', [])
                for line_data in order_lines_data:
                    order_line = OrderLine(
                        sales_order_id=sales_order.id,
                        product_sku=line_data['product_sku'],
                        product_name=line_data.get('product_name', ''),
                        product_description=line_data.get('product_description', ''),
                        quantity=Decimal(str(line_data['quantity'])),
                        quantity_shipped=Decimal(str(line_data.get('quantity_shipped', 0))),
                        quantity_backordered=Decimal(str(line_data.get('quantity_backordered', 0))),
                        unit_of_measure=line_data.get('unit_of_measure', 'EA'),
                        unit_price=Decimal(str(line_data['unit_price'])),
                        discount_percentage=Decimal(str(line_data.get('discount_percentage', 0))),
                        line_total=Decimal(str(line_data.get('line_total', 0))),
                        notes=line_data.get('notes', '')
                    )
                    session.add(order_line)
                
                logger.info(f"Created sales order: {sales_order.order_number}")
                return sales_order
                
        except Exception as e:
            logger.error(f"Failed to create sales order: {e}")
            return None
    
    def get_sales_order_by_id(self, order_id: UUID) -> Optional[SalesOrder]:
        """
        Get sales order by ID.
        
        Args:
            order_id: UUID of the sales order
            
        Returns:
            SalesOrder object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(SalesOrder).filter(
                    SalesOrder.id == order_id
                ).first()
        except Exception as e:
            logger.error(f"Failed to get sales order {order_id}: {e}")
            return None
    
    def get_sales_order_by_number(self, order_number: str) -> Optional[SalesOrder]:
        """
        Get sales order by number.
        
        Args:
            order_number: Sales order number
            
        Returns:
            SalesOrder object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(SalesOrder).filter(
                    SalesOrder.order_number == order_number.upper()
                ).first()
        except Exception as e:
            logger.error(f"Failed to get sales order {order_number}: {e}")
            return None
    
    def get_all_sales_orders(self, status_filter: Optional[str] = None) -> List[SalesOrder]:
        """
        Get all sales orders.
        
        Args:
            status_filter: Optional status filter
            
        Returns:
            List of SalesOrder objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(SalesOrder)
                
                if status_filter:
                    query = query.filter(SalesOrder.status == status_filter)
                
                return query.order_by(SalesOrder.order_number).all()
        except Exception as e:
            logger.error(f"Failed to get sales orders: {e}")
            return []
    
    def search_sales_orders(self, search_term: str, status_filter: Optional[str] = None) -> List[SalesOrder]:
        """
        Search sales orders by number, customer, or product.
        
        Args:
            search_term: Search term
            status_filter: Optional status filter
            
        Returns:
            List of matching SalesOrder objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(SalesOrder).join(Customer)
                
                # Add search conditions
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    (SalesOrder.order_number.ilike(search_pattern)) |
                    (Customer.name.ilike(search_pattern)) |
                    (Customer.company_name.ilike(search_pattern)) |
                    (SalesOrder.customer_purchase_order.ilike(search_pattern))
                )
                
                # Add status filter if specified
                if status_filter:
                    query = query.filter(SalesOrder.status == status_filter)
                
                return query.order_by(SalesOrder.order_number).all()
        except Exception as e:
            logger.error(f"Failed to search sales orders: {e}")
            return []
    
    def update_sales_order(self, order_id: UUID, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing sales order.
        
        Args:
            order_id: UUID of the sales order to update
            update_data: Dictionary containing updated fields
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                sales_order = session.query(SalesOrder).filter(
                    SalesOrder.id == order_id
                ).first()
                
                if not sales_order:
                    logger.warning(f"Sales order {order_id} not found")
                    return False
                
                # Update sales order fields
                for field, value in update_data.items():
                    if hasattr(sales_order, field) and field not in ['id', 'created_at', 'created_by', 'order_lines']:
                        if field == 'order_number':
                            sales_order.order_number = value.upper()
                        elif field in ['subtotal', 'tax_amount', 'shipping_amount', 'total_amount', 'paid_amount']:
                            setattr(sales_order, field, Decimal(str(value)))
                        elif field in ['order_date', 'requested_ship_date', 'promised_ship_date', 'actual_ship_date', 'delivery_date']:
                            setattr(sales_order, field, self._parse_date(value))
                        else:
                            setattr(sales_order, field, value)
                
                sales_order.updated_at = datetime.utcnow()
                
                # Update order lines if provided
                if 'order_lines' in update_data:
                    # Remove existing lines
                    session.query(OrderLine).filter(
                        OrderLine.sales_order_id == order_id
                    ).delete()
                    
                    # Add new lines
                    for line_data in update_data['order_lines']:
                        order_line = OrderLine(
                            sales_order_id=sales_order.id,
                            product_sku=line_data['product_sku'],
                            product_name=line_data.get('product_name', ''),
                            product_description=line_data.get('product_description', ''),
                            quantity=Decimal(str(line_data['quantity'])),
                            quantity_shipped=Decimal(str(line_data.get('quantity_shipped', 0))),
                            quantity_backordered=Decimal(str(line_data.get('quantity_backordered', 0))),
                            unit_of_measure=line_data.get('unit_of_measure', 'EA'),
                            unit_price=Decimal(str(line_data['unit_price'])),
                            discount_percentage=Decimal(str(line_data.get('discount_percentage', 0))),
                            line_total=Decimal(str(line_data.get('line_total', 0))),
                            notes=line_data.get('notes', '')
                        )
                        session.add(order_line)
                
                logger.info(f"Updated sales order: {sales_order.order_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update sales order {order_id}: {e}")
            return False
    
    def update_order_status(self, order_id: UUID, new_status: str, updated_by: str) -> bool:
        """
        Update sales order status with proper validation.
        
        Args:
            order_id: UUID of the sales order
            new_status: New status
            updated_by: User making the change
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                sales_order = session.query(SalesOrder).filter(
                    SalesOrder.id == order_id
                ).first()
                
                if not sales_order:
                    logger.warning(f"Sales order {order_id} not found")
                    return False
                
                # Validate status transition
                if not self._is_valid_status_transition(sales_order.status, new_status):
                    logger.warning(f"Invalid status transition from {sales_order.status} to {new_status}")
                    return False
                
                # Update status and related fields
                old_status = sales_order.status
                sales_order.status = new_status
                sales_order.updated_at = datetime.utcnow()
                
                # Handle status-specific updates
                if new_status == OrderStatus.SHIPPED.value:
                    sales_order.actual_ship_date = date.today()
                elif new_status == OrderStatus.DELIVERED.value:
                    sales_order.delivery_date = date.today()
                elif new_status == OrderStatus.CANCELLED.value:
                    # Handle cancellation logic
                    pass
                
                logger.info(f"Updated sales order {sales_order.order_number} status from {old_status} to {new_status}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update sales order status {order_id}: {e}")
            return False
    
    def delete_sales_order(self, order_id: UUID, deleted_by: str) -> bool:
        """
        Delete a sales order (only if in draft status).
        
        Args:
            order_id: UUID of the sales order to delete
            deleted_by: User performing the deletion
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                sales_order = session.query(SalesOrder).filter(
                    SalesOrder.id == order_id
                ).first()
                
                if not sales_order:
                    logger.warning(f"Sales order {order_id} not found")
                    return False
                
                # Only allow deletion of draft orders
                if sales_order.status != OrderStatus.DRAFT.value:
                    logger.warning(f"Cannot delete sales order {sales_order.order_number} - status is {sales_order.status}")
                    return False
                
                # Delete related records
                session.query(OrderLine).filter(
                    OrderLine.sales_order_id == order_id
                ).delete()
                
                # Delete sales order
                session.delete(sales_order)
                
                logger.info(f"Deleted sales order: {sales_order.order_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete sales order {order_id}: {e}")
            return False
    
    def get_sales_order_statistics(self) -> Dict[str, Any]:
        """
        Get sales order statistics for dashboard.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.db_manager.get_session() as session:
                # Total sales orders
                total_orders = session.query(SalesOrder).count()
                
                # Sales orders by status
                status_counts = {}
                for status in OrderStatus:
                    count = session.query(SalesOrder).filter(
                        SalesOrder.status == status.value
                    ).count()
                    status_counts[status.value] = count
                
                # Total sales amount
                total_sales = session.query(SalesOrder.total_amount).scalar() or 0
                
                # Unpaid amount
                unpaid_amount = session.query(SalesOrder.balance_due).filter(
                    SalesOrder.balance_due > 0
                ).scalar() or 0
                
                # Overdue orders
                today = date.today()
                overdue_count = session.query(SalesOrder).filter(
                    SalesOrder.is_overdue == True
                ).count()
                
                return {
                    'total_orders': total_orders,
                    'status_counts': status_counts,
                    'total_sales': float(total_sales),
                    'unpaid_amount': float(unpaid_amount),
                    'overdue_count': overdue_count
                }
                
        except Exception as e:
            logger.error(f"Failed to get sales order statistics: {e}")
            return {
                'total_orders': 0,
                'status_counts': {},
                'total_sales': 0,
                'unpaid_amount': 0,
                'overdue_count': 0
            }
    
    def get_overdue_orders(self) -> List[SalesOrder]:
        """
        Get overdue sales orders.
        
        Returns:
            List of overdue SalesOrder objects
        """
        try:
            with self.db_manager.get_session() as session:
                today = date.today()
                return session.query(SalesOrder).filter(
                    SalesOrder.order_date < today,
                    SalesOrder.balance_due > 0,
                    SalesOrder.payment_status.in_([PaymentStatus.PENDING.value, PaymentStatus.PARTIALLY_PAID.value])
                ).order_by(SalesOrder.order_date).all()
        except Exception as e:
            logger.error(f"Failed to get overdue orders: {e}")
            return []
    
    def get_recent_orders(self, limit: int = 10) -> List[SalesOrder]:
        """
        Get recent sales orders.
        
        Args:
            limit: Maximum number of orders to return
            
        Returns:
            List of recent SalesOrder objects
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(SalesOrder).order_by(
                    SalesOrder.created_at.desc()
                ).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get recent orders: {e}")
            return []
    
    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """Validate sales order status transitions."""
        valid_transitions = {
            OrderStatus.DRAFT.value: [OrderStatus.PENDING.value, OrderStatus.CANCELLED.value],
            OrderStatus.PENDING.value: [OrderStatus.CONFIRMED.value, OrderStatus.CANCELLED.value],
            OrderStatus.CONFIRMED.value: [OrderStatus.IN_PRODUCTION.value, OrderStatus.READY_TO_SHIP.value, OrderStatus.CANCELLED.value],
            OrderStatus.IN_PRODUCTION.value: [OrderStatus.READY_TO_SHIP.value, OrderStatus.CANCELLED.value],
            OrderStatus.READY_TO_SHIP.value: [OrderStatus.SHIPPED.value, OrderStatus.CANCELLED.value],
            OrderStatus.SHIPPED.value: [OrderStatus.DELIVERED.value],
            OrderStatus.DELIVERED.value: [OrderStatus.RETURNED.value],
            OrderStatus.CANCELLED.value: [],  # No transitions from cancelled
            OrderStatus.RETURNED.value: []   # No transitions from returned
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}")
            return None
