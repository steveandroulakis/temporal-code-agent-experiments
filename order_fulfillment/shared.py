from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class PaymentInfo:
    """Simple payment info."""

    card_number: str
    expiry: str  # MM/YY


@dataclass
class Order:
    """Order details passed to the workflow."""

    order_id: str
    items: List[str]
    payment: PaymentInfo
