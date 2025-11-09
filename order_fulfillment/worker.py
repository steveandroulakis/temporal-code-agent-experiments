#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "temporalio>=1.17.0",
# ]
# ///
"""Worker service for the order fulfillment sample."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker

from activities import deliver_order, process_payment, reserve_inventory
from workflow import OrderWorkflow


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    client = await Client.connect("localhost:7233")
    async with Worker(
        client,
        task_queue="order-task-queue",
        workflows=[OrderWorkflow],
        activities=[process_payment, reserve_inventory, deliver_order],
        activity_executor=ThreadPoolExecutor(),
    ):
        logging.info("Worker started for task queue 'order-task-queue'")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
