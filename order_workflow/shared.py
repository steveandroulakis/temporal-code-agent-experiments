from dataclasses import dataclass
from typing import List


@dataclass
class OrderItem:
    """Represents a single item in an order."""
    product_id: str
    product_name: str
    quantity: int
    unit_price: float

    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class Order:
    """Represents a customer order."""
    order_id: str
    customer_name: str
    customer_email: str
    items: List[OrderItem]
    shipping_address: str

    @property
    def total_amount(self) -> float:
        return sum(item.total_price for item in self.items)

    @property
    def requires_approval(self) -> bool:
        return self.total_amount > 1000.0


@dataclass
class PaymentResult:
    """Result of a payment attempt."""
    success: bool
    transaction_id: str
    message: str


@dataclass
class InventoryResult:
    """Result of an inventory reservation attempt."""
    success: bool
    reservation_id: str
    message: str


@dataclass
class DeliveryResult:
    """Result of a delivery attempt."""
    success: bool
    tracking_number: str
    estimated_delivery_date: str
    message: str


@dataclass
class OrderResult:
    """Final result of the order workflow."""
    order_id: str
    status: str  # "completed", "cancelled", "failed"
    payment_result: PaymentResult | None = None
    inventory_result: InventoryResult | None = None
    delivery_result: DeliveryResult | None = None
    message: str = ""
