from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from activities import square_number
from shared import SquareNumberInput, WorkflowNodeInput, NodeResult
import asyncio
import math

@workflow.defn
class BatchProcessingWorkflow:
    """
    Recursive workflow that processes numbers with automatic tree nesting.

    Each workflow node can:
    1. Process numbers directly as activities (if count <= batch_size)
    2. Spawn child workflows (if count > batch_size)

    Child workflows are limited to max_children per parent, creating a tree structure
    that can scale infinitely.
    """

    @workflow.run
    async def run(self, input: WorkflowNodeInput) -> NodeResult:
        total_numbers = input.end_number - input.start_number + 1

        workflow.logger.info(
            f"[Depth {input.depth}] Processing range [{input.start_number}..{input.end_number}] "
            f"({total_numbers} numbers) - batch_size={input.config.batch_size}, "
            f"max_children={input.config.max_children}"
        )

        # Base case: Small enough to process as activities
        if total_numbers <= input.config.batch_size:
            return await self._process_as_activities(input)

        # Recursive case: Divide into child workflows
        return await self._process_as_children(input)

    async def _process_as_activities(self, input: WorkflowNodeInput) -> NodeResult:
        """Process numbers directly as activities (leaf node)"""
        total_numbers = input.end_number - input.start_number + 1

        workflow.logger.info(
            f"[Depth {input.depth}] LEAF NODE: Processing {total_numbers} activities"
        )

        default_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=100),
            maximum_attempts=3,
        )

        # Create activity tasks for each number in parallel
        tasks = []
        for number in range(input.start_number, input.end_number + 1):
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
            f"[Depth {input.depth}] LEAF COMPLETE: Processed {len(results)} numbers"
        )

        return NodeResult(
            results=list(results),
            total_processed=len(results),
            depth=input.depth
        )

    async def _process_as_children(self, input: WorkflowNodeInput) -> NodeResult:
        """Divide work into child workflows (intermediate node)"""
        total_numbers = input.end_number - input.start_number + 1

        # Calculate how many child workflows we need
        # Each child can handle at most: max_children^(remaining_depth) * batch_size numbers
        # But we want to distribute evenly across max_children
        num_children = min(input.config.max_children, total_numbers)
        numbers_per_child = math.ceil(total_numbers / num_children)

        workflow.logger.info(
            f"[Depth {input.depth}] INTERMEDIATE NODE: Spawning {num_children} children "
            f"({numbers_per_child} numbers each)"
        )

        # Create child workflow inputs
        child_tasks = []
        current_start = input.start_number
        child_id = 0

        for i in range(num_children):
            current_end = min(current_start + numbers_per_child - 1, input.end_number)

            if current_start > input.end_number:
                break

            child_input = WorkflowNodeInput(
                start_number=current_start,
                end_number=current_end,
                config=input.config,
                depth=input.depth + 1
            )

            # Execute child workflow
            child_task = workflow.execute_child_workflow(
                BatchProcessingWorkflow.run,
                child_input,
                id=f"{workflow.info().workflow_id}-c{child_id}",
                task_queue="batch-processing-task-queue",
            )
            child_tasks.append(child_task)

            current_start = current_end + 1
            child_id += 1

        # Wait for all child workflows to complete
        child_results = await asyncio.gather(*child_tasks)

        # Aggregate results from all children
        all_results = []
        total_processed = 0
        max_depth = input.depth

        for child_result in child_results:
            all_results.extend(child_result.results)
            total_processed += child_result.total_processed
            max_depth = max(max_depth, child_result.depth)

        workflow.logger.info(
            f"[Depth {input.depth}] INTERMEDIATE COMPLETE: "
            f"Aggregated {total_processed} numbers from {len(child_tasks)} children"
        )

        return NodeResult(
            results=all_results,
            total_processed=total_processed,
            depth=max_depth
        )
