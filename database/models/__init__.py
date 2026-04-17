"""
Database models for XPanda ERP-Lite.
Exports all SQLAlchemy model classes.
"""

from database.connection import Base
from .inventory import (
    Material,
    MaterialCategory,
    InventoryTransaction,
    TransactionType,
    AdjustmentReason,
    MaterialSupplier,
    InventorySummary,
    StockAdjustment
)
from .production import (
    BillOfMaterial,
    BillOfMaterialLine,
    WorkOrder,
    ProductionStep,
    MaterialConsumption,
    ProductionSchedule,
    BillOfMaterialStatus,
    WorkOrderStatus,
    WorkOrderPriority,
    ProductionStepStatus
)
from .orders import (
    Customer,
    SalesOrder,
    OrderLine,
    Shipment,
    ShipmentLine,
    CustomerStatus,
    OrderStatus,
    OrderPriority,
    PaymentStatus,
    FulfillmentStatus
)
from .quality import (
    Inspection,
    InspectionLine,
    NonConformanceReport,
    CAPAAction,
    QualityMetric,
    InspectionType,
    InspectionStatus,
    NCRStatus,
    NCRSeverity,
    NCRDisposition,
    CAPAStatus,
    CAPAPriority
)

__all__ = [
    'Base',
    # Inventory models
    'Material',
    'MaterialCategory',
    'InventoryTransaction',
    'TransactionType',
    'AdjustmentReason',
    'MaterialSupplier',
    'InventorySummary',
    'StockAdjustment',
    # Production models
    'BillOfMaterial',
    'BillOfMaterialLine',
    'WorkOrder',
    'ProductionStep',
    'MaterialConsumption',
    'ProductionSchedule',
    # Production enums
    'BillOfMaterialStatus',
    'WorkOrderStatus',
    'WorkOrderPriority',
    'ProductionStepStatus',
    # Orders models
    'Customer',
    'SalesOrder',
    'OrderLine',
    'Shipment',
    'ShipmentLine',
    # Orders enums
    'CustomerStatus',
    'OrderStatus',
    'OrderPriority',
    'PaymentStatus',
    'FulfillmentStatus',
    # Quality models
    'Inspection',
    'InspectionLine',
    'NonConformanceReport',
    'CAPAAction',
    'QualityMetric',
    # Quality enums
    'InspectionType',
    'InspectionStatus',
    'NCRStatus',
    'NCRSeverity',
    'NCRDisposition',
    'CAPAStatus',
    'CAPAPriority'
]