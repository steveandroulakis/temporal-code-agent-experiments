from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError
from activities import (
    process_payment,
    reserve_inventory,
    initiate_delivery,
    refund_payment,
    release_inventory,
)
from shared import Order, PaymentResult, InventoryResult, DeliveryResult


@workflow.defn
class OrderWorkflow:
    """
    Order management workflow with human-in-the-loop approval for orders over $1000.

    Workflow steps:
    1. Check if order total > $1000
    2. If yes, wait for approval signal (with timeout)
    3. Reserve inventory
    4. Process payment
    5. Initiate delivery
    6. Return final status

    Compensation: If any step fails, rollback previous steps.
    """

    def __init__(self) -> None:
        self._approval_status = None
        self._approval_received = False
        self._order_status = "pending"
        self._payment_result = None
        self._inventory_result = None
        self._delivery_result = None

    @workflow.run
    async def run(self, order: Order) -> dict:
        """
        Main workflow execution.

        Args:
            order: The order to process

        Returns:
            Dictionary containing workflow results and status
        """
        workflow.logger.info(f"Starting order workflow for order {order.order_id}")
        workflow.logger.info(f"Order total: ${order.total_amount:.2f}")

        self._order_status = "processing"

        # Define retry policy for activities
        default_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=100),
            maximum_attempts=3,
        )

        try:
            # Step 1: Check if order requires approval (over $1000)
            if order.total_amount > 1000.0:
                workflow.logger.info(
                    f"Order amount ${order.total_amount:.2f} exceeds $1000 - "
                    "approval required"
                )
                self._order_status = "awaiting_approval"

                # Wait for approval signal with 5-minute timeout
                approval_timeout = timedelta(minutes=5)
                workflow.logger.info(
                    f"Waiting for approval (timeout: {approval_timeout.total_seconds()}s)"
                )

                await workflow.wait_condition(
                    lambda: self._approval_received,
                    timeout=approval_timeout
                )

                if not self._approval_status:
                    workflow.logger.warning("Order was rejected")
                    self._order_status = "rejected"
                    raise ApplicationError(
                        "Order rejected by approver",
                        non_retryable=True
                    )

                workflow.logger.info("Order approved - proceeding with processing")
                self._order_status = "approved"
            else:
                workflow.logger.info(
                    f"Order amount ${order.total_amount:.2f} is under $1000 - "
                    "no approval required"
                )

            # Step 2: Reserve inventory
            workflow.logger.info("Reserving inventory...")
            self._order_status = "reserving_inventory"
            self._inventory_result = await workflow.execute_activity(
                reserve_inventory,
                order,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=default_retry_policy,
            )

            if not self._inventory_result.success:
                raise ApplicationError(
                    f"Inventory reservation failed: {self._inventory_result.message}",
                    non_retryable=True
                )

            workflow.logger.info(
                f"Inventory reserved: {self._inventory_result.reservation_id}"
            )

            # Step 3: Process payment
            workflow.logger.info("Processing payment...")
            self._order_status = "processing_payment"
            self._payment_result = await workflow.execute_activity(
                process_payment,
                order,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=default_retry_policy,
            )

            if not self._payment_result.success:
                # Compensate: release inventory
                workflow.logger.warning("Payment failed - releasing inventory")
                await self._compensate_inventory()
                raise ApplicationError(
                    f"Payment failed: {self._payment_result.message}",
                    non_retryable=True
                )

            workflow.logger.info(
                f"Payment processed: {self._payment_result.transaction_id}"
            )

            # Step 4: Initiate delivery
            workflow.logger.info("Initiating delivery...")
            self._order_status = "initiating_delivery"
            self._delivery_result = await workflow.execute_activity(
                initiate_delivery,
                order,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=default_retry_policy,
            )

            if not self._delivery_result.success:
                # Compensate: refund payment and release inventory
                workflow.logger.warning("Delivery failed - compensating")
                await self._compensate_payment(order.total_amount)
                await self._compensate_inventory()
                raise ApplicationError(
                    f"Delivery failed: {self._delivery_result.message}",
                    non_retryable=True
                )

            workflow.logger.info(
                f"Delivery initiated: {self._delivery_result.tracking_number}"
            )

            # Success!
            self._order_status = "completed"
            workflow.logger.info(f"Order {order.order_id} completed successfully")

            return {
                "order_id": order.order_id,
                "status": self._order_status,
                "payment": {
                    "transaction_id": self._payment_result.transaction_id,
                    "amount": order.total_amount,
                },
                "inventory": {
                    "reservation_id": self._inventory_result.reservation_id,
                },
                "delivery": {
                    "tracking_number": self._delivery_result.tracking_number,
                    "estimated_delivery": self._delivery_result.estimated_delivery_date,
                },
                "message": "Order processed successfully",
            }

        except ApplicationError as e:
            workflow.logger.error(f"Order workflow failed: {e}")
            return {
                "order_id": order.order_id,
                "status": self._order_status,
                "error": str(e),
                "message": "Order processing failed",
            }

    @workflow.signal
    def approve_order(self, approved: bool) -> None:
        """
        Signal to approve or reject an order requiring approval.

        Args:
            approved: True to approve, False to reject
        """
        workflow.logger.info(f"Received approval signal: {approved}")
        self._approval_status = approved
        self._approval_received = True

    @workflow.query
    def get_status(self) -> str:
        """Query to get current order status."""
        return self._order_status

    @workflow.query
    def requires_approval(self) -> bool:
        """Query to check if order requires approval."""
        return self._order_status == "awaiting_approval"

    async def _compensate_payment(self, amount: float) -> None:
        """Compensate by refunding payment."""
        if self._payment_result:
            workflow.logger.info(
                f"Compensating: refunding payment {self._payment_result.transaction_id}"
            )
            await workflow.execute_activity(
                refund_payment,
                args=[self._payment_result.transaction_id, amount],
                start_to_close_timeout=timedelta(seconds=30),
            )

    async def _compensate_inventory(self) -> None:
        """Compensate by releasing inventory reservation."""
        if self._inventory_result:
            workflow.logger.info(
                f"Compensating: releasing inventory {self._inventory_result.reservation_id}"
            )
            await workflow.execute_activity(
                release_inventory,
                self._inventory_result.reservation_id,
                start_to_close_timeout=timedelta(seconds=30),
            )
