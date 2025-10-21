#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["temporalio>=1.7.0"]
# ///
import asyncio
import logging
import sys
from temporalio.client import Client
from workflow import OrderWorkflow
from shared import Order, OrderItem


async def main() -> None:
    """Start an order workflow with a sample order."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    # Parse command line arguments for order total
    order_total = float(sys.argv[1]) if len(sys.argv) > 1 else 500.0

    # Create a sample order
    # Calculate item price to match desired total
    item_price = order_total / 2  # 2 items

    order = Order(
        order_id=f"ORDER-{int(order_total):04d}",
        customer_id="CUST-12345",
        items=[
            OrderItem(product_id="PROD-001", quantity=1, price=item_price),
            OrderItem(product_id="PROD-002", quantity=1, price=item_price),
        ],
        total_amount=order_total,
    )

    logger.info("=" * 60)
    logger.info(f"Creating order workflow")
    logger.info(f"Order ID: {order.order_id}")
    logger.info(f"Total Amount: ${order.total_amount:.2f}")
    logger.info(f"Items: {len(order.items)}")
    for item in order.items:
        logger.info(f"  - {item.product_id}: {item.quantity} x ${item.price:.2f}")
    logger.info("=" * 60)

    try:
        # Connect to Temporal server
        client = await Client.connect("localhost:7233")
        logger.info("Connected to Temporal server")

        # Start the workflow
        workflow_id = f"order-workflow-{order.order_id}"
        logger.info(f"Starting workflow with ID: {workflow_id}")

        result = await client.execute_workflow(
            OrderWorkflow.run,
            order,
            id=workflow_id,
            task_queue="order-management-task-queue",
        )

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
        elif result.get("status") == "rejected":
            logger.warning("Order was rejected")
            print(f"\nResult: {result.get('error')}")
        else:
            logger.error(f"Order failed: {result.get('error')}")
            print(f"\nResult: Order processing failed - {result.get('error')}")

        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
