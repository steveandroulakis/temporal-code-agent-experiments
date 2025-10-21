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
from activities import square_number
from workflow import BatchProcessingWorkflow

async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Write PID file
    with open("worker.pid", "w") as f:
        f.write(str(os.getpid()))

    logger.info("Worker starting")

    try:
        client = await Client.connect("localhost:7233")
        logger.info("Connected to Temporal server")
    except Exception as e:
        logger.error(f"Failed to connect to Temporal server: {e}")
        raise SystemExit(1)

    async with Worker(
        client,
        task_queue="batch-processing-task-queue",
        workflows=[BatchProcessingWorkflow],
        activities=[square_number],
        activity_executor=ThreadPoolExecutor(10),
        max_concurrent_activities=20,
    ):
        logger.info("Worker ready — polling: batch-processing-task-queue")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Worker shutting down…")

if __name__ == "__main__":
    asyncio.run(main())
