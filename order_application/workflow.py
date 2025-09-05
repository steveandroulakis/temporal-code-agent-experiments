import asyncio
from datetime import timedelta
from temporalio import workflow
from temporalio.exceptions import ApplicationError
from shared import Order
from activities import process_payment, reserve_inventory, deliver_order


@workflow.defn
class OrderWorkflow:
    """Workflow coordinating order fulfilment."""

    def __init__(self) -> None:
        self._approved = False

    @workflow.signal
    async def approve_order(self) -> None:
        """Signal to approve the order."""
        self._approved = True

    @workflow.run
    async def run(self, order: Order) -> str:
        await workflow.execute_activity(
            process_payment,
            order,
            schedule_to_close_timeout=timedelta(seconds=10),
        )

        await workflow.execute_activity(
            reserve_inventory,
            order,
            schedule_to_close_timeout=timedelta(seconds=10),
        )

        try:
            await workflow.wait_condition(lambda: self._approved, timeout=timedelta(seconds=30))
        except asyncio.TimeoutError:
            raise ApplicationError("Order approval timed out")

        result = await workflow.execute_activity(
            deliver_order,
            order,
            schedule_to_close_timeout=timedelta(seconds=10),
        )
        return result
