# Temporal Sample Application — Code Agent Runbook (Python)

**Purpose:** A strict, end‑to‑end checklist and reference to ensure an agent not only writes code, but **runs it live** against a Temporal dev server and validates behavior before finishing.

---

## 0) Golden Rules (Do Not Skip)

* ✅ **You must run the app end‑to‑end**: start the Temporal dev server → start `worker.py` → run `starter.py` → (if applicable) send a **signal** → verify results → cleanly stop the worker.
* ✅ Prefer **`uv run`** for execution and **PID files** for lifecycle control.
* ✅ Fail fast: use timeouts and non‑zero exit codes if anything can’t connect or errors.

---

## 1) Repository / File Layout (required)

```
<your_app_name_here>/ (or choose an appropriate name)
  shared.py          # dataclasses and shared types
  activities.py      # activity defs only
  workflow.py        # workflow defs only
  worker.py          # long‑running worker (PID + logging)
  starter.py         # workflow starter client (timeouts + exit codes)
AGENTS.md            # this file
```

> **Imports:** Use relative imports inside `<your_app_name_here>` (e.g., `from activities import compose_greeting`). This keeps things executable via `uv run` without extra PYTHONPATH setup.

---

## 2) Prerequisites

### 2.1 UV (Python package/runtime manager)

```bash
uv --version
```

If missing:

* **macOS:** `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`
* **Windows:** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
* **Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh`

Useful checks:

```bash
uv --version
uv python list
```

### 2.2 Temporal CLI + Dev Server

```bash
temporal --version
```

If missing, install via your OS package manager or from Temporal downloads.

**Start/verify dev server:**

```bash
curl -f http://localhost:7233 > /dev/null 2>&1 && echo "Server running" || echo "Server not running"
# If not running:
temporal server start-dev
```

> Keep this running in a separate terminal while developing.

---

## 3) Project Setup (new projects)

```bash
uv init temporal-sample-app
cd temporal-sample-app
mkdir <your_app_name_here> # (or choose an appropriate name)
```

**Dependencies**

```bash
uv venv
uv add temporalio
uv add --dev pytest ruff mypy
uv pip list
```

**Recommended `pyproject.toml` bits**

```toml
[project]
name = "temporal-sample-app"
version = "0.1.0"
description = "Temporal workflow sample application"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "temporalio>=1.7.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "ruff>=0.1.0", "mypy>=1.0.0"]

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
```

> **PEP 723** (optional): you may use inline `# /// script` blocks in `worker.py`/`starter.py` with `temporalio>=1.7.0` to make files directly runnable via `uv run`.

---

## 4) End‑to‑End Execution (MANDATORY)

> Follow these exact steps. Do not stop after static checks or imports.

### 4.1 Start/ensure Temporal dev server is running

```bash
curl -f http://localhost:7233 > /dev/null 2>&1 || temporal server start-dev &
```

### 4.2 Start the Worker

```bash
cd <your_app_name_here> # or your app name
uv run worker.py > worker.log 2>&1 &
WORKER_PID=$!; echo $WORKER_PID > worker.pid
sleep 3
ps -p $WORKER_PID > /dev/null || { echo "ERROR: Worker failed to start"; exit 1; }
```

> The worker must log a ready message (e.g., “Worker started … polling …”). Check `worker.log` if unsure.

### 4.3 Run the Workflow Starter (with timeout)

```bash
# Example invocation; customize argument as needed
uv run starter.py "CodeAgent"
```

**Expected:** the starter prints `Result: Hello, CodeAgent!` and exits with code 0.

### 4.4 (Optional but Recommended) Send a Signal, Then Verify

To make signaling testable, add a signal to your workflow (see §6). Once added, either:

* **Python client snippet** (preferred during dev):

  ```bash
  uv run - <<'PY'
  import asyncio, sys
  from temporalio.client import Client
  async def main():
      client = await Client.connect("localhost:7233")
      handle = client.get_workflow_handle("hello-activity-workflow-CodeAgent")
      await handle.signal("update_greeting", "Howdy")
      print("Signal sent")
  asyncio.run(main())
  PY
  ```
* Or execute another workflow that exercises the signaled behavior.

Then **query** or run another execution to verify the changed behavior (see §6 for a query example).

### 4.5 Cleanly Stop the Worker

```bash
kill $(cat worker.pid)
wait $(cat worker.pid) 2>/dev/null || true
rm -f worker.pid
```

> **Success criteria:** server reachable, worker stayed alive and polled, starter completed, optional signal processed, worker shut down cleanly.

---

## 5) One‑Command E2E Script (copy/paste)

```bash
#!/usr/bin/env bash
set -euo pipefail
cd <your_app_name_here> # or your app name

if ! curl -fsS http://localhost:7233 >/dev/null; then
  echo "Starting Temporal dev server..."
  temporal server start-dev &
  sleep 5
fi

echo "Starting worker..."
uv run worker.py > worker.log 2>&1 &
WORKER_PID=$!; echo $WORKER_PID > worker.pid
sleep 3
ps -p $WORKER_PID >/dev/null || { echo "Worker failed to start"; tail -n 200 worker.log; exit 1; }

echo "Running starter..."
uv run starter.py "CodeAgent"

# Optional signal block (requires §6 changes to workflow)
# python - <<'PY'
# import asyncio
# from temporalio.client import Client
# async def main():
#   c = await Client.connect("localhost:7233")
#   h = c.get_workflow_handle("hello-activity-workflow-CodeAgent")
#   await h.signal("update_greeting", "Howdy")
#   print("Signal sent")
# asyncio.run(main())
# PY

echo "Shutting down worker..."
kill "$WORKER_PID"
wait "$WORKER_PID" 2>/dev/null || true
rm -f worker.pid

echo "E2E: OK"
```

---

## 6) Reference Code (minimal; add signals/queries for live validation)

### 6.1 `shared.py`

```python
from dataclasses import dataclass

@dataclass
class ComposeGreetingInput:
    greeting: str
    name: str
```

### 6.2 `activities.py`

```python
from temporalio import activity
from shared import ComposeGreetingInput

@activity.defn
def compose_greeting(input: ComposeGreetingInput) -> str:
    activity.logger.info("Running activity with parameter %s" % input)
    return f"{input.greeting}, {input.name}!"
```

### 6.3 `workflow.py` (with **signal** + **query**)

```python
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from activities import compose_greeting
from shared import ComposeGreetingInput

@workflow.defn
class GreetingWorkflow:
    def __init__(self) -> None:
        self._greeting = "Hello"

    @workflow.run
    async def run(self, name: str) -> str:
        workflow.logger.info("Running workflow with parameter %s" % name)
        default_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=100),
            maximum_attempts=0,
        )
        return await workflow.execute_activity(
            compose_greeting,
            ComposeGreetingInput(self._greeting, name),
            schedule_to_close_timeout=timedelta(seconds=20),
            retry_policy=default_retry_policy,
        )

    @workflow.signal
    def update_greeting(self, new_greeting: str) -> None:
        self._greeting = new_greeting

    @workflow.query
    def current_greeting(self) -> str:
        return self._greeting
```

### 6.4 `worker.py`

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["temporalio>=1.7.0"]
# ///
import asyncio, logging, os
from concurrent.futures import ThreadPoolExecutor
from temporalio.client import Client
from temporalio.worker import Worker
from activities import compose_greeting
from workflow import GreetingWorkflow

async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    with open("worker.pid", "w") as f:
        f.write(str(os.getpid()))
    logger.info("Worker starting")
    client = await Client.connect("localhost:7233")
    async with Worker(
        client,
        task_queue="hello-activity-task-queue",
        workflows=[GreetingWorkflow],
        activities=[compose_greeting],
        activity_executor=ThreadPoolExecutor(5),
    ):
        logger.info("Worker ready — polling: hello-activity-task-queue")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Worker shutting down…")

if __name__ == "__main__":
    asyncio.run(main())
```

### 6.5 `starter.py`

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["temporalio>=1.7.0"]
# ///
import asyncio, logging, sys
from temporalio.client import Client
from workflow import GreetingWorkflow

async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    name = sys.argv[1] if len(sys.argv) > 1 else "World"
    try:
        client = await Client.connect("localhost:7233")
        logger.info(f"Starting workflow for name: {name}")
        result = await client.execute_workflow(
            GreetingWorkflow.run,
            name,
            id=f"hello-activity-workflow-{name}",
            task_queue="hello-activity-task-queue",
        )
        print(f"Result: {result}")
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

**Validate signal & query (after a run):**

```bash
# Send a signal to update greeting
python - <<'PY'
import asyncio
from temporalio.client import Client
async def main():
  c = await Client.connect("localhost:7233")
  h = c.get_workflow_handle("hello-activity-workflow-CodeAgent")
  await h.signal("update_greeting", "Howdy")
  print("Signal sent")
asyncio.run(main())
PY

# Query current greeting
python - <<'PY'
import asyncio
from temporalio.client import Client
async def main():
  c = await Client.connect("localhost:7233")
  h = c.get_workflow_handle("hello-activity-workflow-CodeAgent")
  print(await h.query("current_greeting"))
asyncio.run(main())
PY
```

---

## 7) Development Loop

1. **Stop existing worker**

   ```bash
   [ -f worker.pid ] && kill $(cat worker.pid) || true
   rm -f worker.pid
   pkill -f "worker.py" || true
   ```
2. **Start fresh worker**

   ```bash
   uv run worker.py &
   echo $! > worker.pid
   sleep 3
   ps -p $(cat worker.pid) >/dev/null || { echo "Worker failed"; exit 1; }
   ```
3. **Run starter + verify output**

   ```bash
   uv run starter.py "TestUpdatedCode"
   ```
4. **Clean up**

   ```bash
   kill $(cat worker.pid); wait $(cat worker.pid) 2>/dev/null || true; rm -f worker.pid
   ```

---

## 8) Troubleshooting Quick Hits

* **Worker won’t connect:** ensure dev server at `localhost:7233` is up.
* **Hangs:** add timeouts; check `worker.log`; confirm PID is alive and polling.
* **Dependency woes:** `uv pip check`, `uv sync --reinstall`, `uv lock --upgrade`.
* **CI:** use `uv sync --frozen` for reproducible installs; cache UV downloads.

---

## 9) Success Checklist (agent must confirm)

* [ ] Temporal dev server reachable on `localhost:7233`.
* [ ] Worker started, wrote `worker.pid`, and is polling the task queue.
* [ ] Starter completed and printed the expected result.
* [ ] (If applicable) Signal sent and verified via query or follow‑up run.
* [ ] Worker shutdown was clean and PID file removed.

> Only mark complete if you executed every step above.
