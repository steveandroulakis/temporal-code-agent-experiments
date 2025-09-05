#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["temporalio>=1.7.0"]
# ///

import argparse
import asyncio
import logging
import uuid

from temporalio.client import Client

from shared import Order, PaymentInfo
from workflow import OrderWorkflow


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expiry", default="12/30", help="credit card expiry MM/YY")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    client = await Client.connect("localhost:7233")
    order = Order(
        order_id=str(uuid.uuid4()),
        items=["apple", "banana"],
        payment=PaymentInfo(card_number="4111111111111111", expiry=args.expiry),
    )

    logger.info("Starting workflow for order %s", order.order_id)
    handle = await client.start_workflow(
        OrderWorkflow.run,
        order,
        id=f"order-{order.order_id}",
        task_queue="order-task-queue",
    )
    logger.info("Workflow started with ID %s", handle.id)

    try:
        result = await handle.result()
        print(f"Result: {result}")
    except Exception as err:
        logger.error("Workflow failed: %s", err)
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
