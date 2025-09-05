#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "temporalio>=1.17.0",
# ]
# ///
"""Workflow starter for the order fulfillment sample."""

import asyncio
import logging
import uuid

from temporalio.client import Client

from shared import Order
from workflow import OrderWorkflow


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    order = Order(
        order_id=str(uuid.uuid4()),
        amount=42.0,
        cc_expiry="12/30",  # Change to "12/23" to simulate invalid card
        items=["sprocket", "widget"],
    )
    client = await Client.connect("localhost:7233")
    result = await client.execute_workflow(
        OrderWorkflow.run,
        order,
        id=f"order-{order.order_id}",
        task_queue="order-task-queue",
    )
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
