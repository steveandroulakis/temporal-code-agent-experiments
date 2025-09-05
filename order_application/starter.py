#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["temporalio>=1.3.0"]
# ///

import asyncio
import logging
import sys
import uuid
from temporalio.client import Client
from shared import Order
from workflow import OrderWorkflow


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    expiry = sys.argv[1] if len(sys.argv) > 1 else "12/30"
    order = Order(
        id=str(uuid.uuid4()),
        item="Widget",
        quantity=1,
        credit_card_number="4111111111111111",
        credit_card_expiry=expiry,
    )

    client = await Client.connect("localhost:7233")
    handle = await client.start_workflow(
        OrderWorkflow.run,
        order,
        id=f"order-workflow-{order.id}",
        task_queue="order-task-queue",
    )
    logger.info(f"Started workflow {handle.id}")
    print(handle.id)

    if "--approve" in sys.argv:
        await handle.signal(OrderWorkflow.approve_order)
        result = await handle.result()
        print(f"Result: {result}")
        logger.info("Workflow completed")


if __name__ == "__main__":
    asyncio.run(main())
