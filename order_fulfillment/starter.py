"""Utility script to kick off the order fulfillment workflow."""

from __future__ import annotations

import argparse
import asyncio
import logging
import uuid

from temporalio.client import Client

from shared import Order, OrderItem, PaymentDetails
from workflow import OrderWorkflow, TASK_QUEUE


def parse_expiry(value: str) -> tuple[int, int]:
    try:
        month_str, year_str = value.split("/")
        month = int(month_str)
        year = int(year_str)
    except ValueError as exc:  # pragma: no cover - defensive parsing guard
        raise argparse.ArgumentTypeError("Expiry must be MM/YY") from exc

    if not 1 <= month <= 12:
        raise argparse.ArgumentTypeError("Expiry month must be between 1 and 12")
    if year < 100:
        year += 2000
    return month, year


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start the order fulfillment workflow")
    parser.add_argument("customer_name", nargs="?", default="Temporal Customer")
    parser.add_argument("--workflow-id", help="Custom workflow ID. Defaults to a generated UUID.")
    parser.add_argument(
        "--email",
        default="customer@example.com",
        help="Customer email used for notifications.",
    )
    parser.add_argument(
        "--card-number",
        default="4111111111111111",
        help="Credit card number used for the demo payment.",
    )
    parser.add_argument(
        "--card-expiry",
        default="12/30",
        type=parse_expiry,
        help="Card expiry in MM/YY format (set to 12/23 to simulate a decline).",
    )
    parser.add_argument(
        "--approval-timeout",
        type=int,
        default=30,
        help="Seconds the workflow will wait for the human approval signal before expiring.",
    )
    parser.add_argument(
        "--simulate-inventory-downtime",
        action="store_true",
        help="Fail the reserve inventory activity to mimic an API outage.",
    )
    parser.add_argument(
        "--wait-result",
        action="store_true",
        help="Wait for the workflow result instead of returning immediately.",
    )
    return parser


async def main() -> None:
    args = build_arg_parser().parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger = logging.getLogger("order_fulfillment.starter")

    workflow_id = args.workflow_id or f"order-{uuid.uuid4().hex}"
    expiry_month, expiry_year = args.card_expiry

    order = Order(
        order_id=workflow_id,
        email=args.email,
        payment=PaymentDetails(
            card_number=args.card_number,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            cardholder=args.customer_name,
        ),
        items=[
            OrderItem(sku="temporal-tshirt", quantity=1),
            OrderItem(sku="temporal-mug", quantity=2),
        ],
        simulate_inventory_downtime=args.simulate_inventory_downtime,
        approval_timeout_seconds=args.approval_timeout,
    )

    client = await Client.connect("localhost:7233")
    logger.info("Starting workflow %s on queue %s", workflow_id, TASK_QUEUE)

    handle = await client.start_workflow(
        OrderWorkflow.run,
        order,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    print(f"Started workflow {workflow_id} (run ID: {handle.first_execution_run_id})")
    if args.wait_result:
        result = await handle.result()
        print("Workflow completed:")
        print(result)
    else:
        print("Use `uv run signals.py approve <workflow-id>` to approve or reject the order.")


if __name__ == "__main__":
    asyncio.run(main())
