"""Activity definitions for the order fulfillment sample."""

import asyncio
from temporalio import activity

from shared import Order


@activity.defn
async def process_payment(order: Order) -> str:
    """Validate and process payment details."""
    if order.cc_expiry <= "12/23":
        raise ValueError("credit card expired")
    await asyncio.sleep(1)
    return "payment processed"


@activity.defn
async def reserve_inventory(order: Order) -> str:
    """Reserve inventory for the order.

    Uncomment the next line to simulate an inventory service outage.
    """
    # raise ConnectionError("inventory service unavailable")
    await asyncio.sleep(1)
    return "inventory reserved"


@activity.defn
async def deliver_order(order: Order) -> str:
    """Deliver the order."""
    await asyncio.sleep(1)
    return "order delivered"
