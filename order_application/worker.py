#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["temporalio>=1.3.0"]
# ///

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker
from activities import process_payment, reserve_inventory, deliver_order
from workflow import OrderWorkflow


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    pid = os.getpid()
    with open("worker.pid", "w") as f:
        f.write(str(pid))
    logger.info(f"Worker starting with PID: {pid}")

    client = await Client.connect("localhost:7233")
    logger.info("Connected to Temporal server at localhost:7233")

    async with Worker(
        client,
        task_queue="order-task-queue",
        workflows=[OrderWorkflow],
        activities=[process_payment, reserve_inventory, deliver_order],
        activity_executor=ThreadPoolExecutor(),
    ):
        logger.info("Worker started and polling for tasks on queue: order-task-queue")
        logger.info("Worker ready")
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
