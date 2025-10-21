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
    """
    Start an order workflow.

    Usage:
        python starter.py <order_type>

    Where order_type is:
        - small: Order under $1000 (no approval needed)
        - large: Order over $1000 (requires approval)
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python starter.py <order_type>")
        print("  order_type: 'small' (under $1000) or 'large' (over $1000)")
        sys.exit(1)

    order_type = sys.argv[1].lower()

    # Create different order scenarios
    if order_type == "small":
        order = Order(
            order_id="ORD-001",
            customer_name="Alice Smith",
            customer_email="alice@example.com",
            items=[
                OrderItem(
                    product_id="PROD-101",
                    product_name="Wireless Mouse",
                    quantity=2,
                    unit_price=29.99,
                ),
                OrderItem(
                    product_id="PROD-102",
                    product_name="USB Cable",
                    quantity=3,
                    unit_price=9.99,
                ),
            ],
            shipping_address="123 Main St, Springfield, IL 62701",
        )
    elif order_type == "large":
        order = Order(
            order_id="ORD-002",
            customer_name="Bob Johnson",
            customer_email="bob@example.com",
            items=[
                OrderItem(
                    product_id="PROD-201",
                    product_name="Laptop Computer",
                    quantity=1,
                    unit_price=1299.99,
                ),
                OrderItem(
                    product_id="PROD-202",
                    product_name="External Monitor",
                    quantity=2,
                    unit_price=299.99,
                ),
            ],
            shipping_address="456 Oak Ave, Chicago, IL 60601",
        )
    else:
        logger.error(f"Unknown order type: {order_type}")
        print("Error: order_type must be 'small' or 'large'")
        sys.exit(1)

    try:
        # Connect to Temporal server
        client = await Client.connect("localhost:7233")
        logger.info(f"Connected to Temporal server")

        logger.info(
            f"Starting order workflow for {order.customer_name}, "
            f"order ID: {order.order_id}, "
            f"total: ${order.total_amount:.2f}"
        )

        if order.requires_approval:
            logger.warning(
                f"⚠️  This order requires approval! "
                f"Use approval_sender.py to approve/reject."
            )
            print(f"\n{'='*70}")
            print(f"⚠️  ORDER REQUIRES APPROVAL")
            print(f"{'='*70}")
            print(f"Order ID: {order.order_id}")
            print(f"Amount: ${order.total_amount:.2f}")
            print(f"\nTo approve this order, run:")
            print(f"  uv run approval_sender.py {order.order_id} approve")
            print(f"\nTo reject this order, run:")
            print(f"  uv run approval_sender.py {order.order_id} reject")
            print(f"{'='*70}\n")

        # Start the workflow (non-blocking for large orders)
        handle = await client.start_workflow(
            OrderWorkflow.run,
            order,
            id=f"order-workflow-{order.order_id}",
            task_queue="order-task-queue",
        )

        logger.info(f"Workflow started with ID: {handle.id}")
        logger.info(f"Run ID: {handle.result_run_id}")

        # For small orders, wait for completion
        # For large orders, return immediately (they need approval signal)
        if not order.requires_approval:
            logger.info("Waiting for workflow to complete...")
            result = await handle.result()
            print(f"\n{'='*70}")
            print(f"Order Result: {result.status.upper()}")
            print(f"{'='*70}")
            print(f"Order ID: {result.order_id}")
            print(f"Status: {result.status}")
            print(f"Message: {result.message}")

            if result.payment_result:
                print(f"\nPayment:")
                print(f"  Transaction ID: {result.payment_result.transaction_id}")
                print(f"  {result.payment_result.message}")

            if result.inventory_result:
                print(f"\nInventory:")
                print(f"  Reservation ID: {result.inventory_result.reservation_id}")
                print(f"  {result.inventory_result.message}")

            if result.delivery_result:
                print(f"\nDelivery:")
                print(f"  Tracking Number: {result.delivery_result.tracking_number}")
                print(f"  Estimated Delivery: {result.delivery_result.estimated_delivery_date}")
                print(f"  {result.delivery_result.message}")

            print(f"{'='*70}\n")
        else:
            print(f"Workflow started and waiting for approval...")
            print(f"Workflow will wait up to 5 minutes for approval signal.\n")

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
