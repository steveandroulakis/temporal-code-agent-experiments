# Temporal Order Fulfillment Sample (Python)

This project reimplements the TypeScript order fulfillment sample entirely in Python using the Temporal SDK.
It demonstrates a workflow that processes a payment, reserves inventory, and delivers an order while
covering real-world failure scenarios such as API downtime, invalid payments, human approvals, and
unhandled workflow bugs.

## Project Layout

```
order_fulfillment/
  activities.py        # Activity implementations: process payment, reserve inventory, deliver order
  shared.py            # Dataclasses shared between the workflow, activities, and clients
  starter.py           # Convenience script for starting a workflow execution
  signals.py           # Utility for sending approval signals and querying a running workflow
  worker.py            # Worker hosting the workflow and activities
  workflow.py          # Order workflow definition
  pyproject.toml       # Project configuration (managed by uv)
```

## Prerequisites

* [Temporal CLI](https://docs.temporal.io/cli) installed locally and available on your path.
* Python 3.12+ — this project uses [`uv`](https://docs.astral.sh/uv/) to manage the virtual environment.
* A Temporal dev server running on `localhost:7233`.

Start the Temporal dev server (leave it running in its own terminal):

```bash
temporal operator namespace describe default >/dev/null 2>&1 || temporal server start-dev
```

Install dependencies (only needs to be done once):

```bash
uv sync
```

## Running the Sample

In one terminal, launch the worker:

```bash
cd order_fulfillment
uv run worker.py &
# Optionally confirm the PID
cat worker.pid
```

In a different terminal, start a workflow execution:

```bash
cd order_fulfillment
uv run starter.py "Ada Lovelace"
```

The starter prints the workflow ID so that you can send signals or query it.
Use `uv run signals.py approve <workflow-id>` to approve the order or
`uv run signals.py status <workflow-id>` to view the current status.

When finished, stop the worker:

```bash
kill "$(cat worker.pid)"; wait "$(cat worker.pid)" 2>/dev/null || true
rm -f worker.pid
```

## Demo Scenarios

The Python implementation mirrors the TypeScript sample behaviour. Each scenario below uses the commands above.

### 1. Happy Path

1. Start the worker and the starter (`uv run starter.py`).
2. Approve the order before the timeout expires:
   ```bash
   uv run signals.py approve <workflow-id> --note "Approved instantly"
   ```
3. Query the final result or wait using `--wait-result` when starting the workflow.

### 2. API Downtime Simulation

Run the starter with the downtime flag to have `reserve_inventory` raise an `ApplicationError`:

```bash
uv run starter.py "Outage Test" --simulate-inventory-downtime --wait-result
```

The workflow fails during the inventory reservation step and the worker logs include the failure details.

### 3. Invalid Order Troubleshooting

Specify an expired credit card to reproduce a failed payment check (for example `12/23`):

```bash
uv run starter.py "Invalid Payment" --card-expiry 12/23 --wait-result
```

The `process_payment` activity raises `PaymentValidationError`, showing how Temporal preserves the failure for analysis.

### 4. Human-in-the-Loop Approval

1. Start the workflow without `--wait-result` so it pauses at the approval step.
2. Inspect the status:
   ```bash
   uv run signals.py status <workflow-id>
   ```
3. Approve or reject the order with a note (`uv run signals.py approve ...` or `uv run signals.py reject ...`).

### 5. Auto-Expire Orders

If no approval signal arrives before the configured timeout (30 seconds by default or configured via `--approval-timeout`)
Temporal automatically expires the order:

```bash
uv run starter.py "Timeout Test" --approval-timeout 10 --wait-result
```

Wait longer than the timeout before approving. The workflow transitions to `EXPIRED` and returns without executing delivery.

### 6. Workflow Bug Recovery

Uncomment the line in `workflow.py` that raises `RuntimeError("workflow bug!")` and restart the worker. The workflow task
fails repeatedly until you comment the line back out and redeploy the worker, illustrating Temporal's resiliency to
workflow-code bugs.

## Signals and Queries Reference

* `approve` / `reject` — call the `approve_order` signal with an optional human note.
* `status` — query the current workflow status.
* `approval-message` — query the latest approval decision (or `None` if pending).

Example:

```bash
uv run signals.py approve order-123 --note "Cleared by fraud team"
uv run signals.py status order-123
uv run signals.py approval-message order-123
```

## Cleaning Up

* Stop the worker process and remove `worker.pid`.
* Shut down the Temporal dev server if you started it manually.

## Next Steps

This sample is intentionally small but it demonstrates advanced Temporal features in Python:
activity retries, typed workflow inputs/outputs, timeouts, signals, and failure handling.
Extend it by adding inventory quantity checks, shipping delays, or custom exception types tailored to your business domain.
