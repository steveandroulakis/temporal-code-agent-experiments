# Order Management Workflow - Temporal Python SDK Demo

A complete demonstration of an order processing workflow using Temporal Python SDK, featuring:

- **Payment Processing** - Mock payment activity
- **Inventory Reservation** - Mock inventory management
- **Delivery Arrangement** - Mock shipping coordination
- **Human-in-the-Loop Approval** - Signal-based approval for orders over $1000

## Architecture

```
Order Workflow
├── Check if order > $1000
│   ├── Yes → Wait for approval signal (timeout: 5 minutes)
│   │   ├── Approved → Continue
│   │   └── Rejected → Cancel order
│   └── No → Continue
├── Process Payment (Activity)
├── Reserve Inventory (Activity)
├── Arrange Delivery (Activity)
└── Send Confirmation Email (Activity)
```

## Project Structure

```
order_workflow/
├── shared.py           # Data classes and types
├── activities.py       # Activity definitions (payment, inventory, delivery)
├── workflow.py         # Order workflow with approval logic
├── worker.py           # Temporal worker
├── starter.py          # Workflow starter client
├── approval_sender.py  # Signal sender for approvals/rejections
└── README.md          # This file
```

## Prerequisites

### 1. Install UV (Python Package Manager)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
```

### 2. Install Temporal CLI

**macOS:**
```bash
brew install temporal
```

**Linux:**
```bash
curl -L -o temporal.tar.gz "https://temporal.download/cli/archive/latest?platform=linux&arch=amd64"
tar -xzf temporal.tar.gz
sudo mv temporal /usr/local/bin/
```

**Windows:**
Download from: https://temporal.download/cli/archive/latest?platform=windows&arch=amd64

Verify installation:
```bash
temporal --version
```

## Setup

### 1. Install Python Dependencies

The project uses UV with inline script dependencies. No separate installation needed!
Each script file includes its dependencies in the header.

### 2. Start Temporal Dev Server

In a separate terminal:

```bash
temporal server start-dev
```

This starts a local Temporal server at `localhost:7233` with a web UI at `http://localhost:8233`.

## Running the Demo

### Scenario 1: Small Order (Under $1000) - No Approval Required

1. **Start the worker** (in terminal 1):
```bash
cd order_workflow
uv run worker.py
```

2. **Start a small order** (in terminal 2):
```bash
cd order_workflow
uv run starter.py small
```

**Expected Output:**
```
Starting order workflow for Alice Smith, order ID: ORD-001, total: $89.95
Waiting for workflow to complete...

======================================================================
Order Result: COMPLETED
======================================================================
Order ID: ORD-001
Status: completed
Message: Order processed successfully

Payment:
  Transaction ID: TXN-XXXXXXXXXXXX
  Payment of $89.95 processed successfully

Inventory:
  Reservation ID: RES-XXXXXXXXXXXX
  Reserved 2 item(s) successfully

Delivery:
  Tracking Number: TRACK-XXXXXXXXXXXXXXXX
  Estimated Delivery: 2025-10-24
  Delivery scheduled to 123 Main St, Springfield, IL 62701
======================================================================
```

### Scenario 2: Large Order (Over $1000) - Requires Approval

1. **Start the worker** (if not already running):
```bash
cd order_workflow
uv run worker.py
```

2. **Start a large order** (in terminal 2):
```bash
cd order_workflow
uv run starter.py large
```

**Expected Output:**
```
======================================================================
⚠️  ORDER REQUIRES APPROVAL
======================================================================
Order ID: ORD-002
Amount: $1899.97

To approve this order, run:
  uv run approval_sender.py ORD-002 approve

To reject this order, run:
  uv run approval_sender.py ORD-002 reject
======================================================================

Workflow started and waiting for approval...
Workflow will wait up to 5 minutes for approval signal.
```

3. **Approve the order** (in terminal 3, within 5 minutes):
```bash
cd order_workflow
uv run approval_sender.py ORD-002 approve "High-value customer - approved"
```

**Expected Output:**
```
======================================================================
✅ ORDER APPROVED
======================================================================
Order ID: ORD-002
Reason: High-value customer - approved
======================================================================
The workflow will now proceed with payment and fulfillment.

Workflow completed with status: completed
Message: Order processed successfully
```

**OR reject the order:**
```bash
cd order_workflow
uv run approval_sender.py ORD-002 reject "Insufficient credit check"
```

## Development Workflow

### Clean Stop and Restart

```bash
# Stop worker
pkill -f worker.py
rm -f worker.pid

# Start fresh
cd order_workflow
uv run worker.py > worker.log 2>&1 &
echo $! > worker.pid
```

### Check Worker Logs

```bash
tail -f worker.log
```

### View Workflow History

```bash
# List all workflows
temporal workflow list

# Show specific workflow details
temporal workflow show --workflow-id order-workflow-ORD-001

# Query approval status (while running)
temporal workflow query \
  --workflow-id order-workflow-ORD-002 \
  --type get_approval_status
```

## Testing Both Scenarios End-to-End

Here's a complete test script:

```bash
#!/bin/bash
set -e

echo "🚀 Starting Order Workflow Demo..."

# Ensure Temporal server is running
if ! temporal operator namespace describe default >/dev/null 2>&1; then
  echo "❌ Temporal server not running. Start it with: temporal server start-dev"
  exit 1
fi

cd order_workflow

# Clean up any existing worker
pkill -f worker.py || true
rm -f worker.pid

# Start worker
echo "📦 Starting worker..."
uv run worker.py > worker.log 2>&1 &
WORKER_PID=$!
echo $WORKER_PID > worker.pid
sleep 3

# Verify worker is running
if ! ps -p $WORKER_PID > /dev/null; then
  echo "❌ Worker failed to start"
  tail -n 50 worker.log
  exit 1
fi

echo "✅ Worker started (PID: $WORKER_PID)"

# Test 1: Small order (no approval needed)
echo ""
echo "📋 Test 1: Processing small order (no approval required)..."
uv run starter.py small
sleep 2

# Test 2: Large order with approval
echo ""
echo "📋 Test 2: Starting large order (requires approval)..."
uv run starter.py large &
STARTER_PID=$!
sleep 3

echo "📨 Sending approval signal..."
uv run approval_sender.py ORD-002 approve "Automated test approval"
sleep 5

# Check workflow completion
echo ""
echo "🔍 Verifying workflows..."
temporal workflow list --limit 5

# Cleanup
echo ""
echo "🧹 Cleaning up..."
kill $WORKER_PID
wait $WORKER_PID 2>/dev/null || true
rm -f worker.pid

echo "✅ Demo completed successfully!"
```

## Key Features Demonstrated

1. **Workflow Definition** (`workflow.py`)
   - Durable execution with retries
   - Conditional logic (approval for high-value orders)
   - Signal handling for human-in-the-loop
   - Query support for workflow state

2. **Activities** (`activities.py`)
   - Payment processing
   - Inventory management
   - Delivery coordination
   - Email notifications
   - Proper logging and error handling

3. **Signals** (workflow.py)
   - `approve_order` - Approve a pending order
   - `reject_order` - Reject a pending order

4. **Queries** (workflow.py)
   - `get_approval_status` - Check approval status
   - `get_approval_reason` - Get approval/rejection reason

5. **Timeouts**
   - Approval wait: 5 minutes
   - Activity execution: 30 seconds per activity

## Temporal Web UI

Visit http://localhost:8233 to:
- View running workflows
- Inspect workflow history
- Monitor activity executions
- See signal and query events

## Customization

### Modify Approval Threshold

Edit `shared.py`:
```python
@property
def requires_approval(self) -> bool:
    return self.total_amount > 2000.0  # Change threshold
```

### Adjust Approval Timeout

Edit `workflow.py`:
```python
await workflow.wait_condition(
    lambda: self._approval_status != "pending",
    timeout=timedelta(minutes=10),  # Change timeout
)
```

### Add More Activities

1. Define activity in `activities.py`
2. Add to workflow execution in `workflow.py`
3. Register in worker in `worker.py`

## Troubleshooting

**Worker won't connect:**
- Ensure Temporal dev server is running: `temporal server start-dev`
- Check server is on `localhost:7233`

**Workflow hangs:**
- Check worker logs: `tail -f worker.log`
- Verify worker is polling: Look for "Worker ready — polling"
- Check workflow status: `temporal workflow list`

**Approval timeout:**
- Default is 5 minutes
- Send approval before timeout expires
- Or increase timeout in `workflow.py`

**Dependencies issues:**
- Each script has inline dependencies (PEP 723)
- UV handles them automatically with `uv run`

## Learn More

- [Temporal Documentation](https://docs.temporal.io/)
- [Temporal Python SDK](https://github.com/temporalio/sdk-python)
- [Temporal Samples](https://github.com/temporalio/samples-python)
