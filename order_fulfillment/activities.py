from __future__ import annotations

import os
from datetime import datetime

from temporalio import activity

from shared import Order, PaymentInfo


@activity.defn
async def process_payment(payment: PaymentInfo) -> str:
    """Charge the customer's credit card."""

    exp = datetime.strptime(payment.expiry, "%m/%y")
    now = datetime.now()
    if exp < now.replace(day=1, hour=0, minute=0, second=0, microsecond=0):
        raise RuntimeError("credit card expired")
    # Fake processing
    return "payment processed"


@activity.defn
async def reserve_inventory(items: list[str]) -> str:
    """Reserve items in inventory."""

    if os.getenv("INVENTORY_DOWN"):
        raise RuntimeError("inventory service unavailable")
    return f"reserved {len(items)} items"


@activity.defn
async def deliver_order(order: Order) -> str:
    """Deliver the order."""

    return f"delivered order {order.order_id}"
