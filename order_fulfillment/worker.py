#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["temporalio>=1.7.0"]
# ///

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from activities import deliver_order, process_payment, reserve_inventory
from workflow import OrderWorkflow


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="order-task-queue",
        workflows=[OrderWorkflow],
        activities=[process_payment, reserve_inventory, deliver_order],
    )
    logger.info("Worker ready — polling: order-task-queue")
    async with worker:
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Worker shutting down…")


if __name__ == "__main__":
    asyncio.run(main())
