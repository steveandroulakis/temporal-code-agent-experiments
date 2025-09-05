# Python Order Fulfilment Sample

This project demonstrates a Temporal application that fulfils an order using
three activities executed in sequence:

1. `process_payment`
2. `reserve_inventory`
3. `deliver_order`

The workflow waits for a human approval signal before delivery. If approval is
not received within 30 seconds the order expires.

## Files

All application code lives in `order_application/`:

- `shared.py` – dataclasses for the order information
- `activities.py` – implementations of `process_payment`,
  `reserve_inventory`, and `deliver_order`
- `workflow.py` – `OrderWorkflow` definition with an `approve_order` signal
- `worker.py` – long‑running worker process
- `starter.py` – starts an `OrderWorkflow` execution
- `approve.py` – sends the `approve_order` signal to a workflow

## Running the sample

1. **Start the Temporal development server** (if not already running):
   ```bash
   temporal server start-dev &
   ```
2. **Start the worker**:
   ```bash
   cd order_application
   ./worker.py &
   ```
3. **Start a workflow**:
   ```bash
   ./starter.py 12/30
   ```
   The command prints the workflow ID. The workflow now waits for approval.
4. **Approve the order**:
   ```bash
   ./approve.py <workflow-id>
   ```
   The workflow completes after the approval signal is received.
5. **Cleanup** – stop the worker process when finished.

## Scenarios

- **Happy path** – run the commands above and approve the order.
- **API downtime** – uncomment the request in `reserve_inventory` to simulate a
  failing external service.
- **Invalid order** – start the workflow with an expired card:
  `./starter.py 12/23`. The `process_payment` activity fails.
- **Human in the loop** – start the workflow and send the approval signal from
  `approve.py`.
- **Approve or expire** – if no approval is sent within 30 seconds the workflow
  raises `Order approval timed out`.
- **Bug in workflow** – add `raise RuntimeError("workflow bug!")` inside
  `OrderWorkflow.run` to see workflow failure handling.

## Notes

All scripts use [uv](https://github.com/astral-sh/uv) shebangs to manage
runtime dependencies automatically.
