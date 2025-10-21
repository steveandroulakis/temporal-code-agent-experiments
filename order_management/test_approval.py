#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["temporalio>=1.7.0"]
# ///
"""Test script for order requiring approval."""
import asyncio
import logging
from temporalio.client import Client, WorkflowHandle
from workflow import OrderWorkflow
from shared import Order, OrderItem


async def main() -> None:
    """Test order over $1000 with approval signal."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    # Create an order over $1000
    order = Order(
        order_id="ORDER-1500",
        customer_id="CUST-12345",
        items=[
            OrderItem(product_id="PROD-001", quantity=1, price=750.0),
            OrderItem(product_id="PROD-002", quantity=1, price=750.0),
        ],
        total_amount=1500.0,
    )

    logger.info("=" * 60)
    logger.info("Testing order workflow with approval requirement")
    logger.info(f"Order ID: {order.order_id}")
    logger.info(f"Total Amount: ${order.total_amount:.2f}")
    logger.info("This order requires approval (>$1000)")
    logger.info("=" * 60)

    try:
        # Connect to Temporal server
        client = await Client.connect("localhost:7233")
        logger.info("Connected to Temporal server")

        # Start the workflow (it will wait for approval)
        workflow_id = f"order-workflow-{order.order_id}"
        logger.info(f"Starting workflow with ID: {workflow_id}")

        handle: WorkflowHandle = await client.start_workflow(
            OrderWorkflow.run,
            order,
            id=workflow_id,
            task_queue="order-management-task-queue",
        )

        logger.info("Workflow started - waiting for it to need approval...")
        await asyncio.sleep(2)

        # Check if workflow requires approval
        requires_approval = await handle.query(OrderWorkflow.requires_approval)
        logger.info(f"Workflow requires approval: {requires_approval}")

        if requires_approval:
            logger.info("Sending approval signal...")
            await handle.signal(OrderWorkflow.approve_order, True)
            logger.info("Approval signal sent!")

        # Wait for workflow to complete
        logger.info("Waiting for workflow to complete...")
        result = await handle.result()

        # Print results
        logger.info("=" * 60)
        logger.info("Workflow completed!")
        logger.info(f"Status: {result.get('status')}")

        if result.get("status") == "completed":
            logger.info(f"Transaction ID: {result['payment']['transaction_id']}")
            logger.info(f"Reservation ID: {result['inventory']['reservation_id']}")
            logger.info(f"Tracking Number: {result['delivery']['tracking_number']}")
            logger.info(f"Estimated Delivery: {result['delivery']['estimated_delivery']}")
            print(f"\nResult: {result.get('message')}")
        else:
            logger.error(f"Order failed: {result.get('error')}")
            print(f"\nResult: Order processing failed - {result.get('error')}")

        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
