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
    initiate_delivery,
    refund_payment,
    release_inventory,
)
from workflow import OrderWorkflow


async def main() -> None:
    """Start the order management worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    # Write PID file for lifecycle management
    with open("worker.pid", "w") as f:
        f.write(str(os.getpid()))

    logger.info("Worker starting...")

    # Connect to Temporal server
    try:
        client = await Client.connect("localhost:7233")
        logger.info("Connected to Temporal server at localhost:7233")
    except Exception as e:
        logger.error(f"Failed to connect to Temporal server: {e}")
        logger.error("Make sure Temporal dev server is running: temporal server start-dev")
        raise SystemExit(1)

    # Create worker with workflows and activities
    async with Worker(
        client,
        task_queue="order-management-task-queue",
        workflows=[OrderWorkflow],
        activities=[
            process_payment,
            reserve_inventory,
            initiate_delivery,
            refund_payment,
            release_inventory,
        ],
        activity_executor=ThreadPoolExecutor(max_workers=10),
    ):
        logger.info("=" * 60)
        logger.info("Worker ready and polling task queue: order-management-task-queue")
        logger.info("Registered workflows: OrderWorkflow")
        logger.info("Registered activities: process_payment, reserve_inventory,")
        logger.info("                       initiate_delivery, refund_payment,")
        logger.info("                       release_inventory")
        logger.info("=" * 60)

        try:
            # Keep worker running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Worker shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
