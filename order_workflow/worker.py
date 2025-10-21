#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["temporalio>=1.7.0"]
# ///
import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from temporalio.client import Client
from temporalio.worker import Worker
from activities import (
    process_payment,
    reserve_inventory,
    arrange_delivery,
    send_confirmation_email,
)
from workflow import OrderWorkflow


async def main() -> None:
    """
    Start the Temporal worker to process order workflows.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Write PID file for process management
    with open("worker.pid", "w") as f:
        f.write(str(os.getpid()))

    logger.info("Order workflow worker starting...")

    try:
        # Connect to Temporal server
        client = await Client.connect("localhost:7233")
        logger.info("Connected to Temporal server at localhost:7233")

        # Create worker with all activities and workflows
        async with Worker(
            client,
            task_queue="order-task-queue",
            workflows=[OrderWorkflow],
            activities=[
                process_payment,
                reserve_inventory,
                arrange_delivery,
                send_confirmation_email,
            ],
            activity_executor=ThreadPoolExecutor(max_workers=10),
        ):
            logger.info("Worker ready — polling: order-task-queue")
            logger.info("Worker is processing order workflows...")

            try:
                # Keep worker running
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Worker shutting down...")

    except Exception as e:
        logger.error(f"Worker failed to start: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
