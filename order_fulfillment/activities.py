"""Activity implementations for the order fulfillment sample."""

from __future__ import annotations

import asyncio
import random
from temporalio import activity
from temporalio.exceptions import ApplicationError

from shared import Order, OrderItem, credit_card_is_expired


@activity.defn
async def process_payment(order: Order) -> str:
    """Validate and process a payment for the provided order."""

    activity.logger.info("Processing payment for %s", order.order_id)
    if credit_card_is_expired(order.payment):
        raise ApplicationError(
            "Payment authorization failed: credit card expired",
            type="PaymentValidationError",
        )

    await asyncio.sleep(0.5)
    authorization = f"AUTH-{random.randint(100_000, 999_999)}"
    activity.logger.info("Payment processed for %s", order.order_id)
    return authorization


@activity.defn
async def reserve_inventory(order_id: str, items: list[OrderItem], simulate_downtime: bool) -> str:
    """Reserve inventory for the items in the order."""

    activity.logger.info("Reserving inventory for %s", order_id)
    await asyncio.sleep(0.5)
    if simulate_downtime:
        raise ApplicationError(
            "Inventory service unavailable. Please try again later.",
            type="InventoryServiceDown",
        )

    reservation_code = f"INV-{random.randint(1000, 9999)}"
    activity.logger.info("Inventory reserved for %s", order_id)
    return reservation_code


@activity.defn
async def deliver_order(order_id: str) -> str:
    """Simulate order delivery."""

    activity.logger.info("Delivering order %s", order_id)
    await asyncio.sleep(0.5)
    tracking_number = f"TRACK-{random.randint(10_000, 99_999)}"
    activity.logger.info("Order %s delivered with tracking %s", order_id, tracking_number)
    return tracking_number
