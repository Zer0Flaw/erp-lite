"""
Customer service for XPanda ERP-Lite.
Provides business logic for customer management operations.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from database.models.orders import Customer, CustomerStatus
from database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class CustomerService:
    """Service class for customer operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_customer(self, customer_data: Dict[str, Any]) -> Optional[Customer]:
        """
        Create a new customer.
        
        Args:
            customer_data: Dictionary containing customer information
            
        Returns:
            Created Customer object or None if failed
        """
        try:
            with self.db_manager.get_session() as session:
                # Check if customer code already exists
                existing = session.query(Customer).filter(
                    Customer.customer_code == customer_data['customer_code'].upper(),
                    Customer.deleted_at.is_(None)
                ).first()
                
                if existing:
                    logger.warning(f"Customer with code {customer_data['customer_code']} already exists")
                    return None
                
                # Create new customer
                customer = Customer(
                    customer_code=customer_data['customer_code'].upper(),
                    name=customer_data['name'],
                    company_name=customer_data.get('company_name', ''),
                    contact_person=customer_data.get('contact_person', ''),
                    phone=customer_data.get('phone', ''),
                    email=customer_data.get('email', ''),
                    website=customer_data.get('website', ''),
                    billing_address_line1=customer_data['billing_address_line1'],
                    billing_address_line2=customer_data.get('billing_address_line2', ''),
                    billing_city=customer_data['billing_city'],
                    billing_state=customer_data['billing_state'],
                    billing_postal_code=customer_data['billing_postal_code'],
                    billing_country=customer_data.get('billing_country', 'USA'),
                    shipping_address_line1=customer_data.get('shipping_address_line1', ''),
                    shipping_address_line2=customer_data.get('shipping_address_line2', ''),
                    shipping_city=customer_data.get('shipping_city', ''),
                    shipping_state=customer_data.get('shipping_state', ''),
                    shipping_postal_code=customer_data.get('shipping_postal_code', ''),
                    shipping_country=customer_data.get('shipping_country', ''),
                    customer_type=customer_data.get('customer_type', ''),
                    tax_exempt=customer_data.get('tax_exempt', False),
                    tax_id=customer_data.get('tax_id', ''),
                    credit_limit=Decimal(str(customer_data.get('credit_limit', 0))),
                    payment_terms=customer_data.get('payment_terms', ''),
                    status=customer_data.get('status', CustomerStatus.ACTIVE.value),
                    notes=customer_data.get('notes', ''),
                    created_by=customer_data.get('created_by', 'System')
                )
                
                session.add(customer)
                logger.info(f"Created customer: {customer.customer_code}")
                return customer
                
        except Exception as e:
            logger.error(f"Failed to create customer: {e}")
            return None
    
    def get_customer_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """
        Get customer by ID.
        
        Args:
            customer_id: UUID of the customer
            
        Returns:
            Customer object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(Customer).filter(
                    Customer.id == customer_id,
                    Customer.deleted_at.is_(None)
                ).first()
        except Exception as e:
            logger.error(f"Failed to get customer {customer_id}: {e}")
            return None
    
    def get_customer_by_code(self, customer_code: str) -> Optional[Customer]:
        """
        Get customer by code.
        
        Args:
            customer_code: Customer code
            
        Returns:
            Customer object or None if not found
        """
        try:
            with self.db_manager.get_session() as session:
                return session.query(Customer).filter(
                    Customer.customer_code == customer_code.upper(),
                    Customer.deleted_at.is_(None)
                ).first()
        except Exception as e:
            logger.error(f"Failed to get customer {customer_code}: {e}")
            return None
    
    def get_all_customers(self, active_only: bool = False) -> List[Customer]:
        """
        Get all customers.
        
        Args:
            active_only: Whether to return only active customers
            
        Returns:
            List of Customer objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Customer).filter(
                    Customer.deleted_at.is_(None)
                )
                
                if active_only:
                    query = query.filter(Customer.status == CustomerStatus.ACTIVE.value)
                
                return query.order_by(Customer.customer_code).all()
        except Exception as e:
            logger.error(f"Failed to get customers: {e}")
            return []
    
    def search_customers(self, search_term: str, status_filter: Optional[str] = None) -> List[Customer]:
        """
        Search customers by code, name, or company.
        
        Args:
            search_term: Search term
            status_filter: Optional status filter
            
        Returns:
            List of matching Customer objects
        """
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Customer).filter(
                    Customer.deleted_at.is_(None)
                )
                
                # Add search conditions
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    (Customer.customer_code.ilike(search_pattern)) |
                    (Customer.name.ilike(search_pattern)) |
                    (Customer.company_name.ilike(search_pattern)) |
                    (Customer.contact_person.ilike(search_pattern)) |
                    (Customer.email.ilike(search_pattern))
                )
                
                # Add status filter if specified
                if status_filter:
                    query = query.filter(Customer.status == status_filter)
                
                return query.order_by(Customer.customer_code).all()
        except Exception as e:
            logger.error(f"Failed to search customers: {e}")
            return []
    
    def update_customer(self, customer_id: UUID, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing customer.
        
        Args:
            customer_id: UUID of the customer to update
            update_data: Dictionary containing updated fields
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                customer = session.query(Customer).filter(
                    Customer.id == customer_id,
                    Customer.deleted_at.is_(None)
                ).first()
                
                if not customer:
                    logger.warning(f"Customer {customer_id} not found")
                    return False
                
                # Update customer fields
                for field, value in update_data.items():
                    if hasattr(customer, field) and field not in ['id', 'created_at', 'created_by']:
                        if field == 'customer_code':
                            customer.customer_code = value.upper()
                        elif field in ['credit_limit']:
                            setattr(customer, field, Decimal(str(value)))
                        else:
                            setattr(customer, field, value)
                
                customer.updated_at = datetime.utcnow()
                
                logger.info(f"Updated customer: {customer.customer_code}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update customer {customer_id}: {e}")
            return False
    
    def delete_customer(self, customer_id: UUID, deleted_by: str) -> bool:
        """
        Soft delete a customer.
        
        Args:
            customer_id: UUID of the customer to delete
            deleted_by: User performing the deletion
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                customer = session.query(Customer).filter(
                    Customer.id == customer_id,
                    Customer.deleted_at.is_(None)
                ).first()
                
                if not customer:
                    logger.warning(f"Customer {customer_id} not found")
                    return False
                
                # Check if customer has active orders
                from database.models.orders import SalesOrder
                active_orders = session.query(SalesOrder).filter(
                    SalesOrder.customer_id == customer_id,
                    SalesOrder.status.in_(['Draft', 'Pending', 'Confirmed', 'In Production', 'Ready to Ship'])
                ).count()
                
                if active_orders > 0:
                    logger.warning(f"Cannot delete customer {customer.customer_code} - has {active_orders} active orders")
                    return False
                
                customer.deleted_at = datetime.utcnow()
                
                logger.info(f"Deleted customer: {customer.customer_code}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete customer {customer_id}: {e}")
            return False
    
    def get_customer_statistics(self) -> Dict[str, Any]:
        """
        Get customer statistics for dashboard.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.db_manager.get_session() as session:
                # Total customers
                total_customers = session.query(Customer).filter(
                    Customer.deleted_at.is_(None)
                ).count()
                
                # Active customers
                active_customers = session.query(Customer).filter(
                    Customer.deleted_at.is_(None),
                    Customer.status == CustomerStatus.ACTIVE.value
                ).count()
                
                # Customers by status
                status_counts = {}
                for status in CustomerStatus:
                    count = session.query(Customer).filter(
                        Customer.status == status.value,
                        Customer.deleted_at.is_(None)
                    ).count()
                    status_counts[status.value] = count
                
                # Customers by type
                type_counts = {}
                customer_types = session.query(Customer.customer_type).filter(
                    Customer.customer_type.isnot(None),
                    Customer.deleted_at.is_(None)
                ).distinct().all()
                
                for (customer_type,) in customer_types:
                    count = session.query(Customer).filter(
                        Customer.customer_type == customer_type,
                        Customer.deleted_at.is_(None)
                    ).count()
                    type_counts[customer_type] = count
                
                return {
                    'total_customers': total_customers,
                    'active_customers': active_customers,
                    'status_counts': status_counts,
                    'type_counts': type_counts
                }
                
        except Exception as e:
            logger.error(f"Failed to get customer statistics: {e}")
            return {
                'total_customers': 0,
                'active_customers': 0,
                'status_counts': {},
                'type_counts': {}
            }
    
    def get_customer_options(self) -> List[Dict[str, str]]:
        """
        Get customer options for dropdowns.
        
        Returns:
            List of customer dictionaries with basic info
        """
        try:
            customers = self.get_all_customers(active_only=True)
            
            return [
                {
                    'id': str(customer.id),
                    'customer_code': customer.customer_code,
                    'name': customer.name,
                    'company_name': customer.company_name,
                    'contact_person': customer.contact_person,
                    'email': customer.email,
                    'phone': customer.phone,
                    'customer_type': customer.customer_type,
                    'status': customer.status
                }
                for customer in customers
            ]
            
        except Exception as e:
            logger.error(f"Failed to get customer options: {e}")
            return []
    
    def get_customer_orders_summary(self, customer_id: UUID) -> Dict[str, Any]:
        """
        Get orders summary for a customer.
        
        Args:
            customer_id: UUID of the customer
            
        Returns:
            Dictionary with orders summary
        """
        try:
            with self.db_manager.get_session() as session:
                from database.models.orders import SalesOrder
                
                # Total orders
                total_orders = session.query(SalesOrder).filter(
                    SalesOrder.customer_id == customer_id
                ).count()
                
                # Total amount
                total_amount = session.query(SalesOrder.total_amount).filter(
                    SalesOrder.customer_id == customer_id
                ).scalar() or 0
                
                # Last order date
                last_order = session.query(SalesOrder).filter(
                    SalesOrder.customer_id == customer_id
                ).order_by(SalesOrder.order_date.desc()).first()
                
                last_order_date = last_order.order_date if last_order else None
                
                # Orders by status
                status_counts = {}
                from database.models.orders import OrderStatus
                for status in OrderStatus:
                    count = session.query(SalesOrder).filter(
                        SalesOrder.customer_id == customer_id,
                        SalesOrder.status == status.value
                    ).count()
                    status_counts[status.value] = count
                
                return {
                    'total_orders': total_orders,
                    'total_amount': float(total_amount),
                    'last_order_date': last_order_date.strftime('%Y-%m-%d') if last_order_date else None,
                    'status_counts': status_counts
                }
                
        except Exception as e:
            logger.error(f"Failed to get customer orders summary: {e}")
            return {
                'total_orders': 0,
                'total_amount': 0,
                'last_order_date': None,
                'status_counts': {}
            }
    
    def get_customer_statuses(self) -> List[str]:
        """
        Get all customer status options.
        
        Returns:
            List of status names
        """
        try:
            return [status.value for status in CustomerStatus]
        except Exception as e:
            logger.error(f"Error getting customer statuses: {e}")
            return []
    
    def get_customer_types(self) -> List[str]:
        """
        Get all customer type options.
        
        Returns:
            List of customer type names
        """
        try:
            with self.db_manager.get_session() as session:
                types = session.query(Customer.customer_type).filter(
                    Customer.customer_type.isnot(None),
                    Customer.deleted_at.is_(None)
                ).distinct().all()
                
                return [customer_type for (customer_type,) in types if customer_type]
        except Exception as e:
            logger.error(f"Error getting customer types: {e}")
            return []
