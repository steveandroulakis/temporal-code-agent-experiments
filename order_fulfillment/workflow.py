"""Workflow definition for the order fulfillment sample."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Optional

from temporalio import workflow

from activities import deliver_order, process_payment, reserve_inventory
from shared import FulfillmentResult, Order, OrderStatus

TASK_QUEUE = "order-fulfillment-task-queue"


@workflow.defn
class OrderWorkflow:
    """Workflow that runs the end-to-end order fulfillment process."""

    def __init__(self) -> None:
        self.order: Optional[Order] = None
        self.status: OrderStatus = OrderStatus.CREATED
        self._approval_decided = False
        self._approval_message: Optional[str] = None
        self._payment_authorization: Optional[str] = None
        self._inventory_reservation: Optional[str] = None

    @workflow.signal
    def approve_order(self, approved: bool, note: Optional[str] = None) -> None:
        """Signal invoked by a human to approve or reject the order."""

        if self._approval_decided:
            workflow.logger.info("Approval already decided; ignoring signal")
            return

        self._approval_decided = True
        if approved:
            self.status = OrderStatus.APPROVED
            self._approval_message = note or "Order approved"
        else:
            self.status = OrderStatus.CANCELED
            self._approval_message = note or "Order rejected"
        workflow.logger.info("Approval decided: %s", self.status.value)

    @workflow.query
    def current_status(self) -> str:
        return self.status.value

    @workflow.query
    def approval_message(self) -> Optional[str]:
        return self._approval_message

    @workflow.run
    async def run(self, order: Order) -> FulfillmentResult:
        self.order = order
        workflow.logger.info("Starting workflow for order %s", order.order_id)

        self.status = OrderStatus.CREATED
        self._approval_decided = False
        self._approval_message = None

        # Uncomment the next line to simulate a workflow bug scenario.
        # raise RuntimeError("workflow bug!")

        self._payment_authorization = await workflow.execute_activity(
            process_payment,
            order,
            schedule_to_close_timeout=timedelta(seconds=10),
        )
        self.status = OrderStatus.PAYMENT_PROCESSED
        workflow.logger.info("Payment complete for order %s", order.order_id)

        self._inventory_reservation = await workflow.execute_activity(
            reserve_inventory,
            args=[order.order_id, order.items, order.simulate_inventory_downtime],
            schedule_to_close_timeout=timedelta(seconds=10),
        )
        self.status = OrderStatus.INVENTORY_RESERVED
        workflow.logger.info("Inventory reserved for order %s", order.order_id)

        if not self._approval_decided:
            self.status = OrderStatus.WAITING_FOR_APPROVAL
            workflow.logger.info(
                "Waiting up to %s seconds for human approval",
                order.approval_timeout_seconds,
            )

            try:
                await workflow.wait_condition(
                    lambda: self._approval_decided,
                    timeout=order.approval_timeout_seconds,
                )
            except asyncio.TimeoutError:
                self.status = OrderStatus.EXPIRED
                self._approval_decided = True
                self._approval_message = "Order expired while waiting for approval"
                workflow.logger.info("Order %s expired", order.order_id)

        if self.status == OrderStatus.APPROVED:
            tracking = await workflow.execute_activity(
                deliver_order,
                order.order_id,
                schedule_to_close_timeout=timedelta(seconds=10),
            )
            self.status = OrderStatus.FULFILLED
            workflow.logger.info("Order %s delivered", order.order_id)
            return FulfillmentResult(
                order_id=order.order_id,
                status=self.status,
                message=self._approval_message or "Order fulfilled",
                delivery_receipt=tracking,
                payment_authorization=self._payment_authorization,
                inventory_reservation=self._inventory_reservation,
            )

        if self.status == OrderStatus.CANCELED:
            workflow.logger.info("Order %s rejected", order.order_id)
            return FulfillmentResult(
                order_id=order.order_id,
                status=self.status,
                message=self._approval_message or "Order rejected",
                payment_authorization=self._payment_authorization,
                inventory_reservation=self._inventory_reservation,
            )

        # EXPIRED path
        workflow.logger.info("Order %s expired before approval", order.order_id)
        return FulfillmentResult(
            order_id=order.order_id,
            status=self.status,
            message=self._approval_message or "Order expired before approval",
            payment_authorization=self._payment_authorization,
            inventory_reservation=self._inventory_reservation,
        )
