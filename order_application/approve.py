#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["temporalio>=1.3.0"]
# ///

import asyncio
import sys
from temporalio.client import Client
from workflow import OrderWorkflow


async def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: approve.py <workflow-id>")
        sys.exit(1)
    workflow_id = sys.argv[1]
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal(OrderWorkflow.approve_order)
    print(f"Sent approval signal to {workflow_id}")


if __name__ == "__main__":
    asyncio.run(main())
