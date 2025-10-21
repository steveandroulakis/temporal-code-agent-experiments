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


async def main() -> None:
    """
    Send approval or rejection signal to a running order workflow.

    Usage:
        python approval_sender.py <order_id> <action> [reason]

    Args:
        order_id: The order ID (e.g., ORD-002)
        action: Either 'approve' or 'reject'
        reason: Optional reason for the decision
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Parse command line arguments
    if len(sys.argv) < 3:
        print("Usage: python approval_sender.py <order_id> <action> [reason]")
        print("  order_id: The order ID (e.g., ORD-002)")
        print("  action: 'approve' or 'reject'")
        print("  reason: Optional reason for the decision")
        sys.exit(1)

    order_id = sys.argv[1]
    action = sys.argv[2].lower()
    reason = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else None

    if action not in ["approve", "reject"]:
        logger.error(f"Invalid action: {action}")
        print("Error: action must be 'approve' or 'reject'")
        sys.exit(1)

    try:
        # Connect to Temporal server
        client = await Client.connect("localhost:7233")
        logger.info("Connected to Temporal server")

        # Get handle to the running workflow
        workflow_id = f"order-workflow-{order_id}"
        handle = client.get_workflow_handle(workflow_id)

        # Check current approval status
        try:
            current_status = await handle.query(OrderWorkflow.get_approval_status)
            logger.info(f"Current approval status: {current_status}")

            if current_status != "pending":
                logger.warning(
                    f"Workflow already has status: {current_status}. "
                    f"Cannot change approval."
                )
                print(f"Warning: Order has already been {current_status}")
                return
        except Exception as e:
            logger.error(f"Failed to query workflow status: {e}")
            print(f"Error: Could not find workflow with ID: {workflow_id}")
            print(f"Make sure the order workflow is running.")
            sys.exit(1)

        # Send the appropriate signal
        if action == "approve":
            default_reason = "Approved by manager"
            signal_reason = reason if reason else default_reason
            await handle.signal(OrderWorkflow.approve_order, signal_reason)
            logger.info(f"Sent approval signal to workflow {workflow_id}")
            print(f"\n{'='*70}")
            print(f"✅ ORDER APPROVED")
            print(f"{'='*70}")
            print(f"Order ID: {order_id}")
            print(f"Reason: {signal_reason}")
            print(f"{'='*70}\n")
            print("The workflow will now proceed with payment and fulfillment.")

        else:  # reject
            default_reason = "Rejected by manager"
            signal_reason = reason if reason else default_reason
            await handle.signal(OrderWorkflow.reject_order, signal_reason)
            logger.info(f"Sent rejection signal to workflow {workflow_id}")
            print(f"\n{'='*70}")
            print(f"❌ ORDER REJECTED")
            print(f"{'='*70}")
            print(f"Order ID: {order_id}")
            print(f"Reason: {signal_reason}")
            print(f"{'='*70}\n")
            print("The workflow will be cancelled without processing payment.")

        # Wait a moment and check if workflow completed
        await asyncio.sleep(2)

        # Try to get the result (will only work if workflow completed)
        try:
            result = await asyncio.wait_for(handle.result(), timeout=30)
            print(f"\nWorkflow completed with status: {result.status}")
            print(f"Message: {result.message}")
        except asyncio.TimeoutError:
            logger.info("Workflow is still running (this is normal for approved orders)")
        except Exception as e:
            logger.debug(f"Could not get workflow result: {e}")

    except Exception as e:
        logger.error(f"Failed to send signal: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
