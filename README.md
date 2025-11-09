# Temporal Order Fulfillment Sample (Python)

This sample demonstrates a simple order fulfillment workflow implemented in
Python using [Temporal](https://temporal.io). The workflow runs three
activities in sequence:

1. `process_payment`
2. `reserve_inventory`
3. `deliver_order`

The workflow waits for a human approval signal before delivery and can also
expire if no approval is received within 30 seconds.

## Prerequisites

* [UV](https://docs.astral.sh/uv/) installed
* Temporal CLI (`temporal`) available
* Python 3.11+

## Install dependencies

```bash
uv venv
uv add temporalio
uv add --dev pytest ruff mypy
```

## Running the sample

Start the Temporal dev server (if not already running):

```bash
temporal server start-dev
```

In a new terminal, start the worker:

```bash
uv run order_fulfillment/worker.py &
echo $! > worker.pid
```

Start the workflow:

```bash
uv run order_fulfillment/starter.py
```

In another terminal, approve the order (human in the loop):

```bash
python - <<'PY'
import asyncio
from temporalio.client import Client
async def main():
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle("order-<ID>" )  # replace with ID from starter output
    await handle.signal("approve_order")
asyncio.run(main())
PY
```

When the signal is received, the workflow finishes and prints the result.
Kill the worker when done:

```bash
kill $(cat worker.pid); rm worker.pid
```

## Scenarios

* **Happy path** – run as shown above and send the approval signal.
* **API downtime** – set `INVENTORY_DOWN=1` in the worker's environment to
  simulate a failing inventory service.
* **Invalid order troubleshooting** – run the starter with an expired card:
  `uv run order_fulfillment/starter.py --expiry 12/23`.
* **Human in the loop** – start the workflow and send the `approve_order`
  signal as shown above.
* **Approve or expire order** – either send the approval signal or let the
  30‑second timer expire to see the order expire.
* **Bug in workflow** – uncomment the `raise RuntimeError("workflow bug!")`
  line in `workflow.py` and rerun to see the workflow fail.
