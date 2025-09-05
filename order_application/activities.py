import asyncio
from datetime import datetime
from temporalio import activity
from shared import Order


@activity.defn
async def process_payment(order: Order) -> str:
    """Charge the customer's credit card."""
    await asyncio.sleep(1)
    month, year = order.credit_card_expiry.split("/")
    exp_year = int("20" + year)
    exp_month = int(month)
    now = datetime.utcnow()
    if exp_year < now.year or (exp_year == now.year and exp_month < now.month):
        raise activity.ApplicationError("Credit card expired")
    return f"Payment processed for order {order.id}"


@activity.defn
async def reserve_inventory(order: Order) -> str:
    """Reserve items for the order."""
    await asyncio.sleep(1)
    # Simulated external API call; uncomment to simulate downtime
    # import requests; requests.get("http://localhost:9999/reserve", timeout=1).raise_for_status()
    return f"Inventory reserved for order {order.id}"


@activity.defn
async def deliver_order(order: Order) -> str:
    """Deliver the order to the customer."""
    await asyncio.sleep(1)
    return f"Order {order.id} delivered"
