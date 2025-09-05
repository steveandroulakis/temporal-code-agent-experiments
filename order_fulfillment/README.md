# Order Fulfillment Sample (Python)

This sample demonstrates a simple order fulfillment workflow using [Temporal](https://temporal.io/) and Python. An order is processed through three activities executed in sequence:

1. `process_payment`
2. `reserve_inventory`
3. `deliver_order`

The workflow pauses after processing the payment and waits for a human to approve the order via a signal.

## Prerequisites

- [Temporal CLI](https://temporal.io) installed and a development server running:
  ```bash
  temporal server start-dev
  ```
- [uv](https://github.com/astral-sh/uv) package manager
- Python 3.11+

## Installation

```bash
uv venv              # create virtual environment
uv sync              # install dependencies from pyproject.toml
```

## Running the Sample

In separate terminals:

1. **Start the worker**
   ```bash
   uv run worker.py
   ```
2. **Start a workflow execution**
   ```bash
   uv run starter.py
   ```
   The starter prints the workflow result when it completes.
3. **Approve the order**
   The workflow waits up to 30 seconds for approval. Send a signal using the Temporal CLI (replace WORKFLOW_ID with the printed id):
   ```bash
   temporal workflow signal --workflow-id WORKFLOW_ID --name approve_order
   ```
   If no signal is sent, the workflow fails with `order expired`.

## Scenarios

- **Happy path** – run worker and starter, then approve the order.
- **API downtime** – uncomment the `ConnectionError` line in `activities.py` to simulate an inventory service outage.
- **Invalid order** – change `cc_expiry` in `starter.py` to `12/23` to trigger a payment failure.
- **Human in the loop** – the workflow waits for the `approve_order` signal before reserving inventory.
- **Approve or expire order** – send the signal to approve, or wait 30 seconds to see the workflow fail with `order expired`.
- **Bug in workflow** – uncomment the `raise RuntimeError("workflow bug!")` line in `workflow.py` to simulate a workflow code bug.

## Development

Run linting, type checking, and tests:

```bash
uv run ruff check .
uv run mypy .
uv run pytest
```
