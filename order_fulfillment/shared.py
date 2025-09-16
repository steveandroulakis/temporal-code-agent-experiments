"""Shared dataclasses and helper utilities for the order fulfillment sample."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


@dataclass
class OrderItem:
    """A single line item from an order."""

    sku: str
    quantity: int


@dataclass
class PaymentDetails:
    """Payment information submitted with an order."""

    card_number: str
    expiry_month: int
    expiry_year: int
    cardholder: str


@dataclass
class Order:
    """All information required to fulfill an order."""

    order_id: str
    email: str
    payment: PaymentDetails
    items: List[OrderItem] = field(default_factory=list)
    simulate_inventory_downtime: bool = False
    approval_timeout_seconds: int = 30


class OrderStatus(str, Enum):
    """Lifecycle states for the order workflow."""

    CREATED = "CREATED"
    PAYMENT_PROCESSED = "PAYMENT_PROCESSED"
    INVENTORY_RESERVED = "INVENTORY_RESERVED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    APPROVED = "APPROVED"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"
    FULFILLED = "FULFILLED"


@dataclass
class FulfillmentResult:
    """Result returned by the workflow when it completes."""

    order_id: str
    status: OrderStatus
    message: str
    delivery_receipt: Optional[str] = None
    payment_authorization: Optional[str] = None
    inventory_reservation: Optional[str] = None

    def __post_init__(self) -> None:
        # When results are deserialized from JSON the enum may arrive as a string.
        if isinstance(self.status, str):
            self.status = OrderStatus(self.status)
        elif isinstance(self.status, list):  # defensive guard for JSON arrays
            self.status = OrderStatus("".join(self.status))


def credit_card_is_expired(payment: PaymentDetails, *, now: Optional[datetime] = None) -> bool:
    """Return ``True`` if the payment method has expired."""

    reference = now or datetime.now(timezone.utc)
    # Credit cards expire at the *end* of the expiry month.
    # Advance to the following month and compare.
    if payment.expiry_month == 12:
        expiry_month = 1
        expiry_year = payment.expiry_year + 1
    else:
        expiry_month = payment.expiry_month + 1
        expiry_year = payment.expiry_year
    expiry_boundary = datetime(expiry_year, expiry_month, 1, tzinfo=timezone.utc)
    return reference >= expiry_boundary
