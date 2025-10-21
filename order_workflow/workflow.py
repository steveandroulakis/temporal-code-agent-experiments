from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError
from activities import (
    process_payment,
    reserve_inventory,
    arrange_delivery,
    send_confirmation_email,
)
from shared import Order, OrderResult, PaymentResult, InventoryResult, DeliveryResult


@workflow.defn
class OrderWorkflow:
    """
    Order management workflow with human-in-the-loop approval for high-value orders.

    For orders over $1000, the workflow waits for manual approval via signal
    before proceeding with payment processing.
    """

    def __init__(self) -> None:
        self._approval_status: str = "pending"  # "pending", "approved", "rejected"
        self._approval_reason: str = ""

    @workflow.run
    async def run(self, order: Order) -> OrderResult:
        """
        Main workflow execution.

        Args:
            order: The order to process

        Returns:
            OrderResult with the final status and details
        """
        workflow.logger.info(
            f"Starting order workflow for order {order.order_id}, "
            f"customer: {order.customer_name}, "
            f"total: ${order.total_amount:.2f}"
        )

        # Define retry policy for activities
        default_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
        )

        try:
            # Check if order requires approval (orders over $1000)
            if order.requires_approval:
                workflow.logger.info(
                    f"Order {order.order_id} requires approval (amount: ${order.total_amount:.2f})"
                )

                # Wait for approval signal with timeout (e.g., 5 minutes for demo, could be longer in prod)
                await workflow.wait_condition(
                    lambda: self._approval_status != "pending",
                    timeout=timedelta(minutes=5),
                )

                if self._approval_status == "rejected":
                    workflow.logger.warning(
                        f"Order {order.order_id} was rejected: {self._approval_reason}"
                    )
                    return OrderResult(
                        order_id=order.order_id,
                        status="rejected",
                        message=f"Order rejected: {self._approval_reason}",
                    )

                workflow.logger.info(
                    f"Order {order.order_id} approved: {self._approval_reason}"
                )
            else:
                workflow.logger.info(
                    f"Order {order.order_id} does not require approval (amount: ${order.total_amount:.2f})"
                )

            # Step 1: Process payment
            workflow.logger.info(f"Processing payment for order {order.order_id}")
            payment_result: PaymentResult = await workflow.execute_activity(
                process_payment,
                order,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=default_retry_policy,
            )

            if not payment_result.success:
                raise ApplicationError(
                    f"Payment failed: {payment_result.message}",
                    non_retryable=True,
                )

            # Step 2: Reserve inventory
            workflow.logger.info(f"Reserving inventory for order {order.order_id}")
            inventory_result: InventoryResult = await workflow.execute_activity(
                reserve_inventory,
                order,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=default_retry_policy,
            )

            if not inventory_result.success:
                # In a real system, we'd want to refund the payment here
                raise ApplicationError(
                    f"Inventory reservation failed: {inventory_result.message}",
                    non_retryable=True,
                )

            # Step 3: Arrange delivery
            workflow.logger.info(f"Arranging delivery for order {order.order_id}")
            delivery_result: DeliveryResult = await workflow.execute_activity(
                arrange_delivery,
                order,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=default_retry_policy,
            )

            if not delivery_result.success:
                # In a real system, we'd want to release inventory and refund payment
                raise ApplicationError(
                    f"Delivery arrangement failed: {delivery_result.message}",
                    non_retryable=True,
                )

            # Step 4: Send confirmation email
            workflow.logger.info(
                f"Sending confirmation email for order {order.order_id}"
            )
            await workflow.execute_activity(
                send_confirmation_email,
                args=[order, {"status": "completed"}],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=default_retry_policy,
            )

            workflow.logger.info(f"Order {order.order_id} completed successfully")

            return OrderResult(
                order_id=order.order_id,
                status="completed",
                payment_result=payment_result,
                inventory_result=inventory_result,
                delivery_result=delivery_result,
                message="Order processed successfully",
            )

        except ApplicationError as e:
            workflow.logger.error(f"Order {order.order_id} failed: {str(e)}")
            return OrderResult(
                order_id=order.order_id,
                status="failed",
                message=str(e),
            )

    @workflow.signal
    async def approve_order(self, reason: str = "Approved by manager") -> None:
        """
        Signal to approve a high-value order.

        Args:
            reason: Reason for approval (optional)
        """
        workflow.logger.info(f"Order approval signal received: {reason}")
        self._approval_status = "approved"
        self._approval_reason = reason

    @workflow.signal
    async def reject_order(self, reason: str = "Rejected by manager") -> None:
        """
        Signal to reject a high-value order.

        Args:
            reason: Reason for rejection (optional)
        """
        workflow.logger.info(f"Order rejection signal received: {reason}")
        self._approval_status = "rejected"
        self._approval_reason = reason

    @workflow.query
    def get_approval_status(self) -> str:
        """
        Query the current approval status.

        Returns:
            Current approval status: "pending", "approved", or "rejected"
        """
        return self._approval_status

    @workflow.query
    def get_approval_reason(self) -> str:
        """
        Query the approval/rejection reason.

        Returns:
            Reason for the current approval status
        """
        return self._approval_reason
