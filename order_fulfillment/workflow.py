"""Workflow definition for the order fulfillment sample."""

from __future__ import annotations

from datetime import timedelta
from temporalio import workflow

from activities import deliver_order, process_payment, reserve_inventory
from shared import Order


@workflow.defn
class OrderWorkflow:
    """Workflow that processes an order through three sequential activities."""

    def __init__(self) -> None:
        self._approved = False

    @workflow.signal
    def approve_order(self) -> None:
        """Signal from a human to approve the order."""
        self._approved = True

    @workflow.run
    async def run(self, order: Order) -> str:
        """Run the workflow."""
        await workflow.execute_activity(
            process_payment,
            order,
            schedule_to_close_timeout=timedelta(seconds=10),
        )

        # Uncomment to simulate a workflow bug.
        # raise RuntimeError("workflow bug!")

        try:
            await workflow.wait_condition(
                lambda: self._approved, timeout=timedelta(seconds=30)
            )
        except TimeoutError as exc:  # pragma: no cover - Temporal raises TimeoutError
            raise workflow.ApplicationError("order expired") from exc

        await workflow.execute_activity(
            reserve_inventory,
            order,
            schedule_to_close_timeout=timedelta(seconds=10),
        )
        await workflow.execute_activity(
            deliver_order,
            order,
            schedule_to_close_timeout=timedelta(seconds=10),
        )
        return "order fulfilled"
