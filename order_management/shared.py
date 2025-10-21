from dataclasses import dataclass
from typing import List


@dataclass
class OrderItem:
    """Represents a single item in an order."""
    product_id: str
    quantity: int
    price: float


@dataclass
class Order:
    """Represents a customer order."""
    order_id: str
    customer_id: str
    items: List[OrderItem]
    total_amount: float


@dataclass
class PaymentResult:
    """Result of payment processing."""
    success: bool
    transaction_id: str
    message: str


@dataclass
class InventoryResult:
    """Result of inventory reservation."""
    success: bool
    reservation_id: str
    message: str


@dataclass
class DeliveryResult:
    """Result of delivery initiation."""
    success: bool
    tracking_number: str
    estimated_delivery_date: str
    message: str
