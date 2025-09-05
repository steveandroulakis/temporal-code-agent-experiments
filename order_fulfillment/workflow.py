from __future__ import annotations

import asyncio
from datetime import timedelta

from temporalio import workflow

from activities import deliver_order, process_payment, reserve_inventory
from shared import Order


@workflow.defn
class OrderWorkflow:
    approved: bool
    expired: bool

    def __init__(self) -> None:
        self.approved = False
        self.expired = False

    @workflow.signal
    async def approve_order(self) -> None:
        self.approved = True

    @workflow.signal
    async def expire_order(self) -> None:
        self.expired = True

    @workflow.run
    async def run(self, order: Order) -> str:
        # Uncomment the next line to simulate a workflow bug
        # raise RuntimeError("workflow bug!")

        await workflow.execute_activity(
            process_payment,
            order.payment,
            schedule_to_close_timeout=timedelta(seconds=10),
        )
        await workflow.execute_activity(
            reserve_inventory,
            order.items,
            schedule_to_close_timeout=timedelta(seconds=10),
        )

        try:
            await workflow.wait_condition(
                lambda: self.approved or self.expired,
                timeout=timedelta(seconds=30),
            )
        except asyncio.TimeoutError:
            self.expired = True

        if self.expired:
            return "order expired"

        await workflow.execute_activity(
            deliver_order,
            order,
            schedule_to_close_timeout=timedelta(seconds=10),
        )
        return "order delivered"
