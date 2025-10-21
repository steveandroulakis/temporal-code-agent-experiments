# Temporal Order Management Workflow Demo

A complete Temporal Python SDK demonstration showcasing an order management workflow with:

- **Mock Activities**: Payment processing, inventory reservation, and delivery initiation
- **Signal-based Human-in-the-Loop Approval**: Orders over $1000 require manual approval
- **Compensation Logic**: Automatic rollback of completed steps if any step fails
- **Queries**: Check workflow status and approval requirements in real-time

## Architecture

### Files Structure

```
order_management/
├── shared.py          # Dataclasses for Order, OrderItem, and result types
├── activities.py      # Activity definitions (payment, inventory, delivery)
├── workflow.py        # OrderWorkflow with approval logic
├── worker.py          # Long-running worker process
├── starter.py         # Workflow starter client
├── test_approval.py   # Test script for approval workflow
└── README.md          # This file
```

### Workflow Logic

The `OrderWorkflow` follows these steps:

1. **Check Order Total**: If order > $1000, wait for approval signal
2. **Wait for Approval** (if needed): 5-minute timeout with signal-based approval
3. **Reserve Inventory**: Mock inventory reservation
4. **Process Payment**: Mock payment processing
5. **Initiate Delivery**: Mock delivery scheduling

If any step fails, compensation activities run to rollback previous steps:
- Payment failure → Release inventory
- Delivery failure → Refund payment + Release inventory

## Prerequisites

1. **UV (Python package manager)**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv --version
   ```

2. **Temporal CLI**
   ```bash
   # Linux
   curl -sSf "https://temporal.download/cli/archive/latest?platform=linux&arch=amd64" | tar -xz
   sudo mv temporal /usr/local/bin/

   # macOS
   brew install temporal

   temporal --version
   ```

## Quick Start

### 1. Start Temporal Dev Server

```bash
temporal server start-dev
```

Keep this running in a separate terminal.

### 2. Install Dependencies

```bash
# From the project root
uv venv
uv add temporalio
```

### 3. Start the Worker

```bash
cd order_management
uv run worker.py > worker.log 2>&1 &
echo $! > worker.pid
```

Verify worker is running:
```bash
tail -f worker.log
```

You should see:
```
Worker ready and polling task queue: order-management-task-queue
```

### 4. Run Test Workflows

**Test 1: Order Under $1000 (No Approval Required)**

```bash
uv run starter.py 500
```

Expected output:
```
Result: Order processed successfully
Status: completed
Transaction ID: TXN-XXXXXXXX
Reservation ID: RES-XXXXXXXX
Tracking Number: TRACK-XXXXXXXXXXXX
```

**Test 2: Order Over $1000 (With Approval)**

```bash
uv run test_approval.py
```

Expected output:
```
Workflow requires approval: True
Sending approval signal...
Approval signal sent!
Result: Order processed successfully
```

### 5. Verify with Temporal CLI

List recent workflows:
```bash
temporal workflow list -n default --limit 5
```

Show workflow details:
```bash
temporal workflow show --workflow-id order-workflow-ORDER-1500
```

### 6. Stop the Worker

```bash
kill $(cat worker.pid)
rm worker.pid
```

## Manual Testing: Sending Signals

You can manually test the approval workflow using Python snippets:

### Start a workflow that needs approval:

```bash
uv run - <<'PY'
import asyncio
from temporalio.client import Client
from workflow import OrderWorkflow
from shared import Order, OrderItem

async def main():
    client = await Client.connect("localhost:7233")

    order = Order(
        order_id="ORDER-2000",
        customer_id="CUST-99999",
        items=[
            OrderItem(product_id="PROD-001", quantity=2, price=1000.0)
        ],
        total_amount=2000.0,
    )

    handle = await client.start_workflow(
        OrderWorkflow.run,
        order,
        id="order-workflow-ORDER-2000",
        task_queue="order-management-task-queue",
    )
    print(f"Started workflow: {handle.id}")

asyncio.run(main())
PY
```

### Query if approval is required:

```bash
uv run - <<'PY'
import asyncio
from temporalio.client import Client
from workflow import OrderWorkflow

async def main():
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle("order-workflow-ORDER-2000")
    requires_approval = await handle.query(OrderWorkflow.requires_approval)
    print(f"Requires approval: {requires_approval}")

asyncio.run(main())
PY
```

### Send approval signal:

```bash
uv run - <<'PY'
import asyncio
from temporalio.client import Client
from workflow import OrderWorkflow

async def main():
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle("order-workflow-ORDER-2000")
    await handle.signal(OrderWorkflow.approve_order, True)
    print("Approval sent!")

    # Wait for result
    result = await handle.result()
    print(f"Result: {result}")

asyncio.run(main())
PY
```

### Reject an order:

```bash
uv run - <<'PY'
import asyncio
from temporalio.client import Client
from workflow import OrderWorkflow

async def main():
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle("order-workflow-ORDER-2000")
    await handle.signal(OrderWorkflow.approve_order, False)
    print("Order rejected!")

asyncio.run(main())
PY
```

## Key Concepts Demonstrated

### 1. Activities
Activities are units of work that can fail and be retried:
- `process_payment()` - Simulates payment processing
- `reserve_inventory()` - Simulates inventory reservation
- `initiate_delivery()` - Simulates delivery scheduling
- `refund_payment()` - Compensation activity
- `release_inventory()` - Compensation activity

### 2. Workflows
The `OrderWorkflow` orchestrates activities and implements business logic:
- Conditional logic (approval for orders > $1000)
- Signal handling (`approve_order`)
- Queries (`get_status`, `requires_approval`)
- Error handling and compensation

### 3. Signals
Signals allow external events to interact with running workflows:
```python
@workflow.signal
def approve_order(self, approved: bool) -> None:
    self._approval_status = approved
    self._approval_received = True
```

### 4. Queries
Queries allow reading workflow state without modifying it:
```python
@workflow.query
def get_status(self) -> str:
    return self._order_status
```

### 5. Wait Conditions
Workflows can wait for conditions with timeouts:
```python
await workflow.wait_condition(
    lambda: self._approval_received,
    timeout=timedelta(minutes=5)
)
```

## Troubleshooting

### Worker won't connect
Ensure Temporal dev server is running:
```bash
temporal operator namespace describe default
```

### Workflow appears stuck
Check if it's waiting for approval:
```bash
temporal workflow show --workflow-id order-workflow-ORDER-XXXX
```

Look for `TimerStarted` and `WorkflowExecutionSignaled` events.

### View worker logs
```bash
tail -f worker.log
```

### Kill stuck worker
```bash
pkill -f "worker.py"
rm -f worker.pid
```

## Next Steps

Ideas to extend this demo:

1. **Add more activities**: Shipping notifications, inventory updates
2. **Implement compensation saga**: More complex rollback scenarios
3. **Add child workflows**: Split complex orders into sub-orders
4. **Implement cron workflows**: Periodic order batch processing
5. **Add search attributes**: Enable advanced workflow queries
6. **Implement side effects**: For non-deterministic operations

## Resources

- [Temporal Python SDK Documentation](https://docs.temporal.io/dev-guide/python)
- [Temporal Samples Repository](https://github.com/temporalio/samples-python)
- [Temporal Dev Server Documentation](https://docs.temporal.io/cli/server)
