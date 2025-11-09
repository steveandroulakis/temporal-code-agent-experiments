"""Helper script to interact with running workflows (signals and queries)."""

from __future__ import annotations

import argparse
import asyncio

from temporalio.client import Client

from workflow import OrderWorkflow


async def handle_approve(workflow_id: str, note: str, approved: bool) -> None:
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal(OrderWorkflow.approve_order, args=[approved, note or None])
    decision = "approved" if approved else "rejected"
    print(f"Sent {decision} signal to {workflow_id} with note: {note or 'N/A'}")


async def handle_query(workflow_id: str, query: str) -> None:
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle(workflow_id)
    if query == "status":
        status = await handle.query(OrderWorkflow.current_status)
        print(f"Workflow {workflow_id} status: {status}")
    elif query == "approval-message":
        message = await handle.query(OrderWorkflow.approval_message)
        print(f"Workflow {workflow_id} approval message: {message}")
    else:  # pragma: no cover - defensive guard
        raise ValueError(f"Unknown query {query}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Signal or query a running order workflow")
    sub = parser.add_subparsers(dest="command", required=True)

    approve_cmd = sub.add_parser("approve", help="Approve the order")
    approve_cmd.add_argument("workflow_id")
    approve_cmd.add_argument("--note", default="Approved by support")

    reject_cmd = sub.add_parser("reject", help="Reject the order")
    reject_cmd.add_argument("workflow_id")
    reject_cmd.add_argument("--note", default="Rejected by support")

    status_cmd = sub.add_parser("status", help="Query the current workflow status")
    status_cmd.add_argument("workflow_id")

    message_cmd = sub.add_parser("approval-message", help="Query the approval message")
    message_cmd.add_argument("workflow_id")

    args = parser.parse_args()

    if args.command == "approve":
        await handle_approve(args.workflow_id, args.note, True)
    elif args.command == "reject":
        await handle_approve(args.workflow_id, args.note, False)
    elif args.command == "status":
        await handle_query(args.workflow_id, "status")
    elif args.command == "approval-message":
        await handle_query(args.workflow_id, "approval-message")


if __name__ == "__main__":
    asyncio.run(main())
