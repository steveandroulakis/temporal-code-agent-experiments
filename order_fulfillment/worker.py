"""Worker that hosts the order fulfillment workflow and activities."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from pathlib import Path

from temporalio.client import Client
from temporalio.worker import Worker

from activities import deliver_order, process_payment, reserve_inventory
from workflow import OrderWorkflow, TASK_QUEUE

PID_FILE = Path("worker.pid")


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger = logging.getLogger("order_fulfillment.worker")

    client = await Client.connect("localhost:7233")
    logger.info("Connected to Temporal at localhost:7233")

    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def _request_shutdown() -> None:
        if not shutdown_event.is_set():
            logger.info("Shutdown signal received")
            shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_shutdown)
        except NotImplementedError:
            # add_signal_handler is not available on Windows event loop implementations.
            signal.signal(sig, lambda *_: shutdown_event.set())

    PID_FILE.write_text(str(os.getpid()))
    logger.info("Worker PID %s written to %s", os.getpid(), PID_FILE)

    try:
        async with Worker(
            client,
            task_queue=TASK_QUEUE,
            workflows=[OrderWorkflow],
            activities=[process_payment, reserve_inventory, deliver_order],
        ):
            logger.info("Worker started. Waiting for tasks on %s", TASK_QUEUE)
            await shutdown_event.wait()
    finally:
        try:
            PID_FILE.unlink()
            logger.info("Removed %s", PID_FILE)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
