#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["temporalio>=1.7.0"]
# ///
import asyncio
import logging
import sys
from temporalio.client import Client
from workflow import BatchProcessingWorkflow
from shared import BatchProcessingInput

async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Parse command line arguments
    total_numbers = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    logger.info(f"Starting batch processing workflow for {total_numbers} numbers with batch size {batch_size}")

    try:
        client = await Client.connect("localhost:7233")
    except Exception as e:
        logger.error(f"Failed to connect to Temporal server: {e}")
        raise SystemExit(1)

    workflow_id = f"batch-processing-workflow-{total_numbers}"

    try:
        logger.info(f"Executing workflow with ID: {workflow_id}")
        result = await client.execute_workflow(
            BatchProcessingWorkflow.run,
            BatchProcessingInput(total_numbers=total_numbers, batch_size=batch_size),
            id=workflow_id,
            task_queue="batch-processing-task-queue",
        )

        print("\n" + "="*60)
        print("BATCH PROCESSING COMPLETE")
        print("="*60)
        print(f"Total numbers processed: {result['total_numbers_processed']}")
        print(f"Total batches: {result['total_batches']}")
        print(f"Batch size: {result['batch_size']}")
        print(f"Sum of all squares: {result['sum_of_squares']}")
        print(f"\nFirst 10 results: {result['first_10_results']}")
        print(f"Last 10 results: {result['last_10_results']}")
        print("="*60)

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    asyncio.run(main())
