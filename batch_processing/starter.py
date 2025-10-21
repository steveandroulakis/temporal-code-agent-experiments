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
from shared import WorkflowNodeInput, ProcessingConfig

async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Parse command line arguments
    total_numbers = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    max_children = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    logger.info(
        f"Starting batch processing workflow for {total_numbers} numbers "
        f"(batch_size={batch_size}, max_children={max_children})"
    )

    try:
        client = await Client.connect("localhost:7233")
    except Exception as e:
        logger.error(f"Failed to connect to Temporal server: {e}")
        raise SystemExit(1)

    workflow_id = f"batch-processing-{total_numbers}-b{batch_size}-c{max_children}"

    # Create workflow input
    workflow_input = WorkflowNodeInput(
        start_number=1,
        end_number=total_numbers,
        config=ProcessingConfig(
            batch_size=batch_size,
            max_children=max_children
        ),
        depth=0
    )

    try:
        logger.info(f"Executing workflow with ID: {workflow_id}")
        result = await client.execute_workflow(
            BatchProcessingWorkflow.run,
            workflow_input,
            id=workflow_id,
            task_queue="batch-processing-task-queue",
        )

        print("\n" + "="*70)
        print("BATCH PROCESSING COMPLETE")
        print("="*70)
        print(f"Total numbers processed: {result.total_processed}")
        print(f"Tree depth (max nesting level): {result.depth}")
        print(f"Batch size (activities per leaf): {batch_size}")
        print(f"Max children per workflow: {max_children}")
        print(f"Sum of all squares: {sum(result.results)}")
        print(f"\nFirst 10 results: {result.results[:10]}")
        print(f"Last 10 results: {result.results[-10:]}")
        print("="*70)

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    asyncio.run(main())
