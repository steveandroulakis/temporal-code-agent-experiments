from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from activities import square_number
from shared import SquareNumberInput, BatchInput, BatchResult, BatchProcessingInput
import asyncio

@workflow.defn
class NumberBatchWorkflow:
    """Child workflow that processes a batch of numbers"""

    @workflow.run
    async def run(self, batch_input: BatchInput) -> BatchResult:
        workflow.logger.info(
            f"Processing batch {batch_input.batch_id} with {len(batch_input.numbers)} numbers"
        )

        default_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=100),
            maximum_attempts=3,
        )

        # Process all numbers in this batch in parallel
        tasks = []
        for number in batch_input.numbers:
            task = workflow.execute_activity(
                square_number,
                SquareNumberInput(number=number),
                schedule_to_close_timeout=timedelta(seconds=30),
                retry_policy=default_retry_policy,
            )
            tasks.append(task)

        # Wait for all activities to complete
        results = await asyncio.gather(*tasks)

        workflow.logger.info(
            f"Batch {batch_input.batch_id} completed with {len(results)} results"
        )

        return BatchResult(
            batch_id=batch_input.batch_id,
            results=list(results)
        )


@workflow.defn
class BatchProcessingWorkflow:
    """Main workflow that orchestrates batch processing using child workflows"""

    @workflow.run
    async def run(self, input: BatchProcessingInput) -> dict:
        workflow.logger.info(
            f"Starting batch processing for {input.total_numbers} numbers "
            f"with batch size {input.batch_size}"
        )

        # Generate all numbers from 1 to n
        all_numbers = list(range(1, input.total_numbers + 1))

        # Divide numbers into batches
        batches = []
        for i in range(0, len(all_numbers), input.batch_size):
            batch_numbers = all_numbers[i:i + input.batch_size]
            batch_id = i // input.batch_size
            batches.append(BatchInput(numbers=batch_numbers, batch_id=batch_id))

        workflow.logger.info(f"Created {len(batches)} batches to process")

        # Execute child workflows for each batch
        child_workflow_tasks = []
        for batch in batches:
            # Execute child workflow
            child_task = workflow.execute_child_workflow(
                NumberBatchWorkflow.run,
                batch,
                id=f"batch-{workflow.info().workflow_id}-{batch.batch_id}",
                task_queue="batch-processing-task-queue",
            )
            child_workflow_tasks.append(child_task)

        # Wait for all child workflows to complete
        batch_results = await asyncio.gather(*child_workflow_tasks)

        # Aggregate results
        all_results = []
        for batch_result in batch_results:
            all_results.extend(batch_result.results)

        workflow.logger.info(
            f"Batch processing complete. Processed {len(all_results)} numbers"
        )

        # Calculate some summary statistics
        total_sum = sum(all_results)

        return {
            "total_numbers_processed": len(all_results),
            "total_batches": len(batches),
            "batch_size": input.batch_size,
            "sum_of_squares": total_sum,
            "first_10_results": all_results[:10],
            "last_10_results": all_results[-10:],
        }
